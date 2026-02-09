#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "click", "textual"]
# ///

"""
Claude Lab Manager - Orchestrate isolated k3d clusters with git worktrees and tmux
"""

import os
import json
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime
import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
REGISTRY_PATH = Path.home() / ".claude-lab-port-registry.json"
NOTIFICATIONS_PATH = Path.home() / ".claude-lab-notifications.jsonl"

# Import proxy and DNS managers
try:
    from claude_lab.proxy import ProxyManager
    from claude_lab.dns import DNSManager
    PROXY_AVAILABLE = True
except ImportError:
    PROXY_AVAILABLE = False

# Configuration from environment variables (global defaults)
WORKTREE_BASE_DIR = os.environ.get("CLAUDE_LAB_WORKTREE_DIR", "/tmp/claude-labs")
BASE_PORT = int(os.environ.get("CLAUDE_LAB_BASE_PORT", "8080"))


def load_global_settings():
    """Load global user settings from ~/.lab/settings.yaml if it exists"""
    settings_path = Path.home() / ".lab" / "settings.yaml"

    if not settings_path.exists():
        return {}

    try:
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
            return settings
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load global settings {settings_path}: {e}[/yellow]")
        return {}


def load_project_settings():
    """Load project-specific settings from .lab/settings.yaml if it exists"""
    settings_path = Path.cwd() / ".lab" / "settings.yaml"

    if not settings_path.exists():
        return {}

    try:
        with open(settings_path) as f:
            settings = yaml.safe_load(f) or {}
            return settings
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load {settings_path}: {e}[/yellow]")
        return {}


def get_merged_settings():
    """Get merged settings with proper precedence: project > global > env > defaults"""
    global_settings = load_global_settings()
    project_settings = load_project_settings()

    # Merge settings (project overrides global)
    merged = {**global_settings, **project_settings}

    return merged, bool(project_settings), bool(global_settings)


def get_project_setting(key, default=None):
    """Get a setting with fallback chain: project > global > env > default"""
    merged_settings, has_project, has_global = get_merged_settings()

    # Check merged settings first (project overrides global)
    if key in merged_settings:
        return merged_settings[key]

    # Fallback to environment variables
    env_map = {
        "worktree_dir": ("CLAUDE_LAB_WORKTREE_DIR", "/tmp/claude-labs"),
        "docker_image": ("CLAUDE_LAB_DOCKER_IMAGE", "claude"),
        "base_port": ("CLAUDE_LAB_BASE_PORT", 8080),
    }

    if key in env_map:
        env_var, env_default = env_map[key]
        value = os.environ.get(env_var, env_default)
        if key == "base_port":
            return int(value)
        return value

    return default


def find_templates_dir():
    """
    Find templates directory with priority hierarchy:
    1. Project-specific: .lab/templates/
    2. User-global: ~/.lab/templates/
    3. Built-in: installed package templates/

    Returns Path to templates directory containing templates.json
    """
    # 1. Check project .lab/templates
    project_templates = Path.cwd() / ".lab" / "templates"
    if project_templates.exists() and (project_templates / "templates.json").exists():
        return project_templates

    # 2. Check global ~/.lab/templates
    global_templates = Path.home() / ".lab" / "templates"
    if global_templates.exists() and (global_templates / "templates.json").exists():
        return global_templates

    # 3. Fall back to built-in (installed package)
    return Path(__file__).parent / "templates"


def get_registry():
    """Load the port registry from disk"""
    if not REGISTRY_PATH.exists():
        return {}
    return json.loads(REGISTRY_PATH.read_text())


def save_registry(reg):
    """Save the port registry to disk"""
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2))


def get_next_port():
    """Find the next available port for a new cluster"""
    reg = get_registry()
    base_port = get_project_setting("base_port", 8080)
    ports = [item["port"] for item in reg.values()]
    return max(ports, default=base_port) + 1


def log_notification(message, level="info", source="system"):
    """Write a notification to the notifications file"""
    notification = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "source": source,
        "message": message,
    }
    with open(NOTIFICATIONS_PATH, "a") as f:
        f.write(json.dumps(notification) + "\n")


