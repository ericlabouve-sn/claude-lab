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
)
from textual.binding import Binding
from textual.reactive import reactive

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
• [green]a[/green] - Attach to tmux session
• [yellow]r[/yellow] - Refresh all
• [blue]n[/blue] - Create new lab
• [red]d[/red] - Teardown lab
"""


class NotificationsPanel(Static):
    """Display notifications"""

    selected_lab = reactive(None)

    def render(self) -> str:
        """Render the notifications panel"""
        notifications = get_notifications(limit=50)

        # Filter by lab if specified
        if self.selected_lab:
            notifications = [
                n for n in notifications
                if n.get("source") == self.selected_lab or self.selected_lab in n.get("message", "")
            ]

        if not notifications:
            return "[bold cyan]Notifications[/bold cyan]\n\n[dim]No notifications[/dim]"

        lines = ["[bold cyan]Notifications[/bold cyan]\n"]
        for notif in reversed(notifications[-15:]):  # Show last 15
            timestamp = notif["timestamp"][11:19]  # Just time
            level = notif["level"]
            source = notif.get("source", "system")
            message = notif["message"]

            emoji = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌"
            }
            color = {
                "info": "blue",
                "success": "green",
                "warning": "yellow",
                "error": "red"
            }

            line = (
                f"[dim]{timestamp}[/dim] "
                f"[{color.get(level, 'white')}]{emoji.get(level, '•')}[/] "
                f"[cyan]{source}[/cyan]: {message}"
            )
            lines.append(line)

        return "\n".join(lines)


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

    #notifications {
        height: 1fr;
        border: solid yellow;
        padding: 1;
        overflow-y: auto;
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
        Binding("a", "attach", "Attach"),
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
                yield NotificationsPanel(id="notifications")

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
            # Clear focus_lab after first use
            self.focus_lab = None

    def on_list_view_selected(self, event: ListView.Selected):
        """Handle lab selection"""
        if not self.labs_registry:
            return

        # Get the selected lab name from the index
        lab_names = list(self.labs_registry.keys())
        if 0 <= event.list_view.index < len(lab_names):
            selected_name = lab_names[event.list_view.index]
            selected_info = self.labs_registry[selected_name]

            # Update details panel
            details = self.query_one("#lab-details", LabDetailsPanel)
            details.selected_lab = selected_name
            details.selected_info = selected_info

            # Update notifications panel
            notifications = self.query_one("#notifications", NotificationsPanel)
            notifications.selected_lab = selected_name

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
        notifications = self.query_one("#notifications", NotificationsPanel)

        selected = self.get_selected_lab()
        if selected:
            name, info = selected
            details.selected_lab = name
            details.selected_info = info
            notifications.selected_lab = name

    def action_attach(self):
        """Attach to the selected lab's tmux session"""
        selected = self.get_selected_lab()
        if not selected:
            return

        name, _ = selected

        # Exit the TUI and attach to tmux
        self.exit()
        subprocess.run(["tmux", "attach", "-t", name])

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
