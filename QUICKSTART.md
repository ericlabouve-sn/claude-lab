# Claude Lab Manager - Quick Start Guide

## Installation (One-Time Setup)

Claude Lab is a **global CLI tool** - install it once, use it everywhere.

1. **Clone the claude-lab repository:**
   ```bash
   git clone https://github.com/yourusername/claude-lab.git
   cd claude-lab
   ```

2. **Install globally:**
   ```bash
   # Using uv (recommended)
   uv tool install .

   # Or using the Makefile
   make install-global
   ```

3. **Verify it works from any directory:**
   ```bash
   cd ~
   lab --help
   ```

4. **Check system requirements:**
   ```bash
   lab check
   ```

5. **Install missing tools** (if any):
   ```bash
   lab install
   ```

✨ That's it! Now `lab` is available everywhere.

## Basic Usage

### (Optional) Build a Base Image

For faster lab startup, pre-build an image with tools:

```bash
# Build the base image (recommended for first-time setup)
labimage-build --template base
```

This is optional but recommended - it pre-installs kubectl, helm, k9s, and other tools.

### Create Your First Lab

```bash
# With pre-built image (faster)
labsetup --name my-first-lab --image claude-lab:base

# Or without (uses default Claude sandbox)
labsetup --name my-first-lab
```

This will:
- ✓ Create a git worktree at `../my-first-lab`
- ✓ Spin up a k3d cluster
- ✓ Launch Claude Sandbox in tmux

### Connect to Your Lab

```bash
tmux attach -t my-first-lab
```

### Check What's Running

```bash
lablist
```

### Clean Up When Done

```bash
labteardown --name my-first-lab
```

## Common Commands

### Lab Management

| Command | Description |
|---------|-------------|
| `labcheck` | Check system requirements |
| `labsetup --name <name>` | Create new lab |
| `lablist` | List all labs |
| `labteardown --name <name>` | Remove lab |
| `labnotify --message "..."` | Send notification |
| `labnotifications` | View notification history |
| `labstatus` | Interactive status view |

### Image Management

| Command | Description |
|---------|-------------|
| `labimage-build --template <name>` | Build Docker image |
| `labimage-list` | List templates and images |
| `labimage-update --template <name>` | Rebuild image |
| `labimage-delete --image-tag <tag>` | Delete image |
| `labimage-inspect --image-tag <tag>` | Inspect image |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_LAB_WORKTREE_DIR` | `..` | Where to create worktrees |
| `CLAUDE_LAB_BASE_PORT` | `8080` | Starting port for labs |

Example:
```bash
export CLAUDE_LAB_WORKTREE_DIR="/Users/me/labs"
export CLAUDE_LAB_BASE_PORT=9000
labsetup --name custom-location
```

## Tmux Cheat Sheet

| Command | Description |
|---------|-------------|
| `tmux attach -t <name>` | Connect to lab session |
| `Ctrl+B`, then `D` | Detach from session |
| `tmux ls` | List all sessions |
| `tmux kill-session -t <name>` | Kill a session |

## Kubernetes Access

Inside a lab session:

```bash
# Check cluster is running
kubectl get nodes

# Deploy something
kubectl apply -f manifests/

# Check pods
kubectl get pods -A

# Install helm chart
helm install my-app charts/my-app/
```

## Notifications

From within a lab:

```bash
# Info
labnotify --message "Starting deployment" --level info

# Success
labnotify --message "Tests passed!" --level success

# Warning
labnotify --message "High memory usage" --level warning

# Error
labnotify --message "Build failed" --level error
```

View notifications:
```bash
labnotifications --last 10
```

## Troubleshooting

### "Docker not running"
```bash
# Start Docker Desktop
open -a Docker
```

### "Port already in use"
```bash
# List active labs and their ports
lablist

# Tear down unused labs
labteardown --name <unused-lab>
```

### "Worktree already exists"
```bash
# List worktrees
git worktree list

# Remove stale worktree
git worktree remove <path> --force
```

### "k3d cluster won't start"
```bash
# Check Docker resources
docker system df
docker stats

# Ensure enough RAM allocated to Docker (8GB+ recommended)
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [examples/](examples/) for integration examples
3. See [CLAUDE.md](CLAUDE.md) for Claude Code integration details
4. Review [.claude/skills/claude-lab/SKILL.md](.claude/skills/claude-lab/SKILL.md) for skill usage

## Getting Help

- Check logs: `tmux attach -t <name>` and review output
- View notifications: `labnotifications`
- System check: `labcheck`
- List active labs: `lablist`

## Tips

1. **Use descriptive names**: `feature-auth-v2` not `test1`
2. **Clean up regularly**: Don't let labs pile up
3. **Monitor Docker resources**: Each lab uses RAM/CPU
4. **Use branches**: `--branch develop` for specific work
5. **Force flag**: Only use `--force` when necessary

## Examples

### Parallel Feature Development

```bash
# Create three labs for parallel work
labsetup --name feature-api --branch main
labsetup --name feature-ui --branch main
labsetup --name bugfix-auth --branch develop

# Work in each (separate terminals)
tmux attach -t feature-api
tmux attach -t feature-ui
tmux attach -t bugfix-auth

# Clean up when done
labteardown --name feature-api
labteardown --name feature-ui
labteardown --name bugfix-auth
```

### Quick Test Environment

```bash
# Spin up for quick test
labsetup --name quick-test

# Connect and test
tmux attach -t quick-test
# ... do testing ...
# Ctrl+B, D to detach

# Tear down immediately
labteardown --name quick-test
```

## Advanced: CI/CD Integration

See [examples/python-integration.py](examples/python-integration.py) for programmatic usage in automation pipelines.
