import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

test('focused surface contains seven unique tools', async () => {
  const source = await readFile(new URL('../packages/node-proxy/index.js', import.meta.url), 'utf8');
  const block = source.match(/const DEFAULT_TOOL_NAMES = new Set\(\[([\s\S]*?)\]\);/);
  assert.ok(block);
  const names = [...block[1].matchAll(/'([^']+)'/g)].map(match => match[1]);
  assert.equal(names.length, 7);
  assert.equal(new Set(names).size, 7);
  assert.ok(names.includes('discover_tools'));
  assert.ok(names.includes('project_search'));
});
