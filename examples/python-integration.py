#!/usr/bin/env python3
"""
Example: Programmatic integration with claude-lab manager

This shows how to integrate claude-lab into your own Python scripts.
"""

import subprocess
import json
import time
from pathlib import Path


def run_command(cmd):
    """Run a command and return the result"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout, result.stderr


def get_registry():
    """Load the lab registry"""
    registry_path = Path.home() / ".claude-lab-port-registry.json"
    if not registry_path.exists():
        return {}
    return json.loads(registry_path.read_text())


def create_lab(name, branch=None):
    """Create a new lab environment"""
    cmd = f"lab setup {name}"
    if branch:
        cmd += f" --branch {branch}"

    print(f"Creating lab '{name}'...")
    success, stdout, stderr = run_command(cmd)

    if success:
        print(f"✓ Lab '{name}' created successfully")
        return True
    else:
        print(f"✗ Failed to create lab: {stderr}")
        return False


def teardown_lab(name):
    """Tear down a lab environment"""
    print(f"Tearing down lab '{name}'...")
    success, stdout, stderr = run_command(f"lab teardown {name}")

    if success:
        print(f"✓ Lab '{name}' torn down successfully")
        return True
    else:
        print(f"✗ Failed to tear down lab: {stderr}")
        return False


def send_notification(message, level="info"):
    """Send a notification"""
    cmd = f'lab notify --message "{message}" --level {level}'
    run_command(cmd)


def list_active_labs():
    """List all active labs"""
    registry = get_registry()
    return list(registry.keys())


def main():
    """Example workflow"""
    print("=== Claude Lab Python Integration Example ===\n")

    # Create two labs
    labs = ["python-demo-1", "python-demo-2"]

    for lab in labs:
        if create_lab(lab):
            send_notification(f"Lab {lab} created", "success")

    # Wait a bit
    print("\nWaiting 2 seconds...")
    time.sleep(2)

    # List active labs
    print("\nActive labs:")
    for lab in list_active_labs():
        print(f"  - {lab}")

    # Tear down labs
    print()
    for lab in labs:
        if teardown_lab(lab):
            send_notification(f"Lab {lab} torn down", "info")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
