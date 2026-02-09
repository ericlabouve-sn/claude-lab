"""
Reverse proxy management for claude-lab using Caddy in Docker.

Provides dynamic routing from *.lab-name.local to lab-specific ports
without requiring manual /etc/hosts updates or proxy restarts.
"""

import json
import subprocess
import time
from pathlib import Path
from rich.console import Console

console = Console()

CADDY_ADMIN_API = "http://localhost:2019"
CADDY_CONTAINER_NAME = "claude-lab-proxy"
CADDY_CONFIG_PATH = Path.home() / ".lab" / "caddy-config.json"


class ProxyManager:
    """Manages Caddy reverse proxy in Docker for lab environments"""

    def is_running(self) -> bool:
        """Check if Caddy proxy container is running"""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={CADDY_CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        return CADDY_CONTAINER_NAME in result.stdout

    def _check_port_80(self) -> bool:
        """Check if port 80 is available"""
        result = subprocess.run(
            ["lsof", "-i", ":80"],
            capture_output=True,
            text=True
        )
        # If lsof finds something, port is in use
        # But if it's our own container, that's OK
        if result.returncode == 0 and CADDY_CONTAINER_NAME not in result.stdout:
            return False
        return True

    def start(self, force: bool = False):
        """Start Caddy proxy in Docker on port 80"""
        if self.is_running():
            console.print(f"[yellow]✓ Proxy already running (container: {CADDY_CONTAINER_NAME})[/yellow]")
            return

        # Check if container exists but is stopped
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={CADDY_CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )

        if CADDY_CONTAINER_NAME in result.stdout:
            console.print("[dim]Starting existing proxy container...[/dim]")
            subprocess.run(["docker", "start", CADDY_CONTAINER_NAME], check=True)
            console.print("[green]✅ Proxy started[/green]")
            return

        # Check if port 80 is available
        if not self._check_port_80() and not force:
            console.print("[red]Error: Port 80 already in use[/red]")
            console.print("[dim]Use --force to stop conflicting services[/dim]")
            return

        # Initialize base config
        base_config = {
            "admin": {"listen": "0.0.0.0:2019"},
            "apps": {
                "http": {
                    "servers": {
                        "lab-proxy": {
                            "listen": [":80"],
                            "routes": []
                        }
                    }
                }
            }
        }

        # Ensure config directory exists
        CADDY_CONFIG_PATH.parent.mkdir(exist_ok=True, parents=True)
        CADDY_CONFIG_PATH.write_text(json.dumps(base_config, indent=2))

        console.print("[dim]Starting Caddy proxy container...[/dim]")

        # Start Caddy container
        cmd = [
            "docker", "run", "-d",
            "--name", CADDY_CONTAINER_NAME,
            "--restart", "unless-stopped",
            "-p", "80:80",
            "-p", "2019:2019",
            "-v", f"{CADDY_CONFIG_PATH}:/etc/caddy/config.json",
            "caddy:latest",
            "caddy", "run", "--config", "/etc/caddy/config.json", "--adapter", "json"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            time.sleep(1)  # Give Caddy a moment to start

            if self.is_running():
                console.print("[green]✅ Proxy started on port 80[/green]")
                console.print(f"[dim]Container: {CADDY_CONTAINER_NAME}[/dim]")
                console.print("[dim]Admin API: http://localhost:2019[/dim]")
                console.print("\n[bold]Next steps:[/bold]")
                console.print("  1. Setup DNS: [cyan]lab dns setup[/cyan]")
                console.print("  2. Create a lab: [cyan]lab setup my-lab[/cyan]")
                console.print("  3. Access via: [cyan]http://my-lab.local/[/cyan]")
            else:
                console.print("[red]✗ Failed to start proxy[/red]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Failed to start proxy: {e.stderr.decode()}[/red]")

    def stop(self, remove: bool = False):
        """Stop Caddy proxy container"""
        if not self.is_running():
            # Check if container exists but is stopped
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={CADDY_CONTAINER_NAME}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            if CADDY_CONTAINER_NAME not in result.stdout:
                console.print("[yellow]Proxy container not found[/yellow]")
                return

        console.print("[dim]Stopping proxy container...[/dim]")
        subprocess.run(["docker", "stop", CADDY_CONTAINER_NAME], capture_output=True)

        if remove:
            console.print("[dim]Removing proxy container...[/dim]")
            subprocess.run(["docker", "rm", CADDY_CONTAINER_NAME], capture_output=True)

        console.print("[green]✅ Proxy stopped[/green]")

    def restart(self):
        """Restart Caddy proxy container"""
        if not self.is_running():
            console.print("[yellow]Proxy not running, starting...[/yellow]")
            self.start()
            return

        console.print("[dim]Restarting proxy...[/dim]")
        subprocess.run(["docker", "restart", CADDY_CONTAINER_NAME], check=True)
        console.print("[green]✅ Proxy restarted[/green]")

    def logs(self, follow: bool = False):
        """Show Caddy logs"""
        if not self.is_running():
            console.print("[yellow]Proxy not running[/yellow]")
            return

        cmd = ["docker", "logs"]
        if follow:
            cmd.append("-f")
        cmd.append(CADDY_CONTAINER_NAME)

        subprocess.run(cmd)

    def _call_admin_api(self, method: str, path: str, data: dict = None) -> tuple[bool, str]:
        """Make a request to Caddy admin API"""
        import urllib.request
        import urllib.error

        url = f"{CADDY_ADMIN_API}{path}"

        try:
            req_data = json.dumps(data).encode('utf-8') if data else None
            headers = {'Content-Type': 'application/json'} if data else {}

            request = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=5) as response:
                return True, response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return False, e.read().decode('utf-8')
        except Exception as e:
            return False, str(e)

    def register_lab(self, lab_name: str, port: int):
        """Register lab routes dynamically via Caddy API (zero-downtime)"""
        if not self.is_running():
            console.print("[dim]Proxy not running, skipping route registration[/dim]")
            console.print(f"[dim]💡 Start proxy: lab proxy start[/dim]")
            return

        route = {
            "@id": f"lab-{lab_name}",
            "match": [{
                "host": [f"*.{lab_name}.local", f"{lab_name}.local"]
            }],
            "handle": [{
                "handler": "reverse_proxy",
                "upstreams": [{"dial": f"host.docker.internal:{port}"}],
                "headers": {
                    "request": {
                        "set": {
                            "X-Lab-Name": [lab_name],
                            "X-Lab-Port": [str(port)]
                        }
                    }
                }
            }]
        }

        success, response = self._call_admin_api(
            "POST",
            "/config/apps/http/servers/lab-proxy/routes",
            route
        )

        if success:
            console.print(f"[green]✓ Routes registered: *.{lab_name}.local → localhost:{port}[/green]")
        else:
            console.print(f"[yellow]⚠ Route registration failed: {response}[/yellow]")

    def unregister_lab(self, lab_name: str):
        """Remove lab routes from Caddy (zero-downtime)"""
        if not self.is_running():
            return

        success, response = self._call_admin_api(
            "DELETE",
            f"/id/lab-{lab_name}"
        )

        if success:
            console.print(f"[green]✓ Routes removed for {lab_name}[/green]")
        else:
            console.print(f"[dim]Could not remove routes: {response}[/dim]")

    def list_routes(self):
        """List all registered lab routes"""
        if not self.is_running():
            console.print("[yellow]Proxy not running[/yellow]")
            return

        success, response = self._call_admin_api("GET", "/config/apps/http/servers/lab-proxy/routes")

        if not success:
            console.print(f"[red]Error listing routes: {response}[/red]")
            return

        routes = json.loads(response) if response else []

        if not routes:
            console.print("[dim]No routes registered yet[/dim]")
            console.print("[dim]💡 Create a lab: lab setup my-lab[/dim]")
            return

        from rich.table import Table
        table = Table(title="Lab Proxy Routes")
        table.add_column("Lab Name")
        table.add_column("Domain Pattern")
        table.add_column("Target Port")
        table.add_column("Status")

        for route in routes:
            route_id = route.get("@id", "")
            if route_id.startswith("lab-"):
                lab_name = route_id[4:]  # Remove "lab-" prefix
                domains = route["match"][0]["host"]
                upstream = route["handle"][0]["upstreams"][0]["dial"]
                port = upstream.split(":")[-1]

                # Check if lab is actually running
                from claude_lab.cli import get_registry
                registry = get_registry()
                status = "🟢 Active" if lab_name in registry else "🔴 Inactive"

                table.add_row(lab_name, ", ".join(domains), port, status)

        console.print(table)

    def status(self):
        """Show proxy status"""
        if self.is_running():
            console.print("[green]✅ Proxy is running[/green]")
            console.print(f"[dim]Container: {CADDY_CONTAINER_NAME}[/dim]")
            console.print("[dim]Admin API: http://localhost:2019[/dim]")
            console.print()
            self.list_routes()
        else:
            console.print("[yellow]❌ Proxy is not running[/yellow]")
            console.print("[dim]Start with: lab proxy start[/dim]")
