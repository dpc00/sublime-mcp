// Integration test for packages/node-proxy/index.js.
//
// Unlike hitting port 9500 or 9502 directly, this launches index.js as a real
// subprocess and speaks MCP over stdio — the same code path a real MCP client
// (e.g. Claude Code configured with a stdio server entry) uses. This is what
// caught the missing `_POST["/batch"]` route on the HTTP bridge: node-proxy's
// dynamic tool discovery (loadDynamicTools) picks up `batch` from /mcp_tools
// fine, but the generic passthrough posts to /batch on port 9500, which
// 404'd until that route was added to sublime_mcp.py.
//
// Prerequisites:
//   - Sublime Text running with sublime_mcp.py loaded (HTTP bridge on 9500)
//   - At least one file open in ST
//
// Run:
//   cd packages/node-proxy
//   node test_batch.mjs

import assert from 'node:assert/strict';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function main() {
  const transport = new StdioClientTransport({
    command: 'node',
    args: ['index.js'],
    cwd: import.meta.dirname,
    stderr: 'pipe',
  });

  const client = new Client({ name: 'test-batch', version: '1.0.0' });
  await client.connect(transport);

  try {
    const tools = await client.listTools();
    const names = tools.tools.map(t => t.name);
    assert.ok(names.includes('batch'), 'batch tool not discovered from backend');
    console.log('PASS: batch discovered dynamically (%d tools total)', names.length);

    const result = await client.callTool({
      name: 'batch',
      arguments: { calls: [{ tool: 'get_line_count' }, { tool: 'get_selection' }] },
    });
    const data = JSON.parse(result.content[0].text);
    assert.ok(Array.isArray(data.results), 'batch response missing results array');
    assert.equal(data.results.length, 2, 'expected 2 results');
    assert.ok('line_count' in data.results[0], 'get_line_count result missing line_count');
    assert.ok('selections' in data.results[1], 'get_selection result missing selections');
    console.log('PASS: batch call returned populated results via the real proxy subprocess');

    const failResult = await client.callTool({
      name: 'batch',
      arguments: { calls: [{ tool: 'get_line_count' }, { tool: 'no_such_tool_xyz' }] },
    });
    const failData = JSON.parse(failResult.content[0].text);
    assert.equal(failData.results.length, 2);
    assert.ok('error' in failData.results[1], 'expected error for unknown tool');
    console.log('PASS: batch partial failure does not abort the whole call');
  } finally {
    await client.close();
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
