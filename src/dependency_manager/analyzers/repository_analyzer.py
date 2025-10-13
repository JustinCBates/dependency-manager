#!/usr/bin/env python3
"""
Repository Analyzer for OpenProject Multi-Repository Dependencies.

Analyzes individual repositories for:
- Python dependencies (pyproject.toml, requirements.txt)
- Docker dependencies (Dockerfile, docker-compose.yml)
- System dependencies (scripts, documentation)
- Security vulnerabilities
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import toml
import yaml


class RepositoryAnalyzer:
    """Analyze dependencies in a single repository."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.analysis_result = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Run complete dependency analysis."""
        self.analysis_result = {
            "repository": str(self.repo_path),
            "python_dependencies": self._analyze_python_deps(),
            "docker_dependencies": self._analyze_docker_deps(),
            "system_dependencies": self._analyze_system_deps(),
            "security_issues": self._check_security(),
            "metadata": self._get_repository_metadata()
        }
        return self.analysis_result
        
    def _analyze_python_deps(self) -> Dict[str, Any]:
        """Analyze Python dependencies."""
        python_deps = {
            "pyproject_toml": None,
            "requirements_files": [],
            "installed_packages": [],
            "virtual_environments": []
        }
        
        # Check pyproject.toml
        pyproject_file = self.repo_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                with open(pyproject_file, 'r') as f:
                    pyproject_data = toml.load(f)
                python_deps["pyproject_toml"] = {
                    "dependencies": pyproject_data.get("project", {}).get("dependencies", []),
                    "optional_dependencies": pyproject_data.get("project", {}).get("optional-dependencies", {}),
                    "build_system": pyproject_data.get("build-system", {})
                }
            except Exception as e:
                python_deps["pyproject_toml"] = {"error": str(e)}
                
        # Check requirements files
        for req_file in self.repo_path.glob("*requirements*.txt"):
            try:
                with open(req_file, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                python_deps["requirements_files"].append({
                    "file": str(req_file.relative_to(self.repo_path)),
                    "requirements": requirements
                })
            except Exception as e:
                python_deps["requirements_files"].append({
                    "file": str(req_file.relative_to(self.repo_path)),
                    "error": str(e)
                })
                
        # Check for virtual environments
        for venv_dir in ["venv", ".venv", "env", ".env"]:
            venv_path = self.repo_path / venv_dir
            if venv_path.exists() and venv_path.is_dir():
                python_deps["virtual_environments"].append(str(venv_dir))
                
        return python_deps
        
    def _analyze_docker_deps(self) -> Dict[str, Any]:
        """Analyze Docker-related dependencies."""
        docker_deps = {
            "dockerfiles": [],
            "compose_files": [],
            "base_images": [],
            "exposed_ports": []
        }
        
        # Check Dockerfiles
        for dockerfile in self.repo_path.glob("**/Dockerfile*"):
            try:
                with open(dockerfile, 'r') as f:
                    content = f.read()
                    
                # Extract FROM statements (base images)
                from_statements = []
                for line in content.split('\n'):
                    line = line.strip()
                    if line.upper().startswith('FROM '):
                        from_statements.append(line[5:].strip())
                        
                docker_deps["dockerfiles"].append({
                    "file": str(dockerfile.relative_to(self.repo_path)),
                    "base_images": from_statements
                })
                docker_deps["base_images"].extend(from_statements)
                
            except Exception as e:
                docker_deps["dockerfiles"].append({
                    "file": str(dockerfile.relative_to(self.repo_path)),
                    "error": str(e)
                })
                
        # Check docker-compose files
        for compose_pattern in ["docker-compose*.yml", "docker-compose*.yaml"]:
            for compose_file in self.repo_path.glob(compose_pattern):
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)
                    docker_deps["compose_files"].append({
                        "file": str(compose_file.relative_to(self.repo_path)),
                        "services": list(compose_data.get("services", {}).keys()) if compose_data else []
                    })
                except Exception as e:
                    docker_deps["compose_files"].append({
                        "file": str(compose_file.relative_to(self.repo_path)),
                        "error": str(e)
                    })
                    
        # Remove duplicates from base images
        docker_deps["base_images"] = list(set(docker_deps["base_images"]))
        
        return docker_deps
        
    def _analyze_system_deps(self) -> Dict[str, Any]:
        """Analyze system-level dependencies."""
        system_deps = {
            "shell_scripts": [],
            "package_managers": [],
            "system_requirements": []
        }
        
        # Find shell scripts
        for script_file in self.repo_path.glob("**/*.sh"):
            if not any(exclude in str(script_file) for exclude in ['.git', 'venv', 'env', '__pycache__']):
                system_deps["shell_scripts"].append(str(script_file.relative_to(self.repo_path)))
                
        # Check for package manager usage in scripts
        package_managers = ['apt', 'yum', 'brew', 'pip', 'npm', 'yarn']
        for script_file in self.repo_path.glob("**/*.sh"):
            try:
                with open(script_file, 'r') as f:
                    content = f.read()
                    for pm in package_managers:
                        if pm in content and pm not in system_deps["package_managers"]:
                            system_deps["package_managers"].append(pm)
            except:
                pass
                
        return system_deps
        
    def _check_security(self) -> Dict[str, Any]:
        """Check for security vulnerabilities."""
        security_issues = {
            "python_vulnerabilities": [],
            "docker_vulnerabilities": [],
            "scan_status": "not_implemented"
        }
        
        # TODO: Implement actual security scanning
        # Could use safety, bandit, or other tools
        
        return security_issues
        
    def _get_repository_metadata(self) -> Dict[str, Any]:
        """Get repository metadata."""
        metadata = {
            "git_repository": False,
            "size_mb": 0,
            "file_count": 0,
            "last_modified": None
        }
        
        # Check if it's a git repository
        if (self.repo_path / ".git").exists():
            metadata["git_repository"] = True
            
        # Get basic stats
        try:
            file_count = len(list(self.repo_path.rglob("*")))
            metadata["file_count"] = file_count
        except:
            pass
            
        return metadata
        
    def generate_report(self, format: str = "json") -> str:
        """Generate a formatted report."""
        if not self.analysis_result:
            self.analyze()
            
        if format.lower() == "json":
            return json.dumps(self.analysis_result, indent=2)
        elif format.lower() == "summary":
            return self._generate_summary()
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _generate_summary(self) -> str:
        """Generate a human-readable summary."""
        if not self.analysis_result:
            return "No analysis data available"
            
        summary = f"# Dependency Analysis: {self.analysis_result['repository']}\n\n"
        
        # Python dependencies
        python_deps = self.analysis_result.get("python_dependencies", {})
        if python_deps.get("pyproject_toml"):
            deps = python_deps["pyproject_toml"].get("dependencies", [])
            summary += f"## Python Dependencies ({len(deps)})\n"
            for dep in deps:
                summary += f"- {dep}\n"
            summary += "\n"
            
        # Docker dependencies  
        docker_deps = self.analysis_result.get("docker_dependencies", {})
        if docker_deps.get("base_images"):
            summary += f"## Docker Base Images ({len(docker_deps['base_images'])})\n"
            for image in docker_deps["base_images"]:
                summary += f"- {image}\n"
            summary += "\n"
            
        return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze repository dependencies")
    parser.add_argument("repository", help="Path to repository to analyze")
    parser.add_argument("--format", choices=["json", "summary"], default="summary",
                       help="Output format")
    
    args = parser.parse_args()
    
    analyzer = RepositoryAnalyzer(args.repository)
    print(analyzer.generate_report(args.format))