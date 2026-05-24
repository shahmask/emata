# 🛰️ EMATA (v1.0.11)
### Enduring Multi-Agent Terminal App

**EMATA** is a powerful **AI agent companion** for your terminal. It's built for power users—from software developers and program managers to homelab admins—who need a pragmatic assistant that can autonomously write code, manage files, and execute commands while respecting the user's ultimate authority.

Whether you're managing a complex codebase, orchestrating project workflows, or maintaining a home server, EMATA gives you a professional-grade autonomous shell that stays alive across remote sessions.

---

## ❓ Why EMATA?

EMATA was created to solve specific frustrations with existing CLI agents:

- **Drop-in Replacement**: EMATA follows the established `gemini.md` / `.gemini` paradigm for local project instructions. If you already have these files in your codebase, EMATA will automatically detect and follow them, making it a seamless transition from other Gemini-based tools.
- **The Persistence Problem**: Most CLI agents die the moment you lose your SSH connection or close your laptop. EMATA uses a smart TMUX-based architecture to ensure your agent—and your full conversation context—stays alive until you explicitly close it.
- **The Transition**: With `geminicli` approaching deprecation and newer alternatives like `antigravitycli` not yet being a cost-effective or suitable replacement for many workflows, EMATA provides a pragmatic, local-first alternative.
- **Gemini-First**: Currently, EMATA **only supports Google Gemini models** (including the latest Reasoning models). It is designed to take full advantage of the Gemini 1.5/2.0+ architecture, including native tool-calling and long-context windows.

---

## ✨ Core Capabilities

- **🦾 Session Persistence**: Built on top of TMUX. If your connection drops or you close your laptop, EMATA stays alive. Just re-attach and your work is exactly where you left it.
- **🤪 Crazy Mode**: The "No-Nags" Mode (`:crazy`). By default, the AI agent asks for your permission before running risky commands. Turn this ON to stop the prompts and let the agent work at full speed.
- **🚀 YOLO Mode**: System-Wide Access (`:yolo`). By default, EMATA follows strict **guardrails** to stay inside your current project folder. Turn YOLO ON to remove these guardrails and let it reach anywhere on your machine—perfect for server management or cross-project tasks.
- **💾 Fail-Safe Backups**: **This is your safety net.** EMATA automatically creates `.bak` copies before it modifies any file. If the AI agent makes a mistake, you have an instant "undo" button for every change.
- **🔍 Real-Time Lookup**: Instant access to the internet (`:search`) for checking documentation or troubleshooting errors without leaving your terminal.
- **🧠 Native Reasoning**: Full support for "Reasoning" models. You can actually see the AI's "thought process" as it solves complex problems.

---

## 📦 Installation & Setup

### Option 1: Homebrew (macOS & Linux)
This is the recommended way if you want Homebrew to manage updates for you.

```bash
brew tap shahmask/tap
brew install --HEAD emata
```

### Option 2: One-Liner (Universal)
If you don't use Homebrew, you can use this standalone installer.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/shahmask/emata/main/install.sh)"
```

### 🔐 First Run
When you launch EMATA for the first time, it will automatically detect if your authentication is missing and prompt you to set up your **Gemini API Key** or use **Google Cloud (ADC)**. 

### ⌨️ Control Commands

| Command | Action |
| :--- | :--- |
| `:crazy` | Toggle Crazy Mode (ON = No more "Are you sure?" prompts) |
| `:yolo` | Toggle YOLO Mode (ON = Full system access / Remove guardrails) |
| `:search` | Toggle Real-Time Web Lookup |
| `:auth` | Switch between API Key and Google Auth / Update credentials |
| `:help` | View all available system commands |
| `:mouse` | Toggle TMUX mouse mode (handy for scrolling) |

---

## ⚖️ Responsibility Note
**EMATA** is a powerful AI agent. When **Crazy Mode** or **YOLO Mode** are active, it operates with absolute autonomy and no guardrails. While EMATA creates `.bak` files to prevent data loss, you are the pilot. It does exactly what you tell it to do, making it a high-speed multiplier for your workflow.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.
