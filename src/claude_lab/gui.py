"""
Terminal GUI for Claude Lab Manager
Built with Textual for interactive lab management
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Static,
    RichLog,
)
from textual.binding import Binding
from textual.reactive import reactive
import threading
import time

REGISTRY_PATH = Path.home() / ".claude-lab-port-registry.json"
NOTIFICATIONS_PATH = Path.home() / ".claude-lab-notifications.jsonl"


def get_registry() -> Dict:
    """Load the port registry from disk"""
    if not REGISTRY_PATH.exists():
        return {}
    return json.loads(REGISTRY_PATH.read_text())


def get_notifications(limit: Optional[int] = None) -> List[Dict]:
    """Load notifications from disk"""
    if not NOTIFICATIONS_PATH.exists():
        return []

    with open(NOTIFICATIONS_PATH) as f:
        lines = f.readlines()

    if limit:
        lines = lines[-limit:]

    notifications = []
    for line in lines:
        try:
            notifications.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return notifications


def check_tmux_session(name: str) -> bool:
    """Check if a tmux session is running"""
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        capture_output=True,
    )
    return result.returncode == 0


class LabDetailsPanel(Static):
    """Display details about the selected lab"""

    selected_lab = reactive(None)
    selected_info = reactive(None)

    def render(self) -> str:
        """Render the details panel"""
        if not self.selected_lab or not self.selected_info:
            return "[dim]Select a lab to view details[/dim]"

        status = "🟢 Running" if check_tmux_session(self.selected_lab) else "🔴 Stopped"

        return f"""[bold cyan]Lab Details[/bold cyan]

[bold]Name:[/bold] {self.selected_lab}
[bold]Status:[/bold] {status}
[bold]Branch:[/bold] {self.selected_info.get('branch', 'unknown')}
[bold]Directory:[/bold] {self.selected_info.get('dir', 'N/A')}
[bold]HTTP Port:[/bold] {self.selected_info.get('port', 'N/A')}
[bold]API Port:[/bold] {self.selected_info.get('api_port', 'N/A')}
[bold]Created:[/bold] {self.selected_info.get('created', 'N/A')[:19]}

