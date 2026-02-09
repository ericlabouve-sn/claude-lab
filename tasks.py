"""
Invoke tasks for Claude Lab Manager

Run with: uv run invoke <task>
"""

from invoke import task
from pathlib import Path

SKILL_DIR = Path(".claude/skills/claude-lab")
CLAUDE_LAB_SCRIPT = SKILL_DIR / "claude-lab.py"


@task
def lab_check(c):
    """Check system requirements for claude-lab"""
    c.run(f"uv run {CLAUDE_LAB_SCRIPT} check")


@task
def lab_install(c):
    """Install required system tools for claude-lab"""
    c.run(f"uv run {CLAUDE_LAB_SCRIPT} install")


@task
def lab_setup(c, name, branch=None, image=None):
    """Set up a new isolated lab environment

    Args:
        name: Name of the lab environment
        branch: Git branch to checkout (default: current)
        image: Custom Docker image to use (e.g., claude-lab:k8s-full)
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} setup {name}"
    if branch:
        cmd += f" --branch {branch}"
    if image:
        cmd += f" --image {image}"
    c.run(cmd)


@task
def lab_teardown(c, name, force=False):
    """Tear down a lab environment

    Args:
        name: Name of the lab environment
        force: Force removal even if resources are busy
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} teardown {name}"
    if force:
        cmd += " --force"
    c.run(cmd)


@task
def lab_list(c):
    """List all active lab environments"""
    c.run(f"uv run {CLAUDE_LAB_SCRIPT} list")


@task
def lab_cleanup(c, dry_run=False, all=False, older_than=None):
    """Clean up orphaned or stale lab environments

    Args:
        dry_run: Show what would be cleaned up without cleaning
        all: Clean up all labs
        older_than: Clean up labs older than N hours
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} cleanup"
    if dry_run:
        cmd += " --dry-run"
    if all:
        cmd += " --all"
    if older_than:
        cmd += f" --older-than {older_than}"
    c.run(cmd)


@task
def lab_notify(c, message, level="info", source="user"):
    """Send a notification

    Args:
        message: Notification message
        level: Notification level (info, success, warning, error)
        source: Source of the notification
    """
    c.run(f'uv run {CLAUDE_LAB_SCRIPT} notify --message "{message}" --level {level} --source {source}')


@task
def lab_notifications(c, follow=False, last=None):
    """View notification history

    Args:
        follow: Follow new notifications (like tail -f)
        last: Show last N notifications
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} notifications"
    if follow:
        cmd += " --follow"
    if last:
        cmd += f" --last {last}"
    c.run(cmd)


@task
def lab_status(c):
    """Show interactive lab status (alias for running script without args)"""
    c.run(f"uv run {CLAUDE_LAB_SCRIPT}")


@task
def lab_image_build(c, template, tag=None, no_cache=False):
    """Build a Docker image from a template

    Args:
        template: Template name (minimal, base, k8s-full, python-dev)
        tag: Custom tag for the image
        no_cache: Build without cache
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} image-build {template}"
    if tag:
        cmd += f" --tag {tag}"
    if no_cache:
        cmd += " --no-cache"
    c.run(cmd)


@task
def lab_image_list(c, verbose=False):
    """List available templates and built images

    Args:
        verbose: Show detailed information
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} image-list"
    if verbose:
        cmd += " --verbose"
    c.run(cmd)


@task
def lab_image_delete(c, image_tag, force=False):
    """Delete a built Docker image

    Args:
        image_tag: Tag of the image to delete
        force: Force removal
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} image-delete {image_tag}"
    if force:
        cmd += " --force"
    c.run(cmd)


@task
def lab_image_update(c, template):
    """Rebuild an existing image

    Args:
        template: Template name to rebuild
    """
    c.run(f"uv run {CLAUDE_LAB_SCRIPT} image-update {template}")


@task
def lab_image_inspect(c, image_tag):
    """Show detailed information about an image

    Args:
        image_tag: Tag of the image to inspect
    """
    c.run(f"uv run {CLAUDE_LAB_SCRIPT} image-inspect {image_tag}")


@task
def lab_image_from_project(c, project_path, name=None, base=None, analyze_only=False, dry_run=False):
    """Analyze a project and create a custom Docker image for it

    Args:
        project_path: Path to the project directory
        name: Custom image name (default: project directory name)
        base: Base template to use (default: auto-detect)
        analyze_only: Only analyze project, don't build image
        dry_run: Generate Dockerfile but don't build
    """
    cmd = f"uv run {CLAUDE_LAB_SCRIPT} image-from-project {project_path}"
    if name:
        cmd += f" --name {name}"
    if base:
        cmd += f" --base {base}"
    if analyze_only:
        cmd += " --analyze-only"
    if dry_run:
        cmd += " --dry-run"
    c.run(cmd)


@task(name="lab.all")
def lab_all(c):
    """Show all lab-related commands"""
    print("Claude Lab Manager Commands:")
    print("\n[Environment Management]")
    print("  uv run invoke lab.check               - Check system requirements")
    print("  uv run invoke lab.install             - Install required tools")
    print("  uv run invoke lab.setup --name=<name> - Create new lab environment")
    print("  uv run invoke lab.teardown --name=<name> - Remove lab environment")
    print("  uv run invoke lab.list                - List all environments")
    print("  uv run invoke lab.status              - Interactive status view")
    print("\n[Image Management]")
    print("  uv run invoke lab.image-build --template=<template> - Build Docker image")
    print("  uv run invoke lab.image-list          - List templates and images")
    print("  uv run invoke lab.image-delete --image-tag=<tag> - Delete image")
    print("  uv run invoke lab.image-update --template=<template> - Rebuild image")
    print("  uv run invoke lab.image-inspect --image-tag=<tag> - Inspect image")
    print("\n[Notifications]")
    print("  uv run invoke lab.notify --message='...' - Send notification")
    print("  uv run invoke lab.notifications       - View notification history")


# Namespace for better organization
from invoke import Collection

ns = Collection()
lab = Collection("lab")

lab.add_task(lab_check, "check")
lab.add_task(lab_install, "install")
lab.add_task(lab_setup, "setup")
lab.add_task(lab_teardown, "teardown")
lab.add_task(lab_list, "list")
lab.add_task(lab_cleanup, "cleanup")
lab.add_task(lab_notify, "notify")
lab.add_task(lab_notifications, "notifications")
lab.add_task(lab_status, "status")
lab.add_task(lab_image_build, "image-build")
lab.add_task(lab_image_list, "image-list")
lab.add_task(lab_image_delete, "image-delete")
lab.add_task(lab_image_update, "image-update")
lab.add_task(lab_image_inspect, "image-inspect")
lab.add_task(lab_image_from_project, "image-from-project")
lab.add_task(lab_all, "all")

ns.add_collection(lab)
