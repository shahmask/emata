# 🛡️ Security Policy & Data Privacy

At EMATA, we believe that developers and creators should have absolute control over their local environment, their data, and their secrets. This document outlines our data privacy commitment, key hygiene recommendations, and safety policies.

---

## 🔒 Our Data Privacy Commitment

EMATA is built from the ground up to be **local-first and privacy-respecting**:

1. **Zero External Sync**: We do not maintain any central servers. EMATA never sends telemetry, usage logs, file names, terminal histories, or system statistics to us or any third party.
2. **Local Session Persistence**: All conversation history, directory hashing keys, and settings are stored locally on your own machine inside `~/.emata/sessions/` and `~/.config/emata/`.
3. **Direct API Transits**: All communication from your terminal goes directly to the official Google Gemini API or Google Cloud endpoints using standard secure TLS tunnels. Your data is protected by Google's official privacy terms.

---

## 🔑 Key & Credentials Hygiene (Novice-Friendly)

API Keys and Google Cloud Credentials act like password keys to your account. Keeping them safe is simple if you follow these best practices:

### 1. Protect your `.env` File
* When you run EMATA in a directory, a local `.env` file might be created to store config overrides, or you might set `GEMINI_API_KEY` in a project-level `.env`.
* **CRITICAL RULE**: Never commit `.env` files to Git. We have pre-configured a global `.gitignore` in EMATA to automatically block `.env` files from being committed, but always double-check before pushing a public repository.

### 2. Prefer Google Cloud Auth (ADC) for Teams
* If you are working in an enterprise environment or sharing code repositories, we highly recommend setting up **Google Auth (Application Default Credentials)** instead of standard API Keys.
* Run `gcloud auth application-default login` directly. This stores secure, temporary OAuth tokens in your home directory (`~/.config/gcloud/`) rather than hardcoding static API Key strings in local project files.

---

## 🚀 Safety Warnings: YOLO & Crazy Modes

EMATA is equipped with advanced agentic tools (reading, writing, deleting files, and running shell commands) to automate tedious developer tasks. To protect your system, please read these warnings carefully:

### 🛡️ Default Safety (Safe Mode)
* By default, EMATA will always explain the file edits or terminal commands it wants to run and **explicitly wait for your keyboard permission** (`y/n`) before executing them.
* EMATA is also restricted from making modifications outside your active project workspace.

### ⚠️ YOLO Mode (`emata --yolo`)
* Enabling YOLO mode removes workspace guardrails, allowing the model to inspect and modify directories outside your active project folder if you explicitly ask it to.
* **Recommendation**: Only run in trusted local workspaces. Avoid running EMATA with YOLO mode enabled inside system directories or root drives.

### 🚨 Crazy Mode (`emata --crazy`)
* Enabling Crazy mode **completely bypasses confirmation prompts**, letting the agent execute file edits and shell commands instantly.
* **CAUTION**: This is an advanced feature designed for seasoned developers who are running EMATA in sandboxed environments or disposable virtual machines. If you are a novice, **keep Crazy Mode disabled** to prevent accidental command executions.

---

## 📞 Reporting a Vulnerability

If you discover a security vulnerability or credentials exposure within EMATA, please do not open a public issue on GitHub. Instead, contact the maintainer directly or secure your API dashboard immediately:
* **API Key Exposure**: If you suspect your Gemini API key has been leaked or committed publicly, go directly to [Google AI Studio](https://aistudio.google.com/) and click **Delete Key** to instantly deactivate it, then generate a new one.
* **Security Contact**: Contact the repository owner via the contact email specified in the owner's GitHub profile.
