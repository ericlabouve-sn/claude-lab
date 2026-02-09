#!/bin/bash
# Example: Docker image management workflow

set -e

echo "=== Claude Lab Image Management Workflow ==="
echo

# 1. List available templates
echo "1. Listing available templates..."
labimage-list
echo

# 2. Build a base image
echo "2. Building base image..."
labimage-build --template base
echo

# 3. Build k8s-full image with custom tag
echo "3. Building k8s-full image with custom tag..."
labimage-build --template k8s-full --tag v1.0
echo

# 4. List built images
echo "4. Listing built images..."
labimage-list
echo

# 5. Inspect an image
echo "5. Inspecting base image..."
labimage-inspect --image-tag base
echo

# 6. Create labs with different images
echo "6. Creating labs with different images..."
labsetup --name lab-base --image claude-lab:base
labsetup --name lab-full --image claude-lab:v1.0
echo

# 7. List active labs
echo "7. Listing active labs..."
lablist
echo

# 8. Cleanup
echo "8. Cleaning up labs..."
labteardown --name lab-base
labteardown --name lab-full
echo

# 9. Update an image
echo "9. Updating base image (rebuild)..."
labimage-update --template base
echo

echo "=== Workflow Complete ==="
echo
echo "Image Management Summary:"
echo "  - Built images: base, k8s-full:v1.0"
echo "  - Created and cleaned up 2 labs"
echo "  - Updated base image"
echo
echo "Next steps:"
echo "  - Build more templates: minimal, python-dev"
echo "  - Customize Dockerfiles in .claude/skills/claude-lab/templates/"
echo "  - See docs/IMAGE-MANAGEMENT.md for details"
