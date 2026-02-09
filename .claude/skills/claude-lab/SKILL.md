---
name: claude-lab
description: Manage isolated k3d/Kubernetes development environments with dedicated clusters, git worktrees, and tmux sessions for parallel development workflows. Supports GUI mode, global/project settings, and custom Docker images.
argument-hint: setup <name> [--branch <branch>] [--image <image>] | list | teardown <name> | gui | cleanup [--dry-run] | init [--global]
user-invocable: true
---

# Claude Lab Manager

Use this skill when you need to start a new branch/task in an isolated environment with its own k3d cluster, git worktree, and tmux session.

## Capabilities

- **Setup:** Create a new git worktree, a dedicated k3d cluster (with unique ports), and launch a Claude Sandbox in tmux
- **Teardown:** Clean up all resources (cluster, worktree, tmux session) after a task is finished
- **List:** View all active lab environments with their status and ports
- **GUI Mode:** Interactive terminal UI for managing labs with keyboard navigation
- **Settings:** Global (`~/.lab/`) and project-level (`.lab/`) configuration support
- **Init:** Initialize settings directories with defaults
- **Port Registry:** Automatically avoids port collisions between parallel clusters
- **Notifications:** Lab instances can send notifications back to the user via a notification system
- **Image Management:** Build, manage, and customize Docker images with pre-installed tools (kubectl, helm, k9s, etc.)

## Instructions

### Initializing Settings

Before first use, optionally create settings files:

```bash
# Initialize global settings (applies to all projects)
lab init --global

# Initialize project settings (applies to current project only)
lab init
```

Settings files allow you to configure:
- Default worktree directory location
- Default Docker image
- Additional volume mounts
- Environment variables

**Configuration Precedence:** Command-line > Project (`.lab/`) > Global (`~/.lab/`) > Environment Variables > Built-in Defaults

**Example Global Settings** (`~/.lab/settings.yaml`):
```yaml
worktree_dir: "/tmp/claude-labs"
docker_image: "claude-lab:k8s-full"
base_port: 8080
additional_mounts:
  - "~/.aws/credentials:/root/.aws/credentials:ro"
  - "~/data:/data:ro"
environment:
  AWS_REGION: "us-west-2"
  LOG_LEVEL: "info"
```

**Example Project Settings** (`.lab/settings.yaml`):
```yaml
docker_image: "claude-lab:python-dev"  # Override global
base_port: 9000                      # Project-specific
environment:
  NODE_ENV: "development"
```

### Starting a New Lab Environment

```bash
labsetup --name <environment-name>
```

This will:
1. Create a git worktree at `../<environment-name>` based on the current branch
2. Spin up a k3d cluster with unique ports (automatically assigned)
3. Generate a kubeconfig patched for Docker host access
4. Mount your SSH identity for git operations
5. Launch a Claude Sandbox in a tmux session

### Listing Active Environments

```bash
lablist
```

Shows a table of all active environments with their ports and status.

### Interactive GUI Mode

```bash
lab gui
```

Launch an interactive terminal UI with:
- **Lab List Panel** (left): Browse all active labs with status indicators
- **Details Panel** (top-right): View selected lab details and available actions
- **Notifications Panel** (bottom-right): Real-time notification feed

**Keyboard Controls:**
- `↑/↓` - Navigate lab list
- `a` - Attach to selected lab's tmux session
- `r` - Refresh all data
- `n` - Create new lab (shows instructions)
- `d` - Delete lab (shows instructions)
- `q` - Quit GUI

### Tearing Down an Environment

```bash
labteardown --name <environment-name>
```

Cleans up the k3d cluster, removes the git worktree, kills the tmux session, and updates the port registry.

### Cleaning Up Orphaned Environments

```bash
# Show what would be cleaned up
lab cleanup --dry-run

# Clean up orphaned/stopped labs
lab cleanup

# Clean up labs older than N hours
lab cleanup --older-than 24
```

Automatically cleans up labs where:
- Tmux session has stopped
- k3d cluster is missing
- Worktree directory doesn't exist
- Lab is older than specified time

### System Check

```bash
labcheck
```

Verifies that all required tools (docker, k3d, tmux, git, kubectl, helm) are installed and Docker has sufficient resources.

## Notifications

Lab instances can send notifications to the main user session using:

```bash
labnotify --message "Build completed successfully" --level info
```

Notification levels: `info`, `success`, `warning`, `error`

Notifications are written to `~/.claude-lab-notifications.jsonl` and can be polled or displayed via a TUI.

## Image Management

Build and manage custom Docker images with pre-installed tools:

### Build an Image

```bash
# Available templates: minimal, base, k8s-full, python-dev
labimage-build --template base
labimage-build --template k8s-full --tag v1.0
```

### List Available Images

```bash
labimage-list
labimage-list --verbose
```

