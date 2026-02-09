"""
Project analysis module for claude-lab
Analyzes project directories to determine dependencies and tools needed
"""

import json
from pathlib import Path
from typing import Dict, List, Set
import re


class ProjectAnalyzer:
    """Analyzes a project directory to determine required tools and dependencies"""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.findings = {
            "languages": set(),
            "package_managers": set(),
            "build_tools": set(),
            "k8s_tools": set(),
            "databases": set(),
            "frameworks": set(),
            "dev_tools": set(),
            "files_found": {},
        }

    def analyze(self) -> Dict:
        """Perform full project analysis"""
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")

        self._scan_files()
        self._detect_languages()
        self._detect_package_managers()
        self._detect_build_tools()
        self._detect_k8s_tools()
        self._detect_frameworks()
        self._detect_databases()

        return self._format_results()

    def _scan_files(self):
        """Scan project directory for known files"""
        known_files = {
            # Python
            "pyproject.toml": "python",
            "requirements.txt": "python",
            "setup.py": "python",
            "Pipfile": "python",
            "poetry.lock": "python",
            "uv.lock": "python",
            # JavaScript/TypeScript
            "package.json": "javascript",
            "package-lock.json": "javascript",
            "yarn.lock": "javascript",
            "pnpm-lock.yaml": "javascript",
            "tsconfig.json": "typescript",
            # Go
            "go.mod": "go",
            "go.sum": "go",
            # Rust
            "Cargo.toml": "rust",
            "Cargo.lock": "rust",
            # Java/Kotlin
            "pom.xml": "java",
            "build.gradle": "java",
            "build.gradle.kts": "kotlin",
            # Ruby
            "Gemfile": "ruby",
            "Gemfile.lock": "ruby",
            # Kubernetes
            "kustomization.yaml": "k8s",
            "Chart.yaml": "helm",
            "values.yaml": "helm",
            # Docker
            "Dockerfile": "docker",
            "docker-compose.yml": "docker",
            "docker-compose.yaml": "docker",
            # Build tools
            "Makefile": "make",
            "Taskfile.yml": "task",
            # CI/CD
            ".gitlab-ci.yml": "ci",
            ".travis.yml": "ci",
            # DevContainer
            "devcontainer.json": "devcontainer",
        }

        for file_name, category in known_files.items():
            files = list(self.project_path.rglob(file_name))
            if files:
                self.findings["files_found"][file_name] = len(files)

    def _detect_languages(self):
        """Detect programming languages"""
        files = self.findings["files_found"]

        if any(f in files for f in ["pyproject.toml", "requirements.txt", "setup.py"]):
            self.findings["languages"].add("python")

        if any(f in files for f in ["package.json", "yarn.lock"]):
            self.findings["languages"].add("javascript")

        if "tsconfig.json" in files:
            self.findings["languages"].add("typescript")

        if any(f in files for f in ["go.mod", "go.sum"]):
            self.findings["languages"].add("go")

        if any(f in files for f in ["Cargo.toml", "Cargo.lock"]):
            self.findings["languages"].add("rust")

        if any(f in files for f in ["pom.xml", "build.gradle"]):
            self.findings["languages"].add("java")

        if "Gemfile" in files:
            self.findings["languages"].add("ruby")

    def _detect_package_managers(self):
        """Detect package managers"""
        files = self.findings["files_found"]

        if "pyproject.toml" in files:
            # Check content to determine manager
            pyproject_files = list(self.project_path.rglob("pyproject.toml"))
            for pf in pyproject_files[:3]:  # Check first 3
                try:
                    content = pf.read_text()
                    if "poetry" in content.lower():
                        self.findings["package_managers"].add("poetry")
                    if "uv" in content.lower() or "[tool.uv]" in content:
                        self.findings["package_managers"].add("uv")
                    if "hatch" in content.lower():
                        self.findings["package_managers"].add("hatch")
                except:
                    pass

        if "requirements.txt" in files:
            self.findings["package_managers"].add("pip")

        if "Pipfile" in files:
            self.findings["package_managers"].add("pipenv")

        if "package-lock.json" in files:
            self.findings["package_managers"].add("npm")

        if "yarn.lock" in files:
            self.findings["package_managers"].add("yarn")

        if "pnpm-lock.yaml" in files:
            self.findings["package_managers"].add("pnpm")

    def _detect_build_tools(self):
        """Detect build tools"""
        files = self.findings["files_found"]

        if "Makefile" in files:
            self.findings["build_tools"].add("make")

        if "Taskfile.yml" in files:
            self.findings["build_tools"].add("task")

        if "Dockerfile" in files or "docker-compose.yml" in files:
            self.findings["build_tools"].add("docker")

    def _detect_k8s_tools(self):
        """Detect Kubernetes tools needed"""
        files = self.findings["files_found"]

        # Always include kubectl for k8s projects
        if any(f in files for f in ["kustomization.yaml", "Chart.yaml"]):
            self.findings["k8s_tools"].add("kubectl")

        if "Chart.yaml" in files:
            self.findings["k8s_tools"].add("helm")

        if "kustomization.yaml" in files:
            self.findings["k8s_tools"].add("kustomize")

        # Check for ArgoCD
        argo_files = list(self.project_path.rglob("*argo*.yaml"))
        if argo_files:
            self.findings["k8s_tools"].add("argocd")

        # Check for Flux
        flux_files = list(self.project_path.rglob("*flux*.yaml"))
        if flux_files:
            self.findings["k8s_tools"].add("flux")

    def _detect_frameworks(self):
        """Detect frameworks used"""
        # Check package.json for JS frameworks
        package_json_files = list(self.project_path.rglob("package.json"))
        for pf in package_json_files[:5]:
            try:
                data = json.loads(pf.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                if "react" in deps:
                    self.findings["frameworks"].add("react")
                if "vue" in deps:
                    self.findings["frameworks"].add("vue")
                if "next" in deps:
                    self.findings["frameworks"].add("nextjs")
                if "express" in deps:
                    self.findings["frameworks"].add("express")
            except:
                pass

        # Check for Python frameworks
        pyproject_files = list(self.project_path.rglob("pyproject.toml"))
        req_files = list(self.project_path.rglob("requirements.txt"))

        framework_keywords = {
            "fastapi": "fastapi",
            "django": "django",
            "flask": "flask",
            "starlette": "starlette",
        }

        for pf in pyproject_files[:5] + req_files[:5]:
            try:
                content = pf.read_text().lower()
                for keyword, framework in framework_keywords.items():
                    if keyword in content:
                        self.findings["frameworks"].add(framework)
            except:
                pass

    def _detect_databases(self):
        """Detect databases used"""
        # Check docker-compose files
        compose_files = list(self.project_path.rglob("docker-compose*.y*ml"))
        for cf in compose_files[:5]:
            try:
                content = cf.read_text().lower()
                if "postgres" in content:
                    self.findings["databases"].add("postgresql")
                if "mysql" in content:
                    self.findings["databases"].add("mysql")
                if "mongo" in content:
                    self.findings["databases"].add("mongodb")
                if "redis" in content:
                    self.findings["databases"].add("redis")
            except:
                pass

        # Check for database clients in dependencies
        all_files = list(self.project_path.rglob("*requirements*.txt"))
        all_files += list(self.project_path.rglob("pyproject.toml"))

        for f in all_files[:10]:
            try:
                content = f.read_text().lower()
                if "psycopg" in content or "asyncpg" in content:
                    self.findings["databases"].add("postgresql")
                if "pymongo" in content:
                    self.findings["databases"].add("mongodb")
                if "redis" in content:
                    self.findings["databases"].add("redis")
            except:
                pass

    def _format_results(self) -> Dict:
        """Format findings into a structured result"""
        return {
            "project_path": str(self.project_path),
            "project_name": self.project_path.name,
            "languages": sorted(self.findings["languages"]),
            "package_managers": sorted(self.findings["package_managers"]),
            "build_tools": sorted(self.findings["build_tools"]),
            "k8s_tools": sorted(self.findings["k8s_tools"]),
            "databases": sorted(self.findings["databases"]),
            "frameworks": sorted(self.findings["frameworks"]),
            "files_found": self.findings["files_found"],
        }

    def get_recommended_base_template(self) -> str:
        """Recommend a base template based on findings"""
        langs = self.findings["languages"]
        k8s = self.findings["k8s_tools"]

        # Python-heavy project
        if "python" in langs and not k8s:
            return "python-dev"

        # Kubernetes-heavy project
        if k8s or "helm" in self.findings["files_found"]:
            return "k8s-full"

        # General development
        if langs:
            return "base"

        # Default
        return "minimal"

    def generate_dockerfile(self, base_template: str = None) -> str:
        """Generate a custom Dockerfile for this project"""
        if base_template is None:
            base_template = self.get_recommended_base_template()

        results = self._format_results()

        # Start with base
        dockerfile_lines = [
            f"# Auto-generated Dockerfile for {results['project_name']}",
            f"# Based on template: {base_template}",
            f"# Generated by claude-lab",
            "",
            f"FROM claude-lab:{base_template}",
            "",
            f"LABEL claude-lab.project=\"{results['project_name']}\"",
            f"LABEL claude-lab.auto-generated=\"true\"",
            "",
        ]

        # Add language-specific tools
        if "python" in results["languages"]:
            dockerfile_lines.extend([
                "# Python project dependencies",
                "RUN pip install --no-cache-dir \\",
            ])

            # Add common Python tools
            tools = ["pytest", "black", "ruff", "mypy", "ipython"]

            # Add based on package manager
            if "poetry" in results["package_managers"]:
                tools.append("poetry")
            if "uv" in results["package_managers"]:
                dockerfile_lines.append("    # uv already installed in base")
            if "pipenv" in results["package_managers"]:
                tools.append("pipenv")

            # Add framework-specific tools
            if "fastapi" in results["frameworks"]:
                tools.extend(["fastapi", "uvicorn"])
            if "django" in results["frameworks"]:
                tools.append("django")
            if "flask" in results["frameworks"]:
                tools.append("flask")

            if tools:
                dockerfile_lines.append("    " + " \\\n    ".join(tools))
                dockerfile_lines.append("")

        # Add Node.js if needed
        if "javascript" in results["languages"] or "typescript" in results["languages"]:
            dockerfile_lines.extend([
                "# Node.js and npm",
                "RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \\",
                "    && apt-get install -y nodejs",
                "",
            ])

            if "yarn" in results["package_managers"]:
                dockerfile_lines.extend([
                    "RUN npm install -g yarn",
                    "",
                ])

        # Add database clients
        if results["databases"]:
            dockerfile_lines.append("# Database clients")
            if "postgresql" in results["databases"]:
                dockerfile_lines.append("RUN apt-get update && apt-get install -y postgresql-client")
            if "mysql" in results["databases"]:
                dockerfile_lines.append("RUN apt-get update && apt-get install -y mysql-client")
            if "mongodb" in results["databases"]:
                dockerfile_lines.append("RUN apt-get update && apt-get install -y mongodb-clients")
            dockerfile_lines.append("")

        # Finalize
        dockerfile_lines.extend([
            "# Set working directory",
            "WORKDIR /workspace",
            "",
            "CMD [\"/bin/bash\"]",
        ])

        return "\n".join(dockerfile_lines)
