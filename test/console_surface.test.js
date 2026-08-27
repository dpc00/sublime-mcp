import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const pluginUrl = new URL('../packages/st-plugin/sublime_mcp.py', import.meta.url);
const catalogUrl = new URL('../packages/node-proxy/fallback-tools.json', import.meta.url);

test('console capture is reload-safe and does not wrap stdout', async () => {
  const source = await readFile(pluginUrl, 'utf8');
  assert.match(source, /_CONSOLE_CAPTURE_STATE_KEY/);
  assert.match(source, /_sublime_mcp_console_capture/);
  assert.doesNotMatch(source, /sys\.stdout\.write\s*=\s*_capture_write/);
  assert.match(source, /_unwrap_legacy_console_hook/);
});

test('Windows console capture restores user-visible state', async () => {
  const source = await readFile(pluginUrl, 'utf8');
  assert.match(source, /previous_panel = snapshot\["panel"\]/);
  assert.match(source, /focus_view\(previous_view\)/);
  assert.match(source, /SetCursorPos\(cursor\.x, cursor\.y\)/);
  assert.match(source, /set_clipboard\(snapshot\["clipboard"\]\)/);
  assert.match(source, /console copy did not update the clipboard/);
});

test('fallback catalog exposes unified console modes', async () => {
  const catalog = JSON.parse(await readFile(catalogUrl, 'utf8'));
  const consoleTool = catalog.tools.find(tool => tool.name === 'get_console');
  assert.ok(consoleTool);
  assert.deepEqual(
    consoleTool.inputSchema.properties.mode.enum,
    ['auto', 'visible', 'captured'],
  );
});
