# Docker Image Management

Claude Lab Manager includes a comprehensive image management system to create, customize, and manage Docker images with pre-installed tools like kubectl, helm, k9s, and more.

## Why Custom Images?

Custom base images provide:

- **Faster startup** - Tools are pre-installed, no setup time
- **Consistency** - Same environment across all labs
- **Customization** - Tailor images to your project needs
- **Efficiency** - No repeated installations

## Available Templates

### 1. **minimal** (~300MB)
Lightweight image with just the essentials.

**Tools:**
- kubectl
- helm

**Use case:** Basic Kubernetes operations, minimal overhead

```bash
labimage-build --template minimal
```

### 2. **base** (~800MB) - Default
Standard development environment with common tools.

**Tools:**
- kubectl
- helm
- k9s (Kubernetes CLI UI)
- docker CLI
- git
- vim/nano
- jq/yq
- htop, tree

**Use case:** Standard k8s development workflow

```bash
labimage-build --template base
```

### 3. **k8s-full** (~2GB)
Comprehensive Kubernetes environment with all the tools.

**Tools:**
- kubectl, helm, k9s
- kubectx, kubens
- kustomize
- stern (log tailing)
- flux CLI
- ArgoCD CLI
- Istio CLI
- Terraform
- docker CLI
- Python 3 with kubernetes library

**Use case:** Advanced k8s development, GitOps, service mesh

```bash
labimage-build --template k8s-full
```

### 4. **python-dev** (~1.5GB)
Python development environment for k8s applications.

**Tools:**
- kubectl, helm, k9s
- Python 3.11
- uv (Python package manager)
- pip, pytest, black, ruff, mypy
- kubernetes Python library
- FastAPI, uvicorn
- Jupyter
- Common Python packages

**Use case:** Python microservices development on Kubernetes

```bash
labimage-build --template python-dev
```

## Image Management Commands

### Build an Image

```bash
# Build from template
labimage-build --template base

# Build with custom tag
labimage-build --template k8s-full --tag v1.0

# Build without cache (force rebuild)
labimage-build --template base --no-cache
```

### List Images

```bash
# List all templates and built images
labimage-list

# Show detailed information
labimage-list --verbose
```

### Delete an Image

```bash
# Delete by tag
labimage-delete --image-tag base

# Force delete
labimage-delete --image-tag base --force
```

### Update (Rebuild) an Image

```bash
# Rebuild with latest changes (no-cache)
labimage-update --template base
```

### Inspect an Image

```bash
# Show detailed image information
labimage-inspect --image-tag base
```

## Using Custom Images with Labs

### Create a Lab with Custom Image

```bash
# Use the k8s-full image
labsetup --name feature-api --image claude-lab:k8s-full

# Use the python-dev image
labsetup --name python-service --image claude-lab:python-dev

# Use the minimal image
labsetup --name quick-test --image claude-lab:minimal
```

### Default Behavior

If no `--image` is specified, the lab uses the Claude sandbox default image.

## Customizing Templates

### Location

Templates are stored in `.claude/skills/claude-lab/templates/`:

```
templates/
├── minimal.Dockerfile
├── base.Dockerfile
├── k8s-full.Dockerfile
├── python-dev.Dockerfile
└── templates.json
```

### Adding a New Template

1. **Create a Dockerfile:**

```dockerfile
# .claude/skills/claude-lab/templates/custom.Dockerfile
FROM ubuntu:22.04

LABEL claude-lab.template="custom"
LABEL claude-lab.version="1.0.0"

# Install your tools
RUN apt-get update && apt-get install -y \
    your-tool \
    && rm -rf /var/lib/apt/lists/*

# ... rest of your setup

WORKDIR /workspace
CMD ["/bin/bash"]
```

2. **Add to templates.json:**

```json
{
  "templates": {
    "custom": {
      "name": "custom",
      "dockerfile": "custom.Dockerfile",
      "description": "My custom template",
      "size_estimate": "~500MB",
      "tools": ["tool1", "tool2"],
      "use_case": "Custom development workflow"
    }
  }
}
```

