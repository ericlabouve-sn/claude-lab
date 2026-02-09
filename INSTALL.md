# Installation Guide

## Claude Lab is a Global Tool

Claude Lab is a **system-wide CLI tool**, like `git`, `docker`, or `kubectl`. You install it once and use it for any project.

```
┌─────────────────────────────────────┐
│     Claude Lab (installed once)        │
│     Available everywhere as `lab`   │
└─────────────────────────────────────┘
              │
              ├─> Manage ~/project-1
              ├─> Manage ~/project-2
              └─> Manage ~/project-3
```

## Installation Options

### For End Users (Recommended)

**Global Install** - Install once, use everywhere:
- `uv tool install .` - Isolated environment
- Available system-wide as `lab` command
- No per-project installation needed

### For Claude Lab Developers

**Development Install** - For working on claude-lab itself:
- `uv pip install -e .` - Editable install
- Changes to code immediately reflected
- Only if you're developing claude-lab features

**⚠️ Note:** Most users should use the global install, not the development install.

For detailed global installation options, see [docs/GLOBAL-INSTALL.md](docs/GLOBAL-INSTALL.md).

## Quick Install

### Using Makefile (Easiest)

```bash
# For development (changes reflected immediately)
make install

# For system-wide use (available from any directory)
make install-global

# Complete quickstart
make quickstart
```

### Using uv directly

```bash
# For development (editable install)
uv pip install -e .

# For system-wide CLI tool (recommended for end users)
uv tool install .

# Or install from source
uv pip install .
```

### Using pip

```bash
# Install in development mode
pip install -e .

# Or install from source
pip install .
```

### System-wide Install

```bash
# Install globally with uv
uv tool install .

# Or with pipx (recommended for system-wide CLI tools)
pipx install .
```

## Verify Installation

```bash
# Check the command is available
lab --help

# Check version
lab --version

# Run system check
lab check
```

## Development Install

For development with editable install:

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-lab.git
cd claude-lab

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Uninstall

```bash
# With uv
uv pip uninstall claude-lab

# With pip
pip uninstall claude-lab

# With pipx
pipx uninstall claude-lab
```

## Requirements

Before installing, ensure you have:

- Python 3.12 or higher
- Docker Desktop
- k3d
- tmux
- git

Run `lab install` to install missing system requirements.

## Post-Installation

1. **Verify system requirements:**
   ```bash
   lab check
   ```

2. **Install missing tools:**
   ```bash
   lab install
   ```

3. **Build a base image (optional but recommended):**
   ```bash
   lab image-build base
   ```

4. **Create your first lab:**
   ```bash
   lab setup my-first-lab
   ```

## Troubleshooting

### Command not found

If `lab` command is not found after installation:

1. **Check your PATH:**
   ```bash
   echo $PATH
   ```

2. **Find where it was installed:**
   ```bash
   which lab
   ```

3. **With uv, ensure tools path is in PATH:**
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. **With pipx, ensure pipx bin directory is in PATH:**
   ```bash
   pipx ensurepath
   ```

### Permission errors

If you get permission errors:

```bash
# Don't use sudo, use user-level install instead
pip install --user -e .

# Or use pipx
pipx install .
```

### Import errors

If you get import errors after installation:

```bash
# Reinstall dependencies
uv pip install --force-reinstall -e .

# Check installation
pip show claude-lab
```

## Upgrade

To upgrade to the latest version:

```bash
# From source
git pull
uv pip install --upgrade .

# With pipx
pipx upgrade claude-lab
```

## Multiple Python Versions

If you have multiple Python versions:

```bash
# Install for specific Python version
python3.12 -m pip install -e .

# Or with uv
uv pip install --python 3.12 -e .
```

## Virtual Environment

To install in a virtual environment:

```bash
# Create venv
python -m venv venv

# Activate
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows

# Install
pip install -e .
```

## Docker-only Installation

If you only want to use claude-lab without installing Python:

```bash
# Build a Docker image with claude-lab
docker build -t claude-lab:cli -f Dockerfile.cli .

# Run as container
docker run -it -v /var/run/docker.sock:/var/run/docker.sock claude-lab:cli lab --help
```

(Dockerfile.cli not included yet - create if needed)

## CI/CD Installation

For CI/CD pipelines:

```bash
# GitHub Actions
- uses: astral-sh/setup-uv@v2
- run: uv pip install .
- run: lab check

# GitLab CI
script:
  - pip install .
  - lab check
```

## Next Steps

After installation, see:
- [QUICKSTART.md](QUICKSTART.md) for getting started
- [README.md](README.md) for full documentation
- [docs/IMAGE-MANAGEMENT.md](docs/IMAGE-MANAGEMENT.md) for image management
