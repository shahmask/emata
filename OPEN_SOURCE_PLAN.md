# 🛰️ Project EMATA — Enduring Multi-Agent Terminal App

## 📜 Vision
A lightweight, no-bloat, Gemini-native terminal agent built for real-world engineering environments. **EMATA** excels where others fail: unstable SSH connections, concurrent independent multi-tasking in a single directory, and deep integration with the Gemini 3 "Reasoning" ecosystem.

---

## 🏷️ Naming Brainstorm
*   **G-Agent**: Simple, classic, clear link to Gemini.
*   **Aether**: (Ancient Greek for 'pure air') — Light, invisible, but everywhere in your terminal.
*   **Resilio**: Latin for "to leap back" (Resilient). Focuses on the SSH reconnection strength.
*   **G-Drive** (Terminal version): Plays on the "driving" your terminal concept.
*   **Gemini Sentinel**: Sounds like a background process that guards your work.
*   **Aider?**: No, it's not an acronym. It's just a French/English word for "helper." It's catchy because it's short.

---

## 🛠️ Portability Audit (Roadblocks to Fix)
1.  **Hardcoded Paths**:
    *   `agent.py` currently points to `/home/shaheen/projects/gemini-agent`. 
    *   **Fix**: Use `os.path.dirname(os.path.abspath(__file__))` to auto-locate the source directory.
2.  **Environment Setup**:
    *   Currently requires manual `venv` and `pip install`.
    *   **Fix**: Create an `install.sh` script that handles global linking (to `/usr/local/bin`) and venv creation.
3.  **Authentication**:
    *   Relies on a `.env` in the current folder.
    *   **Fix**: Add support for a global config at `~/.config/gagent/config.yaml`.

---

## 🧠 Model Compatibility Analysis
| Model | Signature Required? | Support Level | Notes |
| :--- | :--- | :--- | :--- |
| **Gemini 3 Flash Preview** | **YES** | Native (Tested) | Requires the "Thought Signature" logic we just added. |
| **Gemini 3.1 Flash-Lite** | Likely Yes | High | Should work perfectly with our "Flattened Memory" logic. |
| **Gemini 3.5 Flash (Low/Med)** | **YES** | High | These models are very sensitive to "Handshake Integrity." Our new `Part`-level signature capture is essential here. |
| **Gemini 1.5 Pro/Flash** | No | Legacy | Still works, but won't emit the "Thoughts" we now support. |

---

## 🚀 Key Open-Source Features Implemented
1.  **"Safe Mode"**:
    *   Agent now asks `[y/N]` before running risky commands (rm, git push, sudo, etc.). Can be toggled with `:safe`.
2.  **Visual Status Indicator**:
    *   Added a live "Agent is working..." spinner during thinking and tool execution phases.
3.  **UI Refinement**:
    *   Refactored banner and help systems to use Rich `Text` objects, eliminating literal markup tags (e.g., `[dim]`) on unstable terminals.
4.  **Deep Clipboard Integration**:
    *   Implemented **OSC 52** support in both the TMUX launcher and the **Nexus Terminal** (Virtual Gemini CLI) frontend, enabling seamless copy-paste over SSH/Web.
5.  **Dynamic Model Discovery**: 
    *   Implemented `:change-model` to fetch available models directly from the API and update global defaults.
6.  **Guided Authentication**:
    *   Implemented `:auth` with a built-in diagnostic flow that checks for `gcloud` and guides users through the ADC handshake (with automated command spawning).

---

## 📅 Immediate Next Steps
1.  **Implement Web-Search Toggle (Item 2)**: Add ability to disable Google Search grounding via `:search` command or CLI flag.
2.  **Portability Refactor**: Remove hardcoded home directory paths in `agent.py`.
3.  **Configuration Migration**: Move from local `.env` to global config at `~/.config/emata/config.yaml`.
4.  **One-Liner Installer**: Create `install.sh` for global linking and venv setup.
5.  **Finalize Name**: Choose between **Emata** and **gagent**.
6.  **Legal**: Draft the GitHub `LICENSE` (MIT) and `CONTRIBUTING.md`.
