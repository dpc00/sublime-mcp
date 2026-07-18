# Sublime-MCP: Universal AI Agent Connector for Sublime Text

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dpc00/sublime-mcp.git
cd sublime-mcp
```

### 2. Install the Sublime Text Plugin

**Windows (Command Prompt):**
```cmd
mklink /J "%APPDATA%\Sublime Text\Packages\sublime-mcp" "C:\path\to\your\sublime-mcp\repo\packages\st-plugin"
```

**macOS/Linux:**
```bash
ln -s "`pwd`/packages/st-plugin" "~/Library/Application Support/Sublime Text/Packages/sublime-mcp"
```

*(Remember to replace `C:\path\to\your\sublime-mcp\repo` with the actual path to where you cloned the repository.)*

### 3. Configure Your Agent

Install the agent-side proxy and configure your agent:

**For Node.js agents:**
```bash
cd packages/node-proxy
npm install .
npx sublime-mcp
```

**For Python agents:**
```bash
cd packages/python-proxy
pip install .
sublime-mcp
```
