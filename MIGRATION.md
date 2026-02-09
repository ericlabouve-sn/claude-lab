# Migration Guide: From `uv run invoke` to `lab` CLI

## Summary of Changes

Claude Lab Manager is now a proper Python CLI tool! Instead of running commands with `uv run invoke lab.*`, you can now use the simple `lab` command.

## Before and After

### Old Way (Invoke-based)
```bash
uv run invoke lab.setup --name feature-api
uv run invoke lab.list
uv run invoke lab.teardown --name feature-api
uv run invoke lab.image-build --template base
```

### New Way (CLI tool)
```bash
lab setup feature-api
lab list
lab teardown feature-api
lab image-build base
```

## Command Mapping

| Old Command | New Command |
|-------------|-------------|
| `uv run invoke lab.check` | `lab check` |
| `uv run invoke lab.install` | `lab install` |
| `uv run invoke lab.setup --name X` | `lab setup X` |
| `uv run invoke lab.setup --name X --branch Y` | `lab setup X --branch Y` |
| `uv run invoke lab.setup --name X --image Y` | `lab setup X --image Y` |
| `uv run invoke lab.teardown --name X` | `lab teardown X` |
| `uv run invoke lab.teardown --name X --force` | `lab teardown X --force` |
| `uv run invoke lab.list` | `lab list` |
| `uv run invoke lab.status` | `lab status` |
| `uv run invoke lab.notify --message "X" --level Y` | `lab notify --message "X" --level Y` |
| `uv run invoke lab.notifications` | `lab notifications` |
| `uv run invoke lab.notifications --last 10` | `lab notifications --last 10` |
| `uv run invoke lab.notifications --follow` | `lab notifications --follow` |
| `uv run invoke lab.image-build --template X` | `lab image-build X` |
| `uv run invoke lab.image-build --template X --tag Y` | `lab image-build X --tag Y` |
| `uv run invoke lab.image-list` | `lab image-list` |
| `uv run invoke lab.image-list --verbose` | `lab image-list --verbose` |
| `uv run invoke lab.image-delete --image-tag X` | `lab image-delete X` |
| `uv run invoke lab.image-update --template X` | `lab image-update X` |
| `uv run invoke lab.image-inspect --image-tag X` | `lab image-inspect X` |
| `uv run invoke lab.gui` | `lab gui` |

## Installation

### First Time Setup

```bash
# Install the package
uv pip install -e .

# Verify installation
lab --help

# Check system requirements
lab check
```

### Upgrading from Invoke Version

If you were using the invoke-based version:

```bash
# Update your installation
git pull

# Reinstall
uv pip install -e .

# Verify
lab --help
```

## What Changed

### 1. Package Structure

**Before:**
```
.
├── .claude/skills/claude-lab/
│   ├── claude-lab.py
│   └── templates/
└── tasks.py
```

**After:**
```
.
├── src/claude_lab/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   └── templates/
├── .claude/skills/claude-lab/
│   ├── SKILL.md
│   └── (reference files)
└── pyproject.toml
```

### 2. Entry Point

**Before:** PEP 723 script with `uv run`
```bash
uv run .claude/skills/claude-lab/claude-lab.py setup my-lab
```

**After:** Installed CLI command
```bash
lab setup my-lab
```

### 3. Benefits

✅ **Shorter commands** - `lab setup` vs `uv run invoke lab.setup`
✅ **Tab completion** - Shell completion support (future)
✅ **System-wide** - Available anywhere after installation
✅ **Proper package** - Can be published to PyPI
✅ **Cleaner** - No need for invoke wrapper
✅ **Faster** - Direct execution, no extra layers

## Breaking Changes

### None!

The old invoke-based commands still work if you prefer them. The `tasks.py` file has been kept for backwards compatibility.

You can use both:
```bash
# New way (recommended)
lab setup my-lab

# Old way (still works)
uv run invoke lab.setup --name my-lab
```

## For Scripts and Automation

### Shell Scripts

Update your shell scripts:

```bash
# Before
#!/bin/bash
uv run invoke lab.setup --name ci-test
uv run invoke lab.teardown --name ci-test

# After
#!/bin/bash
lab setup ci-test
lab teardown ci-test
```

### Python Scripts

Update your Python integration:

```python
# Before
import subprocess
subprocess.run(["uv", "run", "invoke", "lab.setup", "--name", "test"])

# After
import subprocess
subprocess.run(["lab", "setup", "test"])
```

Or use the Python API directly:

```python
# Direct import
from claude_lab.cli import cli

# Can be invoked programmatically if needed
```

### CI/CD Pipelines

Update your CI/CD configs:

```yaml
# Before
steps:
  - run: uv pip install invoke
  - run: uv run invoke lab.setup --name ci-env

# After
steps:
  - run: uv pip install -e .
  - run: lab setup ci-env
```

## Documentation Updates

All documentation has been updated to use the new `lab` command:

- ✅ README.md
- ✅ QUICKSTART.md
- ✅ CLAUDE.md
- ✅ SKILL.md
- ✅ docs/IMAGE-MANAGEMENT.md
- ✅ All example scripts

## Troubleshooting

### Command not found

If `lab` command is not found:

```bash
# Check installation
pip show claude-lab

# Reinstall
uv pip install -e .

# Check PATH (for pipx)
pipx ensurepath
```

### Import errors

```bash
# Reinstall with force
uv pip install --force-reinstall -e .
```

### Still prefer invoke?

The invoke-based commands still work! Just keep using them:

```bash
uv run invoke lab.setup --name my-lab
```

## Questions?

- See [INSTALL.md](INSTALL.md) for installation help
- See [README.md](README.md) for full documentation
- Check `lab --help` for command reference

## Future Enhancements

With the new CLI structure, we can add:

- Shell completion (bash, zsh, fish)
- Better error messages
- Progress bars
- Interactive prompts
- Plugin system
- PyPI distribution