[bold cyan]Available Actions:[/bold cyan]
• [green]Enter[/green] - Attach to tmux session
• [yellow]r[/yellow] - Refresh all
• [blue]n[/blue] - Create new lab
• [red]d[/red] - Teardown lab
"""


class ClaudeLogsPanel(Static):
    """Display recent Claude Code logs from the selected lab"""

    selected_lab = reactive(None)

    def render(self) -> str:
        """Render the Claude logs panel"""
        if not self.selected_lab:
            return "[bold cyan]Claude Code Logs[/bold cyan]\n\n[dim]Select a lab to view logs[/dim]"

        # Check if tmux session is running
        if not check_tmux_session(self.selected_lab):
            return f"[bold cyan]Claude Code Logs[/bold cyan]\n\n[dim]Lab '{self.selected_lab}' is not running[/dim]"

        # Capture recent tmux pane output
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-t", self.selected_lab, "-S", "-100"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                # Take last 30 lines to fit in panel
                recent_lines = lines[-30:]
                log_content = "\n".join(recent_lines)
                return f"[bold cyan]Claude Code Logs[/bold cyan] [dim](last 30 lines)[/dim]\n\n{log_content}"
            else:
                return f"[bold cyan]Claude Code Logs[/bold cyan]\n\n[dim]No output available[/dim]"
        except Exception as e:
            return f"[bold cyan]Claude Code Logs[/bold cyan]\n\n[yellow]Error capturing logs: {e}[/yellow]"


class ClaudeLabGUI(App):
    """Terminal GUI for Claude Lab Manager"""

    CSS = """
    Screen {
        layout: horizontal;
    }

    #sidebar {
        width: 30;
        border: solid cyan;
        padding: 1;
    }

    #main-panel {
        width: 1fr;
        layout: vertical;
    }

    #lab-details {
        height: 1fr;
        border: solid green;
        padding: 1;
    }

    #claude-logs {
        height: 1fr;
        border: solid yellow;
        padding: 1;
        overflow-y: auto;
    }

    ListItem Label {
        width: 100%;
    }

    ListView {
        height: 1fr;
    }

    ListItem {
        padding: 0 1;
    }

    Footer {
        background: $boost;
    }

    .lab-header {
        text-align: center;
        background: $primary;
        padding: 1;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "new_lab", "New Lab"),
        Binding("d", "delete_lab", "Delete"),
    ]

    def __init__(self, focus_lab=None):
        super().__init__()
        self.labs_registry = {}
        self.focus_lab = focus_lab  # Lab to focus on when GUI opens

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header()

        with Horizontal():
            # Left sidebar with lab list
            with Vertical(id="sidebar"):
                yield Static("[bold cyan]Lab Environments[/bold cyan]", classes="lab-header")
                yield ListView(id="lab-list")

            # Right main panel
            with Vertical(id="main-panel"):
                yield LabDetailsPanel(id="lab-details")
                yield ClaudeLogsPanel(id="claude-logs")

        yield Footer()

    def on_mount(self):
        """Called when app is mounted"""
        self.title = "Claude Lab Manager"
        self.sub_title = "Interactive Environment Management"
        self.refresh_labs()

    def refresh_labs(self):
        """Refresh the list of labs"""
        self.labs_registry = get_registry()
        lab_list = self.query_one("#lab-list", ListView)

        # Clear and repopulate
        lab_list.clear()

        if not self.labs_registry:
            lab_list.append(ListItem(Label("[dim]No active labs[/dim]")))
            return

        focus_index = 0  # Default to first item
        for idx, (name, info) in enumerate(self.labs_registry.items()):
            status = "🟢" if check_tmux_session(name) else "🔴"
            branch = info.get("branch", "?")
            port = info.get("port", "?")

            label = Label(f"{status} [cyan]{name}[/cyan] ({branch}:{port})")
            lab_list.append(ListItem(label))

            # Track index of lab to focus on
            if self.focus_lab and name == self.focus_lab:
                focus_index = idx

        # Auto-select focused lab or first item
        if len(lab_list.children) > 0:
            lab_list.index = focus_index

            # Trigger initial display of details
            lab_names = list(self.labs_registry.keys())
            if 0 <= focus_index < len(lab_names):
                selected_name = lab_names[focus_index]
                selected_info = self.labs_registry[selected_name]

                # Update panels
                details = self.query_one("#lab-details", LabDetailsPanel)
                details.selected_lab = selected_name
                details.selected_info = selected_info

                logs = self.query_one("#claude-logs", ClaudeLogsPanel)
                logs.selected_lab = selected_name

            # Clear focus_lab after first use
            self.focus_lab = None

    def on_list_view_highlighted(self, event: ListView.Highlighted):
        """Handle lab navigation (arrow keys) - show details proactively"""
        if not self.labs_registry:
            return

        # Get the highlighted lab name from the index
        lab_names = list(self.labs_registry.keys())
        if event.list_view.index is not None and 0 <= event.list_view.index < len(lab_names):
            selected_name = lab_names[event.list_view.index]
            selected_info = self.labs_registry[selected_name]

            # Update details panel
            details = self.query_one("#lab-details", LabDetailsPanel)
            details.selected_lab = selected_name
            details.selected_info = selected_info

            # Update logs panel
            logs = self.query_one("#claude-logs", ClaudeLogsPanel)
            logs.selected_lab = selected_name

    def on_list_view_selected(self, event: ListView.Selected):
        """Handle lab selection (Enter key) - attach to lab"""
        # Enter key now triggers attach action directly
        self.action_attach()

    def get_selected_lab(self) -> Optional[tuple]:
        """Get the currently selected lab name"""
        lab_list = self.query_one("#lab-list", ListView)
        if not self.labs_registry or lab_list.index is None:
            return None

        lab_names = list(self.labs_registry.keys())
        if 0 <= lab_list.index < len(lab_names):
            name = lab_names[lab_list.index]
            return (name, self.labs_registry[name])

        return None

    def action_quit(self):
        """Quit the application"""
        self.exit()

    def action_refresh(self):
        """Refresh all data"""
        self.refresh_labs()

        # Trigger re-render of panels
        details = self.query_one("#lab-details", LabDetailsPanel)
        logs = self.query_one("#claude-logs", ClaudeLogsPanel)

        selected = self.get_selected_lab()
        if selected:
            name, info = selected
            details.selected_lab = name
            details.selected_info = info
            logs.selected_lab = name

    def action_attach(self):
        """Attach to the selected lab's tmux session in a new Terminal window"""
        selected = self.get_selected_lab()
        if not selected:
            self.notify("No lab selected")
            return

        name, info = selected

        # Check if tmux session is running
        if not check_tmux_session(name):
            self.notify(f"Lab '{name}' tmux session is not running")
            return

        # Open a new Terminal window with tmux attach
        # This keeps the GUI running while opening the session
        try:
            subprocess.Popen([
                "osascript",
                "-e", "tell application \"Terminal\" to activate",
                "-e", f'tell application "Terminal" to do script "tmux attach -t {name}"'
            ])
            self.notify(f"Opening tmux session for '{name}' in new Terminal window")
        except Exception as e:
            self.notify(f"Failed to open terminal: {e}", severity="error")

    def action_new_lab(self):
        """Create a new lab"""
        # For now, just show a message
        # TODO: Implement interactive lab creation dialog
        self.notify("Lab creation via GUI coming soon! Use 'lab setup <name>' for now.")

    def action_delete_lab(self):
        """Delete the selected lab"""
        selected = self.get_selected_lab()
        if not selected:
            return

        name, _ = selected

        # For now, just show a message
        # TODO: Implement confirmation dialog
        self.notify(f"Lab deletion via GUI coming soon! Use 'lab teardown {name}' for now.")


def run_gui(focus_lab=None):
    """Entry point for the GUI"""
    app = ClaudeLabGUI(focus_lab=focus_lab)
    app.run()


if __name__ == "__main__":
    run_gui()
