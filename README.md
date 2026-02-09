# Claude Lab Manager

A Claude Code skill for orchestrating isolated k3d/Kubernetes environments with git worktrees, docker sandbox and tmux for isolated parallel development workflows.

## Overview

Claude Lab Manager allows you to:

- **Spin up isolated development environments** with their own k3d clusters, git worktrees, and tmux sessions
- **Run multiple Claude instances in parallel** working on different branches/features simultaneously
- **Auto-manage port allocation** to avoid conflicts between parallel clusters
- **Share SSH credentials** between host and sandbox for seamless git operations
- **Send notifications** from lab instances back to the main session

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Development Host                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Lab: feature-│  │ Lab: bugfix- │  │ Lab: refactor│     │
│  │ auth         │  │ login        │  │ -api         │     │
│  │              │  │              │  │              │     │
│  │ Git Worktree │  │ Git Worktree │  │ Git Worktree │     │
│  │ k3d Cluster  │  │ k3d Cluster  │  │ k3d Cluster  │     │
│  │ Claude Box   │  │ Claude Box   │  │ Claude Box   │     │
│  │ Tmux Session │  │ Tmux Session │  │ Tmux Session │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  Port Registry: ~/.claude-lab-port-registry.json                  │
│  Notifications: ~/.claude-lab-notifications.jsonl             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **Docker Desktop** (with sufficient RAM, 8GB+ recommended)
- **k3d** - k3s in Docker
- **tmux** - Terminal multiplexer
- **git** - Version control
- **Python 3.12+**
- **kubectl** (optional, can be auto-installed)
- **helm** (optional, can be auto-installed)

## Installation

Claude Lab is a **global CLI tool** - install it once, use it everywhere.

### Quick Install

```bash
# Clone the claude-lab repository
git clone https://github.com/yourusername/claude-lab.git
cd claude-lab

# Install globally with uv (recommended)
uv tool install .

# Or use the Makefile
make install-global
```

Now `lab` is available system-wide from any directory! ✨

### Verify Installation

```bash
# Check the lab command works from any directory
cd ~
lab --help

# Verify system requirements
lab check

# Install missing tools (docker, k3d, tmux, etc.)
lab install
```

### Important

- ✅ Install claude-lab **once** as a global tool
- ✅ Use it to manage **any** project
- ✅ No need to add claude-lab to your project dependencies
- ❌ Don't install claude-lab per-project

For detailed installation and architecture info:
- [INSTALL.md](INSTALL.md) - Complete installation guide
- [docs/GLOBAL-INSTALL.md](docs/GLOBAL-INSTALL.md) - Global installation details
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - How claude-lab works as a global tool

## Getting Started

### Check System Requirements

```bash
labcheck
```

### Install Missing Tools

```bash
# Dry-run to see what would be installed
labinstall --dry-run

# Actually install
labinstall
```

## Usage

### Quick Start

1. **Build a base image (optional but recommended):**

```bash
# Build the base image with pre-installed tools
labimage-build --template base
```

2. **Create a new lab environment:**

```bash
# Using default image
labsetup --name feature-auth

# Or with custom image
labsetup --name feature-auth --image claude-lab:base
```

This creates:
- A git worktree at `../feature-auth`
- A k3d cluster named `feature-auth`
- A kubeconfig file patched for Docker host access
- A tmux session running Claude Sandbox

2. **Connect to the lab:**

```bash
tmux attach -t feature-auth
```

3. **List active labs:**

```bash
lablist
```

4. **Tear down when done:**

```bash
labteardown --name feature-auth
```

#### Clean Up Orphaned Labs

```bash
# Show what would be cleaned up
lab cleanup --dry-run

# Clean up orphaned/stopped labs
lab cleanup

# Clean up labs older than 24 hours
lab cleanup --older-than 24

# Clean up all labs
lab cleanup --all
```

### Advanced Usage

#### Create Lab on Specific Branch

```bash
labsetup --name bugfix-123 --branch develop
```

#### Force Teardown

If resources are busy, force removal:

```bash
labteardown --name feature-auth --force
```

#### Send Notifications

From within a lab instance:

```bash
labnotify --message "Build completed" --level success
```

#### View Notification History

```bash
# Show all notifications
labnotifications

# Show last 10
labnotifications --last 10

# Follow new notifications (like tail -f)
labnotifications --follow
```

#### Interactive Status View

```bash
labstatus
```

Or directly run the script:

```bash
uv run .claude/skills/claude-lab/claude-lab.py
```

### Docker Image Management

Pre-build images with tools like kubectl, helm, k9s for faster lab startup:

#### Build Images

```bash
# List available templates
labimage-list

# Build from template
labimage-build --template base
labimage-build --template k8s-full
labimage-build --template python-dev
```

#### Use Custom Images

```bash
# Create lab with specific image
labsetup --name my-lab --image claude-lab:k8s-full
```

#### Manage Images

```bash
# Update (rebuild) an image
labimage-update --template base

# Inspect an image
labimage-inspect --image-tag base

# Delete an image
labimage-delete --image-tag base
```

