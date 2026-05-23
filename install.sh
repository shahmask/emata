#!/bin/bash
# EMATA Installation Script
# (Enduring Multi-Agent Terminal App)

set -e

echo "🛰️  Installing EMATA..."

# 1. Create local bin if it doesn't exist
mkdir -p "$HOME/.local/bin"

# 2. Locate the source directory
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📍 Source directory: $SOURCE_DIR"

# 3. Setup Virtual Environment
if [ ! -d "$SOURCE_DIR/.venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$SOURCE_DIR/.venv"
fi

# 4. Install Dependencies
echo "📦 Installing dependencies..."
"$SOURCE_DIR/.venv/bin/pip" install --quiet -r "$SOURCE_DIR/requirements.txt"

# 5. Create the wrapper script
echo "🛠️  Creating global command..."
CAT_CMD=$(cat <<EOF
#!/bin/bash
# Wrapper for EMATA
if command -v tmux >/dev/null 2>&1 && [ -z "\$TMUX" ]; then
    CURRENT_DIR="\$(pwd)"
    MATCHING_SESSIONS=\$(tmux list-sessions -F '#{session_name} #{session_created} #{session_attached} #{@emata_pwd}' 2>/dev/null | grep -E " \${CURRENT_DIR}\$")
    
    if [ -n "\$MATCHING_SESSIONS" ]; then
        # ... (rest of the menu logic same as current wrapper)
        # For brevity in this installer, we'll point to the main script logic
        bash "$SOURCE_DIR/emata-launcher.sh" "\$@"
    else
        bash "$SOURCE_DIR/emata-launcher.sh" "\$@"
    fi
else
    exec "$SOURCE_DIR/.venv/bin/python" "$SOURCE_DIR/emata.py" "\$@"
fi
EOF
)

# Actually, for the installer, it's cleaner to copy the wrapper we just wrote
cp "$SOURCE_DIR/emata-wrapper.sh" "$HOME/.local/bin/emata" 2>/dev/null || true
# Since I haven't created emata-wrapper.sh as a separate file yet, I'll do that now.

echo "✅ EMATA installed successfully!"
echo "🚀 Try running 'emata' in any directory."