def _send_macos_notification(message, level, source, request_response, settings):
    """Send macOS system notification using alerter"""
    # Map levels to alerter sounds
    sounds = {
        "info": "Glass",
        "success": "Hero",
        "warning": "Basso",
        "error": "Sosumi"
    }

    # Build alerter command
    cmd = [
        "alerter",
        "-title", "Claude Lab",
        "-subtitle", f"From: {source}",
        "-message", message,
        "-sound", sounds.get(level, "Glass"),
        "-timeout", "30",  # Auto-dismiss after 30 seconds
    ]

    # Add reply button if response is requested
    if request_response:
        cmd.extend(["-reply", "-dropdownLabel", "Quick Reply"])

    # Note: We don't add -execute here because this version of alerter (1.0.1)
    # doesn't support that flag. Instead, we'll handle the click response below.

    # Execute alerter and capture response
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # Wait up to 60 seconds for user response
        )

        # Check if user provided a reply
        if result.returncode == 0 and result.stdout.strip():
            reply = result.stdout.strip()

            # Log the reply
            reply_log = Path.home() / ".claude-lab-responses.jsonl"
            response_entry = {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "original_message": message,
                "reply": reply,
            }
            with open(reply_log, "a") as f:
                f.write(json.dumps(response_entry) + "\n")

            console.print(f"\n[green]✅ User responded: {reply}[/green]")

            # If user clicked the notification (not typed), open Terminal with tmux session
            gui_action = settings.get("click_action", "gui")
            if reply == "@CONTENTCLICKED" and gui_action == "gui":
                console.print(f"[cyan]Opening Terminal with tmux session for {source}...[/cyan]")
                # Use osascript to open Terminal with tmux attach
                try:
                    subprocess.run([
                        "osascript",
                        "-e", "tell application \"Terminal\" to activate",
                        "-e", f'tell application "Terminal" to do script "tmux attach -t {source}"'
                    ], check=False)
                except Exception as e:
                    console.print(f"[yellow]Could not open Terminal: {e}[/yellow]")

            return reply

    except subprocess.TimeoutExpired:
        # User didn't respond in time
        pass
    except Exception as e:
        console.print(f"[dim]Note: macOS notification failed: {e}[/dim]")

    return None


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Claude Lab Manager - Orchestrate parallel development environments"""
    if ctx.invoked_subcommand is None:
        interactive_menu()


def check_command(cmd):
    """Check if a command exists"""
    return shutil.which(cmd) is not None


def check_system():
    """Verify all required tools are installed"""
    console.print("[bold blue]🔍 System Check...[/bold blue]")
    tools = {
        "docker": "Container runtime",
        "k3d": "k3s in Docker",
        "tmux": "Terminal multiplexer",
        "git": "Version control",
    }

    all_ok = True
    for tool, description in tools.items():
        if check_command(tool):
            console.print(f"  ✓ {tool:10} [green]OK[/green] - {description}")
        else:
            console.print(f"  ✗ {tool:10} [red]MISSING[/red] - {description}")
            all_ok = False

    # Check Docker daemon
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        console.print("  ✓ docker daemon [green]RUNNING[/green]")
    except subprocess.CalledProcessError:
        console.print("  ✗ docker daemon [red]NOT RUNNING[/red]")
        all_ok = False

    # Check optional tools (macOS only)
    if sys.platform == "darwin":
        console.print("\n[bold blue]Optional Tools (macOS):[/bold blue]")
        if check_command("alerter"):
            console.print("  ✓ alerter    [green]OK[/green] - Interactive notifications")
        else:
            console.print("  ✗ alerter    [yellow]OPTIONAL[/yellow] - For macOS system notifications")
            console.print("    [dim]Download: https://github.com/vjeantet/alerter/releases[/dim]")
            console.print("    [dim]Then run: sudo xattr -d com.apple.quarantine /usr/local/bin/alerter[/dim]")

    return all_ok


@cli.command()
@click.option("--dry-run", is_flag=True, help="Show what would be installed without installing")
def install(dry_run):
    """Install required system tools for claude-lab"""
    console.print("[bold blue]🔧 Claude Lab Installation[/bold blue]\n")

    # Detect OS
    import platform
    system = platform.system()

    instructions = {
        "Darwin": {  # macOS
            "docker": "brew install --cask docker",
            "k3d": "brew install k3d",
            "tmux": "brew install tmux",
            "git": "brew install git",
            "kubectl": "brew install kubectl",
            "helm": "brew install helm",
        },
        "Linux": {
            "docker": "curl -fsSL https://get.docker.com | sh",
            "k3d": "curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash",
            "tmux": "sudo apt-get install tmux || sudo yum install tmux",
            "git": "sudo apt-get install git || sudo yum install git",
            "kubectl": "curl -LO https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl && sudo install kubectl /usr/local/bin/",
            "helm": "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
        },
    }

    if system not in instructions:
        console.print(f"[red]Unsupported OS: {system}[/red]")
        console.print("Please install the following tools manually:")
        console.print("  - docker, k3d, tmux, git, kubectl, helm")
        sys.exit(1)

    tools = instructions[system]
    missing_tools = []

    # Check what's missing
    for tool in tools.keys():
        if not check_command(tool):
            missing_tools.append(tool)

    if not missing_tools:
        console.print("[green]✅ All required tools are already installed![/green]")
        return

    console.print(f"[yellow]Missing tools: {', '.join(missing_tools)}[/yellow]\n")

    if dry_run:
        console.print("[bold]Installation commands (dry-run):[/bold]\n")
        for tool in missing_tools:
            console.print(f"  {tool}: [cyan]{tools[tool]}[/cyan]")
        return

    # Install missing tools
    console.print("[bold]Installing missing tools...[/bold]\n")
    for tool in missing_tools:
        console.print(f"Installing [cyan]{tool}[/cyan]...")
        cmd = tools[tool]
        try:
            subprocess.run(cmd, shell=True, check=True)
            console.print(f"  ✓ {tool} installed successfully")
        except subprocess.CalledProcessError as e:
            console.print(f"  ✗ Failed to install {tool}")
            console.print(f"    Please install manually: [cyan]{cmd}[/cyan]")

    console.print("\n[bold green]✨ Installation complete! Run 'uv run invoke lab.check' to verify.[/bold green]")


@cli.command()
@click.argument("name")
@click.option("--branch", default=None, help="Branch to checkout (default: current)")
@click.option("--image", default=None, help="Custom Docker image to use (default: uses Claude sandbox default)")
def setup(name, branch, image):
    """Set up a new isolated lab environment"""

    if not check_system():
        console.print("\n[bold red]❌ System check failed. Please install missing tools.[/bold red]")
        sys.exit(1)

    # Check DNS and proxy setup (for seamless domain access)
    if PROXY_AVAILABLE:
        dns_mgr = DNSManager()
        proxy_mgr = ProxyManager()

        # Check DNS configuration
        dns_configured = dns_mgr.is_configured() and dns_mgr.is_resolver_configured()
        proxy_running = proxy_mgr.is_running()

        if not dns_configured:
            console.print("\n[yellow]⚠️  DNS not configured for *.local domains[/yellow]")
            console.print("[dim]Without DNS, you'll need port numbers: http://localhost:8081[/dim]")
            console.print("[dim]With DNS: http://lab-name.local/ (seamless!)[/dim]")
            console.print("\n[cyan]To configure DNS:[/cyan] lab dns setup")

            if not click.confirm("\nContinue without DNS setup?", default=True):
                console.print("[yellow]Cancelled. Run 'lab dns setup' first.[/yellow]")
                sys.exit(0)
            console.print()

        # Check if proxy is running
        if not proxy_running and dns_configured:
            console.print("[yellow]⚠️  Reverse proxy not running[/yellow]")
            console.print("[dim]DNS is configured, but you need the proxy for domain access.[/dim]")

            if click.confirm("\nStart reverse proxy now?", default=True):
                console.print()
                proxy_mgr.start()
                console.print()
            else:
                console.print("[dim]Skipping proxy. Start later: lab proxy start[/dim]")
                console.print()

    # Load project settings
    worktree_dir = get_project_setting("worktree_dir", "..")
    default_image = get_project_setting("docker_image", "claude")

    # Get current branch if not specified
    if branch is None:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        ).decode().strip()

    # Use project-configured worktree directory
    parent_dir = Path(worktree_dir).resolve()
    target_dir = parent_dir / name

    # Use project-configured image if not specified
    if image is None:
        image = default_image if default_image != "claude" else None

    # Check if already exists
    if target_dir.exists():
        console.print(f"[red]Error: Directory {target_dir} already exists[/red]")
        sys.exit(1)

    reg = get_registry()
    if name in reg:
        console.print(f"[red]Error: Lab '{name}' already exists in registry[/red]")
        sys.exit(1)

    port = get_next_port()
    api_port = port + 1000
    kubeconfig = target_dir / f".kubeconfig-{name}"

    console.print(
        Panel(
            f"🚀 Initializing [bold cyan]{name}[/bold cyan]\n"
            f"Directory: {target_dir}\n"
            f"Branch: {branch}\n"
            f"HTTP Port: {port}\n"
            f"API Port: {api_port}",
            title="Lab Setup",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 1. Git Worktree
        task1 = progress.add_task("Creating git worktree...", total=None)
        subprocess.run(
            ["git", "worktree", "add", str(target_dir), branch],
            check=True,
            capture_output=True,
        )
        progress.update(task1, completed=True)

        # 2. k3d Cluster
        task2 = progress.add_task("Creating k3d cluster...", total=None)
        subprocess.run(
            [
                "k3d",
                "cluster",
                "create",
                name,
                "--api-port",
                f"127.0.0.1:{api_port}",
                "-p",
                f"{port}:80@loadbalancer",
                "--kubeconfig-switch-context=false",
            ],
            check=True,
            capture_output=True,
        )
        progress.update(task2, completed=True)

        # 3. Kubeconfig (patched for Docker host access)
        task3 = progress.add_task("Generating kubeconfig...", total=None)
        config_data = subprocess.check_output(["k3d", "kubeconfig", "get", name]).decode()
        patched_config = config_data.replace("127.0.0.1", "host.docker.internal")
        kubeconfig.write_text(patched_config)
        progress.update(task3, completed=True)

        # 4. Prepare Docker Sandbox command
        task4 = progress.add_task("Launching tmux session...", total=None)

        # SSH identity sharing
        ssh_auth = os.environ.get("SSH_AUTH_SOCK", "")
        ssh_mount = f"type=bind,source={ssh_auth},target={ssh_auth}" if ssh_auth else ""

        # Collect config file mounts (read-only)
        config_mounts = []

        # Claude config directory (always mount if exists)
        claude_dir = Path.home() / ".claude"
        if claude_dir.exists():
            config_mounts.append(f"type=bind,source={claude_dir},target=/root/.claude,readonly")

        # Git config (for proper commit attribution)
        gitconfig = Path.home() / ".gitconfig"
        if gitconfig.exists():
            config_mounts.append(f"type=bind,source={gitconfig},target=/root/.gitconfig,readonly")

        # Docker config (for registry authentication)
        docker_config = Path.home() / ".docker" / "config.json"
        if docker_config.exists():
            # Ensure .docker directory exists in container
            config_mounts.append(f"type=bind,source={docker_config},target=/root/.docker/config.json,readonly")

        # Add additional mounts from settings (global or project)
        merged_settings, has_project, has_global = get_merged_settings()
        additional_mounts = merged_settings.get("additional_mounts", [])
        for mount_spec in additional_mounts:
            # Parse mount spec: source:target:mode or source:target
            parts = mount_spec.split(":")
            if len(parts) >= 2:
                source = Path(parts[0]).expanduser()
                target = parts[1]
                mode = parts[2] if len(parts) > 2 else "rw"

                if source.exists():
                    if mode == "ro":
                        config_mounts.append(f"type=bind,source={source},target={target},readonly")
                    else:
                        config_mounts.append(f"type=bind,source={source},target={target}")

        # Build docker sandbox command
        sandbox_cmd = "docker sandbox run claude ."
        if image:
            # Use custom image
            sandbox_cmd = f"docker sandbox run --image {image} ."

        cmd_parts = [
            f"cd {target_dir}",
            sandbox_cmd,
            f"--env KUBECONFIG=/.kubeconfig-{name}",
        ]

        # Add environment variables from settings (global or project)
        project_env = merged_settings.get("environment", {})
        for key, value in project_env.items():
            cmd_parts.append(f"--env {key}={value}")

        if ssh_auth:
            cmd_parts.extend([
                f"--env SSH_AUTH_SOCK={ssh_auth}",
                f"--mount {ssh_mount}",
            ])

        # Mount kubeconfig
        cmd_parts.append(f"--mount type=bind,source={kubeconfig},target=/.kubeconfig-{name}")

        # Mount all config files
        for mount in config_mounts:
            cmd_parts.append(f"--mount {mount}")

        cmd_parts.append("-- --dangerously-skip-permissions")

        cmd = " ".join(cmd_parts)

        # Launch in tmux
        subprocess.run(
            ["tmux", "new-session", "-d", "-s", name, cmd],
            check=True,
        )
        progress.update(task4, completed=True)

    # Save to registry
    reg[name] = {
        "port": port,
        "api_port": api_port,
        "dir": str(target_dir),
        "branch": branch,
        "created": datetime.now().isoformat(),
    }
    save_registry(reg)

    log_notification(f"Lab '{name}' created on branch '{branch}'", "success", "setup")

    console.print(f"\n[bold green]✅ Lab '{name}' is ready![/bold green]")
    console.print(f"[dim]Connect with:[/dim] tmux attach -t {name}")
    console.print(f"[dim]HTTP available at:[/dim] http://localhost:{port}")

    # Show which settings are being used
    project_settings_path = Path.cwd() / ".lab" / "settings.yaml"
    global_settings_path = Path.home() / ".lab" / "settings.yaml"

    if project_settings_path.exists():
        console.print(f"\n[dim]Using project settings from .lab/settings.yaml[/dim]")
    elif global_settings_path.exists():
        console.print(f"\n[dim]Using global settings from ~/.lab/settings.yaml[/dim]")

    # Show mounted configs
    if config_mounts:
        console.print(f"\n[dim]Mounted configs:[/dim]")
        if claude_dir.exists():
            console.print(f"  • ~/.claude → /root/.claude [cyan](skills & settings)[/cyan]")
        if gitconfig.exists():
            console.print(f"  • ~/.gitconfig → /root/.gitconfig [cyan](git identity)[/cyan]")
        if docker_config.exists():
            console.print(f"  • ~/.docker/config.json [cyan](registry auth)[/cyan]")

        # Show additional project mounts
        if additional_mounts:
            console.print(f"\n[dim]Additional mounts from project:[/dim]")
            for mount_spec in additional_mounts:
                parts = mount_spec.split(":")
                if len(parts) >= 2:
                    console.print(f"  • {parts[0]} → {parts[1]} [cyan](project config)[/cyan]")

    # Show environment variables
    if project_env:
        console.print(f"\n[dim]Environment variables:[/dim]")
        for key in list(project_env.keys())[:3]:  # Show first 3
            console.print(f"  • {key}={project_env[key]}")
        if len(project_env) > 3:
            console.print(f"  [dim]... and {len(project_env) - 3} more[/dim]")

    # Auto-register with proxy if running
    if PROXY_AVAILABLE:
        proxy = ProxyManager()
        dns_mgr = DNSManager()
        dns_ready = dns_mgr.is_configured() and dns_mgr.is_resolver_configured()

        if proxy.is_running():
            console.print(f"\n[dim]Registering routes with proxy...[/dim]")
            proxy.register_lab(name, port)

            if dns_ready:
                console.print(f"\n[bold green]🌐 Access via: http://{name}.local/[/bold green]")
                console.print(f"[dim]Subdomains also work: http://subdomain.{name}.local/[/dim]")
            else:
                console.print(f"\n[yellow]⚠️  Proxy running but DNS not configured[/yellow]")
                console.print(f"[dim]Access via: http://localhost:{port}/[/dim]")
                console.print(f"[dim]For domain access, run: lab dns setup[/dim]")
        else:
            if dns_ready:
                console.print(f"\n[yellow]💡 DNS ready but proxy not running:[/yellow]")
                console.print(f"[dim]   lab proxy start[/dim]")
                console.print(f"[dim]   Then: http://{name}.local/[/dim]")
            console.print(f"\n[dim]Access via: http://localhost:{port}/[/dim]")


@cli.command()
@click.argument("name")
@click.option("--force", is_flag=True, help="Force removal even if resources are busy")
def teardown(name, force):
    """Tear down a lab environment and clean up all resources"""
    reg = get_registry()

    if name not in reg:
        console.print(f"[red]Error: Lab '{name}' not found in registry.[/red]")
        console.print("\nAvailable labs:")
        for lab_name in reg.keys():
            console.print(f"  - {lab_name}")
        sys.exit(1)

    console.print(f"🗑️  Tearing down [bold red]{name}[/bold red]...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 1. Delete k3d cluster
        task1 = progress.add_task("Deleting k3d cluster...", total=None)
        subprocess.run(
            ["k3d", "cluster", "delete", name],
            capture_output=True,
        )
        progress.update(task1, completed=True)

        # 2. Remove git worktree
        task2 = progress.add_task("Removing git worktree...", total=None)
        worktree_dir = Path(reg[name]["dir"])

        # First try without force
        result = subprocess.run(
            ["git", "worktree", "remove", str(worktree_dir)],
            capture_output=True,
            text=True,
        )

        # If failed and not using force, try with force flag
        if result.returncode != 0:
            if not force:
                console.print(f"[yellow]Note: Worktree removal failed, retrying with --force...[/yellow]")
                result = subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree_dir)],
                    capture_output=True,
                    text=True,
                )

            # If still failed, report error
            if result.returncode != 0:
                console.print(f"[yellow]Warning: Could not remove worktree: {result.stderr}[/yellow]")

        # Verify directory is actually removed
        if worktree_dir.exists():
            console.print(f"[yellow]Warning: Worktree directory still exists, attempting manual cleanup...[/yellow]")
            try:
                import shutil
                shutil.rmtree(worktree_dir)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not remove directory: {e}[/yellow]")

        progress.update(task2, completed=True)

        # 3. Kill tmux session
        task3 = progress.add_task("Stopping tmux session...", total=None)
        subprocess.run(
            ["tmux", "kill-session", "-t", name],
            stderr=subprocess.DEVNULL,
        )
        progress.update(task3, completed=True)

    # Unregister from proxy if running
    if PROXY_AVAILABLE:
        proxy = ProxyManager()
        if proxy.is_running():
            proxy.unregister_lab(name)

    # Remove from registry
    del reg[name]
    save_registry(reg)

    log_notification(f"Lab '{name}' torn down", "info", "teardown")
    console.print("[bold green]✨ Cleanup complete.[/bold green]")


@cli.command()
def list():
    """List all active lab environments"""
    reg = get_registry()

    if not reg:
        console.print("[yellow]No active lab environments.[/yellow]")
        console.print("\nCreate one with: [cyan]uv run invoke lab.setup --name <name>[/cyan]")
        return

    table = Table(title="Claude Lab Environments", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Branch", style="yellow")
    table.add_column("HTTP Port", style="green")
    table.add_column("API Port", style="blue")
    table.add_column("Directory", style="dim")
    table.add_column("Status", style="green")

    for name, info in reg.items():
        # Check if tmux session is running
        result = subprocess.run(
            ["tmux", "has-session", "-t", name],
            capture_output=True,
        )
        status = "🟢 Running" if result.returncode == 0 else "🔴 Stopped"

        table.add_row(
            name,
            info.get("branch", "unknown"),
            str(info["port"]),
            str(info.get("api_port", "N/A")),
            info["dir"],
            status,
        )

    console.print(table)
    console.print(f"\n[dim]Total environments: {len(reg)}[/dim]")


@cli.command()
def check():
    """Check system requirements and status"""
    if check_system():
        console.print("\n[bold green]✅ All systems ready![/bold green]")
    else:
        console.print("\n[bold red]❌ Some requirements are missing.[/bold red]")
        sys.exit(1)


@cli.command()
def reinstall():
    """Reinstall claude-lab from source (for developers)"""
    console.print("[bold blue]🔄 Reinstalling claude-lab...[/bold blue]\n")

    # Check if we're in a claude-lab project directory
    pyproject = Path.cwd() / "pyproject.toml"
    if not pyproject.exists():
        console.print("[red]Error: pyproject.toml not found in current directory[/red]")
        console.print("[dim]Make sure you're in the claude-lab project root[/dim]")
        sys.exit(1)

    # Verify it's actually claude-lab
    try:
        with open(pyproject) as f:
            content = f.read()
            if "claude-lab" not in content and "claude_lab" not in content:
                console.print("[yellow]Warning: This doesn't appear to be the claude-lab project[/yellow]")
                console.print("[dim]Proceeding anyway...[/dim]\n")
    except Exception:
        pass

    # Run uv tool install
    console.print("[cyan]Running: uv tool install --force --editable .[/cyan]\n")

    try:
        result = subprocess.run(
            ["uv", "tool", "install", "--force", "--editable", "."],
            check=True,
            capture_output=False
        )

        console.print("\n[bold green]✅ Reinstallation complete![/bold green]")
        console.print("[dim]The 'lab' command has been updated with your latest changes.[/dim]")

        # Show version info
        try:
            version_result = subprocess.run(
                ["lab", "--version"],
                capture_output=True,
                text=True
            )
            if version_result.stdout:
                console.print(f"\n[cyan]{version_result.stdout.strip()}[/cyan]")
        except:
            pass

    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]❌ Reinstallation failed[/red]")
        console.print(f"[dim]Error: {e}[/dim]")
        sys.exit(1)
    except FileNotFoundError:
        console.print(f"\n[red]❌ 'uv' command not found[/red]")
        console.print(f"[dim]Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh[/dim]")
        sys.exit(1)


@cli.command()
@click.option("--global", "is_global", is_flag=True, help="Initialize global settings at ~/.lab/")
def init(is_global):
    """Initialize .lab/ directory with default settings"""

    if is_global:
        lab_dir = Path.home() / ".lab"
        settings_file = lab_dir / "settings.yaml"
        scope = "global"
        location = "~/.lab/"
    else:
        lab_dir = Path.cwd() / ".lab"
        settings_file = lab_dir / "settings.yaml"
        scope = "project"
        location = ".lab/"

    # Check if already exists
    if settings_file.exists():
        console.print(f"[yellow]⚠️  {scope.capitalize()} settings already exist at {settings_file}[/yellow]")
        console.print(f"[dim]To reinitialize, delete the file first:[/dim]")
        console.print(f"  rm {settings_file}")
        sys.exit(1)

    # Create directory
    lab_dir.mkdir(parents=True, exist_ok=True)

    # Create default settings file
    default_settings = """# Claude Lab Settings