3. **Build it:**

```bash
labimage-build --template custom
```

### Modifying Existing Templates

Edit the Dockerfile, then rebuild:

```bash
# Edit the file
vim .claude/skills/claude-lab/templates/base.Dockerfile

# Rebuild
labimage-update --template base
```

## Build Arguments

Templates support build arguments for version control:

```dockerfile
ARG KUBECTL_VERSION=v1.29.0
RUN curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
```

You can override these during build by editing the template.

## Best Practices

### 1. Layer Caching

Order Dockerfile commands from least to most frequently changed:

```dockerfile
# System packages (rarely change)
RUN apt-get update && apt-get install -y curl git

# Tools (occasionally change)
RUN install-kubectl

# Project-specific (frequently change)
COPY my-scripts /usr/local/bin/
```

### 2. Minimize Image Size

- Use `apt-get clean` or `rm -rf /var/lib/apt/lists/*`
- Combine RUN commands with `&&`
- Use multi-stage builds if needed

### 3. Version Pinning

Pin versions for reproducibility:

```dockerfile
ARG KUBECTL_VERSION=v1.29.0  # Good
RUN curl ... ${KUBECTL_VERSION} ...

# vs
RUN curl ... latest ...  # Bad - not reproducible
```

### 4. Image Naming

Use meaningful tags:

```bash
# Good
labimage-build --template base --tag v1.0-stable
labimage-build --template base --tag 2024-01-prod

# Avoid
labimage-build --template base --tag test123
```

## Example Workflows

### Build All Templates

```bash
for template in minimal base k8s-full python-dev; do
  labimage-build --template $template
done
```

### Update All Images

```bash
for template in minimal base k8s-full python-dev; do
  labimage-update --template $template
done
```

### Create Labs with Different Images

```bash
# Backend team - k8s-full
labsetup --name backend-api --image claude-lab:k8s-full

# Frontend team - minimal
labsetup --name frontend-app --image claude-lab:minimal

# ML team - python-dev
labsetup --name ml-service --image claude-lab:python-dev
```

## Troubleshooting

### Build Fails

```bash
# Check Docker is running
docker ps

# Try with no-cache
labimage-build --template base --no-cache

# Check logs
docker logs <container-id>
```

### Image Too Large

1. Review Dockerfile
2. Remove unnecessary packages
3. Combine RUN commands
4. Use `--no-install-recommends` with apt-get

### Version Conflicts

Pin specific versions in the Dockerfile:

```dockerfile
ARG KUBECTL_VERSION=v1.29.0
ARG HELM_VERSION=v3.14.0
```

## Integration with CI/CD

### Pre-build Images in CI

```yaml
# .github/workflows/build-images.yml
name: Build Lab Images
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        template: [minimal, base, k8s-full, python-dev]
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v2
      - name: Build ${{ matrix.template }}
        run: labimage-build --template ${{ matrix.template }}
      - name: Push to registry
        run: docker push claude-lab:${{ matrix.template }}
```

## Advanced: Custom Image Registry

To use a private registry:

1. **Build and tag:**
```bash
labimage-build --template base --tag v1.0
docker tag claude-lab:v1.0 registry.example.com/claude-lab:v1.0
```

2. **Push:**
```bash
docker push registry.example.com/claude-lab:v1.0
```

3. **Use in lab:**
```bash
labsetup --name my-lab --image registry.example.com/claude-lab:v1.0
```

## Summary

Image management in Claude Lab Manager provides:

- ✅ Pre-built templates for common use cases
- ✅ Fast lab startup with pre-installed tools
- ✅ Customizable Dockerfiles
- ✅ Easy build/update/delete workflow
- ✅ Integration with lab setup
- ✅ Version control and tagging

For most users, the **base** template is recommended. Use **k8s-full** for comprehensive k8s development or **python-dev** for Python applications.
