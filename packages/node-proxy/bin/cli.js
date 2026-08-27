#!/usr/bin/env node

const command = process.argv[2] || 'serve';

async function probe(name, httpBase, mcpUrl) {
  const report = { name, ok: false, httpBridge: null, mcp: null,
    recommendedCodexConfig: { type: 'http', url: mcpUrl } };

  try {
    const response = await fetch(new URL('/health', httpBase), { signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    report.httpBridge = await response.json();
  } catch (error) {
    report.httpBridge = { ok: false, error: error.message };
  }

  try {
    const rpc = async (id, method, params = {}) => {
      const response = await fetch(mcpUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream' },
        body: JSON.stringify({ jsonrpc: '2.0', id, method, params }),
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    };
    const initialized = await rpc(1, 'initialize', {
      protocolVersion: '2025-03-26', capabilities: {},
      clientInfo: { name: 'sublime-mcp-doctor', version: '1' },
    });
    const listed = await rpc(2, 'tools/list');
    const tools = listed?.result?.tools ?? [];
    report.mcp = {
      ok: Boolean(initialized?.result) && tools.length > 0,
      serverInfo: initialized?.result?.serverInfo ?? null,
      toolCount: tools.length,
      tools: tools.map(tool => tool.name),
    };
  } catch (error) {
    report.mcp = { ok: false, error: error.message, toolCount: 0 };
  }

  report.ok = Boolean(report.httpBridge?.ok && report.mcp?.ok);
  return report;
}

async function doctor() {
  const isWindows = process.platform === 'win32';
  const httpBase = process.env.SUBLIME_MCP_BASE ?? `http://127.0.0.1:${isWindows ? 9500 : 9501}`;
  const mcpUrl = process.env.SUBLIME_MCP_URL ?? `http://127.0.0.1:${isWindows ? 9502 : 9503}/mcp`;
  const main = await probe('sublime-mcp', httpBase, mcpUrl);
  const includeAll = process.argv.includes('--all');
  const companions = includeAll ? await Promise.all([
    probe('debugger-mcp', 'http://127.0.0.1:9515', 'http://127.0.0.1:9505/mcp'),
    probe('lsp-mcp', 'http://127.0.0.1:9516', 'http://127.0.0.1:9506/mcp'),
  ]) : [];
  const report = { ...main, companions };
  report.ok = main.ok && companions.every(item => item.ok);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  process.exitCode = report.ok ? 0 : 1;
}

if (command === 'doctor') {
  await doctor();
} else if (command === 'serve') {
  await import('../index.js');
} else {
  process.stderr.write('Usage: sublime-mcp [serve|doctor [--all]]\n');
  process.exitCode = 2;
}