# Configure default behavior for lab environments
# Documentation: .lab/README.md (project) or ~/.lab/README.md (global)

# Directory where worktrees will be created
# Default: /tmp/claude-labs (temporary, auto-cleanup)
# Options: "../" (parent dir), "~/labs" (home dir), any absolute/relative path
worktree_dir: "/tmp/claude-labs"

# Docker image to use for sandbox environments
# Default: "claude" (Claude Code sandbox)
# Options: "claude-lab:base", "claude-lab:k8s-full", or any Docker image
docker_image: "claude"

# Starting port number for lab HTTP services
# Each lab gets: HTTP port (base_port) and API port (base_port + 1000)
# Default: 8080
base_port: 8080

# Additional volume mounts to include in all labs
# Format: "source:target:mode" where mode is "ro" (read-only) or "rw" (read-write)
#
# Default auto-mounts (always applied when they exist):
#   - ~/.claude → /root/.claude (readonly)
#   - ~/.gitconfig → /root/.gitconfig (readonly)
#   - ~/.docker/config.json → /root/.docker/config.json (readonly)
#   - SSH_AUTH_SOCK (for git operations)
#   - kubeconfig (auto-generated for k3d cluster)
#
# Add your own custom mounts below:
# Example:
#   - "~/data:/data:ro"
#   - "~/.aws/credentials:/root/.aws/credentials:ro"
#   - "~/.kube/config:/root/.kube/config:ro"
additional_mounts: []

