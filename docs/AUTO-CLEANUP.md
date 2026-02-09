# Automatic Cleanup

Claude Lab Manager can automatically clean up lab environments when Claude Code sessions end or when resources become orphaned.

## Cleanup Command

### Basic Usage

```bash
# Show what would be cleaned up
lab cleanup --dry-run

# Clean up orphaned labs (interactive confirmation)
lab cleanup

# Clean up all labs (no confirmation)
lab cleanup --all

# Clean up labs older than 24 hours
lab cleanup --older-than 24
```

### What Gets Cleaned Up

The cleanup command identifies labs that:

1. **Tmux session stopped** - The lab's tmux session is no longer running
2. **k3d cluster missing** - The k3d cluster was deleted manually
3. **Worktree missing** - The git worktree directory doesn't exist
4. **Too old** - Lab is older than specified hours (with `--older-than`)
5. **Auto-cleanup enabled** - Lab was created with auto-cleanup flag

### Examples

```bash
# Dry run to see what would be cleaned up
lab cleanup --dry-run

# Clean up only orphaned labs
lab cleanup

# Clean up everything
lab cleanup --all

# Clean up labs older than 6 hours
lab cleanup --older-than 6

# Combine: clean old and orphaned labs
lab cleanup --older-than 12 --dry-run
```

## Auto-Cleanup on Lab Creation

Enable auto-cleanup when creating a lab:

```bash
# Set environment variable before creating lab
export CLAUDE_LAB_AUTO_CLEANUP=true
lab setup temp-lab

# This lab will be marked for auto-cleanup
# and removed by periodic cleanup jobs
```

## Claude Code Session Integration

### Method 1: Manual Cleanup (Recommended)

Run cleanup at the end of your Claude Code session:

```bash
# Before ending session
lab cleanup

# Or add to your workflow
lab teardown my-lab  # Clean specific lab
```

### Method 2: Exit Hook

Create a cleanup script that runs when your shell exits:

```bash
# Add to ~/.bashrc or ~/.zshrc
function claude_lab_cleanup() {
    if command -v lab &> /dev/null; then
        lab cleanup --older-than 24 &
    fi
}

# Run on exit
trap claude_lab_cleanup EXIT
```

### Method 3: Tmux Hook

Configure tmux to cleanup when sessions end:

```bash
# Add to ~/.tmux.conf
set-hook -g session-closed 'run-shell "lab cleanup --dry-run >> /tmp/lab-cleanup.log 2>&1"'
```

### Method 4: Periodic Cron Job

Run cleanup periodically:

```bash
# Edit crontab
crontab -e

# Add cleanup job (runs every hour)
0 * * * * /usr/local/bin/lab cleanup --older-than 24 >> /tmp/lab-cleanup.log 2>&1

# Or every 6 hours
0 */6 * * * /usr/local/bin/lab cleanup --older-than 12

# Or daily at 2am
0 2 * * * /usr/local/bin/lab cleanup --older-than 48
```

### Method 5: Systemd Timer (Linux)

Create a systemd timer for automatic cleanup:

```bash
# /etc/systemd/system/claude-lab-cleanup.service
[Unit]
Description=Claude Lab Cleanup Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/lab cleanup --older-than 24
User=%u

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/claude-lab-cleanup.timer
[Unit]
Description=Claude Lab Cleanup Timer

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:

```bash
systemctl --user enable claude-lab-cleanup.timer
systemctl --user start claude-lab-cleanup.timer
systemctl --user status claude-lab-cleanup.timer
```

### Method 6: launchd (macOS)

Create a launchd agent for automatic cleanup:

```xml
<!-- ~/Library/LaunchAgents/com.claudelab.cleanup.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claudelab.cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/lab</string>
        <string>cleanup</string>
        <string>--older-than</string>
        <string>24</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/claude-lab-cleanup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/claude-lab-cleanup-error.log</string>
</dict>
</plist>
```

Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.claudelab.cleanup.plist
launchctl start com.claudelab.cleanup
launchctl list | grep claudelab
```

## Session Tracking

Labs now track session information:

```json
{
  "my-lab": {
    "port": 8080,
    "api_port": 9080,
    "dir": "/path/to/worktree",
    "branch": "main",
    "created": "2024-01-15T10:30:00",
    "pid": 12345,
    "ppid": 12344,
    "session_id": "claude-session-abc123",
    "auto_cleanup": false
  }
}
```

This enables:
- Tracking which labs belong to which sessions
- Identifying orphaned labs
- Auto-cleanup based on session state

## Cleanup Strategies

### Conservative (Manual)