**Available Templates:**
- `minimal` (~300MB) - kubectl + helm only
- `base` (~800MB) - Standard dev tools
- `k8s-full` (~2GB) - All k8s tools (GitOps, service mesh, etc.)
- `python-dev` (~1.5GB) - Python 3.11 + k8s tools

See [docs/IMAGE-MANAGEMENT.md](docs/IMAGE-MANAGEMENT.md) for detailed information.

#### Create Custom Images from Your Project

```bash
# Analyze your project
lab image-from-project /path/to/your/project --analyze-only

# Build custom image tailored for your project
lab image-from-project /path/to/your/project

# Use it in a lab
lab setup my-lab --image claude-lab:your-project-name
```

The analyzer detects:
- Languages (Python, Node, Go, Rust, etc.)
- Package managers (pip, poetry, npm, yarn, etc.)
- Frameworks (FastAPI, Django, React, etc.)
- K8s tools (helm, kustomize, argocd, etc.)
- Databases (PostgreSQL, MongoDB, Redis, etc.)

And creates a custom Docker image with everything pre-installed!

See [docs/PROJECT-IMAGES.md](docs/PROJECT-IMAGES.md) for complete documentation.

## Automatic Cleanup

Claude Lab can automatically clean up orphaned or stale labs:

### Quick Cleanup

```bash
# Check for orphaned labs
lab cleanup --dry-run

# Clean up orphaned labs
lab cleanup
```

### Setup Auto-Cleanup

```bash
# Run the setup script
./scripts/setup-auto-cleanup.sh

# Or manually with cron (runs daily at 2am)
crontab -e
# Add: 0 2 * * * lab cleanup --older-than 48
```

### Auto-Cleanup on Lab Creation

```bash
# Create a lab that will be auto-cleaned up
export CLAUDE_LAB_AUTO_CLEANUP=true
lab setup temp-lab
```

See [docs/AUTO-CLEANUP.md](docs/AUTO-CLEANUP.md) for complete documentation.

## Port Management

Each lab environment gets two ports automatically assigned:

- **HTTP Port**: For ingress/LoadBalancer access (starts at 8080)
- **API Port**: For Kubernetes API access (HTTP port + 1000)

Port allocations are tracked in `~/.claude-lab-port-registry.json` and automatically managed.

## Notification System

Labs can send notifications back to the main session:

```bash
# From within a lab
labnotify --message "Tests passed!" --level success
labnotify --message "Deployment failed" --level error
```

Notification levels:
- `info` - General information
- `success` - Successful operations
- `warning` - Warnings
- `error` - Errors or failures

Notifications are logged to `~/.claude-lab-notifications.jsonl` in JSON Lines format.

## SSH Identity Sharing

The lab manager automatically:
1. Detects your `SSH_AUTH_SOCK`
2. Mounts it into the Claude Sandbox
3. Sets the environment variable

This allows Claude instances to:
- Push to private git repositories
- Pull from private container registries
- Access SSH-authenticated resources

## File Structure

```
.
├── .claude/
│   └── skills/
│       └── claude-lab/
│           ├── SKILL.md          # Skill definition for Claude
│           └── claude-lab.py        # Main manager script
├── tasks.py                       # Invoke tasks wrapper
├── pyproject.toml                 # Python project config
└── README.md                      # This file
```

## Workflow Example

### Parallel Feature Development

```bash
# Main branch work
git checkout main

# Start three parallel labs
labsetup --name feature-auth --branch main
labsetup --name feature-payments --branch main
labsetup --name bugfix-login --branch develop

# Check status
lablist

# Work in each lab (in separate terminals)
tmux attach -t feature-auth
tmux attach -t feature-payments
tmux attach -t bugfix-login

# When done, tear them all down
labteardown --name feature-auth
labteardown --name feature-payments
labteardown --name bugfix-login
```

## Troubleshooting

### Lab Won't Start

Check system requirements:
```bash
labcheck
```

Verify Docker is running:
```bash
docker ps
```

### Port Conflicts

Manually edit `~/.claude-lab-port-registry.json` to remove stale entries.

### Stale Worktrees

List all worktrees:
```bash
git worktree list
```

Prune stale references:
```bash
git worktree prune
```

### Tmux Session Issues

List all sessions:
```bash
tmux ls
```

Kill a specific session:
```bash
tmux kill-session -t <name>
```

## Claude Code Integration

This skill is designed to be invoked by Claude Code. When Claude needs to work on a task in isolation, it can:

1. Use the skill to create a new lab environment
2. Work within that environment with full k3s/kubectl access
3. Send notifications about progress
4. Tear down the environment when complete

See `.claude/skills/claude-lab/SKILL.md` for Claude-specific instructions.

## Future Enhancements

- [ ] GUI mode for human interaction (TUI with textual)
- [ ] Auto-installation of kubectl/helm in sandbox
- [ ] Resource limits per lab (CPU/memory)
- [ ] Lab snapshots and restore
- [ ] Multi-node k3d clusters
- [ ] Integration with CI/CD pipelines
- [ ] Lab templates for common setups
- [ ] Web UI for monitoring all labs

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
