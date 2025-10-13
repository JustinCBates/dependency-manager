#!/usr/bin/env python3
"""
Dependency Manager Demo - Showcase cross-repository dependency analysis.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dependency_manager.analyzers import RepositoryAnalyzer
from dependency_manager.trackers import DependencyTracker


def demo_analyzer():
    """Demonstrate repository analysis capabilities."""
    print("🔍 Repository Analysis Demo")
    print("=" * 50)
    
    # Analyze each repository in the workspace
    repos_to_analyze = [
        "/opt/openproject",
        "/opt/openproject/external/config-manager", 
        "/opt/openproject/external/deploy-manager",
        "/opt/openproject/external/prober",
        "/opt/openproject/external/control-flow",
        "/opt/openproject/external/dependency-manager"
    ]
    
    for repo_path in repos_to_analyze:
        if Path(repo_path).exists():
            print(f"\n📁 Analyzing: {Path(repo_path).name}")
            print("-" * 30)
            
            analyzer = RepositoryAnalyzer(repo_path)
            result = analyzer.analyze()
            
            # Python dependencies
            python_deps = result.get("python_dependencies", {})
            if python_deps.get("pyproject_toml"):
                deps = python_deps["pyproject_toml"].get("dependencies", [])
                print(f"   🐍 Python dependencies: {len(deps)}")
                if deps:
                    print(f"      Examples: {', '.join(deps[:3])}")
                    
            # Docker dependencies  
            docker_deps = result.get("docker_dependencies", {})
            dockerfiles = docker_deps.get("dockerfiles", [])
            if dockerfiles:
                print(f"   🐳 Docker files: {len(dockerfiles)}")
                
            # System dependencies
            system_deps = result.get("system_dependencies", {})
            if system_deps.get("package_managers"):
                print(f"   📦 Package managers: {', '.join(system_deps['package_managers'])}")


def demo_tracker():
    """Demonstrate cross-repository dependency tracking."""
    print("\n\n🔗 Cross-Repository Dependency Tracking")
    print("=" * 50)
    
    tracker = DependencyTracker("/opt/openproject")
    
    # Find version conflicts
    print("\n⚠️  Checking for version conflicts...")
    conflicts = tracker.find_version_conflicts()
    
    if conflicts:
        print(f"Found {len(conflicts)} version conflicts:")
        for dep_name, usages in conflicts.items():
            print(f"\n   {dep_name}:")
            for usage in usages:
                print(f"      {usage['repository']}: {usage['requirement']}")
    else:
        print("   ✅ No version conflicts detected")
        
    # Find shared dependencies
    print("\n🔄 Checking for shared dependencies...")
    shared_deps = tracker.find_shared_dependencies()
    
    if shared_deps:
        print(f"Found {len(shared_deps)} shared dependencies:")
        for dep_name, repos in shared_deps.items():
            if len(repos) >= 2:  # Show dependencies used in 2+ repos
                print(f"   {dep_name}: {', '.join(repos)}")
    else:
        print("   No shared dependencies found")
        
    # Compatibility check
    print("\n🧪 Overall compatibility assessment...")
    compatibility = tracker.check_compatibility()
    
    print(f"   Total repositories: {compatibility['total_repositories']}")
    print(f"   Python repositories: {compatibility['python_repositories']}")
    print(f"   Docker repositories: {compatibility['docker_repositories']}")
    print(f"   Version conflicts: {len(compatibility['version_conflicts'])}")
    print(f"   Shared dependencies: {len(compatibility['shared_dependencies'])}")


def main():
    """Run the dependency manager demonstration."""
    print("🚀 OpenProject Dependency Manager Demonstration")
    print("=" * 60)
    print()
    
    try:
        demo_analyzer()
        demo_tracker()
        
        print("\n\n🎉 Demonstration completed successfully!")
        print("\nThe dependency manager provides:")
        print("• Repository-level dependency analysis")
        print("• Cross-repository version conflict detection")
        print("• Shared dependency identification")
        print("• Unified installation and management")
        print("• Security and license validation")
        print("• CLI interface for all operations")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()