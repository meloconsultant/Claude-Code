# Claude Code

Claude Code is an agentic coding tool from Anthropic that lives in your terminal.

## Installation

### Windows (PowerShell)

```powershell
irm https://claude.ai/install.ps1 | iex
```

The script will:
1. Check for Node.js 18+ (installing it via **winget** if absent)
2. Install `@anthropic-ai/claude-code` globally with npm
3. Verify the `claude` command is available on your `PATH`

### macOS / Linux

```bash
npm install -g @anthropic-ai/claude-code
```

## Getting started

```
claude
```

## Documentation

Full documentation is available at <https://docs.anthropic.com/claude-code>.

## Agents & Tools

### Legal Case Manager

[`legal-case-manager.md`](./legal-case-manager.md) — A senior paralegal + litigator hybrid agent that scans uploaded files, builds exhibits lists, tracks case status, flags next steps, and executes tasks. Useful for e-discovery, trial prep, and litigation organization (including California Government Claims Act matters).