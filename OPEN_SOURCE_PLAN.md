# 🛰️ Project EMATA — Enduring Multi-Agent Terminal App
## **Status: v1.0.1 Released 🚀**

## 📜 Vision
A lightweight, no-bloat, Gemini-native terminal agent built for real-world engineering environments. **EMATA** excels where others fail: unstable SSH connections, concurrent independent multi-tasking in a single directory, and deep integration with the Gemini 3 "Reasoning" ecosystem.

---

## ✅ Completed Milestones (v1.0.1)
1.  **Core Architecture**: Stable multi-agent loop with "Thought Signature" capture for Gemini 3 reasoning models.
2.  **SSH Resilience**: TMUX-based launcher (`emata-launcher.sh`) for persistent sessions.
3.  **Crazy Mode**: Toggleable safety confirmation (`:crazy`) for no-prompt autonomy.
4.  **YOLO Mode**: Workspace guardrail management (`:yolo`) for full system access.
5.  **Auto-Backups**: Automatic `.bak` file creation before any file modification.
6.  **Google Search Grounding**: On-the-fly search toggle (`:search`) with visual status indicators.
7.  **Global Portability**:
    *   Migrated config to `~/.config/emata/config.yaml`.
    *   Removed all hardcoded home directory paths.
    *   Created a robust universal `install.sh`.
6.  **MacBook Optimization**: Integrated `Option + Up/Down` keyboard scrolling for Mac users in TMUX.
8.  **Integrated Auth Flow**:
    *   Interactive first-run prompt for API Key or Google Cloud (ADC).
    *   Dynamic agent re-initialization on auth changes (no restart required).
    *   Robust Google Cloud ADC handshake with explicit scope handling.

---

## 🏷️ The Identity
*   **Name**: EMATA (Enduring Multi-Agent Terminal App)
*   **License**: MIT (Open Source)
*   **Version**: 1.0-Beta

---

## 📅 Future Roadmap (Post-Beta)
1.  **Multi-Pane Intelligence**: Ability for the agent to spawn/monitor multiple terminal panes simultaneously.
2.  **Streaming Tools**: Optimization for tool outputs that take a long time to return (e.g. long builds).
3.  **Local Context Cache**: Implementing a local vector store for long-term memory of massive codebases.
4.  **Telemetry-Lite**: Optional, anonymous error reporting to help improve model prompts (Opt-in only).
5.  **Refined GUI**: A lightweight web-frontend for users who prefer a browser-based "Nexus Terminal" while keeping the agent local.

---

## 🛠️ Maintenance Notes
*   Source is located at `~/projects/emata`.
*   GitHub Repository: `https://github.com/shahmask/emata`
*   Global binary linked at `/usr/local/bin/emata`.
*   Config lives at `~/.config/emata/config.yaml`.
