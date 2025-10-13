#!/usr/bin/env python3
"""
Dependency Tracker for OpenProject Multi-Repository Dependencies.

Tracks dependencies across multiple repositories and identifies:
- Version conflicts between repositories
- Shared dependencies that could be consolidated
- Missing dependencies that cause cross-repo issues
- Dependency update opportunities
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from packaging import version
from packaging.requirements import Requirement

from ..analyzers.repository_analyzer import RepositoryAnalyzer


class DependencyTracker:
    """Track and analyze dependencies across multiple repositories."""
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.repositories = {}
        self.analysis_cache = {}
        
    def discover_repositories(self) -> List[Path]:
        """Discover all repositories in the workspace."""
        repositories = []
        
        # Look for git repositories
        for item in self.workspace_path.iterdir():
            if item.is_dir() and (item / ".git").exists():
                repositories.append(item)
                
        # Also check external/ directory if it exists
        external_dir = self.workspace_path / "external"
        if external_dir.exists():
            for item in external_dir.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    repositories.append(item)
                    
        return repositories
        
    def analyze_all_repositories(self) -> Dict[str, Any]:
        """Analyze all discovered repositories."""
        repos = self.discover_repositories()
        
        for repo_path in repos:
            repo_name = repo_path.name
            print(f"Analyzing {repo_name}...")
            
            analyzer = RepositoryAnalyzer(str(repo_path))
            self.repositories[repo_name] = analyzer.analyze()
            
        return self.repositories
        
    def find_version_conflicts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Find version conflicts across repositories."""
        conflicts = {}
        
        # Collect all Python dependencies with versions
        all_deps = {}
        
        for repo_name, repo_data in self.repositories.items():
            python_deps = repo_data.get("python_dependencies", {})
            pyproject_data = python_deps.get("pyproject_toml")
            
            if pyproject_data and "dependencies" in pyproject_data:
                for dep_string in pyproject_data["dependencies"]:
                    try:
                        req = Requirement(dep_string)
                        dep_name = req.name.lower()
                        
                        if dep_name not in all_deps:
                            all_deps[dep_name] = []
                            
                        all_deps[dep_name].append({
                            "repository": repo_name,
                            "requirement": str(req),
                            "specifier": str(req.specifier) if req.specifier else "any"
                        })
                    except Exception as e:
                        print(f"Warning: Could not parse requirement '{dep_string}' in {repo_name}: {e}")
                        
        # Find conflicts
        for dep_name, usages in all_deps.items():
            if len(usages) > 1:
                # Check if there are conflicting version requirements
                specifiers = [usage["specifier"] for usage in usages if usage["specifier"] != "any"]
                
                if len(set(specifiers)) > 1:
                    conflicts[dep_name] = usages
                    
        return conflicts
        
    def find_shared_dependencies(self) -> Dict[str, List[str]]:
        """Find dependencies that are shared across repositories."""
        shared_deps = {}
        
        for repo_name, repo_data in self.repositories.items():
            python_deps = repo_data.get("python_dependencies", {})
            pyproject_data = python_deps.get("pyproject_toml")
            
            if pyproject_data and "dependencies" in pyproject_data:
                for dep_string in pyproject_data["dependencies"]:
                    try:
                        req = Requirement(dep_string)
                        dep_name = req.name.lower()
                        
                        if dep_name not in shared_deps:
                            shared_deps[dep_name] = []
                            
                        if repo_name not in shared_deps[dep_name]:
                            shared_deps[dep_name].append(repo_name)
                    except Exception:
                        pass
                        
        # Only return dependencies used in multiple repos
        return {dep: repos for dep, repos in shared_deps.items() if len(repos) > 1}
        
    def check_compatibility(self) -> Dict[str, Any]:
        """Check overall compatibility across repositories."""
        compatibility_report = {
            "version_conflicts": self.find_version_conflicts(),
            "shared_dependencies": self.find_shared_dependencies(),
            "total_repositories": len(self.repositories),
            "python_repositories": 0,
            "docker_repositories": 0
        }
        
        # Count repository types
        for repo_data in self.repositories.values():
            if repo_data.get("python_dependencies", {}).get("pyproject_toml"):
                compatibility_report["python_repositories"] += 1
            if repo_data.get("docker_dependencies", {}).get("dockerfiles"):
                compatibility_report["docker_repositories"] += 1
                
        return compatibility_report
        
    def generate_update_plan(self) -> Dict[str, Any]:
        """Generate a plan for updating dependencies."""
        update_plan = {
            "recommendations": [],
            "conflicts_to_resolve": [],
            "shared_deps_to_consolidate": []
        }
        
        # Find version conflicts that need resolution
        conflicts = self.find_version_conflicts()
        for dep_name, usages in conflicts.items():
            update_plan["conflicts_to_resolve"].append({
                "dependency": dep_name,
                "usages": usages,
                "recommendation": f"Standardize {dep_name} version across all repositories"
            })
            
        # Find shared dependencies that could be consolidated
        shared_deps = self.find_shared_dependencies()
        for dep_name, repos in shared_deps.items():
            if len(repos) >= 3:  # Used in 3+ repositories
                update_plan["shared_deps_to_consolidate"].append({
                    "dependency": dep_name,
                    "repositories": repos,
                    "recommendation": f"Consider creating shared dependency configuration for {dep_name}"
                })
                
        return update_plan
        
    def generate_report(self, format: str = "json") -> str:
        """Generate a comprehensive dependency report."""
        if not self.repositories:
            self.analyze_all_repositories()
            
        report_data = {
            "summary": {
                "total_repositories": len(self.repositories),
                "analysis_timestamp": str(Path.cwd())
            },
            "repositories": self.repositories,
            "compatibility": self.check_compatibility(),
            "update_plan": self.generate_update_plan()
        }
        
        if format.lower() == "json":
            return json.dumps(report_data, indent=2)
        elif format.lower() == "summary":
            return self._generate_summary_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _generate_summary_report(self, report_data: Dict[str, Any]) -> str:
        """Generate a human-readable summary report."""
        summary = "# Multi-Repository Dependency Analysis\n\n"
        
        # Summary statistics
        summary += f"## Summary\n"
        summary += f"- **Repositories analyzed**: {report_data['summary']['total_repositories']}\n"
        summary += f"- **Python repositories**: {report_data['compatibility']['python_repositories']}\n"
        summary += f"- **Docker repositories**: {report_data['compatibility']['docker_repositories']}\n\n"
        
        # Version conflicts
        conflicts = report_data['compatibility']['version_conflicts']
        if conflicts:
            summary += f"## Version Conflicts ({len(conflicts)})\n"
            for dep_name, usages in conflicts.items():
                summary += f"### {dep_name}\n"
                for usage in usages:
                    summary += f"- {usage['repository']}: {usage['requirement']}\n"
                summary += "\n"
        else:
            summary += "## Version Conflicts\n✅ No version conflicts detected\n\n"
            
        # Shared dependencies
        shared_deps = report_data['compatibility']['shared_dependencies']
        if shared_deps:
            summary += f"## Shared Dependencies ({len(shared_deps)})\n"
            for dep_name, repos in shared_deps.items():
                summary += f"- **{dep_name}**: {', '.join(repos)}\n"
            summary += "\n"
            
        # Update recommendations
        update_plan = report_data['update_plan']
        if update_plan['recommendations'] or update_plan['conflicts_to_resolve']:
            summary += "## Recommendations\n"
            for conflict in update_plan['conflicts_to_resolve']:
                summary += f"⚠️ {conflict['recommendation']}\n"
            for consolidation in update_plan['shared_deps_to_consolidate']:
                summary += f"💡 {consolidation['recommendation']}\n"
            summary += "\n"
            
        return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Track dependencies across repositories")
    parser.add_argument("--workspace", default=".", help="Path to workspace directory")
    parser.add_argument("--format", choices=["json", "summary"], default="summary",
                       help="Output format")
    
    args = parser.parse_args()
    
    tracker = DependencyTracker(args.workspace)
    print(tracker.generate_report(args.format))