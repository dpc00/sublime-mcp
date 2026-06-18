# "I have inserted below the Project Brief for the Sublime Text AI UI plugin. Let's
start building it incrementally. To begin, please provide the absolute
minimum Python boilerplate code for a Sublime Text 4 plugin that opens our
two-pane layout and renders a basic interactive minihtml phantom with a
working on_navigate URL link handler."


# this is the contents of sublime_claude_mcp_brief.md:


# Project Brief: Sublime Text + Claude Code / MCP Integration Plugin

## Core Objective
Build a lightweight, zero-fatigue Sublime Text plugin that acts as a highly scannable, graphical UI wrapper around Claude Code and the Model Context Protocol (MCP). The goal is to eliminate developer exhaustion by separating the chat interface from state, configurations, and tool logs.

## Architectural Requirements
1. **Max Plan Authentication:** Must route commands through the local Claude Code CLI binary or leverage local session tokens located in `~/.claude/.credentials.json`. Do not rely on direct pay-as-you-go API keys.
2. **Separation of Concerns:** 
   - No terminal spam, tool logs, or slash commands in the main chat view.
   - Use structured formatting (like XML tags or JSON streams) to intercept meta-data.
3. **UI Windows & Routing:**
   - **Fixed Layout:** Vertical split via `window.set_layout()`. Code files on the left, minimalist chat prompt panel on the right.
   - **Statusline:** Use Sublime's native status bar for instantaneous agent states (e.g., THINKING, INDEXING, IDLE) and token usage.
   - **Interactive Elements:** Use Sublime Text's `minihtml` for phantoms (inline green/red code diffs with `[Approve]/[Reject]` link buttons) and popups (hover context cards powered by local MCP servers).
   - **Dashboard Control:** A custom view tab rendered via `minihtml` displaying checkboxes/toggle links for active MCP servers and config states.

## Next Steps for Execution
- Initialize the basic Sublime Text plugin boilerplate (`EventListener` and `TextCommand`).
- Implement the `on_navigate` event listener to catch `minihtml` anchor links acting as checkboxes.
- Set up an asynchronous background thread using Python's `subprocess` to orchestrate communication with the local Claude environment.


sublime_ai_ui.py:

import sublime
import sublime_plugin

class SetupClaudeWorkspaceCommand(sublime_plugin.WindowCommand):
    """
    Creates the dual-pane layout: code on the left, minimalist chat panel on the right.
    Trigger via Command Palette: "Setup Claude Workspace"
    """
    def run(self):
        # 1. Configure a 2-column vertical split layout (Left: 65% width, Right: 35% width)
        self.window.set_layout({
            "cols": [0.0, 0.65, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
        })
        
        # 2. Open or focus the chat view in the right-hand column (Group 1)
        self.window.focus_group(1)
        chat_view = self.window.new_file()
        chat_view.set_name("Claude Chat Interface")
        chat_view.set_scratch(True) # Prevents Sublime from prompting to save on close
        chat_view.settings().set("word_wrap", True)
        
        # Insert greeting placeholder text
        chat_view.run_command("append", {"characters": "--- Claude Chat Interface ---\nType your prompts here...\n\n"})
        
        # 3. Create a sample interactive UI component inside the chat window
        self.render_mcp_dashboard(chat_view)
        
        # 4. Return focus to the main code workspace on the left (Group 0)
        self.window.focus_group(0)

    def render_mcp_dashboard(self, view):
        # Unique key to track this specific HTML phantom block
        phantom_key = "claude_mcp_dashboard"
        
        # Minihtml content styled with basic CSS
        html_content = """
        <body style="background-color: #1e1e1e; padding: 10px; border-radius: 4px;">
            <style>
                h3 { margin: 0 0 8px 0; color: #66d9ef; font-family: sans-serif; }
                .status-row { margin-bottom: 5px; font-size: 12px; }
                .btn { color: #a6e22e; text-decoration: none; font-weight: bold; }
                .btn-danger { color: #f92672; text-decoration: none; font-weight: bold; }
            </style>
            <h3>🤖 Claude Agent Controls</h3>
            <div class="status-row">
                <span style="color: #a6e22e;">●</span> <b>Filesystem MCP:</b> Enabled 
                <a class="btn-danger" href="toggle_mcp:filesystem">[Disable]</a>
            </div>
            <div class="status-row">
                <span style="color: #75715e;">●</span> <b>Postgres MCP:</b> Disabled 
                <a class="btn" href="toggle_mcp:postgres">[Enable]</a>
            </div>
        </body>
        """
        
        # Place the phantom layout container at the very top of the chat view
        target_region = sublime.Region(0, 0)
        
        # Render the component using the structural Phantom API
        view.add_phantom(
            phantom_key,
            target_region,
            html_content,
            sublime.LAYOUT_BELOW,
            on_navigate=self.handle_ui_click # Bind the click router below
        )

    def handle_ui_click(self, href):
        """
        Interceptors href click data sent from minihtml anchor links.
        This completely supplants the need to type interactive slash text commands.
        """
        sublime.status_message(f"UI Action Intercepted: {href}")
        
        if href.startswith("toggle_mcp:"):
            server_name = href.split(":")[1]
            # State logic placeholder: This is where your Python background worker 
            # will dynamically prune or add the server to your payload schema.
            sublime.message_dialog(f"MCP Dashboard toggled server: '{server_name}'\nThis state modification changes the prompt payload dynamically.")


class ClaudeStatuslineListener(sublime_plugin.EventListener):
    """
    Listens to background updates to instantly feed status info to the fixed statusline,
    bypassing the chat box entirely.
    """
    def on_activated(self, view):
        # Quick demonstration updating Sublime's native footer status bar dynamically
        if view.name() == "Claude Chat Interface":
            view.set_status("claude_meta", "Claude State: IDLE | Active MCPs: 1")
        else:
            view.erase_status("claude_meta")


# this is the proposed content of Default (Windows).sublime-keymap:

[
    { "keys": ["ctrl+shift+c"], "command": "setup_claude_workspace" }
]

# "I have successfully combined the UI and layout logic into a single working
 Sublime Text plugin file. Now, I want to add an asynchronous Python
 background thread to this exact file. This thread needs to quietly launch
 the local claude CLI process, capture its streaming stdout text, and look
 for custom tags so we can route information directly into our minihtml
 phantoms and status bar without filling up our main text view. Please update
 our file to include this background loop logic."
 