### Use Custom Image in Lab

```bash
labsetup --name my-lab --image claude-lab:k8s-full
```

### Update (Rebuild) an Image

```bash
labimage-update --template base
```

### Delete an Image

```bash
labimage-delete --image-tag base
```

### Image Templates

- **minimal** (~300MB): kubectl, helm only
- **base** (~800MB): Standard tools (kubectl, helm, k9s, docker, git)
- **k8s-full** (~2GB): All k8s tools (kubectl, helm, k9s, kubectx, kustomize, stern, flux, argocd, istio, terraform)
- **python-dev** (~1.5GB): Python 3.11 + k8s tools (uv, pytest, black, ruff, jupyter)

### Custom Templates

Create project-specific or user-global Docker templates:

**Template Priority:**
1. `.lab/templates/` - Project-specific (versioned in git)
2. `~/.lab/templates/` - User-global custom templates
3. Built-in templates - Package defaults

**Create a custom template:**

```bash
# Create project template directory
mkdir -p .lab/templates

# Copy and modify a built-in template
cp src/claude_lab/templates/base.Dockerfile .lab/templates/my-custom.Dockerfile

# Create templates.json
cat > .lab/templates/templates.json <<EOF
{
  "image_prefix": "claude-lab",
  "default_template": "my-custom",
  "templates": {
    "my-custom": {
      "dockerfile": "my-custom.Dockerfile",
      "description": "Custom template with project tools",
      "size_estimate": "~500MB",
      "tools": ["kubectl", "helm", "your-tool"]
    }
  }
}
EOF

# Build and use it
lab image-build my-custom
lab setup --name test --image claude-lab:my-custom
```

**Benefits:**
- Version control project templates in git
- Share team-specific tooling
- Override built-ins without modifying package
- User-global templates across all projects

### Create Project-Specific Images

Analyze a project directory and create a custom image:

```bash
# Analyze project to see what will be included
lab image-from-project /path/to/project --analyze-only

# Build custom image for the project
lab image-from-project /path/to/project

# Use custom image in lab
lab setup my-lab --image claude-lab:project-name
```

The analyzer automatically detects:
- Programming languages (Python, Node, Go, Rust, etc.)
- Package managers (pip, poetry, npm, yarn, etc.)
- Frameworks (FastAPI, Django, React, Next.js, etc.)
- K8s tools needed (helm, kustomize, argocd, etc.)
- Databases (PostgreSQL, MongoDB, Redis, etc.)

And generates a Dockerfile with all dependencies pre-installed!

## Architecture

- **Global Settings:** `~/.lab/settings.yaml` - User-wide defaults for all projects
- **Project Settings:** `.lab/settings.yaml` - Project-specific overrides
- **Port Registry:** `~/.claude-lab-port-registry.json` - Tracks allocated ports
- **Notifications:** `~/.claude-lab-notifications.jsonl` - Stores notification events
- **Worktrees:** Created in configured location (default: `/tmp/claude-labs/<name>`)
- **k3d Clusters:** Each gets unique API port (base+1000) and HTTP port (auto-assigned)
- **SSH Identity:** Automatically mounted via `SSH_AUTH_SOCK` for git push/pull
- **Auto-Mounts:** Automatically mounts `~/.claude`, `~/.gitconfig`, `~/.docker/config.json` when present

## Requirements

- Docker Desktop with sufficient RAM (8GB+ recommended)
- k3d (k3s in docker)
- tmux
- git
- uv (for Python script execution)
- Python 3.12+ with dependencies: rich, click, textual, pyyaml
- kubectl (optional, auto-installed in sandbox)
- helm (optional, auto-installed in sandbox)

## Examples

```bash
# Initialize settings for your workflow
lab init --global
lab init  # in project directory

# Start working on a feature in isolation
lab setup feature-auth

# Launch interactive GUI to manage labs
lab gui

# Check on running environments
lab list

# When done, clean up
lab teardown feature-auth

# Clean up orphaned labs
lab cleanup --dry-run
lab cleanup

# Send a notification from within a lab
lab notify --message "Tests passed!" --level success

# Use custom image for a specific project
lab setup my-lab --image claude-lab:k8s-full --branch main
```

## Notes

- Each lab environment is completely isolated with its own cluster and worktree
- Port allocation is automatic - no manual configuration needed
- Settings are merged with proper precedence (project overrides global)
- Common config files (`~/.claude`, `~/.gitconfig`, `~/.docker/config.json`) are auto-mounted when present
- SSH credentials are shared so you can git push from within labs
- The kubeconfig is patched to use `host.docker.internal` for Docker-to-host access
- Use `tmux attach -t <name>` to connect to a running lab session
- GUI mode provides real-time view of all labs and notifications
- Default worktree location is `/tmp/claude-labs` for automatic cleanup on reboot
