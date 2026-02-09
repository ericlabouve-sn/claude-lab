# Project-Specific Lab Configuration

This directory contains project-specific settings for Claude Lab environments.

## Overview

The `.lab/settings.yaml` file allows you to configure default behavior for all labs created within this project, overriding global defaults.

## Configuration File

### Location

`.lab/settings.yaml` in your project root

### Structure

```yaml
# Worktree directory for isolated environments
worktree_dir: "/tmp/claude-labs"

# Default Docker image for sandboxes
docker_image: "claude"

# Starting port number
base_port: 8080

# Additional volume mounts
additional_mounts:
  - "~/data:/data:ro"
  - "~/.aws/credentials:/root/.aws/credentials:ro"

# Environment variables
environment:
  NODE_ENV: "development"
  DEBUG: "true"

# Auto-cleanup settings
auto_cleanup:
  enabled: false
  max_age_days: 30
  stopped_age_days: 7
```

## Settings Reference

### `worktree_dir`

**Type:** String (path)
**Default:** `/tmp/claude-labs`

Directory where git worktrees will be created for labs.

**Options:**
- Absolute path: `/tmp/claude-labs`, `/home/user/labs`
- Relative path: `..` (parent directory), `./labs` (project subdirectory)
- Home directory: `~/labs`

**Example:**
```yaml
worktree_dir: "/tmp/claude-labs"  # Temporary, isolated work
# or
worktree_dir: ".."              # Parent directory (old default)
# or
worktree_dir: "~/my-labs"       # Persistent home directory
```

### `docker_image`

**Type:** String
**Default:** `"claude"`

Docker image to use for sandbox environments.

**Built-in Images:**
- `"claude"` - Default Claude Code sandbox
- `"claude-lab:base"` - Minimal K8s tools (kubectl, helm)
- `"claude-lab:k8s-full"` - Full K8s environment (ArgoCD, k9s, etc.)

**Custom Images:**
- Any Docker image: `"my-org/my-image:tag"`
- Local images: `"my-custom-env:latest"`

**Example:**
```yaml
# Use comprehensive K8s environment
docker_image: "claude-lab:k8s-full"

# Use custom organization image
docker_image: "ghcr.io/my-org/dev-env:v1.2.0"
```

### `base_port`

**Type:** Integer
**Default:** `8080`

Starting port number for lab HTTP services. Each lab gets:
- **HTTP Port:** Base port (e.g., 8080)
- **API Port:** Base port + 1000 (e.g., 9080)

**Example:**
```yaml
base_port: 9000  # Labs will use 9000, 9001, 9002, etc.
```

### `additional_mounts`

**Type:** List of strings
**Default:** `[]`

Additional volume mounts to include in all labs.

**Format:** `source:target:mode`
- `source` - Path on host (supports `~` for home directory)
- `target` - Path in container
- `mode` - Optional: `ro` (read-only) or `rw` (read-write, default)

**Common Use Cases:**

```yaml
additional_mounts:
  # AWS credentials (read-only for safety)
  - "~/.aws/credentials:/root/.aws/credentials:ro"

  # Shared data directory
  - "~/data:/data:ro"

  # NPM cache (speeds up npm install)
  - "~/.npm:/root/.npm:rw"

  # SSH config for jump hosts
  - "~/.ssh/config:/root/.ssh/config:ro"

  # Project-specific scripts
  - "./scripts:/scripts:ro"
```

**Security Notes:**
- ⚠️ Use `ro` (read-only) by default for safety
- ⚠️ Be cautious with AWS credentials and secrets
- ✅ Consider environment variables instead of mounting credential files
- ✅ Files must exist on host or they'll be skipped

### `environment`

**Type:** Dictionary (key-value pairs)
**Default:** `{}`

Environment variables to set in all labs.

**Common Use Cases:**

```yaml
environment:
  # Node.js development
  NODE_ENV: "development"
  DEBUG: "app:*"

  # Python development
  PYTHONUNBUFFERED: "1"
  DJANGO_SETTINGS_MODULE: "project.settings.dev"

  # AWS region
  AWS_REGION: "us-west-2"
  AWS_DEFAULT_REGION: "us-west-2"

  # Feature flags
  ENABLE_FEATURE_X: "true"
  API_BASE_URL: "https://api.staging.example.com"
```

**Notes:**
- Values are always strings
- Prefer environment variables over mounted credential files
- Consider using `.env` files in your project instead

### `auto_cleanup`

**Type:** Dictionary
**Default:** `enabled: false`

Automatic cleanup settings for old labs (future feature).

**Options:**
```yaml
auto_cleanup:
  enabled: true
  max_age_days: 30        # Delete labs older than 30 days
  stopped_age_days: 7     # Delete stopped labs after 7 days
```

**Current Status:** Not yet implemented. Reserved for future use.

## Precedence

Settings are resolved in this order (highest to lowest priority):

