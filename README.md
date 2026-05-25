# 🛰️ EMATA — The Enduring Multi-Agent Terminal App
> **Persistent, Workspace-Aware, and Agentic Terminal AI for Modern Engineering.**

EMATA is a lightweight, no-bloat, Gemini-native terminal AI agent companion. It is engineered specifically for real-world engineering environments, solving the volatility issues of standard CLI wrappers while packing robust agentic autonomy.

> [!IMPORTANT]
> **Built for Quota Efficiency & Long-Term Compatibility:**
> EMATA acts as the ultimate drop-in replacement for the deprecated `geminicli`. While heavy developer agents like **Antigravity** can incinerate your usage quotas with complex background loops, EMATA allows you to run cost-effective models like **Gemini 3 Flash Preview** natively. Keep your automated workflows fast, lightweight, and within your **AI Pro 5TB** quota.

---

## ❓ Why EMATA?

Standard conversational CLIs are volatile and isolated. EMATA is designed to be **indestructible** and **integrated**:

*   **Indestructible TMUX-Powered Sessions**: Runs inside a backgrounded, persistent TMUX session. If your laptop lid closes or your SSH connection drops, EMATA remains exactly where you left it. Simply type `emata` to re-attach.
*   **Deep Agentic Autonomy**: Not just a chat: EMATA reads, writes, and creates files (with automatic `.bak` backups), searches with `ripgrep`, and runs terminal commands.
*   **Smart Permissions**: Inherently safe. Safe actions (like reading files or `ls`) run automatically, while "dangerous" actions (like `write_file` or `delete`) prompt for your `y/n` confirmation unless **CRAZY** mode is on.
*   **Multi-Key Manager**: Store multiple API keys with **nicknames** (e.g., "primary", "work", "pro"). Switch between different quota pools or projects instantly without restarting.
*   **Vibrant Terminal UI**: A refined, color-coded interface with status badges for **YOLO** and **CRAZY** modes and a dynamic model display.

---

## 🛡️ Technical Safeguards & Resilience

EMATA v1.1.7+ includes "Novice-Friendly" deep-integration safeguards to handle the granular complexities of the `google-genai` SDK:

*   **Context Flood Protection**: Automatically strips ANSI escape codes and terminal noise from tool outputs to save tokens and improve reasoning clarity.
*   **Tool Output Hard-Caps**: Smart truncation for `search_grep`, `read_file`, and `run_command` prevents single massive outputs from "incinerating" your 1M token budget.
*   **Automatic Crash Recovery**: If a query exceeds the token limit, EMATA detects the `400 INVALID_ARGUMENT` error, aggressively truncates the history, and **automatically retries** the request for you.
*   **Proactive History Management**: Automatically prunes oldest conversation turns when history grows too large to maintain high speeds and prevent model hallucinations.
*   **Rate-Limit Awareness**: Built-in handling for `429 Resource Exhausted` errors with clear user instructions instead of raw SDK stack traces.

---

## 🚀 Runtime Commands

Type these inside the EMATA shell for instant control:

*   **`:help`** - Show the command guide.
*   **`:keys`** - Open the **API Key Manager** (add, switch, or delete keys).
*   **`:model`** - Dynamic **Model Selector**. Fetches all available Gemini models from the API for you to choose from.
*   **`:clear`** - Reset session history (fixes performance/hallucination in long sessions).
*   **`:yolo`** - Toggle **YOLO Mode** (removes workspace guardrails).
*   **`:crazy`** - Toggle **CRAZY Mode** (bypasses tool execution prompts).
*   **`:session`** - Show current details (active key, model, and environment).
*   **`:report`** - Generate diagnostics and report an issue on GitHub.
*   **`:exit`** - Save and close the current session.

---

## 🛠️ Advanced CLI Features

EMATA excels both as an **interactive agent shell** and as a **flexible, general-purpose CLI tool**.

### 1. Single-Shot & Standard Piping
Pipe logs or files directly into EMATA for instant analysis:
```bash
cat server.log | emata "explain this stack trace"
```

### 2. Context Hydration Flags
Instantly inject files, directories, or git changes as system prompt context on startup:
```bash
# Inject specific files
emata -f main.py -f utils.py "refactor these"

# Inject directory listing
emata -d src/ "find where the routes are"

# Git-Diff Awareness
emata --diff "review my active changes"
```

### 3. Configuration Overrides
Inject dynamic overrides directly into the terminal invocation:
- `--model <name>`: Switch active model.
- `--search`: Enable Google Search grounding.
- `--yolo`: Start with guardrails disabled.
- `--crazy`: Start without tool confirmation prompts.

---

## 📦 Installation

Run the one-line installer on your Mac or Linux terminal:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/shahmask/emata/main/install.sh)"
```

### **Prerequisites**
* **Python (3.10+)**: EMATA v1.1.7+ is optimized for modern Python environments.
* **Git & Tmux**: Required for source management and persistent sessions.
* **Gemini API Key**: Get one for free at [Google AI Studio](https://aistudio.google.com/).

---

## 📄 License
EMATA is open-source software distributed under the **MIT License**.
