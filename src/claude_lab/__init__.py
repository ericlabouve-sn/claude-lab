"""
Claude Lab Manager - Orchestrate isolated k3d clusters with git worktrees
"""

__version__ = "0.1.0"
__author__ = "Claude Lab Contributors"

from .cli import cli

__all__ = ["cli"]
