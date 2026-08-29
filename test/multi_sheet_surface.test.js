import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const sourceUrl = new URL('../packages/st-plugin/sublime_mcp.py', import.meta.url);
const fallbackUrl = new URL('../packages/node-proxy/fallback-tools.json', import.meta.url);
const pythonCatalogUrl = new URL('../packages/python-proxy/tool_catalog.py', import.meta.url);

test('multi-sheet API operations have dedicated MCP tools', async () => {
  const source = await readFile(sourceUrl, 'utf8');
  const names = [
    'get_selected_sheets',
    'get_sheet_index',
    'select_sheets',
    'focus_sheet',
    'set_sheet_index',
    'move_sheets_to_group',
    'unselect_others',
    'unselect_to_left',
    'unselect_to_right',
    'select_to_left',
    'select_to_right',
    'focus_to_left',
    'focus_to_right',
  ];

  for (const name of names) {
    assert.match(source, new RegExp(`\\("${name}",`), `${name} is missing from _MCP_TOOLS`);
  }
});

test('generated proxy catalogs include the multi-sheet tools', async () => {
  const fallback = JSON.parse(await readFile(fallbackUrl, 'utf8'));
  const pythonCatalog = await readFile(pythonCatalogUrl, 'utf8');
  const fallbackNames = new Set(fallback.tools.map(tool => tool.name));
  for (const name of [
    'get_selected_sheets',
    'select_sheets',
    'focus_sheet',
    'set_sheet_index',
    'move_sheets_to_group',
    'select_to_left',
    'focus_to_right',
  ]) {
    assert.ok(fallbackNames.has(name), `${name} is missing from the Node fallback catalog`);
    assert.match(pythonCatalog, new RegExp(`'name': '${name}'`));
  }
});

test('get_sheets exposes native group, selection, and focus metadata', async () => {
  const source = await readFile(sourceUrl, 'utf8');
  for (const field of ['group', 'index_in_group', 'is_selected', 'is_focused', 'is_active_group']) {
    assert.match(source, new RegExp(`"${field}"`), `${field} metadata is missing`);
  }
});

test('multi-sheet handlers call Sublime public sheet APIs', async () => {
  const source = await readFile(sourceUrl, 'utf8');
  for (const api of [
    'selected_sheets_in_group',
    'select_sheets',
    'focus_sheet',
    'get_sheet_index',
    'set_sheet_index',
    'move_sheets_to_group',
  ]) {
    assert.match(source, new RegExp(`\\.${api}\\(`), `${api} is not used`);
  }
});
