# 🤝 Contributing to EMATA

First off, thank you for checking out EMATA! Whether you are a seasoned open-source veteran or a novice looking to make your first contribution, we welcome you to the community. 

EMATA (**Enduring Multi-Agent Terminal App**) is built on a philosophy of **lightweight efficiency, resilience, and user empowerment**. We designed it to be indestructible (via TMUX sessions), cost-effective (via low-thinking model configurations), and globally portable.

---

## 🧭 Our Architecture & Philosophy

Before writing code, it helps to understand the foundational rules that keep EMATA reliable:

1. **Resilience First**: EMATA is designed to survive environment failures (SSH drops, reboots, sleeps). The python core must always exit cleanly (exit status `0`) without ugly tracebacks. Always wrap console input sequences in `try...except (KeyboardInterrupt, EOFError)`.
2. **Local-First Privacy**: EMATA respects data sovereignty. We never send telemetry, statistics, or code snippets outside the user's official Google API or Google Cloud authentication boundaries.
3. **No-Bloat Agentic Autonomy**: Tools should be focused and lightweight. EMATA writes, reads, and executes local commands in a non-interactive format (e.g. using silent `-y` or `--quiet` flags).
4. **Safety & Guardrails**:
   * **Workspace Isolation**: History is partitioned by hashing the active directory path (`PWD`).
   * **Automatic Backups**: Always create a `.bak` backup copy before modifying or overwriting any user file.
   * **Safe by Default**: YOLO and Crazy modes are configurations the user must explicitly choose—the default experience should always prompt for confirmation on critical actions.

---

## 🛠️ Developer Setup Guide

Getting a local development environment running is straightforward:

### 1. Fork & Clone
Fork the repository on GitHub and clone your fork locally:
```bash
git clone https://github.com/YOUR_USERNAME/emata.git
cd emata
```

### 2. Setup Virtual Environment
Create and activate a clean, isolated Python virtual environment to protect your system dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Running EMATA Natively
To test your modifications in real-time without starting the TMUX launcher wrapper:
```bash
python3 emata.py --no-tmux
```
To run a single-shot query with piped inputs:
```bash
cat server.log | python3 emata.py --no-tmux "explain this error"
```

---

## 📥 Submitting Changes

1. **Branch Hygiene**: Create a clean, descriptively named branch for your feature or bug fix:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Commit Messages**: Write clear, imperative commit messages following standard open-source conventions:
   * `feat: Add dynamic thinking budget slider`
   * `fix: Handle empty standard input safely`
   * `docs: Clarify novice-friendly API registration`
3. **Open a Pull Request**: Push your branch to GitHub and open a Pull Request (PR) against the `main` branch. Provide a brief summary of what the change does and how you tested it.

---

## 💬 Community & Code of Conduct

We are dedicated to providing a welcoming, helpful, and harassment-free environment for everyone—regardless of experience level, background, or identity. 
* **Be Kind**: Help newcomers understand terminal concepts (like environment variables and symlinks) with patience and clarity.
* **Be Respectful**: Disagreements on technical design should remain constructive and professional.

Thank you for helping us make EMATA the ultimate terminal companion!
