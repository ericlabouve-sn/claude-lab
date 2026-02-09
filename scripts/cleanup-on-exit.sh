#!/bin/bash
# Cleanup script for claude-lab
# Can be used as an exit hook or run manually

set -e

# Configuration
DEFAULT_AGE_HOURS=24
DRY_RUN=${DRY_RUN:-false}
VERBOSE=${VERBOSE:-false}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    if [ "$VERBOSE" = "true" ]; then
        echo -e "${GREEN}[claude-lab-cleanup]${NC} $1"
    fi
}

error() {
    echo -e "${RED}[claude-lab-cleanup ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[claude-lab-cleanup WARN]${NC} $1"
}

# Check if lab command exists
if ! command -v lab &> /dev/null; then
    error "lab command not found. Is claude-lab installed?"
    exit 1
fi

# Determine cleanup age
AGE_HOURS=${CLAUDE_LAB_CLEANUP_AGE:-$DEFAULT_AGE_HOURS}

log "Starting cleanup (age: ${AGE_HOURS}h, dry-run: ${DRY_RUN})"

# Build cleanup command
CMD="lab cleanup --older-than $AGE_HOURS"

if [ "$DRY_RUN" = "true" ]; then
    CMD="$CMD --dry-run"
fi

# Run cleanup
if [ "$VERBOSE" = "true" ]; then
    $CMD
else
    $CMD > /dev/null 2>&1 || {
        error "Cleanup failed"
        exit 1
    }
fi

log "Cleanup complete"
exit 0
