#!/usr/bin/env python3
"""
Dependency Installer for OpenProject Multi-Repository Environment.

Handles installation of dependencies across multiple repositories with:
- Unified virtual environment management
- Dependency conflict resolution
- Cross-repository compatibility checking
- Development vs production environment handling
"""

import subprocess
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from packaging.requirements import Requirement

from ..analyzers.repository_analyzer import RepositoryAnalyzer
from ..trackers.dependency_tracker import DependencyTracker


class DependencyInstaller:
    """Install and manage dependencies across multiple repositories."""
    
    def __init__(self, workspace_path: str = None, use_poetry: bool = False):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.use_poetry = use_poetry
        self.venv_path = self.workspace_path / ".venv"
        self.tracker = DependencyTracker(str(self.workspace_path))
        
    def create_virtual_environment(self, force_recreate: bool = False) -> bool:
        """Create a unified virtual environment for all repositories."""
        if self.venv_path.exists() and not force_recreate:
            print(f"Virtual environment already exists at {self.venv_path}")
            return True
            
        if self.venv_path.exists() and force_recreate:
            print(f"Removing existing virtual environment...")
            subprocess.run([sys.executable, "-m", "shutil", "rmtree", str(self.venv_path)], 
                         check=False)
                         
        print(f"Creating virtual environment at {self.venv_path}")
        result = subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating virtual environment: {result.stderr}")
            return False
            
        # Upgrade pip
        pip_cmd = self._get_pip_command()
        subprocess.run([*pip_cmd, "install", "--upgrade", "pip"], 
                      capture_output=True, text=True)
        
        return True
        
    def _get_pip_command(self) -> List[str]:
        """Get the pip command for the virtual environment."""
        if sys.platform == "win32":
            return [str(self.venv_path / "Scripts" / "pip.exe")]
        else:
            return [str(self.venv_path / "bin" / "pip")]
            
    def _get_python_command(self) -> List[str]:
        """Get the python command for the virtual environment."""
        if sys.platform == "win32":
            return [str(self.venv_path / "Scripts" / "python.exe")]
        else:
            return [str(self.venv_path / "bin" / "python")]
            
    def collect_all_dependencies(self) -> Dict[str, Set[str]]:
        """Collect all dependencies from all repositories."""
        repos = self.tracker.discover_repositories()
        all_dependencies = {
            "main": set(),
            "dev": set(),
            "optional": set()
        }
        
        for repo_path in repos:
            analyzer = RepositoryAnalyzer(str(repo_path))
            repo_data = analyzer.analyze()
            
            python_deps = repo_data.get("python_dependencies", {})
            pyproject_data = python_deps.get("pyproject_toml")
            
            if pyproject_data:
                # Main dependencies
                if "dependencies" in pyproject_data:
                    all_dependencies["main"].update(pyproject_data["dependencies"])
                    
                # Development dependencies
                if "optional-dependencies" in pyproject_data:
                    for group, deps in pyproject_data["optional-dependencies"].items():
                        if "dev" in group.lower() or "test" in group.lower():
                            all_dependencies["dev"].update(deps)
                        else:
                            all_dependencies["optional"].update(deps)
                            
            # Also check requirements.txt files
            requirements_files = python_deps.get("requirements_files", [])
            for req_file in requirements_files:
                if "dev" in req_file.lower() or "test" in req_file.lower():
                    all_dependencies["dev"].update(self._read_requirements_file(req_file))
                else:
                    all_dependencies["main"].update(self._read_requirements_file(req_file))
                    
        return all_dependencies
        
    def _read_requirements_file(self, file_path: str) -> Set[str]:
        """Read dependencies from a requirements.txt file."""
        dependencies = set()
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        dependencies.add(line)
        except FileNotFoundError:
            pass
        return dependencies
        
    def resolve_conflicts(self, dependencies: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """Resolve version conflicts in dependencies."""
        resolved = {
            "main": [],
            "dev": [],
            "optional": []
        }
        
        for dep_type, deps in dependencies.items():
            dep_dict = {}
            
            for dep_string in deps:
                try:
                    req = Requirement(dep_string)
                    dep_name = req.name.lower()
                    
                    if dep_name in dep_dict:
                        # Merge requirements - for now, use the more restrictive one
                        existing_req = dep_dict[dep_name]
                        # This is a simplification - in practice, you'd want more sophisticated merging
                        if str(req.specifier) and not str(existing_req.specifier):
                            dep_dict[dep_name] = req
                        elif str(req.specifier) and str(existing_req.specifier):
                            # For now, just use the first one - could be improved
                            pass
                    else:
                        dep_dict[dep_name] = req
                        
                except Exception as e:
                    print(f"Warning: Could not parse requirement '{dep_string}': {e}")
                    resolved[dep_type].append(dep_string)
                    
            # Convert back to strings
            for req in dep_dict.values():
                resolved[dep_type].append(str(req))
                
        return resolved
        
    def install_dependencies(self, include_dev: bool = True, 
                           include_optional: bool = False,
                           upgrade: bool = False) -> bool:
        """Install all resolved dependencies."""
        if not self.venv_path.exists():
            if not self.create_virtual_environment():
                return False
                
        # Collect and resolve dependencies
        all_deps = self.collect_all_dependencies()
        resolved_deps = self.resolve_conflicts(all_deps)
        
        pip_cmd = self._get_pip_command()
        
        # Install main dependencies
        if resolved_deps["main"]:
            print("Installing main dependencies...")
            cmd = [*pip_cmd, "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.extend(resolved_deps["main"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error installing main dependencies: {result.stderr}")
                return False
                
        # Install development dependencies
        if include_dev and resolved_deps["dev"]:
            print("Installing development dependencies...")
            cmd = [*pip_cmd, "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.extend(resolved_deps["dev"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error installing dev dependencies: {result.stderr}")
                return False
                
        # Install optional dependencies
        if include_optional and resolved_deps["optional"]:
            print("Installing optional dependencies...")
            cmd = [*pip_cmd, "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.extend(resolved_deps["optional"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Warning: Some optional dependencies failed to install: {result.stderr}")
                
        print("✅ Dependencies installed successfully!")
        return True
        
    def generate_lockfile(self) -> Dict[str, Any]:
        """Generate a lockfile with installed packages and their versions."""
        if not self.venv_path.exists():
            return {}
            
        pip_cmd = self._get_pip_command()
        result = subprocess.run([*pip_cmd, "freeze"], capture_output=True, text=True)
        
        if result.returncode != 0:
            return {}
            
        lockfile = {
            "generated_by": "dependency-manager",
            "python_version": sys.version,
            "packages": {}
        }
        
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                lockfile["packages"][name] = version
                
        return lockfile
        
    def save_lockfile(self, filename: str = "dependencies.lock.json") -> bool:
        """Save the lockfile to disk."""
        lockfile = self.generate_lockfile()
        lockfile_path = self.workspace_path / filename
        
        try:
            with open(lockfile_path, 'w') as f:
                json.dump(lockfile, f, indent=2)
            print(f"✅ Lockfile saved to {lockfile_path}")
            return True
        except Exception as e:
            print(f"Error saving lockfile: {e}")
            return False
            
    def install_from_lockfile(self, filename: str = "dependencies.lock.json") -> bool:
        """Install dependencies from a lockfile."""
        lockfile_path = self.workspace_path / filename
        
        if not lockfile_path.exists():
            print(f"Lockfile {lockfile_path} not found")
            return False
            
        try:
            with open(lockfile_path, 'r') as f:
                lockfile = json.load(f)
        except Exception as e:
            print(f"Error reading lockfile: {e}")
            return False
            
        if not self.venv_path.exists():
            if not self.create_virtual_environment():
                return False
                
        pip_cmd = self._get_pip_command()
        packages = [f"{name}=={version}" for name, version in lockfile["packages"].items()]
        
        if packages:
            print(f"Installing {len(packages)} packages from lockfile...")
            result = subprocess.run([*pip_cmd, "install"] + packages, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error installing from lockfile: {result.stderr}")
                return False
                
        print("✅ Dependencies installed from lockfile successfully!")
        return True
        
    def check_security(self) -> Dict[str, Any]:
        """Check for security vulnerabilities in installed packages."""
        if not self.venv_path.exists():
            return {"error": "No virtual environment found"}
            
        pip_cmd = self._get_pip_command()
        
        # Try to install safety if not available
        subprocess.run([*pip_cmd, "install", "safety"], capture_output=True)
        
        # Run safety check
        safety_cmd = [*pip_cmd, "run", "safety", "check", "--json"]
        result = subprocess.run(safety_cmd, capture_output=True, text=True)
        
        try:
            return json.loads(result.stdout)
        except:
            return {"error": "Could not run security check"}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Install dependencies across repositories")
    parser.add_argument("--workspace", default=".", help="Path to workspace directory")
    parser.add_argument("--dev", action="store_true", help="Include development dependencies")
    parser.add_argument("--optional", action="store_true", help="Include optional dependencies")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade existing packages")
    parser.add_argument("--lockfile", help="Install from lockfile")
    parser.add_argument("--save-lockfile", action="store_true", help="Save lockfile after install")
    
    args = parser.parse_args()
    
    installer = DependencyInstaller(args.workspace)
    
    if args.lockfile:
        success = installer.install_from_lockfile(args.lockfile)
    else:
        success = installer.install_dependencies(
            include_dev=args.dev,
            include_optional=args.optional,
            upgrade=args.upgrade
        )
        
    if success and args.save_lockfile:
        installer.save_lockfile()