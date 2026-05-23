# 🚀 gagent — Gemini Terminal Agent

`gagent` is a lightweight, high-performance command-line AI coding agent that runs directly in any local folder. It is designed to mirror the autonomous file-manipulation and command-execution workflows of advanced AI systems, providing you with a raw, fast, and unbloated terminal partner.

---

## ⚡ Core Features

- 💻 **Terminal Execution**: Safely executes shell commands in the directory it is launched from and feeds output directly back to the LLM.
- 📁 **Filesystem Access**: Native tools to read, write, create, and delete files with robust path resolution and automatic directory creation.
- ⚙️ **Directory-Specific Rules**: Detects and imports local `.gemini` or `gemini.md` files inside the working directory to apply customized project-level system instructions.
- 🔄 **Rugged Error Recovery**: Automatic exponential backoff retries for transient API errors (503 High Demand, 500 Internal Error) and graceful handling of 429 Quota limits.
- 🧠 **Persistent Tool State**: Uses cryptographic "Thought Signatures" to maintain state integrity across complex, multi-turn tool-calling loops.
- 🌐 **Real-Time Grounding**: Built-in Google Search support for fetching the latest documentation, pricing, and live web data.
- 🎨 **Beautiful real-time UI**: Powered by `rich.live`, providing word-by-word Markdown rendering and clear separation between Reasoning (Thinking) and Final Answers.
- 🛠️ **Visual Tool Feedback**: Dedicated UI panels that show exactly which tool the agent is running and its arguments in real-time.

---

## 💬 In-Session Commands

Type these special commands directly into the `gagent > ` prompt:

| Command | Action |
| :--- | :--- |
| `:sessions` | List all active TMUX-managed gagent sessions and recent history files. |
| `:clear` | Reset active conversation history and start fresh. |
| `:model <name>` | Switch the active model on the fly. |
| `:config` | View active configuration parameters (model, local rules, etc.). |
| `:help` | View help details. |
| `:exit` / `:quit` | Exit the CLI and clear the current session. |

---

## 🛠️ Usage & Troubleshooting

### Running in Debug Mode
If you experience connectivity issues or want to see the raw API handshake, launch with the `--debug` flag:
```bash
gagent --debug
```
Detailed logs are persisted to `~/.gagent/gagent.log`.

### Persistence Behavior
- **Auto-Resume**: If you close your terminal or lose connection, `gagent` will automatically reload your history when you return to that directory.
- **Fresh Start**: To start a 100% clean session, type `:exit` or `:clear`.

---

## 🔄 Self-Modification & Upgrades

`gagent` is self-aware. You can command it to modify its own source code at `/home/shaheen/projects/gemini-agent`.

**Example Prompt**:
> `"Inspect your tools.py file. Add a new tool that can analyze git commit history."`

---

## ✨ Recent Stability Enhancements (May 22, 2026)

- **Word-by-Word Rendering**: Fixed the "Redundant Response" bug. Answers now stream beautifully in real-time as formatted Markdown.
- **Memory Flattening**: Refactored history serialization to "flatten" complex reasoning blocks into standard text, significantly reducing 503 "High Demand" errors for long sessions.
- **Quota Resilience**: Added explicit logic to catch 429 errors. The agent now notifies you when it hits a rate limit and automatically waits for the "token bucket" to refill.
- **Handshake Integrity**: Implemented full support for `thought_signature` and `include_server_side_tool_invocations`, ensuring Gemini 3 models can execute terminal tools without validation errors.
- **Session Cleanup**: Standardized `:exit` behavior to clear the working session by default, preventing history bloat and model confusion.

---

## 📂 Project Structure

```text
gemini-agent/
├── .venv/            # Dedicated Python Virtual Environment
├── requirements.txt  # Dependencies (google-genai, rich, python-dotenv, google-api-core)
├── config.py         # Environment & local .gemini loader
├── tools.py          # Local system tools (filesystem & execution bindings)
├── agent.py          # AI conversation engine & manual tool dispatcher
├── logging_config.py # Centralized logging infrastructure
└── gagent.py         # Main CLI application entry point and REPL loop
```
