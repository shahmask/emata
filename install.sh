#!/bin/bash

# EMATA Global Installer
# "The Enduring Multi-Agent Terminal App"

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛰️  Installing EMATA (v1.0.11)...${NC}"

# 1. Dependency Checks
for cmd in git python3 tmux; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed.${NC}"
        exit 1
    fi
done

# 2. Setup Directory
INSTALL_DIR="$HOME/.emata"
if [ -d "$INSTALL_DIR" ]; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo -e "${BLUE}Updating existing EMATA installation...${NC}"
        cd "$INSTALL_DIR" && git pull
    else
        echo -e "${RED}Warning: $INSTALL_DIR exists but is not a git repository.${NC}"
        echo -e "${BLUE}Re-installing to $INSTALL_DIR...${NC}"
        rm -rf "$INSTALL_DIR"
        git clone https://github.com/shahmask/emata.git "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
else
    echo -e "${BLUE}Cloning EMATA to $INSTALL_DIR...${NC}"
    git clone https://github.com/shahmask/emata.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi


# 3. Virtual Environment
echo -e "${BLUE}Setting up virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet -r requirements.txt
pip install --quiet pyyaml # Ensure YAML support

# 4. Global Symlink
echo -e "${BLUE}Creating global symlink...${NC}"
sudo ln -sf "$INSTALL_DIR/emata-launcher.sh" /usr/local/bin/emata

# 5. MacBook Scrolling Optimization
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}🍎 macOS detected. Adding Option+Arrow scrolling to ~/.tmux.conf...${NC}"
    if ! grep -q "M-Up" ~/.tmux.conf 2>/dev/null; then
        cat <<EOT >> ~/.tmux.conf
# EMATA MacBook Scrolling
bind -n M-Up copy-mode -u
bind -n M-Down copy-mode
EOT
        tmux source-file ~/.tmux.conf 2>/dev/null || true
    fi
fi

# 6. Global Config Initialization
mkdir -p ~/.config/emata

echo -e "\n${BLUE}🛡️  Security Configuration (Vibe Check):${NC}"
echo -e "🤪 Crazy Mode: Disables all safety confirmation prompts. (Not recommended for regular humans)"
echo -e "🚀 YOLO Mode: Removes workspace guardrails, allowing full system access."
echo -e ""

read -p "Enable Crazy Mode by default? (y/N): " ENABLE_CRAZY
CRAZY_VAL="false"
if [[ "$ENABLE_CRAZY" =~ ^[Yy]$ ]]; then
    CRAZY_VAL="true"
fi

read -p "Enable YOLO Mode by default? (y/N): " ENABLE_YOLO
YOLO_VAL="true"
if [[ "$ENABLE_YOLO" =~ ^[Nn]$ ]]; then
    YOLO_VAL="false"
fi

if [ ! -f ~/.config/emata/config.yaml ]; then
    cat <<EOT > ~/.config/emata/config.yaml
# EMATA Global Configuration
model: "gemini-3-flash-preview"
crazy_mode: $CRAZY_VAL
yolo_mode: $YOLO_VAL
search_enabled: true
auth_mode: "api_key"
EOT
fi

echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "You can now run EMATA from any directory by typing: ${GREEN}emata${NC}"
echo -e "Don't forget to set your ${BLUE}GEMINI_API_KEY${NC} in ${BLUE}~/.config/emata/config.yaml${NC}"
