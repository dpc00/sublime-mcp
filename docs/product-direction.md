# Product direction: Sublime as an agent IDE companion

Status: accepted direction, 2026-08-16

Execution is divided into independently verifiable parts in
`docs/roadmap.md`. The current part validates the three existing MCP servers
before any new protocol implementation begins.

## Product thesis

Let a user keep an external coding agent in its native CLI or application while
the agent collaborates with the exact workspace state visible in Sublime Text:
unsaved buffers, selections, diagnostics, navigation, diffs, builds, and
debugger state.

This project will not build another general agent chat UI. Sublime-Claude and
TermMate already occupy that product category. ACP may later support a native
agent frontend, but it is not the first implementation target.

## Architecture

One Sublime package owns a reusable editor-state core and presents adapters:

1. Published IDE Companion Spec compatibility for automatic IDE companion
   behavior, beginning with Gemini CLI and compatible derivatives.
2. A Claude Code `/ide` adapter where its de facto contract differs.
3. A small generic MCP surface for other external agents.
4. An on-demand capability catalog preserving the existing Sublime, LSP,
   Debugger, and Package operations.
5. Raw `run_command` and `eval_python` escape hatches in an advanced profile.

The current tool catalog remains available during migration. Compatibility is
removed only after measured replacement, not because a tool was absent from a
short transcript window.

## Milestone 0: establish the IDE companion contracts

Gemini CLI publishes an IDE Companion Spec explicitly intended for plugins for
editors including Sublime Text. It defines local MCP-over-HTTP transport,
authenticated discovery files, workspace validation, editor-context updates,
and native diff tools. This published contract is the baseline.

Claude Code's `/ide` connection is a separate de facto compatibility interface
built on local JSON-RPC/MCP transport, discovery, and authentication. It is not
assumed to be wire-compatible with the published Gemini contract and is not
treated as stable until verified.

Deliverables:

- implement tests from the published Gemini IDE Companion Spec;
- compare Qwen Code's derived companion contract and renamed discovery
  variables;
- inventory official Claude Code VS Code and JetBrains extension behavior;
- inventory compatible open-source implementations;
- document discovery files, transport, authentication, initialization, tool
  schemas, notifications, and lifecycle;
- capture sanitized protocol fixtures from a real connection;
- create contract tests that replay the fixtures without running Sublime;
- identify version-sensitive behavior and fail gracefully when unsupported.

No runtime implementation begins from guessed wire behavior.

## Milestone 1: editor-state core

Extract reusable operations from the current plugin:

- enumerate windows and views with stable handles;
- report active view, selection, dirty state, file path, syntax, and workspace;
- read file-backed and unsaved buffers consistently;
- focus and navigate without relying on ambient active-view state;
- expose structured diagnostics from the configured LSP package;
- present and resolve a native diff review;
- perform all Sublime API work on the correct thread.

Every mutation returns post-operation state sufficient for verification.

## Milestone 2: minimal IDE companion vertical slice

A terminal-based Gemini or compatible agent session should:

1. discover a running Sublime window;
2. connect with the expected authorization mechanism;
3. obtain the current selection and workspace context;
4. read diagnostics;
5. navigate to a file and location;
6. present a proposed change in Sublime for accept/reject review;
7. reconnect cleanly after plugin reload or Sublime restart.

Installation target: install one Package Control package, start a compatible
agent CLI, and connect through its normal `/ide` workflow without hand-editing
MCP settings. Claude Code compatibility follows through its dedicated adapter
once its differing contract is verified.

## Milestone 3: small generic MCP surface

Retain interoperability for agents without `/ide` support through a focused
surface such as:

- `get_editor_state`
- `list_views`
- `read_view`
- `focus_view`
- `apply_edit`
- `save_view`
- `close_view`
- `get_diagnostics`
- `run_build`
- `wait_for_event`
- `search_capabilities`
- `invoke_capability`

Names and schemas remain provisional until workflow tests establish them.

## Milestone 4: capability migration

The existing command work becomes a searchable capability catalog instead of
hundreds of always-visible tools. Each capability records:

- owning domain/package;
- target type (application, window, or view);
- input and result schema;
- mutation and UI side effects;
- focus requirements;
- safety classification;
- verification operation;
- availability in the running Sublime instance.

Frequently used, semantically important operations may graduate into dedicated
tools. Rare commands remain available through `invoke_capability`.

## Milestone 5: skills and external validation

Create two small skills only after the stable APIs exist:

- editor-state and review workflow;
- optional terminal-package workflow.

Recruit existing Sublime users and measure installation success, task success,
wrong-view errors, dirty-buffer incidents, calls per task, escape-hatch usage,
and repeat usage. Use those results to decide which legacy tools remain public.

## Non-goals for the first release

- replacing Claude Code, Codex, or other agent engines;
- building a new multi-provider chat frontend;
- replacing Windows Terminal or implementing a terminal emulator;
- exposing every Sublime command as a default top-level tool;
- deleting LSP, Debugger, or package work before a measured migration;
- claiming compatibility based only on a successful connection handshake.

## First decision gate

Proceed from protocol research to runtime implementation only when tests define
the minimum `/ide` contract and demonstrate that it can be implemented without
depending on copied proprietary extension code.
