# Global Installation Guide

## Making `lab` Available System-Wide

There are several ways to install the `lab` CLI tool so it's available from anywhere on your system.

## Option 1: uv tool install (Recommended) ⭐

This is the **best and cleanest** approach. `uv tool` manages CLI tools in isolated environments.

### From Local Directory

```bash
# Navigate to the project directory
cd /path/to/claude-lab

# Install as a tool
uv tool install .

# Verify it works
lab --help
```

### From Git Repository

```bash
# Install directly from git (future)
uv tool install git+https://github.com/yourusername/claude-lab.git
```

### Benefits

- ✅ Isolated environment (doesn't conflict with other packages)
- ✅ Available system-wide from any directory
- ✅ Easy to update: `uv tool upgrade claude-lab`
- ✅ Easy to uninstall: `uv tool uninstall claude-lab`
- ✅ No need to manage PATH manually

### Update and Manage

```bash
# List installed tools
uv tool list

# Update to latest version
uv tool upgrade claude-lab

# Uninstall
uv tool uninstall claude-lab

# Reinstall (after making changes)
cd /path/to/claude-lab
uv tool uninstall claude-lab
uv tool install .
```

## Option 2: pipx (Alternative)

`pipx` is a popular tool for installing Python CLI applications in isolated environments.

### Install pipx (if not installed)

```bash
# macOS
brew install pipx
pipx ensurepath

# Linux
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Verify
pipx --version
```

### Install claude-lab with pipx

```bash
# From local directory
cd /path/to/claude-lab
pipx install .

# Or in editable mode (for development)
pipx install -e .

# Verify
lab --help
```

### Update and Manage

```bash
# List installed apps
pipx list

# Upgrade
cd /path/to/claude-lab
pipx upgrade claude-lab

# Reinstall
pipx reinstall claude-lab

# Uninstall
pipx uninstall claude-lab
```

## Option 3: System-wide pip install (Not Recommended)

This works but can cause dependency conflicts:

```bash
# Global install (requires sudo on some systems)
pip install .

# User-level install (better)
pip install --user .

# Verify
lab --help
```

**Note:** You may need to add `~/.local/bin` to your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

## Option 4: Development Symlink (For Active Development)

If you're actively developing claude-lab, use editable install:

```bash
# With uv (recommended for dev)
cd /path/to/claude-lab
uv pip install -e .

# Or with pipx
pipx install -e .

# Now any changes to the code are immediately available
```

## Comparison

| Method | Isolation | Easy Update | Dev Friendly | Recommended |
|--------|-----------|-------------|--------------|-------------|
| `uv tool install` | ✅ Yes | ✅ Yes | ⚠️ Manual | ⭐ Best for users |
| `pipx` | ✅ Yes | ✅ Yes | ⚠️ Manual | ✅ Alternative |
| `uv pip install -e` | ❌ No | ✅ Yes | ✅ Yes | ⭐ Best for dev |
| `pip install --user` | ❌ No | ⚠️ Manual | ❌ No | ⚠️ Use others |

## Verification

After installation with any method:

```bash
# Check it's available
which lab
# Should show: /Users/you/.local/bin/lab (or similar)

# Test it works
lab --help

# Test from any directory
cd /tmp
lab check
lab image-list
```

## Troubleshooting

### Command not found

1. **Check installation:**
   ```bash
   uv tool list
   # or
   pipx list
   ```

2. **Check PATH:**
   ```bash
   echo $PATH
   ```

3. **For uv tools, ensure path is set:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. **For pipx, run:**
   ```bash
   pipx ensurepath
   # Then restart your shell
   ```

### Permission errors

Don't use `sudo`! Use user-level install instead:
```bash
pip install --user .
# or
uv tool install .
```

### Old version showing

```bash
# Clear pip cache
pip cache purge

# Reinstall
uv tool uninstall claude-lab
uv tool install .
```

### Want to test without installing

```bash
# Run directly from source
cd /path/to/claude-lab
python -m claude_lab --help

# Or use the cli.py directly
python src/claude_lab/cli.py --help
```

## Recommended Workflow

### For End Users

```bash
# One-time setup
uv tool install /path/to/claude-lab

# Use anywhere
lab setup my-lab
lab list
lab teardown my-lab
```

### For Developers

```bash
# One-time setup
cd /path/to/claude-lab
uv pip install -e .

# Make changes to code
vim src/claude_lab/cli.py

# Test immediately (no reinstall needed)
lab --help
```

### For CI/CD

```bash
# Install in CI environment
pip install .

# Use in pipeline
lab check
lab setup ci-test
```

## Environment Variables (Not Recommended)

You asked about environment variables and PATH. This approach works but is **not recommended** for Python packages:

```bash
# DON'T do this (old approach)
export CLAUDE_LAB_HOME=/path/to/claude-lab
export PATH="$CLAUDE_LAB_HOME:$PATH"

# Instead, use proper installation:
uv tool install .
```

**Why not recommended:**
- ❌ Doesn't handle dependencies properly
- ❌ Requires manual PATH management
- ❌ Doesn't work if script expects to be installed
- ❌ Breaks when you move the directory
- ✅ Proper installation is cleaner and more reliable

## Summary

**Best for most users:**
```bash
cd /path/to/claude-lab
uv tool install .
lab --help  # Works from anywhere!
```

**Best for developers:**
```bash
cd /path/to/claude-lab
uv pip install -e .
lab --help  # Works from anywhere, reflects code changes
```

**Uninstall:**
```bash
uv tool uninstall claude-lab
```

That's it! No environment variables or PATH manipulation needed. 🎉
