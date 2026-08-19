// Integration test for the generated fallback catalog (F10).
//
// Launches index.js as a real MCP stdio subprocess against a fake backend
// that deliberately fails `/mcp_tools` discovery, forcing the fallback path.
// Before the fix that path exposed a hand-maintained 71-tool subset; it must
// now expose the full generated catalog and route calls correctly.
//
// No Sublime Text required — the fake backend stands in for the HTTP bridge.
//
// Run:
//   cd packages/node-proxy
//   node test_fallback_catalog.mjs

import assert from 'node:assert/strict';
import http from 'node:http';
import { readFileSync } from 'node:fs';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const CATALOG = JSON.parse(
  readFileSync(new URL('./fallback-tools.json', import.meta.url), 'utf8'),
).tools;

// Fake bridge: 404 on /mcp_tools (kills discovery), echo on POST /{tool}.
function startFakeBackend() {
  const seen = [];
  const server = http.createServer((req, res) => {
    if (req.url.startsWith('/mcp_tools')) {
      res.writeHead(404).end('no discovery for you');
      return;
    }
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      seen.push({ url: req.url, method: req.method, body });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ echo: req.url, args: body ? JSON.parse(body) : null }));
    });
  });
  return new Promise(resolve => {
    server.listen(0, '127.0.0.1', () => resolve({ server, seen, port: server.address().port }));
  });
}

async function main() {
  const { server, seen, port } = await startFakeBackend();

  const transport = new StdioClientTransport({
    command: 'node',
    args: ['index.js'],
    cwd: import.meta.dirname,
    env: { ...process.env, SUBLIME_MCP_BASE: `http://127.0.0.1:${port}` },
    stderr: 'pipe',
  });

  const client = new Client({ name: 'test-fallback-catalog', version: '1.0.0' });
  await client.connect(transport);

  try {
    const listed = await client.listTools();
    const names = new Set(listed.tools.map(t => t.name));

    assert.equal(
      names.size,
      CATALOG.length,
      `fallback exposed ${names.size} tools, expected the full generated catalog (${CATALOG.length})`,
    );
    for (const tool of CATALOG) {
      assert.ok(names.has(tool.name), `fallback is missing ${tool.name}`);
    }
    console.log('PASS: discovery failure still exposes all %d generated tools', names.size);

    // batch was the headline F10 omission: absent from the old hand-written
    // fallback, so a discovery miss removed it from the agent entirely.
    assert.ok(names.has('batch'), 'batch missing from fallback catalog');
    const result = await client.callTool({
      name: 'batch',
      arguments: { calls: [{ tool: 'get_line_count' }] },
    });
    const data = JSON.parse(result.content[0].text);
    assert.equal(data.echo, '/batch', 'batch did not route to POST /batch');
    assert.deepEqual(data.args, { calls: [{ tool: 'get_line_count' }] });
    console.log('PASS: batch routes through the fallback path with its arguments intact');

    // A no-parameter tool must still post cleanly.
    await client.callTool({ name: 'get_line_count', arguments: {} });
    assert.ok(
      seen.some(r => r.url === '/get_line_count' && r.method === 'POST'),
      'get_line_count did not POST to its tool-name alias',
    );
    console.log('PASS: no-parameter tools post to their /{name} alias');

    // Schemas must survive, not degrade to untyped passthrough.
    const openFile = listed.tools.find(t => t.name === 'open_file');
    assert.ok(openFile.inputSchema?.properties?.path, 'open_file lost its typed schema');
    console.log('PASS: generated schemas reach the client');
  } finally {
    await client.close();
    server.close();
  }
}

main()
  .then(() => {
    console.log('All tests passed.');
    process.exit(0);
  })
  .catch(err => {
    console.error('FAIL:', err);
    process.exit(1);
  });
