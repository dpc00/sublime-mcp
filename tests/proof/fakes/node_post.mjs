// Probe production node-proxy HTTP client without starting the MCP server.
import { post } from '../../../packages/node-proxy/http.js';

const result = await post('/batch', { calls: [{ tool: 'get_line_count' }] });
process.stdout.write(JSON.stringify(result));
