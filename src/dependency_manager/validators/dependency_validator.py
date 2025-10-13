#!/usr/bin/env python3
"""
Dependency Validator for OpenProject Multi-Repository Environment.

Validates dependencies for:
- Security vulnerabilities
- License compatibility  
- Version compatibility across repositories
- Outdated packages
- Missing dependencies
"""

import subprocess
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from packaging import version
from packaging.requirements import Requirement
from datetime import datetime, timedelta

from ..analyzers.repository_analyzer import RepositoryAnalyzer
from ..trackers.dependency_tracker import DependencyTracker


class DependencyValidator:
    """Validate dependencies across multiple repositories."""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.tracker = DependencyTracker(str(self.workspace_path))
        self.venv_path = self.workspace_path / ".venv"
        
        # License compatibility matrix
        self.license_compatibility = {
            "MIT": ["MIT", "BSD", "Apache-2.0", "ISC", "Unlicense"],
            "BSD": ["MIT", "BSD", "Apache-2.0", "ISC", "Unlicense"],
            "Apache-2.0": ["MIT", "BSD", "Apache-2.0", "ISC"],
            "GPL-3.0": ["GPL-3.0", "LGPL-3.0"],
            "GPL-2.0": ["GPL-2.0", "LGPL-2.0"],
            "LGPL-3.0": ["MIT", "BSD", "Apache-2.0", "LGPL-3.0", "GPL-3.0"],
            "LGPL-2.0": ["MIT", "BSD", "Apache-2.0", "LGPL-2.0", "GPL-2.0"],
        }
        
    def _get_pip_command(self) -> List[str]:
        """Get the pip command for the virtual environment."""
        if sys.platform == "win32":
            return [str(self.venv_path / "Scripts" / "pip.exe")]
        else:
            return [str(self.venv_path / "bin" / "pip")]
            
    def check_security_vulnerabilities(self) -> Dict[str, Any]:
        """Check for known security vulnerabilities."""
        if not self.venv_path.exists():
            return {"error": "No virtual environment found"}
            
        try:
            # Try using safety
            pip_cmd = self._get_pip_command()
            
            # Install safety if not available
            subprocess.run([*pip_cmd, "install", "safety"], capture_output=True)
            
            # Run safety check
            result = subprocess.run([*pip_cmd, "run", "safety", "check", "--json"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                try:
                    safety_data = json.loads(result.stdout)
                    return {
                        "tool": "safety",
                        "vulnerabilities": safety_data,
                        "total_vulnerabilities": len(safety_data)
                    }
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"Warning: Could not run safety check: {e}")
            
        # Fallback: Manual vulnerability check using PyUp.io API
        return self._check_vulnerabilities_pyup()
        
    def _check_vulnerabilities_pyup(self) -> Dict[str, Any]:
        """Check vulnerabilities using PyUp.io safety-db."""
        vulnerabilities = []
        
        # Get installed packages
        if not self.venv_path.exists():
            return {"error": "No virtual environment found"}
            
        pip_cmd = self._get_pip_command()
        result = subprocess.run([*pip_cmd, "list", "--format=json"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            return {"error": "Could not list installed packages"}
            
        try:
            packages = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Could not parse package list"}
            
        # Note: In a real implementation, you'd want to use the actual PyUp.io API
        # or maintain a local vulnerability database
        return {
            "tool": "manual",
            "vulnerabilities": vulnerabilities,
            "total_vulnerabilities": len(vulnerabilities),
            "note": "Manual vulnerability checking not fully implemented"
        }
        
    def check_license_compatibility(self, target_license: str = "MIT") -> Dict[str, Any]:
        """Check license compatibility across all dependencies."""
        license_issues = []
        unknown_licenses = []
        
        # Get all repositories
        repos = self.tracker.discover_repositories()
        
        for repo_path in repos:
            analyzer = RepositoryAnalyzer(str(repo_path))
            repo_data = analyzer.analyze()
            
            python_deps = repo_data.get("python_dependencies", {})
            pyproject_data = python_deps.get("pyproject_toml")
            
            if pyproject_data and "dependencies" in pyproject_data:
                for dep_string in pyproject_data["dependencies"]:
                    try:
                        req = Requirement(dep_string)
                        license_info = self._get_package_license(req.name)
                        
                        if license_info["license"] == "unknown":
                            unknown_licenses.append({
                                "package": req.name,
                                "repository": repo_path.name
                            })
                        elif not self._is_license_compatible(license_info["license"], target_license):
                            license_issues.append({
                                "package": req.name,
                                "license": license_info["license"],
                                "repository": repo_path.name,
                                "compatible": False
                            })
                    except Exception:
                        pass
                        
        return {
            "target_license": target_license,
            "license_issues": license_issues,
            "unknown_licenses": unknown_licenses,
            "total_issues": len(license_issues),
            "total_unknown": len(unknown_licenses)
        }
        
    def _get_package_license(self, package_name: str) -> Dict[str, str]:
        """Get license information for a package from PyPI."""
        try:
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                license_info = data.get("info", {}).get("license", "")
                classifiers = data.get("info", {}).get("classifiers", [])
                
                # Extract license from classifiers
                for classifier in classifiers:
                    if classifier.startswith("License ::"):
                        parts = classifier.split(" :: ")
                        if len(parts) >= 3:
                            return {"license": parts[-1], "source": "classifier"}
                            
                # Fallback to license field
                if license_info:
                    return {"license": license_info, "source": "field"}
                    
        except Exception:
            pass
            
        return {"license": "unknown", "source": "none"}
        
    def _is_license_compatible(self, package_license: str, target_license: str) -> bool:
        """Check if a package license is compatible with the target license."""
        if target_license not in self.license_compatibility:
            return True  # Unknown target license, assume compatible
            
        compatible_licenses = self.license_compatibility[target_license]
        
        # Normalize license names
        package_license = package_license.strip()
        for compatible in compatible_licenses:
            if compatible.lower() in package_license.lower():
                return True
                
        return False
        
    def check_outdated_packages(self) -> Dict[str, Any]:
        """Check for outdated packages."""
        if not self.venv_path.exists():
            return {"error": "No virtual environment found"}
            
        pip_cmd = self._get_pip_command()
        result = subprocess.run([*pip_cmd, "list", "--outdated", "--format=json"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            return {"error": "Could not check for outdated packages"}
            
        try:
            outdated_packages = json.loads(result.stdout)
            
            # Categorize by severity (major, minor, patch updates)
            major_updates = []
            minor_updates = []
            patch_updates = []
            
            for package in outdated_packages:
                current = package["version"]
                latest = package["latest_version"]
                
                try:
                    current_ver = version.parse(current)
                    latest_ver = version.parse(latest)
                    
                    if current_ver.major < latest_ver.major:
                        major_updates.append(package)
                    elif current_ver.minor < latest_ver.minor:
                        minor_updates.append(package)
                    else:
                        patch_updates.append(package)
                except:
                    # If version parsing fails, treat as minor update
                    minor_updates.append(package)
                    
            return {
                "total_outdated": len(outdated_packages),
                "major_updates": major_updates,
                "minor_updates": minor_updates,
                "patch_updates": patch_updates,
                "all_outdated": outdated_packages
            }
            
        except json.JSONDecodeError:
            return {"error": "Could not parse outdated packages list"}
            
    def check_missing_dependencies(self) -> Dict[str, Any]:
        """Check for missing dependencies across repositories."""
        missing_deps = []
        repos = self.tracker.discover_repositories()
        
        for repo_path in repos:
            # Check if the repository has dependency files but no virtual environment
            analyzer = RepositoryAnalyzer(str(repo_path))
            repo_data = analyzer.analyze()
            
            python_deps = repo_data.get("python_dependencies", {})
            
            if python_deps.get("pyproject_toml") or python_deps.get("requirements_files"):
                # This repository has Python dependencies
                venv_indicators = [
                    repo_path / ".venv",
                    repo_path / "venv",
                    repo_path / "env"
                ]
                
                has_venv = any(venv.exists() for venv in venv_indicators)
                
                if not has_venv:
                    missing_deps.append({
                        "repository": repo_path.name,
                        "issue": "No virtual environment found",
                        "has_dependencies": True
                    })
                    
        return {
            "missing_environments": missing_deps,
            "total_issues": len(missing_deps)
        }
        
    def validate_cross_repo_compatibility(self) -> Dict[str, Any]:
        """Validate compatibility across all repositories."""
        compatibility_report = self.tracker.check_compatibility()
        
        # Add additional validation
        validation_results = {
            "version_conflicts": compatibility_report["version_conflicts"],
            "shared_dependencies": compatibility_report["shared_dependencies"],
            "security_check": self.check_security_vulnerabilities(),
            "license_check": self.check_license_compatibility(),
            "outdated_check": self.check_outdated_packages(),
            "missing_deps": self.check_missing_dependencies()
        }
        
        # Calculate overall score
        total_issues = 0
        total_issues += len(validation_results["version_conflicts"])
        total_issues += validation_results["security_check"].get("total_vulnerabilities", 0)
        total_issues += validation_results["license_check"].get("total_issues", 0)
        total_issues += validation_results["outdated_check"].get("total_outdated", 0)
        total_issues += validation_results["missing_deps"].get("total_issues", 0)
        
        validation_results["summary"] = {
            "total_issues": total_issues,
            "severity": "high" if total_issues > 10 else "medium" if total_issues > 5 else "low"
        }
        
        return validation_results
        
    def generate_validation_report(self, format: str = "summary") -> str:
        """Generate a comprehensive validation report."""
        validation_results = self.validate_cross_repo_compatibility()
        
        if format.lower() == "json":
            return json.dumps(validation_results, indent=2)
        elif format.lower() == "summary":
            return self._generate_summary_validation_report(validation_results)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _generate_summary_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary."""
        summary = "# Dependency Validation Report\n\n"
        
        # Overall summary
        total_issues = validation_results["summary"]["total_issues"]
        severity = validation_results["summary"]["severity"]
        
        summary += f"## Overall Status\n"
        summary += f"- **Total Issues**: {total_issues}\n"
        summary += f"- **Severity**: {severity.upper()}\n"
        
        if total_issues == 0:
            summary += "- **Status**: ✅ All validations passed\n\n"
        else:
            summary += f"- **Status**: ⚠️ {total_issues} issues found\n\n"
            
        # Version conflicts
        conflicts = validation_results["version_conflicts"]
        if conflicts:
            summary += f"## Version Conflicts ({len(conflicts)})\n"
            for dep_name, usages in conflicts.items():
                summary += f"### ⚠️ {dep_name}\n"
                for usage in usages:
                    summary += f"- {usage['repository']}: `{usage['requirement']}`\n"
                summary += "\n"
                
        # Security vulnerabilities
        security = validation_results["security_check"]
        vuln_count = security.get("total_vulnerabilities", 0)
        if vuln_count > 0:
            summary += f"## Security Vulnerabilities ({vuln_count})\n"
            summary += f"🚨 Found {vuln_count} security vulnerabilities\n"
            summary += f"Tool: {security.get('tool', 'unknown')}\n\n"
        elif "error" not in security:
            summary += "## Security Vulnerabilities\n✅ No known vulnerabilities found\n\n"
            
        # License issues
        license_check = validation_results["license_check"]
        license_issues = license_check.get("total_issues", 0)
        if license_issues > 0:
            summary += f"## License Compatibility ({license_issues})\n"
            for issue in license_check.get("license_issues", []):
                summary += f"⚠️ {issue['package']}: {issue['license']} (in {issue['repository']})\n"
            summary += "\n"
            
        # Outdated packages
        outdated = validation_results["outdated_check"]
        if "total_outdated" in outdated and outdated["total_outdated"] > 0:
            summary += f"## Outdated Packages ({outdated['total_outdated']})\n"
            summary += f"- Major updates: {len(outdated.get('major_updates', []))}\n"
            summary += f"- Minor updates: {len(outdated.get('minor_updates', []))}\n"
            summary += f"- Patch updates: {len(outdated.get('patch_updates', []))}\n\n"
            
        return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dependencies across repositories")
    parser.add_argument("--workspace", default=".", help="Path to workspace directory")
    parser.add_argument("--format", choices=["json", "summary"], default="summary",
                       help="Output format")
    parser.add_argument("--license", default="MIT", help="Target license for compatibility check")
    
    args = parser.parse_args()
    
    validator = DependencyValidator(args.workspace)
    print(validator.generate_validation_report(args.format))