1. **Command-line arguments** - `lab setup --image my-image`
2. **Project settings** - `.lab/settings.yaml`
3. **Environment variables** - `CLAUDE_LAB_WORKTREE_DIR=/tmp/labs`
4. **Built-in defaults** - Hardcoded in CLI

## Examples

### Minimal Configuration

```yaml
# .lab/settings.yaml
worktree_dir: "/tmp/claude-labs"
docker_image: "claude-lab:k8s-full"
```

### Node.js Project

```yaml
# .lab/settings.yaml
worktree_dir: "~/labs/my-project"
docker_image: "node:20-alpine"
base_port: 3000

additional_mounts:
  - "~/.npm:/root/.npm:rw"

environment:
  NODE_ENV: "development"
  PORT: "3000"
```

### Python + AWS Project

```yaml
# .lab/settings.yaml
worktree_dir: "/tmp/claude-labs"
docker_image: "python:3.12"
base_port: 8000

additional_mounts:
  - "~/.aws/credentials:/root/.aws/credentials:ro"
  - "~/data:/data:ro"

environment:
  PYTHONUNBUFFERED: "1"
  AWS_REGION: "us-west-2"
  DEBUG: "true"
```

### Kubernetes Development

```yaml
# .lab/settings.yaml
worktree_dir: "/tmp/claude-labs"
docker_image: "claude-lab:k8s-full"
base_port: 8080

environment:
  KUBECTL_NAMESPACE: "development"
  HELM_EXPERIMENTAL_OCI: "1"
```

## Usage

### Creating Labs

Settings are automatically loaded when you create a lab:

```bash
# Uses settings from .lab/settings.yaml
lab setup my-feature

# Override image from command line
lab setup my-feature --image claude-lab:base

# Override branch
lab setup my-feature --branch develop
```

### Viewing Settings

Currently applied settings are shown during lab creation:

```
✅ Lab 'my-feature' is ready!
Connect with: tmux attach -t my-feature
HTTP available at: http://localhost:8080

Using project settings from .lab/settings.yaml

Mounted configs:
  • ~/.claude → /root/.claude (skills & settings)
  • ~/.gitconfig → /root/.gitconfig (git identity)
  • ~/.docker/config.json (registry auth)

Additional mounts from project:
  • ~/data → /data (project config)

Environment variables:
  • NODE_ENV=development
  • DEBUG=true
```

## Troubleshooting

### Settings Not Loading

**Problem:** Labs don't use `.lab/settings.yaml`

**Solutions:**
1. Check file exists: `ls .lab/settings.yaml`
2. Verify YAML syntax: `cat .lab/settings.yaml`
3. Check you're in project root: `pwd`
4. Look for warning message during `lab setup`

### Mount Not Working

**Problem:** Additional mount doesn't appear in container

**Solutions:**
1. Verify source file exists: `ls ~/path/to/file`
2. Check path expansion: Use absolute paths or `~`
3. Review mount format: `source:target:mode`
4. Check sandbox permissions

### Invalid YAML

**Problem:** `Could not load settings.yaml`

**Solutions:**
1. Validate YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('.lab/settings.yaml'))"`
2. Check indentation (use spaces, not tabs)
3. Quote strings with special characters
4. Use online YAML validator

## Best Practices

### ✅ Do

- **Use read-only mounts** for configuration files
- **Keep worktrees in /tmp** for automatic cleanup
- **Document custom settings** in project README
- **Commit `.lab/settings.yaml`** to version control
- **Use environment variables** for sensitive data when possible

### ❌ Don't

- **Don't mount entire home directory** (security risk)
- **Don't use read-write mounts** unless necessary
- **Don't hardcode secrets** in settings.yaml
- **Don't mount SSH private keys** (use SSH agent instead)
- **Don't ignore .lab/** in .gitignore (settings should be shared)

## Migration

### From Environment Variables

**Old:**
```bash
export CLAUDE_LAB_WORKTREE_DIR="/tmp/labs"
export CLAUDE_LAB_DOCKER_IMAGE="claude-lab:k8s-full"
export CLAUDE_LAB_BASE_PORT="9000"
```

**New:**
```yaml
# .lab/settings.yaml
worktree_dir: "/tmp/labs"
docker_image: "claude-lab:k8s-full"
base_port: 9000
```

### From Old Default (Parent Directory)

**Old behavior:**
- Worktrees created in `../lab-name`

**New behavior:**
- Worktrees created in `/tmp/claude-labs/lab-name`

**To keep old behavior:**
```yaml
# .lab/settings.yaml
worktree_dir: ".."
```

## Future Enhancements

Planned features for `.lab/settings.yaml`:

- **Resource limits:** CPU/memory per lab
- **Auto-cleanup:** Scheduled deletion of old labs
- **Lab templates:** Pre-configured lab types
- **Hooks:** Custom scripts on lab creation/deletion
- **Profiles:** Multiple configuration sets (dev/staging/prod)