```bash
# Review what needs cleanup
lab cleanup --dry-run

# Selectively teardown specific labs
lab teardown lab1
lab teardown lab2

# Or clean up orphaned only
lab cleanup
```

### Moderate (Scheduled)

```bash
# Daily cleanup of old labs (cron)
0 2 * * * /usr/local/bin/lab cleanup --older-than 48

# Check before ending work
alias end-work='lab cleanup --dry-run && lab list'
```

### Aggressive (Automatic)

```bash
# Short-lived labs with auto-cleanup
export CLAUDE_LAB_AUTO_CLEANUP=true
lab setup temp-lab

# Frequent cleanup (hourly)
0 * * * * /usr/local/bin/lab cleanup --older-than 6
```

## Best Practices

### 1. Regular Cleanup

Run cleanup regularly to avoid resource exhaustion:

```bash
# Add to your daily routine
alias lab-status='lab list && lab cleanup --dry-run'
```

### 2. Name Labs Meaningfully

Use descriptive names to identify important labs:

```bash
# Good - clearly shows purpose and importance
lab setup feature-auth-prod
lab setup temp-test-123

# During cleanup, you'll know which to keep
```

### 3. Use Time-based Cleanup

Set up automatic cleanup for old labs:

```bash
# Clean up labs older than 2 days
lab cleanup --older-than 48
```

### 4. Pre-session Cleanup

Clean up before starting new work:

```bash
# Add to your startup script
lab cleanup --older-than 24
lab list
```

### 5. Notifications

Monitor cleanup activity:

```bash
# Check cleanup history
lab notifications | grep cleanup

# Watch cleanup in real-time
lab notifications --follow
```

## Troubleshooting

### Cleanup Not Working

```bash
# Check what would be cleaned up
lab cleanup --dry-run

# Force cleanup of specific lab
lab teardown my-lab --force

# Manually clean up resources
k3d cluster delete my-lab
git worktree remove /path/to/worktree --force
tmux kill-session -t my-lab
```

### Cron Job Not Running

```bash
# Check cron logs
tail -f /var/log/cron
# or
tail -f /tmp/lab-cleanup.log

# Test command manually
/usr/local/bin/lab cleanup --older-than 24

# Ensure PATH is set in crontab
PATH=/usr/local/bin:/usr/bin:/bin
0 * * * * lab cleanup --older-than 24
```

### Systemd Timer Not Running

```bash
# Check timer status
systemctl --user status claude-lab-cleanup.timer

# Check service logs
journalctl --user -u claude-lab-cleanup.service

# Restart timer
systemctl --user restart claude-lab-cleanup.timer
```

## Environment Variables

Control cleanup behavior with environment variables:

```bash
# Enable auto-cleanup for new labs
export CLAUDE_LAB_AUTO_CLEANUP=true

# Set default cleanup age (hours)
export CLAUDE_LAB_CLEANUP_AGE=24

# Session tracking (automatically set by Claude Code)
export CLAUDE_SESSION_ID=session-abc123
```

## Integration Examples

### Claude Code Workflow

```bash
# 1. Start session, create lab
lab setup feature-xyz

# 2. Work in lab
tmux attach -t feature-xyz

# 3. Before ending Claude session
lab cleanup --dry-run
lab teardown feature-xyz  # or lab cleanup
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - run: lab setup ci-${{ github.run_id }}
      - run: # run tests
      - run: lab teardown ci-${{ github.run_id }}
        if: always()  # Always cleanup
```

### Shell Script

```bash
#!/bin/bash
set -e

# Create temp lab
export CLAUDE_LAB_AUTO_CLEANUP=true
lab setup temp-$$

# Ensure cleanup on exit
trap "lab teardown temp-$$" EXIT

# Do work
tmux send-keys -t temp-$$ "kubectl apply -f manifests/" Enter

# Automatic cleanup on exit
```

## Summary

Automatic cleanup options:

| Method | Complexity | Reliability | Best For |
|--------|------------|-------------|----------|
| Manual cleanup | Low | High | Development |
| Exit hook | Medium | Medium | Personal use |
| Cron job | Medium | High | Server/always-on |
| Systemd timer | High | High | Linux servers |
| launchd | High | High | macOS |
| Auto-cleanup flag | Low | High | Temporary labs |

**Recommended setup:**

1. Enable periodic cleanup (cron/systemd)
2. Use `--older-than` for automatic age-based cleanup
3. Set `CLAUDE_LAB_AUTO_CLEANUP=true` for temporary labs
4. Manually review with `lab cleanup --dry-run` regularly
