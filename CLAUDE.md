# Claude Code Project Configuration

This project uses the Claude Lab Manager skill for parallel development workflows.

## Available Skills

### claude-lab

Use the `/claude-lab` skill when you need to work on a task in an isolated environment with its own:
- Git worktree
- k3d Kubernetes cluster
- Dedicated ports
- Tmux session

## Workflow Guidelines

### When to Use claude-lab

Use claude-lab for:
- **Feature development** that requires Kubernetes testing
- **Parallel work** on multiple branches simultaneously
- **Isolation** to avoid conflicts with main development environment
- **Experimentation** with cluster configurations
- **Integration testing** with full k8s API access

### Configuration System

Claude Lab uses a three-tier configuration system:

**1. Global Settings** - `~/.lab/settings.yaml` (user-wide defaults)
**2. Project Settings** - `.lab/settings.yaml` (project-specific)
**3. Command-line** - Flags override everything

#### Settings Precedence

1. Command-line arguments - `lab setup --image my-image` (highest)
2. Project settings - `.lab/settings.yaml` in project root
3. Global settings - `~/.lab/settings.yaml` in home directory
4. Environment variables - `CLAUDE_LAB_*`
5. Built-in defaults - `/tmp/claude-labs`, `claude`, `8080` (lowest)

#### Initialize Settings

```bash
# Create global settings (applies to all projects)
lab init --global

# Create project settings (applies to this project only)
lab init
```

#### Example: Global Settings

```yaml
# ~/.lab/settings.yaml
worktree_dir: "/tmp/claude-labs"
docker_image: "claude"

additional_mounts:
  - "~/.aws/credentials:/root/.aws/credentials:ro"
```

#### Example: Project Settings

```yaml
# .lab/settings.yaml
docker_image: "claude-lab:k8s-full"  # Override global default
base_port: 9000

environment:
  NODE_ENV: "development"
```

See `.lab/README.md` (project) or `~/.lab/README.md` (global) for complete documentation.

### Environment Variables (Global Defaults)

These can be overridden by project settings:

- `CLAUDE_LAB_WORKTREE_DIR`: Override default worktree directory (default: `/tmp/claude-labs`)
- `CLAUDE_LAB_BASE_PORT`: Override starting port number (default: `8080`)
- `CLAUDE_LAB_DOCKER_IMAGE`: Override default Docker image (default: `claude`)

### Example Usage

#### GUI Mode (Recommended for Humans)

```bash
# Launch the interactive terminal GUI
lab gui

# Use arrow keys to navigate labs
# Press 'a' to attach to a lab's tmux session
# Press 'r' to refresh all data
# Press 'q' to quit
```

#### CLI Mode (For Automation)

```bash
# Check if system is ready
lab check

# Create a new isolated environment
lab setup feature-new-api

# Work in the environment
tmux attach -t feature-new-api

# From within the lab, you have kubectl access
kubectl get nodes
helm list

# Send progress updates
lab notify --message "API endpoint implemented" --level success

# When done, clean up
lab teardown feature-new-api
```

## Automated Workflows

You can automate lab management in CI/CD:

```yaml
# .github/workflows/parallel-tests.yml
name: Parallel Tests
on: [push]

jobs:
  test-claude-lab:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v2
      - run: labcheck
      - run: labsetup --name ci-${{ github.run_id }}
      - run: tmux send-keys -t ci-${{ github.run_id }} "kubectl apply -f manifests/" Enter
      - run: labteardown --name ci-${{ github.run_id }}
```

## Best Practices

1. **Always tear down labs** when finished to free resources
2. **Use descriptive names** for labs (e.g., `feature-auth-v2`, `bugfix-memory-leak`)
3. **Monitor notifications** to track progress across labs
4. **Check lab.list regularly** to see active environments
5. **Use --force flag cautiously** when tearing down (may lose uncommitted work)

## Port Allocation

Each lab gets two ports:
- **HTTP Port**: For LoadBalancer/Ingress (auto-assigned, starting at 8080)
- **API Port**: For Kubernetes API (HTTP port + 1000)

Ports are tracked in `~/.claude-lab-port-registry.json`.

## SSH Authentication

Your SSH identity is automatically shared with lab environments, allowing:
- Pushing to private git repositories
- Pulling from private container registries
- Accessing private helm charts

## Automatic Configuration Mounting

Lab environments automatically mount common configuration files (read-only) if they exist:

