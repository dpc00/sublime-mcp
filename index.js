#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const port = process.platform === 'win32' ? 9500 : 9501;
const BASE = process.env.SUBLIME_MCP_BASE ?? `http://127.0.0.1:${port}`;
const TIMEOUT = 10_000;

process.stderr.write(`mcp-commander: BASE=${BASE} platform=${process.platform}\n`);

async function get(endpoint, params = {}) {
  const url = new URL(endpoint, BASE);
  for (const [k, v] of Object.entries(params)) {
    url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT) });
  if (!r.ok) throw new Error(`HTTP ${r.status} from ${endpoint}`);
  return r.json();
}

async function post(endpoint, body = {}) {
  const r = await fetch(new URL(endpoint, BASE), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(TIMEOUT),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} from ${endpoint}`);
  return r.json();
}

function ok(data) {
  return { content: [{ type: 'text', text: JSON.stringify(data) }] };
}

const server = new McpServer({ name: 'sublime-mcp', version: '1.2.4' });

// ── no-parameter passthrough tools ────────────────────────────────────────────

const PASSTHROUGH = [
  ['get_active_file', 'GET', '/active_file', "Return the active file's path, full content, cursor line/col, dirty flag, and syntax name."],
  ['get_selection', 'GET', '/selection', 'Return the current selection(s): text and begin/end line+col for each.'],
  ['get_open_files', 'GET', '/open_files', 'List all files open in the current window (path, name, is_dirty).'],
  ['get_sheets', 'GET', '/sheets', 'List ALL sheets (tabs) in the current window by index, including images and untitled buffers.\nReturns index, type (TextSheet/ImageSheet), path, name, is_dirty for each.\nUse index with get_sheet_content to read a specific tab.'],
  ['get_project_folders', 'GET', '/project_folders', "Return the project's root folder paths."],
  ['get_symbols', 'GET', '/symbols', 'Return all symbols (functions, classes, etc.) in the active file with line numbers.'],
  ['get_project_data', 'GET', '/project_data', 'Return the raw .sublime-project JSON data for the current project.'],
  ['get_variables', 'GET', '/variables', "Return Sublime Text's build variables: $file, $project_path, $platform, etc."],
  ['get_active_panel', 'GET', '/active_panel', 'Return the active panel id and, if it is an output panel, its content.'],
  ['get_syntaxes', 'GET', '/syntaxes', 'List all syntax definitions available in Sublime Text (name + path).'],
  ['get_encoding', 'GET', '/encoding', 'Return the character encoding of the active file.'],
  ['get_scope_at_cursor', 'GET', '/scope_at_cursor', 'Return the full syntax scope string at the cursor position.'],
  ['get_word_at_cursor', 'GET', '/word_at_cursor', 'Return the word under the cursor and its line/col.'],
  ['get_bookmarks', 'GET', '/bookmarks', 'Return all bookmarked positions in the active file.'],
  ['get_line_count', 'GET', '/line_count', 'Return the total number of lines in the active file.'],
  ['get_layout', 'GET', '/layout', 'Return the current window layout (groups, cells) and which files are in each group.'],
  ['save_all', 'POST', '/save_all', 'Save all open files.'],
  ['revert_file', 'POST', '/revert_file', 'Revert the active file to its last saved state, discarding unsaved changes.'],
  ['undo', 'POST', '/undo', 'Undo the last edit in the active file.'],
  ['redo', 'POST', '/redo', 'Redo the last undone edit in the active file.'],
  ['duplicate_line', 'POST', '/duplicate_line', 'Duplicate the current line(s) in the active file.'],
  ['toggle_sidebar', 'POST', '/toggle_sidebar', 'Show or hide the Sublime Text sidebar.'],
];

for (const [name, method, endpoint, description] of PASSTHROUGH) {
  server.registerTool(name, { description }, async () =>
    ok(await (method === 'GET' ? get(endpoint) : post(endpoint)))
  );
}

// ── parameterised tools ───────────────────────────────────────────────────────

server.registerTool('get_cursor_context', {
  description: 'Return `lines` lines above and below the cursor with 1-based line numbers prepended.',
  inputSchema: { lines: z.number().int().default(10) },
}, async ({ lines }) => ok(await get('/cursor_context', { lines })));

server.registerTool('get_sheet_content', {
  description: 'Return the content of any tab by its sheet index (from get_sheets).\nWorks for text tabs including untitled buffers and Terminus tabs.\nFor image tabs returns the file path only.',
  inputSchema: { index: z.number().int() },
}, async ({ index }) => ok(await get('/sheet_content', { index })));

server.registerTool('get_file_content', {
  description: 'Return the full content of an already-open file by its path.',
  inputSchema: { path: z.string() },
}, async ({ path }) => ok(await get('/file_content', { path })));

server.registerTool('get_view_content', {
  description: 'Return the full content of any open tab by name (partial match, case-insensitive).\nWorks for Terminus tabs and other nameless views that have no file path.\nUse index (0-based, from get_open_files) to target a tab by position instead of name.\nOmit both to read the active view.',
  inputSchema: { name: z.string().default(''), index: z.number().int().default(-1) },
}, async ({ name, index }) => ok(await get('/view_content', { name, index })));

server.registerTool('get_view_size', {
  description: 'Return the total character count of any open tab by name (partial match, case-insensitive).\nUse before get_view_chars to compute offsets — e.g. begin=size-5000, end=size for the tail.\nOmit name for the active view.',
  inputSchema: { name: z.string().default('') },
}, async ({ name }) => ok(await get('/view_size', { name })));

server.registerTool('get_view_chars', {
  description: 'Return text at character offsets begin..end (0-based, end exclusive) from any open tab.\nWorks for Terminus tabs and any other view. Clamps to buffer bounds automatically.\nUse get_view_size first, then e.g. begin=size-5000, end=size to read the last 5000 chars.\nOmit name for the active view.',
  inputSchema: { begin: z.number().int(), end: z.number().int(), name: z.string().default('') },
}, async ({ begin, end, name }) => ok(await get('/view_chars', { name, begin, end })));

server.registerTool('get_view_phantoms', {
  description: "Return phantom HTML and extracted text from a view by name.\nIf key is omitted, defaults to the common 'pybackup' phantom key.",
  inputSchema: { name: z.string().default(''), key: z.string().default('') },
}, async ({ name, key }) => ok(await get('/view_phantoms', { name, key })));

server.registerTool('get_output_panel', {
  description: "Return the text content of an output panel.\nIf name is omitted, read the active output panel. Use name='exec' for build output.",
  inputSchema: { name: z.string().default('') },
}, async ({ name }) => ok(await get('/output_panel', { name })));

server.registerTool('lookup_symbol', {
  description: 'Find where a symbol is defined across all open files.',
  inputSchema: { symbol: z.string() },
}, async ({ symbol }) => ok(await get('/lookup_symbol', { symbol })));

server.registerTool('add_folder', {
  description: 'Add a folder to the current project.',
  inputSchema: { path: z.string() },
}, async ({ path }) => {
  const data = (await get('/project_data')).project_data ?? {};
  const folders = data.folders ?? [];
  if (folders.some(f => f.path === path)) return ok({ ok: true, note: 'already present' });
  folders.push({ path });
  data.folders = folders;
  return ok(await post('/set_project_data', { data }));
});

server.registerTool('remove_folder', {
  description: 'Remove a folder from the current project by path.',
  inputSchema: { path: z.string() },
}, async ({ path }) => {
  const data = (await get('/project_data')).project_data ?? {};
  const folders = data.folders ?? [];
  const newFolders = folders.filter(f => f.path !== path);
  if (newFolders.length === folders.length) return ok({ ok: false, note: 'folder not found' });
  data.folders = newFolders;
  return ok(await post('/set_project_data', { data }));
});

server.registerTool('send_to_view', {
  description: 'Send a string to any open tab by name (partial match, case-insensitive).\nFor Terminus tabs this types the text into the terminal as if the user typed it.\nInclude a trailing newline (\\n) to execute a command.\nUse index (0-based, from get_open_files) to target a tab by position instead of name.\nOmit both name and index to target the active view.',
  inputSchema: { text: z.string(), name: z.string().default(''), index: z.number().int().default(-1) },
}, async ({ text, name, index }) => ok(await post('/send_to_view', { text, name, index })));

server.registerTool('open_file', {
  description: 'Open a file in Sublime Text, optionally jumping to a specific line and column.',
  inputSchema: { path: z.string(), line: z.number().int().default(0), col: z.number().int().default(0) },
}, async ({ path, line, col }) => ok(await post('/open_file', { path, line, col })));

server.registerTool('goto_line', {
  description: 'Move the cursor to a line (and optional column) in the active file.',
  inputSchema: { line: z.number().int(), col: z.number().int().default(1) },
}, async ({ line, col }) => ok(await post('/goto_line', { line, col })));

server.registerTool('show_panel', {
  description: "Bring an output panel to the front. Use name='exec' for the build panel.",
  inputSchema: { name: z.string().default('exec') },
}, async ({ name }) => ok(await post('/show_panel', { name })));

server.registerTool('replace_selection', {
  description: 'Replace the current selection(s) with text.',
  inputSchema: { text: z.string() },
}, async ({ text }) => ok(await post('/replace_selection', { text })));

server.registerTool('replace_lines', {
  description: 'Replace lines begin through end (inclusive, 1-based) in the active file with text.\nPass path to target a specific open file regardless of which tab is focused.\nUse index (0-based, from get_open_files) to target a nameless tab by position.',
  inputSchema: {
    begin: z.number().int(),
    end: z.number().int(),
    text: z.string(),
    path: z.string().default(''),
    index: z.number().int().default(-1),
  },
}, async ({ begin, end, text, path, index }) =>
  ok(await post('/replace_lines', { begin, end, text, path, index })));

server.registerTool('run_command', {
  description: "Run any Sublime Text command. scope='window' (default) or 'view'.",
  inputSchema: {
    command: z.string(),
    args: z.record(z.unknown()).optional(),
    scope: z.string().default('window'),
  },
}, async ({ command, args, scope }) =>
  ok(await post('/run_command', { command, args: args ?? {}, scope })));

server.registerTool('run_build', {
  description: 'Trigger the current build system, or pass cmd/shell_cmd to run a specific command.',
  inputSchema: {
    cmd: z.array(z.string()).optional(),
    shell_cmd: z.string().optional(),
    working_dir: z.string().default(''),
  },
}, async ({ cmd, shell_cmd, working_dir }) => {
  const body = {};
  if (cmd) body.cmd = cmd;
  if (shell_cmd) body.shell_cmd = shell_cmd;
  if (working_dir) body.working_dir = working_dir;
  return ok(await post('/run_build', body));
});

server.registerTool('set_status', {
  description: "Write a message to Sublime Text's status bar.",
  inputSchema: { value: z.string(), key: z.string().default('sublime_mcp') },
}, async ({ value, key }) => ok(await post('/set_status', { key, value })));

server.registerTool('save_file', {
  description: 'Save a file. Pass path to save a specific open file; omit path to save the active file.',
  inputSchema: { path: z.string().default('') },
}, async ({ path }) => ok(await post('/save_file', path ? { path } : {})));

server.registerTool('close_file', {
  description: 'Close a file by path, or close the active file if path is omitted.',
  inputSchema: { path: z.string().default('') },
}, async ({ path }) => ok(await post('/close_file', { path })));

server.registerTool('toggle_comment', {
  description: 'Toggle line comment (or block comment if block=true) on the current selection.',
  inputSchema: { block: z.boolean().default(false) },
}, async ({ block }) => ok(await post('/toggle_comment', { block })));

server.registerTool('sort_lines', {
  description: 'Sort the selected lines (or all lines if nothing is selected).',
  inputSchema: { case_sensitive: z.boolean().default(false) },
}, async ({ case_sensitive }) => ok(await post('/sort_lines', { case_sensitive })));

server.registerTool('select_lines', {
  description: 'Select lines begin through end (1-based, inclusive). end defaults to begin.',
  inputSchema: { begin: z.number().int(), end: z.number().int().default(0) },
}, async ({ begin, end }) => ok(await post('/select_lines', { begin, end: end || begin })));

server.registerTool('fold_lines', {
  description: 'Fold (collapse) lines begin through end (1-based) in the active file.',
  inputSchema: { begin: z.number().int(), end: z.number().int() },
}, async ({ begin, end }) => ok(await post('/fold_lines', { begin, end })));

server.registerTool('insert_snippet', {
  description: "Insert a snippet at the cursor using Sublime Text's snippet syntax (e.g. $1 for tab stops).",
  inputSchema: { contents: z.string() },
}, async ({ contents }) => ok(await post('/insert_snippet', { contents })));

server.registerTool('find_in_file', {
  description: 'Find all occurrences of pattern in the active file. Returns list of {line, col, text}.',
  inputSchema: {
    pattern: z.string(),
    case_sensitive: z.boolean().default(false),
    regex: z.boolean().default(false),
  },
}, async ({ pattern, case_sensitive, regex }) =>
  ok(await post('/find_in_file', { pattern, case_sensitive, regex })));

server.registerTool('find_in_files', {
  description: 'Search for pattern across project folders (or the supplied folder list).\nSkips .git, __pycache__, node_modules, .venv. Returns list of {path, line, match}.',
  inputSchema: {
    pattern: z.string(),
    folders: z.array(z.string()).optional(),
    case_sensitive: z.boolean().default(false),
    regex: z.boolean().default(false),
    max_results: z.number().int().default(200),
  },
}, async ({ pattern, folders, case_sensitive, regex, max_results }) => {
  const body = { pattern, case_sensitive, regex, max_results };
  if (folders) body.folders = folders;
  return ok(await post('/find_in_files', body));
});

server.registerTool('get_command_palette', {
  description: 'List Command Palette entries from installed *.sublime-commands resources.\nOptional filters: package, command id, or caption substring.',
  inputSchema: {
    package: z.string().default(''),
    command: z.string().default(''),
    caption: z.string().default(''),
  },
}, async ({ package: pkg, command, caption }) =>
  ok(await get('/command_palette', { package: pkg, command, caption })));

server.registerTool('get_commands', {
  description: 'List runnable Sublime command ids from loaded command classes, optionally enriched\nwith matching Command Palette entries from installed packages.',
  inputSchema: {
    package: z.string().default(''),
    command: z.string().default(''),
    include_palette: z.boolean().default(true),
  },
}, async ({ package: pkg, command, include_palette }) =>
  ok(await get('/commands', { package: pkg, command, include_palette: String(include_palette) })));

server.registerTool('get_menu_items', {
  description: 'List installed menu items from *.sublime-menu resources.\nOptional filters: menu filename, caption substring, or command id substring.',
  inputSchema: {
    menu: z.string().default(''),
    caption: z.string().default(''),
    command: z.string().default(''),
  },
}, async ({ menu, caption, command }) =>
  ok(await get('/menu_items', { menu, caption, command })));

server.registerTool('set_syntax', {
  description: 'Set the syntax of the active file by name (case-insensitive partial match is fine).',
  inputSchema: { name: z.string() },
}, async ({ name }) => ok(await post('/set_syntax', { name })));

server.registerTool('set_encoding', {
  description: "Set the character encoding of the active file (e.g. 'UTF-8', 'Western (Windows 1252)').",
  inputSchema: { encoding: z.string() },
}, async ({ encoding }) => ok(await post('/set_encoding', { encoding })));

server.registerTool('get_setting', {
  description: "Get a Sublime Text setting by key. scope='view' (default) or 'window'.",
  inputSchema: { key: z.string(), scope: z.string().default('view') },
}, async ({ key, scope }) => ok(await post('/get_setting', { key, scope })));

server.registerTool('set_setting', {
  description: "Set a Sublime Text setting by key. scope='view' (default) or 'window'.",
  inputSchema: { key: z.string(), value: z.unknown(), scope: z.string().default('view') },
}, async ({ key, value, scope }) => ok(await post('/set_setting', { key, value, scope })));

server.registerTool('focus_group', {
  description: 'Move focus to a pane group by 0-based index.',
  inputSchema: { group: z.number().int() },
}, async ({ group }) => ok(await post('/focus_group', { group })));

server.registerTool('set_layout', {
  description: 'Set the window pane layout. layout must be a ST layout dict with cols, rows, cells keys.',
  inputSchema: { layout: z.record(z.unknown()) },
}, async ({ layout }) => ok(await post('/set_layout', { layout })));

server.registerTool('str_replace_based_edit_tool', {
  description: `ST-native file editor implementing the standard str_replace_based_edit_tool interface.
Edits appear live in Sublime Text with full undo (Ctrl+Z), gutter diff markers,
and 30-second highlight annotations showing what changed.

command='str_replace': replace old_str with new_str in path.
  old_str must match exactly once (whitespace-sensitive).
  Returns error if 0 or 2+ matches, listing ambiguous line numbers.

command='insert': insert insert_text after line insert_line (1-based).
  insert_line=0 inserts at the very start of the file.

command='create': create a new file at path with file_text content.
  Syntax is auto-detected from the file extension. Errors if path exists.

command='view': return file content with 1-based line numbers prepended.
  Optional view_range=[start, end] to read a slice (end=-1 for EOF).

All commands auto-open the file in ST if not already open.`,
  inputSchema: {
    command: z.string(),
    path: z.string().default(''),
    old_str: z.string().optional(),
    new_str: z.string().optional(),
    insert_line: z.number().int().optional(),
    insert_text: z.string().optional(),
    file_text: z.string().optional(),
    view_range: z.array(z.number().int()).length(2).optional(),
  },
}, async ({ command, path, old_str, new_str, insert_line, insert_text, file_text, view_range }) => {
  const body = { command, path };
  if (old_str !== undefined) body.old_str = old_str;
  if (new_str !== undefined) body.new_str = new_str;
  if (insert_line !== undefined) body.insert_line = insert_line;
  if (insert_text !== undefined) body.insert_text = insert_text;
  if (file_text !== undefined) body.file_text = file_text;
  if (view_range !== undefined) body.view_range = view_range;
  return ok(await post('/edit_file', body));
});

server.registerTool('eval_python', {
  description: "Execute arbitrary Python in Sublime Text's main thread.\nLocals: sublime, window, view, print. Returns captured stdout in 'output'.",
  inputSchema: { code: z.string() },
}, async ({ code }) => ok(await post('/eval_python', { code })));

server.registerTool('get_console_log', {
  description: 'Return recent Sublime Text console output (plugin log messages and stdout).\ntail=N limits to the last N entries. tail=0 returns all captured entries.',
  inputSchema: { tail: z.number().int().default(100) },
}, async ({ tail }) => ok(await get('/console_log', { tail })));

server.registerTool('get_console_full', {
  description: 'Capture the FULL Sublime Text Python console (entire session history) by simulating Ctrl+A, Ctrl+C in the console output panel and reading the clipboard.\nReturns the complete text including startup messages, plugin load events, and all errors.\nNote: briefly takes keyboard focus from ST to perform the macro.',
  inputSchema: {},
}, async () => ok(await get('/console_full')));

server.registerTool('eval_python_latest', {
  description: "Execute Python code using the system Python interpreter outside Sublime Text's embedded sandbox.\nUseful for newer stdlib features or third-party packages not available in ST's embedded Python.\nReturns stdout, stderr, and returncode.",
  inputSchema: { code: z.string() },
}, async ({ code }) => ok(await post('/eval_python_latest', { code })));

// ── startup ───────────────────────────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);
