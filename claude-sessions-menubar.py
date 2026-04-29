#!/usr/bin/env python3
"""
claude-sessions menu bar item.

Shows a status icon in the macOS menu bar with the live session count and a
dropdown listing each session. Click a session to focus its iTerm2 tab (if
iTerm2 is being used); click "Restore Now" to run the restore command.

Dependencies: rumps (pip install --user rumps)

Usage:
    /usr/bin/python3 claude-sessions-menubar.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import rumps
except ImportError:
    print("rumps is not installed. Run: python3 -m pip install --user rumps", file=sys.stderr)
    sys.exit(1)

HOME = Path.home()
MANAGER_DIR = HOME / ".claude" / "session-manager"
SESSIONS_DIR = HOME / ".claude" / "sessions"
BACKUP = MANAGER_DIR / "backup-manifest.json"
CONFIG = MANAGER_DIR / "config"
LOG_FILE = MANAGER_DIR / "logs" / "claude-sessions.log"
NO_RESTORE_FLAG = MANAGER_DIR / ".no-restore"
CLI = MANAGER_DIR / "claude-sessions"

REFRESH_SECONDS = 10
MAX_SESSIONS_IN_MENU = 30


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def read_sessions() -> list[dict[str, Any]]:
    """Read all interactive CLI sessions from ~/.claude/sessions/."""
    if not SESSIONS_DIR.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            s = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if s.get("kind") != "interactive" or s.get("entrypoint") != "cli":
            continue
        s["_alive"] = pid_alive(int(s.get("pid", 0)))
        out.append(s)
    return out


def short_label(s: dict[str, Any]) -> str:
    name = (s.get("name") or "").strip()
    if name:
        return name
    cwd = s.get("cwd", "")
    return os.path.basename(cwd) or (s.get("sessionId", "")[:8])


def focus_iterm_tab(session_id: str) -> None:
    """Bring iTerm2 forward and select the tab whose name matches the session's label.
    Since tabs are named by short_label, we search for a matching tab name.
    Falls back to activating iTerm2 if nothing matches.
    """
    # Find the session to get its label
    sessions = read_sessions()
    target = next((s for s in sessions if s.get("sessionId") == session_id), None)
    if not target:
        subprocess.run(["osascript", "-e", 'tell application "iTerm2" to activate'])
        return
    label = short_label(target).replace('"', '\\"')
    script = f'''
tell application "iTerm2"
    activate
    repeat with w in windows
        repeat with t in tabs of w
            repeat with sess in sessions of t
                if name of sess is "{label}" then
                    select t
                    return
                end if
            end repeat
        end repeat
    end repeat
end tell
'''
    subprocess.run(["osascript", "-e", script])


def run_cli(*args: str) -> None:
    if not CLI.exists():
        rumps.alert("claude-sessions", f"CLI not found at {CLI}")
        return
    subprocess.Popen([str(CLI), *args])


def open_path(path: Path) -> None:
    subprocess.run(["open", str(path)])


class ClaudeSessionsApp(rumps.App):
    def __init__(self) -> None:
        super().__init__("⎋ 0", quit_button=None)
        self._build_menu()
        rumps.Timer(self._refresh, REFRESH_SECONDS).start()
        # First paint
        self._refresh(None)

    def _build_menu(self) -> None:
        self.session_items: list[rumps.MenuItem] = []
        self.status_item = rumps.MenuItem("Loading…")
        self.status_item.set_callback(None)
        self.menu = [
            self.status_item,
            None,
            rumps.MenuItem("Restore Now", callback=self._restore),
            rumps.MenuItem("Disable Auto-Restore", callback=self._toggle_auto_restore),
            None,
            rumps.MenuItem("Open Status in Terminal", callback=self._open_status),
            rumps.MenuItem("Open Logs", callback=self._open_logs),
            rumps.MenuItem("Open Config", callback=self._open_config),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]

    # ─── Menu actions ───────────────────────────────────────────────────────
    def _restore(self, _: rumps.MenuItem) -> None:
        run_cli("restore")

    def _toggle_auto_restore(self, sender: rumps.MenuItem) -> None:
        if NO_RESTORE_FLAG.exists():
            run_cli("enable")
            sender.title = "Disable Auto-Restore"
        else:
            run_cli("disable")
            sender.title = "Enable Auto-Restore"

    def _open_status(self, _: rumps.MenuItem) -> None:
        script = f'''
tell application "Terminal"
    activate
    do script "{CLI} status"
end tell
'''
        subprocess.run(["osascript", "-e", script])

    def _open_logs(self, _: rumps.MenuItem) -> None:
        if LOG_FILE.exists():
            open_path(LOG_FILE)

    def _open_config(self, _: rumps.MenuItem) -> None:
        if CONFIG.exists():
            open_path(CONFIG)

    def _focus_session(self, session_id: str):
        def _callback(_: rumps.MenuItem) -> None:
            focus_iterm_tab(session_id)
        return _callback

    # ─── Refresh ────────────────────────────────────────────────────────────
    def _refresh(self, _timer: rumps.Timer | None) -> None:
        try:
            sessions = read_sessions()
        except Exception as e:
            self.title = "⎋ ?"
            self.status_item.title = f"Error: {e}"
            return

        alive = [s for s in sessions if s.get("_alive")]
        dead = [s for s in sessions if not s.get("_alive")]

        # Update icon/title
        self.title = f"⎋ {len(alive)}"
        status_bits = [f"{len(alive)} live"]
        if dead:
            status_bits.append(f"{len(dead)} stale")
        if NO_RESTORE_FLAG.exists():
            status_bits.append("auto-restore OFF")
        self.status_item.title = " · ".join(status_bits)

        # Rebuild the session list section of the menu. rumps doesn't support
        # "replace a slice" well, so we clear and rebuild.
        self.menu.clear()
        self.menu.add(self.status_item)
        self.menu.add(rumps.separator)

        # Live sessions (click to focus iTerm tab)
        if alive:
            header = rumps.MenuItem(f"— Live ({len(alive)}) —")
            header.set_callback(None)
            self.menu.add(header)
            for s in alive[:MAX_SESSIONS_IN_MENU]:
                label = short_label(s)
                cwd = s.get("cwd", "")
                # Display: "IDXsiteOG  —  /Volumes/workplace/IDXsiteOG"
                disp = f"{label}  —  {cwd.replace(str(HOME), '~')}"
                item = rumps.MenuItem(disp, callback=self._focus_session(s["sessionId"]))
                self.menu.add(item)
            if len(alive) > MAX_SESSIONS_IN_MENU:
                overflow = rumps.MenuItem(f"… +{len(alive) - MAX_SESSIONS_IN_MENU} more")
                overflow.set_callback(None)
                self.menu.add(overflow)
            self.menu.add(rumps.separator)

        # Stale sessions (informational only)
        if dead:
            header = rumps.MenuItem(f"— Stale ({len(dead)}) —")
            header.set_callback(None)
            self.menu.add(header)
            for s in dead[:10]:
                label = short_label(s)
                cwd = s.get("cwd", "").replace(str(HOME), "~")
                self.menu.add(rumps.MenuItem(f"{label}  —  {cwd}", callback=None))
            self.menu.add(rumps.separator)

        # Actions
        auto_restore_label = (
            "Enable Auto-Restore" if NO_RESTORE_FLAG.exists() else "Disable Auto-Restore"
        )
        self.menu.add(rumps.MenuItem("Restore Now", callback=self._restore))
        self.menu.add(rumps.MenuItem(auto_restore_label, callback=self._toggle_auto_restore))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Open Status in Terminal", callback=self._open_status))
        self.menu.add(rumps.MenuItem("Open Logs", callback=self._open_logs))
        self.menu.add(rumps.MenuItem("Open Config", callback=self._open_config))
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))


def main() -> None:
    ClaudeSessionsApp().run()


if __name__ == "__main__":
    main()
