.PHONY: help install install-dev install-global uninstall test clean check

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install for development (editable)
	uv pip install -e .
	@echo ""
	@echo "✅ Installed in development mode"
	@echo "Run 'lab --help' to verify"

install-dev: install ## Alias for install

install-global: ## Install globally with uv tool
	uv tool install .
	@echo ""
	@echo "✅ Installed globally with uv tool"
	@echo "Run 'lab --help' from any directory to verify"

install-pipx: ## Install globally with pipx
	pipx install .
	@echo ""
	@echo "✅ Installed globally with pipx"
	@echo "Run 'lab --help' from any directory to verify"

uninstall: ## Uninstall from uv tool
	-uv tool uninstall claude-lab
	@echo "✅ Uninstalled from uv tool"

uninstall-pipx: ## Uninstall from pipx
	-pipx uninstall claude-lab
	@echo "✅ Uninstalled from pipx"

reinstall: ## Reinstall (uninstall + install-global)
	$(MAKE) uninstall
	$(MAKE) install-global

test: ## Run CLI tests
	python test_cli.py

check: ## Check system requirements
	lab check

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

build: clean ## Build distribution packages
	uv build

# Development helpers
dev-check: install ## Install and run system check
	lab check

dev-image: install ## Install and build base image
	lab image-build base

dev-test: install ## Install and run full test
	lab check
	lab image-list
	@echo ""
	@echo "✅ Development environment ready!"

# Quick start for new users
quickstart: install-global dev-check ## Complete quickstart (install + check)
	@echo ""
	@echo "🚀 Quickstart complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. lab image-build base      # Build base image (optional)"
	@echo "  2. lab setup my-first-lab    # Create your first lab"
	@echo "  3. tmux attach -t my-first-lab  # Connect to it"

# Show installation status
status: ## Show installation status
	@echo "=== Installation Status ==="
	@echo ""
	@echo "uv tool:"
	@uv tool list | grep claude-lab || echo "  Not installed"
	@echo ""
	@echo "pipx:"
	@pipx list | grep claude-lab || echo "  Not installed"
	@echo ""
	@echo "Command location:"
	@which lab || echo "  Command not found in PATH"
	@echo ""
	@echo "Version:"
	@lab --version 2>/dev/null || echo "  Not available"
