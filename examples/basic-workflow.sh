#!/bin/bash
# Example workflow for using claude-lab

set -e

echo "=== Claude Lab Basic Workflow Example ==="
echo

# 1. Check system requirements
echo "1. Checking system requirements..."
labcheck
echo

# 2. Create a new lab environment
echo "2. Creating lab environment 'demo-lab'..."
labsetup --name demo-lab
echo

# 3. List active labs
echo "3. Listing active labs..."
lablist
echo

# 4. Send a test notification
echo "4. Sending test notification..."
labnotify --message "Demo lab is running" --level info
echo

# 5. Show notification history
echo "5. Showing notifications..."
labnotifications --last 5
echo

# 6. Instructions for next steps
echo "Next steps:"
echo "  - Connect to lab: tmux attach -t demo-lab"
echo "  - Test kubectl: kubectl get nodes"
echo "  - Tear down: labteardown --name demo-lab"
echo

echo "=== Demo Complete ==="
echo "Note: Run 'labteardown --name demo-lab' when done"