# Environment variables to set in all labs
# Example:
#   NODE_ENV: "development"
#   DEBUG: "true"
environment: {}

# macOS system notifications (requires alerter)
# Download: https://github.com/vjeantet/alerter/releases
# After install: sudo xattr -d com.apple.quarantine /usr/local/bin/alerter
macos_notifications:
  enabled: true                    # Enable macOS system notification banners
  click_action: "gui"              # Action when banner is clicked: "gui" to open lab GUI

# Auto-cleanup settings (future feature)
auto_cleanup:
  enabled: false
  max_age_days: 30
  stopped_age_days: 7
"""

    settings_file.write_text(default_settings)

    console.print(f"\n[bold green]✅ Initialized {scope} lab settings![/bold green]")
    console.print(f"\n[cyan]Created:[/cyan] {settings_file}")

    if not is_global:
        console.print(f"\n[dim]This project now has custom lab settings.[/dim]")
        console.print(f"[dim]Edit .lab/settings.yaml to configure:[/dim]")
        console.print(f"  • Worktree directory")
        console.print(f"  • Docker image")
        console.print(f"  • Additional mounts")
        console.print(f"  • Environment variables")
    else:
        console.print(f"\n[dim]These settings apply to all projects by default.[/dim]")
        console.print(f"[dim]Project-specific .lab/settings.yaml files override these.[/dim]")

    console.print(f"\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Edit {settings_file}")
    console.print(f"  2. Run: lab setup <name>")
    console.print(f"  3. Settings will be automatically applied")

    # Check for alerter on macOS
    if sys.platform == "darwin":
        if not shutil.which("alerter"):
            console.print(f"\n[yellow]💡 Optional: Install alerter for macOS system notifications[/yellow]")
            console.print(f"   [dim]Download: https://github.com/vjeantet/alerter/releases[/dim]")
            console.print(f"   [dim]Then run: sudo xattr -d com.apple.quarantine /usr/local/bin/alerter[/dim]")
            console.print(f"   [dim]Enables interactive notification banners with reply capability[/dim]")


@cli.command()
@click.option("--message", required=True, help="Notification message")
@click.option("--level", default="info", type=click.Choice(["info", "success", "warning", "error"]))
@click.option("--source", default="user", help="Source of the notification")
@click.option("--request-response", "-r", is_flag=True, help="Request a response from the user (interactive)")
def notify(message, level, source, request_response):
    """Send a notification to the main user session"""
    log_notification(message, level, source)

    # Also print to console
    emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
    color = {"info": "blue", "success": "green", "warning": "yellow", "error": "red"}

    console.print(f"[{color[level]}]{emoji[level]} {message}[/{color[level]}]")

    # Check if macOS notifications are enabled
    merged_settings, _, _ = get_merged_settings()
    macos_notif_settings = merged_settings.get("macos_notifications", {})

    if not isinstance(macos_notif_settings, dict):
        macos_notif_settings = {"enabled": True}  # Default to enabled

    enabled = macos_notif_settings.get("enabled", True)

    # Only send macOS notification if enabled and on macOS
    if enabled and sys.platform == "darwin":
        # Check if alerter is installed
        alerter_path = shutil.which("alerter")

        if not alerter_path:
            # First time: provide installation instructions
            install_file = Path.home() / ".claude-lab-alerter-install-shown"
            if not install_file.exists():
                console.print("\n[dim]💡 Tip: Install alerter for macOS system notifications:[/dim]")
                console.print("[dim]   brew install --cask alerter[/dim]")
                console.print("[dim]   or download from: https://github.com/vjeantet/alerter/releases[/dim]")
                install_file.touch()
        else:
            # Send macOS notification using alerter
            _send_macos_notification(message, level, source, request_response, macos_notif_settings)


@cli.command()
@click.option("--source", "-s", help="Filter responses by source")
@click.option("--last", "-n", type=int, help="Show last N responses")
@click.option("--clear", is_flag=True, help="Clear all responses after reading")
def responses(source, last, clear):
    """View user responses to notifications"""
    response_file = Path.home() / ".claude-lab-responses.jsonl"

    if not response_file.exists():
        console.print("[yellow]No responses yet.[/yellow]")
        return

    with open(response_file) as f:
        lines = f.readlines()

    responses_list = [json.loads(line) for line in lines]

    # Filter by source if specified
    if source:
        responses_list = [r for r in responses_list if r.get("source") == source]

    if not responses_list:
        console.print(f"[yellow]No responses{f' from {source}' if source else ''}.[/yellow]")
        return

    # Show last N if specified
    if last:
        responses_list = responses_list[-last:]

    # Display responses
    table = Table(title="User Responses", show_header=True, header_style="bold magenta")
    table.add_column("Time", style="dim")
    table.add_column("Source", style="cyan")
    table.add_column("Original Message", style="yellow")
    table.add_column("Reply", style="green")

    for resp in responses_list:
        timestamp = resp["timestamp"][:19].replace("T", " ")
        table.add_row(
            timestamp,
            resp["source"],
            resp["original_message"][:50] + "..." if len(resp["original_message"]) > 50 else resp["original_message"],
            resp["reply"]
        )

    console.print(table)
    console.print(f"\n[dim]Total responses: {len(responses_list)}[/dim]")

    # Clear responses if requested
    if clear:
        response_file.unlink()
        console.print("[green]✅ Responses cleared.[/green]")


@cli.command()
@click.option("--follow", "-f", is_flag=True, help="Follow new notifications (like tail -f)")
@click.option("--last", "-n", type=int, help="Show last N notifications")
def notifications(follow, last):
    """View notification history"""

    if not NOTIFICATIONS_PATH.exists():
        console.print("[yellow]No notifications yet.[/yellow]")
        return

    with open(NOTIFICATIONS_PATH) as f:
        lines = f.readlines()

    if last:
        lines = lines[-last:]

    for line in lines:
        notif = json.loads(line)
        timestamp = notif["timestamp"][:19]  # Trim microseconds
        level = notif["level"]
        source = notif["source"]
        message = notif["message"]

        emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        color = {"info": "blue", "success": "green", "warning": "yellow", "error": "red"}

        console.print(
            f"[dim]{timestamp}[/dim] "
            f"[{color[level]}]{emoji[level]}[/{color[level]}] "
            f"[cyan]{source}[/cyan]: {message}"
        )

    if follow:
        console.print("\n[dim]Watching for new notifications... (Ctrl+C to stop)[/dim]\n")
        try:
            subprocess.run(["tail", "-f", str(NOTIFICATIONS_PATH)])
        except KeyboardInterrupt:
            console.print("\n[dim]Stopped watching.[/dim]")


@cli.command(name="image-build")
@click.argument("template")
@click.option("--tag", default=None, help="Custom tag for the image")
@click.option("--no-cache", is_flag=True, help="Build without cache")
def image_build(template, tag, no_cache):
    """Build a Docker image from a template"""
    templates_dir = find_templates_dir()
    templates_file = templates_dir / "templates.json"

    # Load template metadata
    if not templates_file.exists():
        console.print("[red]Templates configuration not found![/red]")
        sys.exit(1)

    with open(templates_file) as f:
        templates_data = json.load(f)

    templates = templates_data["templates"]
    image_prefix = templates_data.get("image_prefix", "claude-lab")

    if template not in templates:
        console.print(f"[red]Template '{template}' not found![/red]")
        console.print(f"\nAvailable templates: {', '.join(templates.keys())}")
        sys.exit(1)

    template_info = templates[template]
    dockerfile = templates_dir / template_info["dockerfile"]

    if not dockerfile.exists():
        console.print(f"[red]Dockerfile not found: {dockerfile}[/red]")
        sys.exit(1)

    # Determine image name and tag
    image_name = f"{image_prefix}:{tag}" if tag else f"{image_prefix}:{template}"

    console.print(Panel(
        f"🐳 Building Docker Image\n"
        f"Template: [cyan]{template}[/cyan]\n"
        f"Image: [cyan]{image_name}[/cyan]\n"
        f"Description: {template_info['description']}\n"
        f"Estimated size: {template_info['size_estimate']}",
        title="Image Build",
    ))

    # Build the image
    build_cmd = [
        "docker", "build",
        "-f", str(dockerfile),
        "-t", image_name,
        str(templates_dir),
    ]

    if no_cache:
        build_cmd.append("--no-cache")

    console.print(f"\n[dim]Running: {' '.join(build_cmd)}[/dim]\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Building {image_name}...", total=None)
            result = subprocess.run(build_cmd, check=True)
            progress.update(task, completed=True)

        console.print(f"\n[bold green]✅ Image '{image_name}' built successfully![/bold green]")
        log_notification(f"Docker image '{image_name}' built", "success", "image-build")

        # Show image info
        subprocess.run(["docker", "images", image_name])

    except subprocess.CalledProcessError as e:
        console.print(f"\n[bold red]❌ Build failed![/bold red]")
        sys.exit(1)


@cli.command(name="image-list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def image_list(verbose):
    """List available templates and built images"""
    templates_dir = find_templates_dir()
    templates_file = templates_dir / "templates.json"

    if not templates_file.exists():
        console.print("[red]Templates configuration not found![/red]")
        sys.exit(1)

    with open(templates_file) as f:
        templates_data = json.load(f)

    templates = templates_data["templates"]
    image_prefix = templates_data.get("image_prefix", "claude-lab")
    default_template = templates_data.get("default_template", "base")

    console.print(Panel.fit(
        "[bold cyan]Claude Lab Image Templates[/bold cyan]",
        border_style="cyan",
    ))

    # Show templates
    table = Table(title="Available Templates", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Size", style="yellow")
    table.add_column("Tools", style="green")

    for name, info in templates.items():
        is_default = " [bold yellow](default)[/bold yellow]" if name == default_template else ""
        tools = ", ".join(info["tools"][:5])
        if len(info["tools"]) > 5:
            tools += f" +{len(info['tools']) - 5} more"

        table.add_row(
            name + is_default,
            info["description"],
            info["size_estimate"],
            tools,
        )

    console.print("\n")
    console.print(table)

    # Show built images
    console.print("\n")
    result = subprocess.run(
        ["docker", "images", "--filter", f"reference={image_prefix}:*", "--format", "{{json .}}"],
        capture_output=True,
        text=True,
    )

    if result.stdout.strip():
        image_table = Table(title="Built Images", show_header=True, header_style="bold green")
        image_table.add_column("Repository", style="cyan")
        image_table.add_column("Tag", style="yellow")
        image_table.add_column("Image ID", style="dim")
        image_table.add_column("Size", style="green")
        image_table.add_column("Created", style="blue")

        for line in result.stdout.strip().split("\n"):
            img = json.loads(line)
            image_table.add_row(
                img["Repository"],
                img["Tag"],
                img["ID"][:12],
                img["Size"],
                img["CreatedSince"],
            )

        console.print(image_table)
    else:
        console.print("[yellow]No images built yet. Use 'image-build' to build one.[/yellow]")

    if verbose:
        console.print("\n[bold]Template Details:[/bold]")
        for name, info in templates.items():
            console.print(f"\n[cyan]{name}[/cyan]:")
            console.print(f"  Description: {info['description']}")
            console.print(f"  Use case: {info['use_case']}")
            console.print(f"  Tools: {', '.join(info['tools'])}")


@cli.command(name="image-delete")
@click.argument("image_tag")
@click.option("--force", "-f", is_flag=True, help="Force removal")
def image_delete(image_tag, force):
    """Delete a built Docker image"""
    templates_dir = find_templates_dir()
    templates_file = templates_dir / "templates.json"

    with open(templates_file) as f:
        templates_data = json.load(f)

    image_prefix = templates_data.get("image_prefix", "claude-lab")
    image_name = f"{image_prefix}:{image_tag}"

    console.print(f"🗑️  Deleting image [red]{image_name}[/red]...")

    cmd = ["docker", "rmi", image_name]
    if force:
        cmd.append("--force")

    try:
        subprocess.run(cmd, check=True)
        console.print(f"[bold green]✅ Image '{image_name}' deleted successfully![/bold green]")
        log_notification(f"Docker image '{image_name}' deleted", "info", "image-delete")
    except subprocess.CalledProcessError:
        console.print(f"[bold red]❌ Failed to delete image '{image_name}'[/bold red]")
        console.print("[dim]Tip: Use --force to force removal[/dim]")
        sys.exit(1)


@cli.command(name="image-update")
@click.argument("template")
def image_update(template):
    """Rebuild an existing image (no-cache build)"""
    console.print(f"🔄 Updating image for template [cyan]{template}[/cyan]...")
    # This just calls image-build with --no-cache
    ctx = click.get_current_context()
    ctx.invoke(image_build, template=template, tag=None, no_cache=True)


@cli.command(name="image-inspect")
@click.argument("image_tag")
def image_inspect(image_tag):
    """Show detailed information about an image"""
    templates_dir = find_templates_dir()
    templates_file = templates_dir / "templates.json"

    with open(templates_file) as f:
        templates_data = json.load(f)

    image_prefix = templates_data.get("image_prefix", "claude-lab")
    image_name = f"{image_prefix}:{image_tag}"

    console.print(f"🔍 Inspecting image [cyan]{image_name}[/cyan]...\n")

    # Check if image exists
    result = subprocess.run(
        ["docker", "images", "-q", image_name],
        capture_output=True,
        text=True,
    )

    if not result.stdout.strip():
        console.print(f"[red]Image '{image_name}' not found![/red]")
        console.print("\nUse 'image-list' to see available images.")
        sys.exit(1)

    # Get image details
    inspect_result = subprocess.run(
        ["docker", "inspect", image_name],
        capture_output=True,
        text=True,
    )

    if inspect_result.returncode == 0:
        data = json.loads(inspect_result.stdout)[0]

        # Show basic info
        console.print(Panel(
            f"[bold]Image:[/bold] {image_name}\n"
            f"[bold]ID:[/bold] {data['Id'][:19]}...\n"
            f"[bold]Created:[/bold] {data['Created'][:19]}\n"
            f"[bold]Size:[/bold] {data['Size'] / (1024**2):.2f} MB\n"
            f"[bold]Architecture:[/bold] {data['Architecture']}\n"
            f"[bold]OS:[/bold] {data['Os']}",
            title="Image Information",
        ))

        # Show labels if any
        if data.get("Config", {}).get("Labels"):
            console.print("\n[bold]Labels:[/bold]")
            for key, value in data["Config"]["Labels"].items():
                console.print(f"  {key}: {value}")

        # Show layers
        console.print(f"\n[bold]Layers:[/bold] {len(data['RootFS']['Layers'])}")

    # Show history
    console.print("\n[bold]Image History:[/bold]")
    subprocess.run(["docker", "history", image_name, "--human"])


@cli.command()
@click.option("--focus", "-f", default=None, help="Pre-select a specific lab by name")
def gui(focus):
    """Launch interactive GUI mode (TUI)"""
    try:
        from claude_lab.gui import run_gui
        run_gui(focus_lab=focus)
    except ImportError as e:
        console.print("[bold red]❌ GUI dependencies not available![/bold red]")
        console.print(f"Error: {e}")
        console.print("\nPlease ensure 'textual' is installed:")
        console.print("  pip install textual")
        sys.exit(1)


# ============================================================================
# Proxy Commands
# ============================================================================

@cli.group()
def proxy():
    """Manage reverse proxy for seamless domain access"""
    pass


@proxy.command(name="start")
@click.option("--force", is_flag=True, help="Force start even if port 80 is in use")
def proxy_start(force):
    """Start Caddy reverse proxy on port 80"""
    if not PROXY_AVAILABLE:
        console.print("[red]Proxy module not available[/red]")
        return
    ProxyManager().start(force=force)


@proxy.command(name="stop")
@click.option("--remove", is_flag=True, help="Remove container (not just stop)")
def proxy_stop(remove):
    """Stop Caddy reverse proxy"""
    if not PROXY_AVAILABLE:
        console.print("[red]Proxy module not available[/red]")
        return
    ProxyManager().stop(remove=remove)


@proxy.command(name="restart")
def proxy_restart():
    """Restart Caddy reverse proxy"""
    if not PROXY_AVAILABLE:
        console.print("[red]Proxy module not available[/red]")
        return
    ProxyManager().restart()


@proxy.command(name="status")
def proxy_status():
    """Show proxy status and routes"""
    if not PROXY_AVAILABLE:
        console.print("[red]Proxy module not available[/red]")
        return
    ProxyManager().status()


@proxy.command(name="logs")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def proxy_logs(follow):
    """Show Caddy logs"""
    if not PROXY_AVAILABLE:
        console.print("[red]Proxy module not available[/red]")
        return
    ProxyManager().logs(follow=follow)


# ============================================================================
# DNS Commands
# ============================================================================

@cli.group()
def dns():
    """Manage DNS configuration for *.local domains"""
    pass


@dns.command(name="setup")
def dns_setup():
    """Complete DNS setup for wildcard .local resolution"""
    if not PROXY_AVAILABLE:
        console.print("[red]DNS module not available[/red]")
        return
    DNSManager().setup()


@dns.command(name="status")
def dns_status():
    """Show DNS configuration status"""
    if not PROXY_AVAILABLE:
        console.print("[red]DNS module not available[/red]")
        return
    DNSManager().status()


@dns.command(name="test")
def dns_test():
    """Test DNS resolution"""
    if not PROXY_AVAILABLE:
        console.print("[red]DNS module not available[/red]")
        return
    DNSManager().test()


@dns.command(name="restart")
def dns_restart():
    """Restart dnsmasq service"""
    if not PROXY_AVAILABLE:
        console.print("[red]DNS module not available[/red]")
        return
    DNSManager().restart()


# ============================================================================
# Interactive Menu
# ============================================================================

def interactive_menu():
    """Display interactive menu when no command is given"""
    console.print(Panel.fit(
        "[bold cyan]Claude Lab Manager[/bold cyan]\n"
        "Orchestrate isolated k3d clusters with git worktrees",
        border_style="cyan",
    ))

    # Show current environments
    reg = get_registry()
    if reg:
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Name", style="cyan")
        table.add_column("Port", style="green")
        table.add_column("Status", style="yellow")

        for name, info in reg.items():
            result = subprocess.run(
                ["tmux", "has-session", "-t", name],
                capture_output=True,
            )
            status = "🟢" if result.returncode == 0 else "🔴"
            table.add_row(name, str(info["port"]), status)

        console.print("\n")
        console.print(table)
    else:
        console.print("\n[dim]No active environments[/dim]")

    console.print("\n[yellow]Available Commands:[/yellow]")
    console.print("  setup <name>       Create a new lab environment")
    console.print("  teardown <name>    Remove a lab environment")
    console.print("  list               Show all environments")
    console.print("  check              Verify system requirements")
    console.print("  proxy              Manage reverse proxy (seamless domains)")
    console.print("  dns                Manage DNS configuration")
    console.print("  notify             Send a notification")
    console.print("  notifications      View notification history")
    console.print("\n[dim]Run with --help for more options[/dim]")


if __name__ == "__main__":
    cli()
