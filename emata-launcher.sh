#!/bin/bash
# EMATA Central Launcher
# This script handles the TMUX session management and history independent multi-tenancy.

# 1. RESOLVE TRUE PATH (Handles symlinks correctly)
TARGET_FILE=$0
while [ -L "$TARGET_FILE" ]; do
    TARGET_FILE=$(readlink "$TARGET_FILE")
done
SOURCE_DIR=$(cd "$(dirname "$TARGET_FILE")" && pwd)

CURRENT_DIR="$(pwd)"
PYTHON_BIN="$SOURCE_DIR/.venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Error: Virtual environment not found at $PYTHON_BIN"
    echo "Please run the installer again."
    exit 1
fi

# 2. SMART FIRST-RUN (For stability on Mac)
# If auth isn't configured, run the first setup in Direct Mode to avoid Tmux 'flashing'
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Quick check if config exists and has an auth mode
    CONFIG_FILE="$HOME/.config/emata/config.yaml"
    if [ ! -f "$CONFIG_FILE" ] || ! grep -q "auth_mode" "$CONFIG_FILE"; then
        echo "🔐 Initializing EMATA Authentication..."
        "$PYTHON_BIN" "$SOURCE_DIR/emata.py" "$@"
        # After setup, we continue to the tmux check
    fi
fi

if [ "$1" == "--no-tmux" ]; then
    shift
    echo "🛰️  Starting EMATA in Direct Mode (No Tmux)..."
    exec "$PYTHON_BIN" "$SOURCE_DIR/emata.py" "$@"
fi

if command -v tmux >/dev/null 2>&1 && [ -z "$TMUX" ]; then
    # Find matching sessions for this directory based on the @emata_pwd tmux option
    MATCHING_SESSIONS=$(tmux list-sessions -F '#{session_name} #{session_created} #{session_attached} #{@emata_pwd}' 2>/dev/null | grep -E " ${CURRENT_DIR}$")

    # If we have any active sessions, show the menu
    if [ -n "$MATCHING_SESSIONS" ]; then
        echo -e "\n⚠️  Active EMATA sessions found for this directory:"
        
        declare -a SESS_NAMES
        index=1
        
        while read -r name created attached dir; do
            SESS_NAMES[$index]="$name"
            created_time=$(date -d "@$created" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -r "$created" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$created")
            
            if [ "$attached" -eq 1 ]; then
                status="🟢 Connected"
            else
                status="⚪ Detached"
            fi
            
            echo "  [$index] Session: $name"
            echo "      Created: $created_time"
            echo "      Status : $status"
            echo ""
            index=$((index+1))
        done <<< "$MATCHING_SESSIONS"
        
        NUM_SESSIONS=$((index-1))
        
        echo "What would you like to do?"
        echo "  [1-$NUM_SESSIONS] Reconnect/Join a session above"
        echo "  [k] Kill an existing session"
        echo "  [n] Start a BRAND NEW independent EMATA session"
        echo "  [d] Start in DIRECT MODE (No Tmux/Persistent session)"
        echo "  [q] Exit"
        echo ""
        read -p "Select an option (default: n): " OPTION
        OPTION=${OPTION:-n}
        
        if [ "$OPTION" = "d" ]; then
            echo "🛰️  Starting EMATA in Direct Mode..."
            exec "$PYTHON_BIN" "$SOURCE_DIR/emata.py" "$@"
        elif [[ "$OPTION" =~ ^[0-9]+$ ]] && [ "$OPTION" -ge 1 ] && [ "$OPTION" -le "$NUM_SESSIONS" ]; then
            TARGET_SESSION="${SESS_NAMES[$OPTION]}"
            echo "🔄 Reconnecting to '$TARGET_SESSION'..."
            exec tmux attach-session -t "$TARGET_SESSION"
        elif [ "$OPTION" = "k" ]; then
            echo ""
            echo "Which session would you like to kill?"
            for (( i=1; i<=$NUM_SESSIONS; i++ )); do
                echo "  [$i] ${SESS_NAMES[$i]}"
            done
            read -p "Select session number: " KILL_NUM
            if [[ "$KILL_NUM" =~ ^[0-9]+$ ]] && [ "$KILL_NUM" -ge 1 ] && [ "$KILL_NUM" -le "$NUM_SESSIONS" ]; then
                TARGET_KILL="${SESS_NAMES[$KILL_NUM]}"
                echo "💀 Killing session '$TARGET_KILL'..."
                tmux kill-session -t "$TARGET_KILL"
                echo "Session killed."
            fi
            exit 0
        elif [ "$OPTION" = "n" ]; then
            # Generate new unique session name
            ID_PREFIX=$(date "+%y%m%d")$(date "+%a" | cut -c1-2)$(date "+%H%M")
            suffix="a"
            for char in {a..z}; do
                if ! tmux has-session -t "${ID_PREFIX}${char}" 2>/dev/null; then
                    suffix="$char"
                    break
                fi
            done
            SESSION_NAME="${ID_PREFIX}${suffix}"
            echo "🚀 Starting brand new independent EMATA session '$SESSION_NAME'..."
        else
            echo "Exiting."
            exit 0
        fi
    else
        # No existing sessions, create first one
        ID_PREFIX=$(date "+%y%m%d")$(date "+%a" | cut -c1-2)$(date "+%H%M")
        suffix="a"
        for char in {a..z}; do
            if ! tmux has-session -t "${ID_PREFIX}${char}" 2>/dev/null; then
                suffix="$char"
                break
            fi
        done
        SESSION_NAME="${ID_PREFIX}${suffix}"
        echo "🚀 Starting first EMATA session in this directory ('$SESSION_NAME')..."
    fi

    # Create session (detached)
    if tmux new-session -d -s "$SESSION_NAME" -n "emata" 2>/dev/null; then
        # Send setup and start commands
        tmux send-keys -t "$SESSION_NAME" "export TMUX_SESSION_NAME='$SESSION_NAME'" C-m
        tmux send-keys -t "$SESSION_NAME" "cd '$CURRENT_DIR'" C-m
        tmux send-keys -t "$SESSION_NAME" "'$PYTHON_BIN' '$SOURCE_DIR/emata.py' $@" C-m
        tmux send-keys -t "$SESSION_NAME" "echo -e '\n[Process Exited]'; read" C-m
        
        tmux set-option -t "$SESSION_NAME" @emata_pwd "$CURRENT_DIR"
        
        # SMOOTH SCROLLING: Configure tmux to scroll 1 line per mouse wheel notch
        tmux bind-key -T copy-mode WheelUpPane send-keys -X scroll-up
        tmux bind-key -T copy-mode WheelDownPane send-keys -X scroll-down
        tmux bind-key -T copy-mode-vi WheelUpPane send-keys -X scroll-up
        tmux bind-key -T copy-mode-vi WheelDownPane send-keys -X scroll-down

        # CLIPBOARD INTEGRATION: Use OSC 52 to sync tmux buffer with system clipboard
        tmux set-option -t "$SESSION_NAME" set-clipboard on
        # Automatically copy mouse selection to system clipboard on release
        tmux bind-key -T copy-mode MouseDragEnd1Pane send-keys -X copy-selection-and-cancel
        tmux bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-selection-and-cancel

        exec tmux attach-session -t "$SESSION_NAME"
    else
        echo "⚠️  Tmux session creation failed. Falling back to Direct Mode..."
        exec "$PYTHON_BIN" "$SOURCE_DIR/emata.py" "$@"
    fi

else
    # Fallback to direct execution
    exec "$PYTHON_BIN" "$SOURCE_DIR/emata.py" "$@"
fi
