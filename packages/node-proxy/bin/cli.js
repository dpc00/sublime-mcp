#!/usr/bin/env node

const fs = require('fs/promises');
const path = require('path');
const prompts = require('prompts');

async function main() {
  console.log('Sublime-MCP Agent Configurator');

  const response = await prompts({
    type: 'text',
    name: 'configFile',
    message: 'Please enter the path to your AI agent\'s configuration file (e.g., ~/.claude/settings.json):',
    validate: async (value) => {
      try {
        // Resolve ~ to the home directory
        const resolvedPath = value.startsWith('~') ? path.join(process.env.HOME || process.env.USERPROFILE, value.slice(1)) : value;
        await fs.access(resolvedPath);
        return true;
      } catch (e) {
        return 'File not found. Please enter a valid path.';
      }
    }
  });

  if (!response.configFile) {
    console.log('Configuration cancelled.');
    return;
  }

  const configPath = response.configFile.startsWith('~') ? path.join(process.env.HOME || process.env.USERPROFILE, response.configFile.slice(1)) : response.configFile;
  console.log(Reading configuration file: );

  try {
    const configContent = await fs.readFile(configPath, 'utf-8');
    const config = JSON.parse(configContent);

    console.log('Successfully parsed configuration file.');

    // Determine the correct port based on the platform
    const port = process.platform === 'win32' ? 9502 : 9503;
    const mcpEntry = {
      "sublime-mcp": { "type": "sse", "url": http://127.0.0.1:/sse }
    };

    // Add or update the mcpServers entry
    if (!config.mcpServers) {
      config.mcpServers = {};
    }
    config.mcpServers = { ...config.mcpServers, ...mcpEntry };

    // Write the updated configuration back to the file
    const newConfigContent = JSON.stringify(config, null, 2);
    await fs.writeFile(configPath, newConfigContent, 'utf-8');

    console.log('Successfully updated the configuration file with the sublime-mcp server.');
    console.log('Please restart your AI agent for the changes to take effect.');

  } catch (error) {
    console.error(Error processing configuration file: );
    console.error('Please ensure the file is a valid JSON file.');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('An error occurred:', err);
  process.exit(1);
});
