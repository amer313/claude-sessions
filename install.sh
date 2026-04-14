#!/usr/bin/env bash
# Install claude-sessions — auto-resume Claude Code after Mac restart
set -euo pipefail

MANAGER_DIR="$HOME/.claude/session-manager"
SCRIPT_URL="https://raw.githubusercontent.com/amer313/claude-sessions/main/claude-sessions"

echo "Installing claude-sessions..."
mkdir -p "$MANAGER_DIR"
curl -fsSL "$SCRIPT_URL" -o "$MANAGER_DIR/claude-sessions"
chmod +x "$MANAGER_DIR/claude-sessions"
"$MANAGER_DIR/claude-sessions" install
