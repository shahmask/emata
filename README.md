# 🛰️ EMATA — The Enduring Multi-Agent Terminal App
> **Persistent, Workspace-Aware, and Agentic Terminal AI for Modern Engineering.**

EMATA is a lightweight, no-bloat, Gemini-native terminal AI agent companion. It is engineered specifically for real-world engineering environments, solving the volatility issues of standard CLI wrappers while packing robust agentic autonomy.

> [!IMPORTANT]
> **Built for Quota Efficiency & Long-Term Compatibility:**
> EMATA acts as the ultimate drop-in replacement for the deprecated `geminicli`. Unlike resource-heavy developer agents that incinerate usage quotas, EMATA lets you target highly cost-effective, high-reasoning preview and workhorse models like **Gemini 3 Flash Preview**, **Gemini 3.1 Flash-Lite**, and **Gemini 3.5** with fine-grained thinking budgets (low/minimal thinking). Keep your automated workflows running fast, robustly, and within quota.

---

## ❓ Why EMATA?

Standard conversational CLIs (like generic `gemini-cli`) are volatile and isolated. EMATA is designed to be **indestructible** and **integrated**:

*   **Indestructible TMUX-Powered Sessions**: Runs inside a backgrounded, persistent TMUX session. If your laptop lid closes, your SSH connection drops, or your network times out, EMATA remains exactly where you left it. Simply type `emata` to re-attach.
*   **Directory-Level Multi-Tenancy**: Automatically partitions and persists conversation history by hashing the `PWD` (current working directory) and TMUX session name. Run independent concurrent sessions across different workspaces or within the same directory without cross-talk.
*   **Deep Agentic Autonomy**: Not just a conversational chat: EMATA reads, writes, and creates files (with automatic `.bak` backups), searches with ripgrep, and runs non-interactive console commands.
*   **High-Reasoning Gemini 3 Support**: Designed for the Gemini 3 ecosystem. Natively parses, flattens, and preserves **Thought Signatures** from advanced reasoning models, preventing capacity drops (503 errors).

---

## 🚀 Advanced CLI Features

EMATA excels both as an **interactive agent shell** and as a **flexible, general-purpose CLI tool**.

### 1. Single-Shot & Standard Piping (Direct Mode)
Pipe files, standard input, or logs directly into EMATA for instant answers without opening the interactive loop:
```bash
# Pipe code/logs for explanations
cat server.log | emata "explain this stack trace and suggest a fix"

# Run quick direct queries
emata "write a python function to compute prime numbers" > primes.py
```

### 2. Context Hydration Flags (`-f` / `--file` and `-d` / `--dir`)
Instantly inject files or directories as structured system prompt context on startup:
```bash
# Hydrate specific code files
emata -f main.py -f utils.py "refactor both to use async handlers"

# Hydrate directory structure
emata -d src/ "find where the active routes are defined"
```

### 3. Active Workspace Git-Diff Awareness (`--diff`)
Provide the agent with immediate context of what you are working on by attaching your unstaged git changes automatically:
```bash
emata --diff "review my active changes for security issues"
```

### 4. Configuration Override Toggles
Inject dynamic overrides directly into the terminal invocation:
- `--model <name>`: Switch active model (e.g., `--model gemini-3.5-pro`)
- `--search` / `--no-search`: Toggle Google Search grounding
- `--yolo` / `--safe`: Toggle workspace guardrails
- `--crazy`: Bypass safety confirmation prompts for autonomous tool executions

---

## 📦 One-Line Installation

Run the installer directly on your Mac or Linux terminal. On Apple Silicon M-series Macs, EMATA installs seamlessly without requiring `sudo` by integration with the Homebrew path:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/shahmask/emata/main/install.sh)"
```

### Next Steps & Shell Commands
*   **Interactive Loops**: Start/Attach sessions with `emata` (standalone) or `emata --no-tmux` (direct loop).
*   **Upgrade EMATA**: Keep everything updated and stabilized by running `:upgrade` directly inside the agent shell.

---

## 📄 License
EMATA is open-source software distributed under the **MIT License**.
