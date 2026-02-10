"""
DNS configuration for claude-lab using dnsmasq.

Provides wildcard DNS resolution for *.local domains to 127.0.0.1
without requiring manual /etc/hosts updates.
"""

import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

DNSMASQ_CONF_PATH = Path("/opt/homebrew/etc/dnsmasq.conf")
RESOLVER_PATH = Path("/etc/resolver/local")


class DNSManager:
    """Manages dnsmasq for wildcard .local DNS resolution"""

    def is_installed(self) -> bool:
        """Check if dnsmasq is installed"""
        result = subprocess.run(
            ["which", "dnsmasq"],
            capture_output=True
        )
        return result.returncode == 0

    def is_configured(self) -> bool:
        """Check if dnsmasq is configured for .local domains"""
        if not DNSMASQ_CONF_PATH.exists():
            return False

        config = DNSMASQ_CONF_PATH.read_text()
        return "address=/.local/127.0.0.1" in config

    def is_resolver_configured(self) -> bool:
        """Check if macOS resolver is configured"""
        return RESOLVER_PATH.exists()

    def is_running(self) -> bool:
        """Check if dnsmasq service is running"""
        result = subprocess.run(
            ["brew", "services", "list"],
            capture_output=True,
            text=True
        )
        return "dnsmasq" in result.stdout and "started" in result.stdout

    def install(self):
        """Install dnsmasq via Homebrew"""
        if self.is_installed():
            console.print("[green]✓ dnsmasq already installed[/green]")
            return True

        console.print("[dim]Installing dnsmasq via Homebrew...[/dim]")
        result = subprocess.run(
            ["brew", "install", "dnsmasq"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print("[green]✓ dnsmasq installed[/green]")
            return True
        else:
            console.print(f"[red]✗ Failed to install dnsmasq: {result.stderr}[/red]")
            return False

    def configure(self):
        """Configure dnsmasq for .local wildcard DNS"""
        if self.is_configured():
            console.print("[green]✓ dnsmasq already configured[/green]")
        else:
            console.print("[yellow]⚠ dnsmasq configuration needs to be updated[/yellow]")
            console.print(f"[dim]Adding wildcard .local resolution to {DNSMASQ_CONF_PATH}[/dim]")

            # This requires sudo
            cmd = f"echo 'address=/.local/127.0.0.1' | sudo tee -a {DNSMASQ_CONF_PATH}"
            console.print(f"[bold]Running:[/bold] {cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
                text=True
            )

            if result.returncode == 0:
                console.print("[green]✓ dnsmasq configured[/green]")
            else:
                console.print("[red]✗ Failed to configure dnsmasq[/red]")
                return False

        return True

    def configure_resolver(self):
        """Configure macOS resolver to use dnsmasq for .local domains"""
        if self.is_resolver_configured():
            console.print("[green]✓ macOS resolver already configured[/green]")
            return True

        console.print("[yellow]⚠ macOS resolver needs to be configured[/yellow]")
        console.print(f"[dim]Creating {RESOLVER_PATH}[/dim]")

        # This requires sudo
        commands = [
            "sudo mkdir -p /etc/resolver",
            f"echo 'nameserver 127.0.0.1' | sudo tee {RESOLVER_PATH}"
        ]

        for cmd in commands:
            console.print(f"[bold]Running:[/bold] {cmd}")
            result = subprocess.run(cmd, shell=True)

            if result.returncode != 0:
                console.print("[red]✗ Failed to configure resolver[/red]")
                return False

        console.print("[green]✓ macOS resolver configured[/green]")
        return True

    def start(self):
        """Start dnsmasq service"""
        if self.is_running():
            console.print("[green]✓ dnsmasq already running[/green]")
            return True

        console.print("[dim]Starting dnsmasq service...[/dim]")
        console.print("[bold]Running:[/bold] sudo brew services start dnsmasq")

        result = subprocess.run(
            ["sudo", "brew", "services", "start", "dnsmasq"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print("[green]✓ dnsmasq started[/green]")
            return True
        else:
            console.print(f"[red]✗ Failed to start dnsmasq: {result.stderr}[/red]")
            return False

    def restart(self):
        """Restart dnsmasq service"""
        console.print("[dim]Restarting dnsmasq...[/dim]")
        console.print("[bold]Running:[/bold] sudo brew services restart dnsmasq")

        result = subprocess.run(
            ["sudo", "brew", "services", "restart", "dnsmasq"]
        )

        if result.returncode == 0:
            console.print("[green]✓ dnsmasq restarted[/green]")
        else:
            console.print("[red]✗ Failed to restart dnsmasq[/red]")

    def test(self):
        """Test DNS resolution"""
        console.print("\n[bold]Testing DNS resolution...[/bold]")

        test_domains = [
            "test.local",
            "anything.local",
            "kepler-test.local",
            "api.kepler-test.local"
        ]

        from rich.table import Table
        table = Table(title="DNS Resolution Test")
        table.add_column("Domain")
        table.add_column("Result")
        table.add_column("Status")

        for domain in test_domains:
            # Use dscacheutil on macOS which respects /etc/resolver
            result = subprocess.run(
                ["dscacheutil", "-q", "host", "-a", "name", domain],
                capture_output=True,
                text=True
            )

            # Check if resolved to 127.0.0.1
            if "127.0.0.1" in result.stdout or "ip_address: 127.0.0.1" in result.stdout:
                table.add_row(domain, "127.0.0.1", "✅")
            else:
                # Fallback to ping test (more reliable)
                ping_result = subprocess.run(
                    ["ping", "-c", "1", "-t", "1", domain],
                    capture_output=True,
                    text=True
                )
                if "127.0.0.1" in ping_result.stdout:
                    table.add_row(domain, "127.0.0.1", "✅")
                else:
                    table.add_row(domain, "Not resolved", "❌")

        console.print(table)
        console.print("\n[dim]Note: These are test domains to verify DNS is working.[/dim]")
        console.print("[dim]They don't need actual services - just need to resolve to 127.0.0.1[/dim]")

    def setup(self):
        """Complete DNS setup workflow"""
        console.print(Panel.fit(
            "[bold cyan]Claude Lab DNS Setup[/bold cyan]\n"
            "Configure wildcard DNS for *.local domains"
        ))

        # Pre-authenticate sudo to avoid multiple password prompts
        console.print("\n[bold]Authenticating sudo access...[/bold]")
        console.print("[dim]You'll be prompted for your password once.[/dim]")
        result = subprocess.run(["sudo", "-v"], capture_output=True)
        if result.returncode != 0:
            console.print("[red]✗ Sudo authentication failed[/red]")
            return False
        console.print("[green]✓ Sudo authenticated[/green]")

        # Step 1: Install dnsmasq
        console.print("\n[bold]Step 1: Install dnsmasq[/bold]")
        if not self.install():
            return False

        # Step 2: Configure dnsmasq
        console.print("\n[bold]Step 2: Configure dnsmasq[/bold]")
        if not self.configure():
            return False

        # Step 3: Configure macOS resolver
        console.print("\n[bold]Step 3: Configure macOS resolver[/bold]")
        if not self.configure_resolver():
            return False

        # Step 4: Restart dnsmasq (to apply new config)
        console.print("\n[bold]Step 4: Restart dnsmasq[/bold]")
        if self.is_running():
            console.print("[dim]Restarting dnsmasq to apply configuration...[/dim]")
            self.restart()
        else:
            if not self.start():
                return False

        # Step 5: Test
        console.print("\n[bold]Step 5: Test DNS resolution[/bold]")
        self.test()

        console.print("\n[green]✅ DNS setup complete![/green]")
        console.print("\n[bold]All *.local domains now resolve to 127.0.0.1[/bold]")
        console.print("[dim]You can now access labs via: http://lab-name.local/[/dim]")

        return True

    def status(self):
        """Show DNS configuration status"""
        console.print("[bold]DNS Configuration Status:[/bold]\n")

        checks = [
            ("dnsmasq installed", self.is_installed()),
            ("dnsmasq configured", self.is_configured()),
            ("macOS resolver configured", self.is_resolver_configured()),
            ("dnsmasq running", self.is_running())
        ]

        for check_name, result in checks:
            status = "[green]✓[/green]" if result else "[red]✗[/red]"
            console.print(f"{status} {check_name}")

        if not all(result for _, result in checks):
            console.print("\n[yellow]⚠ DNS not fully configured[/yellow]")
            console.print("[dim]Run: lab dns setup[/dim]")
        else:
            console.print("\n[green]✅ DNS fully configured[/green]")
