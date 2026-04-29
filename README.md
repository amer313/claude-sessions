<p align="center">
  <img src="assets/banner.svg" alt="claude-sessions" width="640">
</p>

# claude-sessions

Auto-resume all your Claude Code sessions after a Mac restart.

## How it works

Claude Code tracks live sessions in `~/.claude/sessions/<PID>.json`. These files survive a restart, but the processes die. On login, this tool reads those files, finds dead PIDs, and resumes each one with `claude --resume <session-id>` — by default, as tabs inside a single terminal window instead of N separate windows.

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
claude-sessions status              # What's running now
claude-sessions restore             # Manually resume dead sessions
claude-sessions prune [days]        # Remove dead session files older than N days
claude-sessions disable             # Skip next auto-restore
claude-sessions enable              # Re-enable auto-restore
claude-sessions menubar install     # Add menu bar item (optional)
claude-sessions menubar uninstall   # Remove menu bar item
claude-sessions uninstall           # Remove everything
```

## Config

Edit `~/.claude/session-manager/config`:

```bash
# Extra flags passed to `claude` on resume
CLAUDE_RESUME_FLAGS="--dangerously-skip-permissions"

# Terminal override: "iTerm2" or "Terminal" (auto-detected if empty)
TERMINAL=""

# Restore layout:
#   tabs    — one window with one tab per session (default)
#   windows — one window per session (old behavior)
#   tmux    — one tmux session "claude" with one window per session
LAYOUT="tabs"

# Auto-prune dead session files older than N days (snapshot daemon does this).
# Also always prunes dead sessions whose CWD no longer exists. Set 0 to disable.
PRUNE_DAYS=7
```

### Auto-prune

The snapshot daemon (runs every 5 min) automatically drops stale session files:

- **Always**: any dead-PID session whose `cwd` no longer exists on disk
- **By age**: dead-PID sessions older than `PRUNE_DAYS` days (default 7)

This keeps `~/.claude/sessions/` and the backup manifest clean without any work on your part. For a manual pass: `claude-sessions prune [days]`.

### Layouts

**`tabs` (default)** — One window titled `Claude Sessions (N)` with one named tab per session. Tab names use the session name, or the CWD basename if unnamed. This keeps your desktop clean with many sessions.

**`windows`** — Legacy behavior: one new terminal window per session. Useful if you prefer spatial separation over tabs.

**`tmux`** — Creates (or reuses) a tmux session named `claude` with one window per Claude session. Attach with `tmux attach -t claude`. Best for power users comfortable with tmux. Requires `tmux` on `$PATH`.

## Menu bar item (optional)

A lightweight menu bar icon shows the live session count and a dropdown with each session. Click a live session to jump to its iTerm2 tab; click "Restore Now" to resume dead sessions.

```bash
claude-sessions menubar install
```

The menu bar:

- Shows `⎋ N` where N is the live session count
- Lists all live sessions (click to focus that iTerm2 tab)
- Lists stale sessions waiting for restore
- Actions: Restore Now, Disable/Enable Auto-Restore, Open Logs, Open Config

It's pure Python (`rumps`), installed to `~/.claude/session-manager/` and started on login via LaunchAgent.

## What happens on restart

1. Mac restarts, all Claude processes die
2. You log in
3. 10 seconds later, the restore agent reads the session files
4. Opens a single terminal window with one tab per dead session (default layout)
5. Each tab runs `claude --resume <session-id>` in the original directory
6. macOS notification confirms how many were restored

## Requirements

- macOS (uses LaunchAgents)
- Python 3 (ships with macOS)
- Claude Code CLI
- `tmux` (only if `LAYOUT=tmux`)
- `rumps` Python package (only if using the menu bar; installed automatically)

## Uninstall

```bash
claude-sessions uninstall
```
