# claude-sessions

Auto-resume all your Claude Code sessions after a Mac restart.

## How it works

Claude Code tracks live sessions in `~/.claude/sessions/<PID>.json`. These files survive a restart, but the processes die. On login, this tool reads those files, finds dead PIDs, and opens a terminal window for each with `claude --resume <session-id>`.

A lightweight backup daemon (every 5 min) keeps a safety-net copy in case the session files get cleaned up before restore runs.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/amer313/claude-sessions/main/install.sh | bash
```

Or manually:

```bash
mkdir -p ~/.claude/session-manager
curl -fsSL https://raw.githubusercontent.com/amer313/claude-sessions/main/claude-sessions \
  -o ~/.claude/session-manager/claude-sessions
chmod +x ~/.claude/session-manager/claude-sessions
~/.claude/session-manager/claude-sessions install
```

## Usage

```
claude-sessions status      # What's running now
claude-sessions restore     # Manually resume dead sessions
claude-sessions disable     # Skip next auto-restore
claude-sessions enable      # Re-enable auto-restore
claude-sessions uninstall   # Remove everything
```

## Config

Edit `~/.claude/session-manager/config`:

```bash
# Extra flags passed to `claude` on resume
CLAUDE_RESUME_FLAGS="--dangerously-skip-permissions"

# Terminal override: "iTerm2" or "Terminal" (auto-detected if empty)
TERMINAL=""
```

## What happens on restart

1. Mac restarts, all Claude processes die
2. You log in
3. 10 seconds later, the restore agent reads the session files
4. Opens a Terminal/iTerm2 window for each dead session
5. Each runs `claude --resume <session-id>` in the original directory
6. macOS notification confirms how many were restored

## Requirements

- macOS (uses LaunchAgents)
- Python 3 (ships with macOS)
- Claude Code CLI

## Uninstall

```bash
claude-sessions uninstall
```
