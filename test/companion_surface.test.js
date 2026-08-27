import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const cases = [
  ['debugger', '../packages/debugger-mcp/debugger_mcp.py', [
    'debugger_get_help', 'debugger_batch', 'debugger_discover_tools',
    'debugger_open', 'debugger_get_state', 'debugger_control',
    'debugger_toggle_breakpoint',
  ]],
  ['lsp', '../packages/lsp-mcp/lsp_mcp.py', [
    'lsp_get_help', 'lsp_batch', 'lsp_discover_tools',
    'lsp_get_diagnostics', 'lsp_hover_info', 'lsp_goto_definition',
    'lsp_find_references',
  ]],
];

for (const [name, path, expected] of cases) {
  test(`${name} focused surface contains the intended seven tools`, async () => {
    const source = await readFile(new URL(path, import.meta.url), 'utf8');
    const block = source.match(/_DEFAULT_TOOL_NAMES\s*=\s*frozenset\(\{([\s\S]*?)\n\}\)/);
    assert.ok(block);
    const names = [...block[1].matchAll(/["']([^"']+)["']/g)].map(match => match[1]);
    assert.deepEqual(names, expected);
    assert.equal(new Set(names).size, 7);
  });
}
