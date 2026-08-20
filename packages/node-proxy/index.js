#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { BASE, get, post } from './http.js';

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

// Fallback catalog, generated from the backend _MCP_TOOLS. Used only when
// dynamic /mcp_tools discovery fails.
const FALLBACK_TOOLS = JSON.parse(
  readFileSync(join(dirname(fileURLToPath(import.meta.url)), 'fallback-tools.json'), 'utf8'),
).tools;

process.stderr.write(`mcp-commander: BASE=${BASE} platform=${process.platform}\n`);

function ok(data) {
  return { content: [{ type: 'text', text: JSON.stringify(data) }] };
}

// Version comes from package.json so the advertised MCP serverInfo cannot
// drift from the published package (it had already fallen behind at 1.4.0).
// package.json is BOM-prefixed here and JSON.parse rejects a leading BOM.
const VERSION = JSON.parse(
  readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), 'package.json'),
    'utf8',
  ).replace(/^\uFEFF/, ''),
).version;

const server = new McpServer({ name: 'sublime-mcp', version: VERSION });
server.setToolRequestHandlers();

// ── JSON Schema → Zod (shallow) for dynamic discovery ────────────────────────
// Backend /mcp_tools returns full JSON Schemas; MCP SDK registerTool requires
// Zod shapes. Convert properties/required/defaults so clients still see real
// param docs instead of empty passthrough objects.

function jsonSchemaPropToZod(prop) {
  if (!prop || typeof prop !== 'object') return z.unknown();
  let t;
  switch (prop.type) {
    case 'string':
      t = z.string();
      break;
    case 'integer':
      t = z.number().int();
      break;
    case 'number':
      t = z.number();
      break;
    case 'boolean':
      t = z.boolean();
      break;
    case 'array':
      t = z.array(prop.items ? jsonSchemaPropToZod(prop.items) : z.unknown());
      break;
    case 'object':
      t = prop.properties ? jsonSchemaToZod(prop) : z.record(z.string(), z.unknown());
      break;
    default:
      t = z.unknown();
  }
  if (prop.description) t = t.describe(prop.description);
  return t;
}

function jsonSchemaToZod(schema) {
  if (!schema || typeof schema !== 'object') return z.object({}).passthrough();
  const props = schema.properties || {};
  const required = new Set(schema.required || []);
  const shape = {};
  for (const [key, prop] of Object.entries(props)) {
    let field = jsonSchemaPropToZod(prop);
    if (!required.has(key)) {
      if (prop && Object.prototype.hasOwnProperty.call(prop, 'default')) {
        field = field.default(prop.default);
      } else {
        field = field.optional();
      }
    } else if (prop && Object.prototype.hasOwnProperty.call(prop, 'default')) {
      field = field.default(prop.default);
    }
    shape[key] = field;
  }
  if (Object.keys(shape).length === 0) return z.object({}).passthrough();
  // Allow extra keys agents sometimes send; backend is the real validator.
  return z.object(shape).passthrough();
}

// ── Dynamic tool discovery from backend ──────────────────────────────────────

async function loadDynamicTools() {
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 2000;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const toolsList = await get('/mcp_tools');
      if (!toolsList?.tools) throw new Error('backend returned no tool list');

      for (const tool of toolsList.tools) {
        const inputSchema = jsonSchemaToZod(tool.inputSchema);
        server.registerTool(
          tool.name,
          { description: tool.description, inputSchema },
          async (args) => ok(await post('/' + tool.name, args ?? {})),
        );
      }
      process.stderr.write(`mcp-commander: loaded ${toolsList.tools.length} dynamic tools from backend (attempt ${attempt})\n`);
      return true;
    } catch (e) {
      if (attempt === MAX_RETRIES) {
        process.stderr.write(`mcp-commander: dynamic tool discovery failed after ${MAX_RETRIES} attempts: ${e.message}\n`);
      } else {
        process.stderr.write(`mcp-commander: dynamic tool discovery attempt ${attempt} failed, retrying...\n`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
      }
    }
  }

  return false;
}

// ── generated fallback catalog ────────────────────────────────────────────────

function registerFallbackTools() {
  // GENERATED CATALOG. fallback-tools.json is produced from the backend's
  // _MCP_TOOLS by tools/generate_fallback_catalog.py, so a discovery miss
  // exposes the same tool surface the backend actually serves instead of a
  // hand-maintained subset (F10). Every backend tool has a POST /{name}
  // alias, so one uniform call shape works for all of them.
  for (const tool of FALLBACK_TOOLS) {
    server.registerTool(
      tool.name,
      { description: tool.description, inputSchema: jsonSchemaToZod(tool.inputSchema) },
      async (args) => ok(await post('/' + tool.name, args ?? {})),
    );
  }
  process.stderr.write(`mcp-commander: registered ${FALLBACK_TOOLS.length} generated fallback tools\n`);
}

// ── startup ───────────────────────────────────────────────────────────────────

if (!await loadDynamicTools()) {
  process.stderr.write('mcp-commander: dynamic discovery failed, using generated fallback catalog\n');
  registerFallbackTools();
}

const transport = new StdioServerTransport();
await server.connect(transport);
