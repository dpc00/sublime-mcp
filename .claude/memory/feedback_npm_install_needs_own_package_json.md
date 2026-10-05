---
name: npm-install-needs-own-package-json
description: "2026-10-05: `npm install <pkg>` in a new empty folder installed into C:\\Users\\donal (home) and pruned 131 packages that sublime-mcp's node tests rely on; create a package.json first, never rely on cwd"
metadata:
  type: feedback
---

On 2026-10-05, installing the CoffeeScript compiler for the CoffeeCompile test, I ran `npm install coffeescript` in a freshly created `C:\Users\donal\tools\coffee_npm`. npm walks up to find a project root, found `C:\Users\donal\node_modules`, installed there, wrote `C:\Users\donal\package.json`/`package-lock.json`, and pruned 131 extraneous packages (the MCP SDK, zod, prompts and their dependencies).

**Why it mattered:** `packages/node-proxy` in the sublime-mcp repo has no `node_modules` of its own, so `node test/*.test.js` (release step 3 in [[reference_sublime_mcp_release_steps]]) resolves `@modelcontextprotocol/sdk`, `zod` and `prompts` from the home `node_modules`. Without them the node tests fail. I do not know what else (if anything) was in that folder before; `.svelte2tsx-language-server-files` is a leftover from a Svelte language-server test.

**Repair done the same day:** sent my new package.json and lock to the Recycle Bin and ran `npm install --no-save --no-package-lock "@modelcontextprotocol/sdk@^1.29.0" "zod@^4.4.3" "prompts@^2.4.2"` in the home folder (97 entries back); the three node tests pass again. The original 131-package set was not recorded, so it is not an exact restore.

**How to apply:** before any `npm install`, create a `package.json` in the target folder (`{"name":"x","private":true}`) or use `--prefix`, and look at the "added/removed" line; "removed N packages" means it touched an older project. Better long-term fix (not done, Donald's call): give `packages/node-proxy` its own `node_modules` so the tests do not depend on the home folder.