### `~/.claude` → `/root/.claude`
- **Global Skills**: Access to all your Claude Code skills within labs
- **Shared Configuration**: Consistent settings across all environments
- **Keybindings**: Your custom keyboard shortcuts work in labs
- **Project Templates**: Reuse project configurations

### `~/.gitconfig` → `/root/.gitconfig`
- **Commit Attribution**: Your name and email on all commits
- **Git Aliases**: All your custom git shortcuts work
- **Consistent Behavior**: Same git settings everywhere

### `~/.docker/config.json` → `/root/.docker/config.json`
- **Registry Authentication**: Pull from private Docker registries
- **No Re-login**: Credentials automatically available
- **Multi-registry Support**: All your configured registries work

All mounts are **read-only** to ensure labs cannot modify your global configurations. This provides a consistent development experience across all environments while maintaining security.

## GUI Mode

The Claude Lab Manager includes a beautiful terminal GUI for interactive management:

### Features

- **Interactive Lab List**: Browse all active labs with arrow keys
- **Real-time Status**: See which labs are running (🟢) or stopped (🔴)
- **Detailed Lab View**: View comprehensive information about each lab
- **Notifications Panel**: Monitor activity across all labs with color-coded messages
- **Quick Actions**: Attach to tmux sessions, refresh data, and more

### Navigation

| Key | Action |
|-----|--------|
| `↑`/`↓` or `j`/`k` | Navigate lab list |
| `Enter` | Select lab to view details |
| `a` | Attach to selected lab's tmux session |
| `r` | Refresh all panels |
| `q` | Quit |

### Layout

```
┌──────────────────────────────────────────────────────────┐
│ Claude Lab Manager         Interactive Management        │
├──────────────┬───────────────────────────────────────────┤
│ Labs         │ Lab Details                               │
│              │                                           │
│ 🟢 feature-api│ Name: feature-api                         │
│ 🔴 test-env   │ Status: 🟢 Running                        │
│ 🟢 demo-v2    │ Branch: feature/new-api                   │
│              │ ...                                       │
│              ├───────────────────────────────────────────┤
│              │ Notifications                             │
│              │                                           │
│              │ 10:32:45 ✅ feature-api: Tests passed!    │
│              │ 10:31:20 ℹ️ feature-api: Starting deploy  │
└──────────────┴───────────────────────────────────────────┘
```

See `.claude/skills/claude-lab/GUI_README.md` for complete documentation.

## Notifications

Labs can notify the main session:

```bash
# Info level
lab notify --message "Starting deployment" --level info

# Success level
lab notify --message "Tests passed!" --level success

# Warning level
lab notify --message "Memory usage high" --level warning

# Error level
lab notify --message "Deployment failed" --level error
```

View notifications:
```bash
# Show all
lab notifications

# Show last 20
lab notifications --last 20

# Follow in real-time
lab notifications --follow
```

Or use the GUI to view notifications in real-time with visual formatting.

## Resource Management

Each k3d cluster uses Docker resources. Ensure Docker Desktop has:
- **Memory**: 2GB+ per lab (8GB+ total recommended)
- **CPU**: 2+ cores per lab
- **Disk**: 10GB+ free space

Check Docker resources:
```bash
docker system df
docker stats
```

## Troubleshooting

### Lab Won't Start
1. Check system requirements: `labcheck`
2. Verify Docker is running: `docker ps`
3. Check port availability: `lablist`

### Stale Worktrees
```bash
git worktree list
git worktree prune
```

### Port Conflicts
Edit `~/.claude-lab-port-registry.json` to remove stale entries.

### Stuck Tmux Sessions
```bash
tmux ls
tmux kill-session -t <name>
```

## Development Workflow Example

```bash
# 1. Start a new feature lab
labsetup --name feature-webhook --branch main

# 2. Connect and develop
tmux attach -t feature-webhook

# 3. Inside the lab (as Claude or developer):
# - Edit code
# - kubectl apply -f manifests/
# - Run tests
# - Send notifications

# 4. When complete
labteardown --name feature-webhook
```

## Future Features (Roadmap)

- ✅ GUI mode for human-friendly interaction (COMPLETED)
- Interactive lab creation/deletion dialogs in GUI
- Auto-installation of tools in sandbox
- Lab templates for quick setup
- Resource limits per lab
- Multi-node cluster support
- Lab snapshots and restore
- Real-time resource monitoring in GUI
- Log streaming from labs in GUI
