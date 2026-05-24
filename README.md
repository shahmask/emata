# 🛰️ EMATA — The Enduring Multi-Agent Terminal App
> **Persistent, Workspace-Aware, and Agentic Terminal AI for Modern Engineering.**

EMATA is a lightweight, no-bloat, Gemini-native terminal AI agent companion. It is engineered specifically for real-world engineering environments, solving the volatility issues of standard CLI wrappers while packing robust agentic autonomy.

> [!IMPORTANT]
> **Built for Quota Efficiency & Long-Term Compatibility:**
> EMATA acts as the ultimate drop-in replacement for the deprecated `geminicli`. While heavy developer agents like **Antigravity** (especially *Antigravity Flash Medium*) can incinerate your usage quotas with complex, costly background reasoning loops, they also lack support for highly cost-effective models like **Gemini 3 Flash Preview**, **Gemini 3.1 Flash-Lite**, and **Gemini 3.5** configured with **low-thinking budgets**. 
> 
> EMATA bridges this gap perfectly, allowing you to run these exact high-reasoning, low-thinking models natively. Keep your automated workflows fast, lightweight, and within quota.

---

## ❓ Why EMATA?

Standard conversational CLIs (like generic `gemini-cli`) are volatile and isolated. EMATA is designed to be **indestructible** and **integrated**:

*   **Indestructible TMUX-Powered Sessions**: Runs inside a backgrounded, persistent TMUX session. If your laptop lid closes, your SSH connection drops, or your network times out, EMATA remains exactly where you left it. Simply type `emata` to re-attach.
*   **Directory-Level Multi-Tenancy**: Automatically partitions and persists conversation history by hashing the `PWD` (current working directory) and TMUX session name. Run independent concurrent sessions across different workspaces or within the same directory without cross-talk.
*   **Deep Agentic Autonomy**: Not just a conversational chat: EMATA reads, writes, and creates files (with automatic `.bak` backups), searches with ripgrep, and runs non-interactive console commands.
*   **High-Reasoning Gemini 3 Support**: Designed for the Gemini 3 ecosystem. Natively parses, flattens, and preserves **Thought Signatures** from advanced reasoning models, preventing capacity drops (503 errors).
*   **Dual Authentication Flexibility**: Natively supports both **Google Auth (Application Default Credentials / `gcloud`)** and standard **Gemini API Key** authentication. Transition seamlessly using the `:auth` shell command.

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

## 🔰 Beginner's Guide & Fast Onboarding

If you are new to working with terminal tools, command-line interfaces (CLIs), or the Google Gemini API, don't worry! EMATA is built to be simple, self-configuring, and highly accessible.

### 1. What do I need before installing?
You only need two standard tools installed on your computer:
* **Python (version 3.9 or higher)**: The programming language EMATA runs on.
* **Git**: The tool used to fetch and update EMATA's source code automatically.
* *Need to check if you have them?* Open your terminal application (e.g., Terminal on Mac) and type `python3 --version` and `git --version`.

### 2. Getting your Gemini API Key
To communicate with the Gemini models, you need an API key. It takes 1 minute to get one for free:
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Log in with your standard Google Account.
3. Click the blue **Get API Key** button at the top left.
4. Copy the key (it starts with `AIzaSy...`). Keep it safe!

### 3. Installing & First Run
Simply copy the installer command below, paste it into your terminal, and press **Enter**. The installer will:
1. Fetch the codebase automatically.
2. Build an isolated "virtual environment" (meaning it installs the exact packages EMATA needs without cluttering your system settings).
3. Set up the globally executable `emata` command.
4. Prompt you interactively to configure your API Key or connect via Google Auth.

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

## 📄 License & Community
EMATA is open-source software distributed under the **MIT License**.

We believe in making the open-source AI community a welcoming and secure place. Check out our guidance:
* **[Contributing Guide](file:///Volumes/shaheen/projects/emata/CONTRIBUTING.md)**: Fork the code and learn how to contribute.
* **[Security & Privacy Policy](file:///Volumes/shaheen/projects/emata/SECURITY.md)**: Learn how we keep your API keys and local data safe.
