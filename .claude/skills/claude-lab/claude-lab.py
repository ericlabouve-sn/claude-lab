#!/usr/bin/env python3
"""
Claude Lab Manager Skill - Thin wrapper to installed 'lab' CLI command

This skill script delegates all functionality to the globally installed
'lab' command from the claude-lab package. Install with:
    uv tool install claude-lab

For development, install from source:
    uv tool install --editable .
"""

import subprocess
import sys
import shutil

def main():
    # Check if 'lab' command is available
    if not shutil.which('lab'):
        print("Error: 'lab' command not found. Please install claude-lab:")
        print("  uv tool install claude-lab")
        print("\nOr install from source:")
        print("  uv tool install --editable .")
        sys.exit(1)

    # Pass all arguments to the installed 'lab' command
    result = subprocess.run(['lab'] + sys.argv[1:])
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
