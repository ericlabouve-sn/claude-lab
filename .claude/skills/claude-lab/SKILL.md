---
name: claude-lab
description: Use this skill when you need to start a new branch/task in an isolated environment with its own k3d cluster, git worktree, and tmux session. Supports GUI mode, global/project settings, custom Docker images, and seamless domain access via reverse proxy.
argument-hint: setup <name> [--branch <branch>] [--image <image>] | list | teardown <name> | gui | proxy start | dns setup | init [--global]
user-invocable: true
---

# Claude Lab Manager

Use this skill when you need to start a new branch/task in an isolated environment with its own k3d cluster, git worktree, and tmux session.

## Capabilities

- **Setup:** Create a new git worktree, a dedicated k3d cluster (with unique ports), and launch a Claude Sandbox in tmux
- **Teardown:** Clean up all resources (cluster, worktree, tmux session) after a task is finished
- **List:** View all active lab environments with their status and ports
- **GUI Mode:** Interactive terminal UI for managing labs with keyboard navigation
- **Reverse Proxy:** Seamless domain access (http://lab-name.local/) via Caddy proxy
- **DNS Management:** Wildcard DNS for *.local domains via dnsmasq
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
lab setup --name <environment-name>
```

This will:
1. Create a git worktree at `${worktree_dir}/<environment-name>` based on the current branch
2. Spin up a k3d cluster with unique ports (automatically assigned)
3. Generate a kubeconfig patched for Docker host access
4. Mount your SSH identity for git operations
5. Launch a Claude Sandbox in a tmux session

### Listing Active Environments

```bash
lab list
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

### Seamless Domain Access (Reverse Proxy + DNS)

Access labs via `http://lab-name.local/` instead of port numbers:

```bash
# One-time setup (requires sudo for DNS)
lab dns setup      # Configure dnsmasq for *.local wildcard DNS
lab proxy start    # Start Caddy reverse proxy on port 80

# Create a lab (auto-registers routes!)
lab setup my-lab

# Access seamlessly:
http://my-lab.local/
http://api.my-lab.local/
http://subdomain.my-lab.local/
```

**How it works:**
- **DNS (dnsmasq)**: Resolves all `*.local` domains to `127.0.0.1`
- **Proxy (Caddy in Docker)**: Routes `*.lab-name.local` → `localhost:port`
- **Auto-registration**: Routes added/removed automatically during setup/teardown
- **Zero-downtime**: Routes updated via Caddy admin API without restarts

**Proxy commands:**
```bash
lab proxy start          # Start Caddy on port 80
lab proxy stop           # Stop proxy
lab proxy restart        # Restart proxy
lab proxy status         # Show all routes
lab proxy logs -f        # Follow logs
```

**DNS commands:**
```bash
lab dns setup    # Complete DNS configuration
lab dns status   # Check configuration
lab dns test     # Test DNS resolution
lab dns restart  # Restart dnsmasq
```

**Note:** If Docker Desktop crashes, restart the proxy with `lab proxy start`. This does NOT overwrite your settings - it only restarts the Caddy container.

### Tearing Down an Environment

```bash
lab teardown --name <environment-name>
```

Cleans up the k3d cluster, removes the git worktree, kills the tmux session, and updates the port registry.

### System Check

```bash
lab check
```

Verifies that all required tools (docker, k3d, tmux, git, kubectl, helm) are installed and Docker has sufficient resources.

## Notifications

### When to Use Notifications

**Use notifications strategically** to get the user's attention when:

1. **Need User Input**: A decision point requires user feedback
   - Example: "Multiple configuration files found. Which should I use?"
   - Use `--request-response` flag for interactive reply

2. **Long-Running Tasks Complete**: Operations that take >30 seconds finish
   - Example: "Build completed successfully (took 2m 34s)"
   - User might be working elsewhere and wants to know

3. **Errors Require Attention**: Critical failures that block progress
   - Example: "Deployment failed: insufficient cluster resources"
   - Use `--level error` with `--request-response` to ask how to proceed

4. **Important Milestones**: Key progress checkpoints
   - Example: "All 15 tests passed! Ready to deploy?"
   - Use `--request-response` to get confirmation

**Don't overuse**: Avoid notifications for routine operations or frequent updates. Reserve them for truly important moments.

### Sending Notifications

```bash
# Basic notification
lab notify --message "Build completed successfully" --level success

# Request user response (interactive on macOS)
lab notify --message "Found 3 config files. Use production config?" --level warning --request-response

# From specific source (helps user identify which lab)
lab notify --message "Tests passed!" --level success --source "feature-auth"
```

**Notification levels**: `info`, `success`, `warning`, `error`

### Interactive macOS Notifications

On macOS (with `alerter` installed), notifications appear as system banners with:
- **Reply button**: User can type a quick response (with `--request-response`)
- **Click action**: Directly opens Terminal with the lab's tmux session for immediate interaction with Claude
- **Auto-dismiss**: Closes after 30 seconds if ignored

### Checking for User Responses

After sending an interactive notification, check for responses:

```bash
# View all user responses
lab responses

# View responses from specific lab
lab responses --source "feature-auth"

# View last response only
lab responses --last 1

# Clear responses after reading
lab responses --clear
```

### Example Workflow

```bash
# Claude instance needs user decision
lab notify --message "Deploy to staging or wait for QA review?" \
  --level info \
  --request-response \
  --source "feature-auth"

# Wait a moment for response
sleep 5

# Check if user responded
response=$(lab responses --source "feature-auth" --last 1)
if [[ $response == *"staging"* ]]; then
  # User said to deploy to staging
  kubectl apply -f staging/
elif [[ $response == *"wait"* ]]; then
  # User said to wait
  lab notify --message "Waiting for QA review" --level info --source "feature-auth"
fi
```

### Installation (macOS)

For interactive notifications, install `alerter`:

```bash
# Download from GitHub
curl -L https://github.com/vjeantet/alerter/releases/download/1.0.1/alerter_v1.0.1_darwin_amd64.zip -o /tmp/alerter.zip
unzip -o /tmp/alerter.zip -d /tmp
sudo mv /tmp/alerter /usr/local/bin/alerter
sudo chmod +x /usr/local/bin/alerter

# Remove macOS quarantine (bypass Gatekeeper)
sudo xattr -d com.apple.quarantine /usr/local/bin/alerter

# Clean up
rm /tmp/alerter.zip
```

Configure in settings:

```yaml
# .lab/settings.yaml or ~/.lab/settings.yaml
macos_notifications:
  enabled: true           # Enable system notifications
  click_action: "gui"     # Open Terminal with tmux session when banner is clicked
```

## Image Management

Build and manage custom Docker images with pre-installed tools:

### Build an Image

```bash
# Available templates: minimal, base, k8s-full, python-dev
lab image-build --template base
lab image-build --template k8s-full --tag v1.0
```

### List Available Images

```bash
lab image-list
lab image-list --verbose
```

### Use Custom Image in Lab

```bash
lab setup --name my-lab --image claude-lab:k8s-full
```

### Update (Rebuild) an Image

```bash
lab image-update --template base
```

### Delete an Image

```bash
lab image-delete --image-tag base
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
