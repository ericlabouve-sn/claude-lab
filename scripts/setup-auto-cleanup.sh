#!/bin/bash
# Setup automatic cleanup for claude-lab

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Claude Lab Auto-Cleanup Setup ===${NC}\n"

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     OS_TYPE=Linux;;
    Darwin*)    OS_TYPE=Mac;;
    *)          OS_TYPE="UNKNOWN:${OS}"
esac

echo -e "${GREEN}Detected OS: $OS_TYPE${NC}\n"

# Get lab command path
LAB_CMD=$(which lab || echo "/usr/local/bin/lab")
if [ ! -x "$LAB_CMD" ]; then
    echo -e "${RED}Error: lab command not found at $LAB_CMD${NC}"
    echo "Please install claude-lab first: uv tool install ."
    exit 1
fi

echo -e "${GREEN}Found lab command: $LAB_CMD${NC}\n"

# Ask for cleanup age
read -p "Cleanup labs older than how many hours? [24]: " AGE_HOURS
AGE_HOURS=${AGE_HOURS:-24}

# Ask for frequency
echo -e "\nHow often should cleanup run?"
echo "1) Hourly"
echo "2) Every 6 hours"
echo "3) Daily"
echo "4) On shell exit only (manual)"
read -p "Choice [3]: " FREQ_CHOICE
FREQ_CHOICE=${FREQ_CHOICE:-3}

case $FREQ_CHOICE in
    1) FREQ_DESC="hourly";;
    2) FREQ_DESC="every 6 hours";;
    3) FREQ_DESC="daily";;
    4) FREQ_DESC="on shell exit";;
    *) FREQ_DESC="daily"; FREQ_CHOICE=3;;
esac

echo -e "\n${YELLOW}Configuration:${NC}"
echo "  Cleanup age: $AGE_HOURS hours"
echo "  Frequency: $FREQ_DESC"
echo ""

read -p "Proceed with installation? [y/N]: " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Installation cancelled."
    exit 0
fi

echo ""

# Setup based on OS and choice
if [ "$FREQ_CHOICE" = "4" ]; then
    # Shell exit hook
    HOOK_CODE="
# Claude Lab auto-cleanup on shell exit
claude_lab_cleanup() {
    if command -v lab &> /dev/null; then
        lab cleanup --older-than $AGE_HOURS > /dev/null 2>&1 &
    fi
}
trap claude_lab_cleanup EXIT
"

    SHELL_RC=""
    if [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        echo -e "${YELLOW}Warning: Could not detect shell. Add the hook manually.${NC}"
        echo "$HOOK_CODE"
        exit 0
    fi

    echo -e "${BLUE}Adding exit hook to $SHELL_RC${NC}"
    if grep -q "claude_lab_cleanup" "$SHELL_RC" 2>/dev/null; then
        echo -e "${YELLOW}Hook already exists in $SHELL_RC${NC}"
    else
        echo "$HOOK_CODE" >> "$SHELL_RC"
        echo -e "${GREEN}✓ Added hook to $SHELL_RC${NC}"
    fi

    echo -e "\n${GREEN}Setup complete!${NC}"
    echo "Restart your shell or run: source $SHELL_RC"

elif [ "$OS_TYPE" = "Linux" ]; then
    # Systemd timer
    echo -e "${BLUE}Setting up systemd timer...${NC}\n"

    # Determine schedule
    case $FREQ_CHOICE in
        1) SCHEDULE="hourly";;
        2) SCHEDULE="*-*-* 0/6:00:00";;
        3) SCHEDULE="daily";;
    esac

    # Create service file
    SERVICE_FILE="$HOME/.config/systemd/user/claude-lab-cleanup.service"
    TIMER_FILE="$HOME/.config/systemd/user/claude-lab-cleanup.timer"

    mkdir -p "$HOME/.config/systemd/user"

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Claude Lab Cleanup Service

[Service]
Type=oneshot
ExecStart=$LAB_CMD cleanup --older-than $AGE_HOURS

[Install]
WantedBy=default.target
EOF

    cat > "$TIMER_FILE" <<EOF
[Unit]
Description=Claude Lab Cleanup Timer

[Timer]
OnCalendar=$SCHEDULE
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable and start timer
    systemctl --user daemon-reload
    systemctl --user enable claude-lab-cleanup.timer
    systemctl --user start claude-lab-cleanup.timer

    echo -e "${GREEN}✓ Created systemd service and timer${NC}"
    echo -e "\nStatus:"
    systemctl --user status claude-lab-cleanup.timer --no-pager

elif [ "$OS_TYPE" = "Mac" ]; then
    # launchd agent
    echo -e "${BLUE}Setting up launchd agent...${NC}\n"

    # Determine interval (in seconds)
    case $FREQ_CHOICE in
        1) INTERVAL=3600;;
        2) INTERVAL=21600;;
        3) INTERVAL=86400;;
    esac

    PLIST_FILE="$HOME/Library/LaunchAgents/com.claudelab.cleanup.plist"
    mkdir -p "$HOME/Library/LaunchAgents"

    cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claudelab.cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>$LAB_CMD</string>
        <string>cleanup</string>
        <string>--older-than</string>
        <string>$AGE_HOURS</string>
    </array>
    <key>StartInterval</key>
    <integer>$INTERVAL</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/claude-lab-cleanup.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/claude-lab-cleanup-error.log</string>
</dict>
</plist>
EOF

    # Load the agent
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"

    echo -e "${GREEN}✓ Created launchd agent${NC}"
    echo -e "\nAgent loaded. Check status with:"
    echo "  launchctl list | grep claudelab"

else
    echo -e "${RED}Unsupported OS: $OS_TYPE${NC}"
    echo "Please set up cleanup manually using cron or your system's scheduler."
    exit 1
fi

echo -e "\n${GREEN}=== Setup Complete! ===${NC}"
echo -e "\nAutomatic cleanup is now enabled:"
echo "  Frequency: $FREQ_DESC"
echo "  Max age: $AGE_HOURS hours"
echo -e "\nManual cleanup: ${BLUE}lab cleanup --dry-run${NC}"
echo -e "View logs: ${BLUE}lab notifications | grep cleanup${NC}"
