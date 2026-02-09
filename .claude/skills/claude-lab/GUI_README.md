# Claude Lab Manager - Terminal GUI

A beautiful terminal user interface (TUI) for managing K3s lab environments.

## Features

### Current Features ✅

- **Interactive Lab List**: Browse all active lab environments with arrow keys
- **Real-time Status**: See which labs are running (🟢) or stopped (🔴)
- **Detailed Lab View**: View comprehensive information about selected labs
  - Name, branch, status
  - Directory location
  - HTTP and API ports
  - Creation timestamp
- **Notifications Panel**: Monitor activity across all labs
  - Filtered by selected lab
  - Color-coded by severity (info, success, warning, error)
  - Timestamped entries
- **Quick Actions**:
  - `a` - Attach to lab's tmux session
  - `r` - Refresh all data
  - `q` - Quit GUI

### Navigation

| Key | Action |
|-----|--------|
| `↑`/`↓` or `j`/`k` | Navigate lab list |
| `Enter` | Select lab to view details |
| `a` | Attach to selected lab's tmux session |
| `r` | Refresh all panels |
| `n` | Create new lab (coming soon) |
| `d` | Delete selected lab (coming soon) |
| `q` | Quit |

## Usage

### Quick Start

```bash
# Launch the GUI
lab gui
```

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Claude Lab Manager                Interactive Environment Management│
├──────────────────┬───────────────────────────────────────────────┤
│ Lab Environments │ Lab Details                                   │
│                  │                                               │
│ 🟢 feature-api   │ Name: feature-api                             │
│ 🔴 test-cluster  │ Status: 🟢 Running                            │
│ 🟢 demo-v2       │ Branch: feature/new-api                       │
│                  │ Directory: ../feature-api                     │
│                  │ HTTP Port: 8080                               │
│                  │ API Port: 9080                                │
│                  │ Created: 2026-02-08 10:30:15                  │
│                  │                                               │
│                  │ Available Actions:                            │
│                  │ • a - Attach to tmux session                  │
│                  │ • r - Refresh all                             │
│                  │ • n - Create new lab                          │
│                  │ • d - Teardown lab                            │
│                  ├───────────────────────────────────────────────┤
│                  │ Notifications                                 │
│                  │                                               │
│                  │ 10:32:45 ✅ feature-api: Tests passed!        │
│                  │ 10:31:20 ℹ️ feature-api: Starting deployment  │
│                  │ 10:30:15 ✅ setup: Lab 'feature-api' created  │
│                  │                                               │
└──────────────────┴───────────────────────────────────────────────┘
│ q quit │ r refresh │ n new-lab │ d delete │ a attach            │
└──────────────────────────────────────────────────────────────────┘
```

## Technical Details

### Architecture

The GUI is built with [Textual](https://textual.textualize.io/), a modern Python TUI framework that provides:

- Rich terminal rendering
- Reactive data binding
- CSS-like styling
- Event-driven architecture

### Components

1. **LabDetailsPanel**: Reactive widget showing selected lab information
2. **NotificationsPanel**: Auto-updating notification feed
3. **ListView**: Native Textual list for lab selection
4. **K3sLabGUI**: Main application controller

### Dependencies

- `textual` - TUI framework
- `rich` - Terminal formatting (already included)
- `click` - CLI integration (already included)

Dependencies are automatically installed by the `uv` shebang in `claude-lab.py`.

## Development

### Running the GUI Directly

```bash
# From the skill directory
cd ~/.claude/skills/claude-lab

# Run with uv (auto-installs dependencies)
uv run gui.py
```

### Testing Without Labs

The GUI gracefully handles an empty lab registry, showing:
- "No active labs" message in the sidebar
- Instructions to create a lab in the details panel

### Adding New Features

To add new features to the GUI:

1. **Add a new action**:
   - Add a binding in `BINDINGS`
   - Implement `action_<name>()` method
   - Update the details panel text

2. **Add a new panel**:
   - Create a new `Static` subclass with `reactive` variables
   - Add to `compose()` method
   - Update CSS for layout

3. **Add real-time updates**:
   - Use `set_interval()` for periodic updates
   - Use `watch_<variable>()` for reactive updates

## Future Enhancements

### Planned Features

- [ ] Interactive lab creation dialog
- [ ] Confirmation dialog for lab deletion
- [ ] Real-time resource monitoring (CPU, memory)
- [ ] Log streaming from labs (follow mode)
- [ ] Kubectl command execution from GUI
- [ ] Multi-lab selection for bulk operations
- [ ] Search/filter labs by name or branch
- [ ] Lab templates selection
- [ ] Port conflict resolution

### Ideas

- Integration with k9s for inline cluster management
- Gantt chart view of lab lifecycle
- GitHub integration for PR status
- Slack notifications from labs
- Lab snapshots and restore

## Troubleshooting

### GUI Won't Start

**Problem**: `ModuleNotFoundError: No module named 'textual'`

**Solution**: The script should auto-install via `uv`. If not:
```bash
pip install textual
```

### Garbled Display

**Problem**: Terminal shows incorrect characters or layout

**Solution**: Ensure you're using a modern terminal:
- iTerm2 (macOS)
- Windows Terminal (Windows)
- GNOME Terminal (Linux)
- Any terminal with 256 color support

### Can't Attach to Lab

**Problem**: Pressing `a` doesn't attach to tmux

**Solution**: Check that:
1. The lab's tmux session is running (should show 🟢)
2. You have tmux installed: `tmux -V`
3. The session name matches: `tmux ls`

## Examples

### Typical Workflow

```bash
# 1. Launch GUI
lab gui

# 2. Navigate with arrow keys to your target lab

# 3. Press 'a' to attach
# (GUI exits and drops you into the lab's tmux session)

# 4. Work in the lab
kubectl get pods
helm list

# 5. Detach from tmux (Ctrl+B, D)

# 6. Return to GUI
lab gui

# 7. Check notifications for updates from other labs
```

### Monitoring Multiple Labs

The GUI is perfect for monitoring multiple parallel labs:

1. Keep GUI open in one tmux pane
2. Work in labs in other panes
3. Labs send notifications via `lab notify`
4. Press `r` in GUI to refresh and see updates

## Contributing

To contribute to the GUI:

1. Follow the existing code style
2. Test with multiple labs (0, 1, 5+ labs)
3. Ensure all keybindings work
4. Update this README with new features
5. Add docstrings to new methods

## License

Part of the Claude Lab Manager skill for Claude Code.
