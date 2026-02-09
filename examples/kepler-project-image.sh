#!/bin/bash
# Example: Creating a custom image for the Kepler platform project

set -e

KEPLER_PATH="/Users/ericlabouve/Desktop/git/github/upstream/kepler-base/platform-labs-kepler"

echo "=== Kepler Platform Custom Image Example ==="
echo

# Check if path exists
if [ ! -d "$KEPLER_PATH" ]; then
    echo "Error: Kepler project not found at $KEPLER_PATH"
    echo "Update KEPLER_PATH in this script to point to your Kepler project"
    exit 1
fi

# 1. Analyze the Kepler project
echo "1. Analyzing Kepler project..."
lab image-from-project "$KEPLER_PATH" --analyze-only
echo

# 2. Generate Dockerfile without building (dry-run)
echo "2. Generating Dockerfile..."
lab image-from-project "$KEPLER_PATH" --dry-run
echo

# 3. Show the generated Dockerfile
if [ -f "$KEPLER_PATH/Dockerfile.claude-lab" ]; then
    echo "3. Generated Dockerfile:"
    echo "---"
    cat "$KEPLER_PATH/Dockerfile.claude-lab"
    echo "---"
    echo
fi

# 4. Ask if user wants to build
echo "4. Ready to build?"
echo
echo "To build the image, run:"
echo "  lab image-from-project $KEPLER_PATH"
echo
echo "Or build with a custom name:"
echo "  lab image-from-project $KEPLER_PATH --name kepler-dev"
echo
echo "Then create a lab with the custom image:"
echo "  lab setup kepler --image claude-lab:platform-labs-kepler"
echo

echo "=== Example Complete ==="
