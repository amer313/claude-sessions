#!/usr/bin/env bash
# Install claude-sessions — auto-resume Claude Code after Mac restart.
#
# Default: installs LaunchAgents + menu bar in one go.
# Opt out of menu bar: pass --no-menubar (e.g. CLAUDE_SESSIONS_NO_MENUBAR=1).
set -euo pipefail

MANAGER_DIR="$HOME/.claude/session-manager"
BASE_URL="https://raw.githubusercontent.com/amer313/claude-sessions/main"
SCRIPT_URL="$BASE_URL/claude-sessions"
MENUBAR_SCRIPT_URL="$BASE_URL/claude-sessions-menubar.py"
MENUBAR_ICON_URL="$BASE_URL/assets/menubar-icon.png"

want_menubar=1
for arg in "$@"; do
    case "$arg" in
        --no-menubar) want_menubar=0 ;;
    esac
done
[[ "${CLAUDE_SESSIONS_NO_MENUBAR:-0}" = "1" ]] && want_menubar=0

echo "Installing claude-sessions..."
mkdir -p "$MANAGER_DIR" "$MANAGER_DIR/logs"

curl -fsSL "$SCRIPT_URL"         -o "$MANAGER_DIR/claude-sessions"
curl -fsSL "$MENUBAR_SCRIPT_URL" -o "$MANAGER_DIR/claude-sessions-menubar.py" 2>/dev/null || true
curl -fsSL "$MENUBAR_ICON_URL"   -o "$MANAGER_DIR/menubar-icon.png"           2>/dev/null || true
chmod +x "$MANAGER_DIR/claude-sessions" "$MANAGER_DIR/claude-sessions-menubar.py" 2>/dev/null || true

"$MANAGER_DIR/claude-sessions" install

if [[ "$want_menubar" -eq 1 ]]; then
    echo ""
    echo "Installing menu bar (pass --no-menubar to skip)..."
    "$MANAGER_DIR/claude-sessions" menubar install || {
        echo "Menu bar install failed — you can retry later with: claude-sessions menubar install"
    }
fi
