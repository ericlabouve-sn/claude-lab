# Claude Lab Architecture

## Overview

Claude Lab is a **global CLI tool** that manages isolated development environments for any project.

## Installation Model

```
┌───────────────────────────────────────────────┐
│           Your System                         │
│                                               │
│  ┌─────────────────────────────────────┐    │
│  │  Claude Lab (installed once)           │    │
│  │  Location: ~/.local/bin/lab         │    │
│  │  or /usr/local/bin/lab             │    │
│  └─────────────────────────────────────┘    │
│                    │                          │
│                    │ (manages)                │
│                    ▼                          │
│  ┌──────────────────────────────────────┐   │
│  │  Your Projects (anywhere)            │   │
│  │                                      │   │
│  │  ~/work/api-project/                 │   │
│  │  ~/work/frontend-project/            │   │
│  │  ~/clients/project-x/                │   │
│  │  /tmp/experiments/                   │   │
│  └──────────────────────────────────────┘   │
│                                               │
└───────────────────────────────────────────────┘
```

## How It Works

### 1. Global Installation

Claude Lab is installed **once** on your system:

```bash
# Install to ~/.local/bin/lab (or /usr/local/bin/lab)
uv tool install /path/to/claude-lab

# Now available everywhere
cd ~
lab --help  # ✓ Works

cd /tmp
lab --help  # ✓ Works

cd ~/any/project
lab --help  # ✓ Works
```

### 2. Managing Projects

Use `lab` to manage **any** project on your system:

```bash
# Project A
cd ~/projects/api
lab image-from-project .
lab setup api-dev --image claude-lab:api

# Project B (different directory)
cd ~/projects/frontend
lab image-from-project .
lab setup frontend-dev --image claude-lab:frontend

# Project C (anywhere else)
cd /tmp/experiment
lab setup test-env
```

### 3. Lab Environments

Each lab creates:
- **Git worktree** (in parent directory)
- **k3d cluster** (isolated Kubernetes)
- **Tmux session** (terminal multiplexer)
- **Docker container** (sandbox environment)

```
Project: ~/projects/api
                │
                ├─> Lab: api-dev
                │   ├─> Worktree: ~/projects/api-dev/
                │   ├─> k3d cluster: api-dev
                │   ├─> Tmux session: api-dev
                │   └─> Docker sandbox: running
                │
                └─> Lab: api-test
                    ├─> Worktree: ~/projects/api-test/
                    ├─> k3d cluster: api-test
                    ├─> Tmux session: api-test
                    └─> Docker sandbox: running
```

## Not a Project Dependency

**Important:** Claude Lab is **NOT** a project dependency.

❌ **Don't do this:**
```bash
cd ~/my-project
pip install claude-lab          # Wrong!
npm install claude-lab          # Wrong!
poetry add claude-lab           # Wrong!
```

✅ **Do this instead:**
```bash
# Install once, globally
uv tool install /path/to/claude-lab

# Use for any project
cd ~/my-project
lab setup dev
```

## Comparison with Other Tools

| Tool | Type | Installation |
|------|------|--------------|
| `git` | Global CLI | Install once, use everywhere |
| `docker` | Global CLI | Install once, use everywhere |
| `kubectl` | Global CLI | Install once, use everywhere |
| **`lab`** | **Global CLI** | **Install once, use everywhere** |
| `pytest` | Project dependency | Install per-project |
| `react` | Project dependency | Install per-project |

## Directory Structure

### Claude Lab Repository (installed once)

```
/path/to/claude-lab/  (can be anywhere)
├── src/claude_lab/
│   ├── cli.py
│   ├── project_analyzer.py
│   └── templates/
├── pyproject.toml
└── README.md

After installation:
~/.local/bin/lab  (or /usr/local/bin/lab)
```

### Your Projects (anywhere on system)

```
~/projects/
├── api/
│   ├── src/
│   ├── tests/
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   └── package.json
│
└── infra/
    ├── terraform/
    └── helm/

(No claude-lab files in project directories!)
```

### Created Lab Worktrees

```
~/projects/
├── api/              (original)
├── api-dev/          (worktree created by lab)
├── api-feature/      (another worktree)
│
├── frontend/         (original)
├── frontend-dev/     (worktree created by lab)
│
└── infra/            (original)
    └── infra-test/   (worktree created by lab)
```

## State Management

Claude Lab tracks state in user home directory:

```
~/.claude-lab-port-registry.json         # Port allocations
~/.claude-lab-notifications.jsonl    # Notification log
```

**Not** in project directories.

## Usage Pattern

### Good Pattern ✅

```bash
# 1. Install claude-lab once
cd ~/downloads/claude-lab
uv tool install .

# 2. Use it for projects
cd ~/work/project-a
lab setup dev

cd ~/work/project-b
lab setup dev

cd ~/clients/project-c
lab setup dev
```

### Bad Pattern ❌

```bash
# Don't install per-project
cd ~/work/project-a
uv pip install claude-lab  # Wrong!

cd ~/work/project-b
uv pip install claude-lab  # Wrong!
```

## Integration with Projects

Claude Lab **analyzes** your projects but doesn't become part of them:

```bash
# Analyze project dependencies
cd ~/my-project
lab image-from-project .

# Creates custom image based on project
# But claude-lab is NOT added to project dependencies

# Check project files - no claude-lab
ls -la
# No claude-lab in pyproject.toml, package.json, etc.
```

## Multi-User System

On shared systems, each user has their own lab installation:

```
User 1: ~/.local/bin/lab
        └─> Manages ~/user1/projects/

User 2: ~/.local/bin/lab
        └─> Manages ~/user2/projects/

User 3: ~/.local/bin/lab
        └─> Manages ~/user3/projects/
```

## CI/CD Integration

Install globally in CI environment:

```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - name: Install claude-lab globally
        run: |
          git clone https://github.com/org/claude-lab
          cd claude-lab
          uv tool install .

      - name: Use claude-lab for testing
        run: |
          cd $GITHUB_WORKSPACE
          lab setup ci-test
          # Run tests in lab
```

## Summary

- ✅ Claude Lab is a **global CLI tool**
- ✅ Install **once** on your system
- ✅ Use for **any project**
- ✅ Similar to `git`, `docker`, `kubectl`
- ❌ **Not** a project dependency
- ❌ **Not** installed per-project
- ❌ **Not** in project requirements

**Think of it like `git` - you install git once, then use it to manage many repositories. Claude Lab works the same way - install once, manage many projects.**
