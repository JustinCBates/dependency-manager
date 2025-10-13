#!/usr/bin/env python3
"""
Test script for dependency-manager without installation.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dependency_manager.analyzers import RepositoryAnalyzer
from dependency_manager.trackers import DependencyTracker


def test_analyzer():
    """Test the repository analyzer."""
    print("Testing RepositoryAnalyzer...")
    
    # Analyze the current dependency-manager repository
    analyzer = RepositoryAnalyzer(".")
    result = analyzer.analyze()
    
    print(f"✅ Analysis completed")
    print(f"   Python dependencies: {'Yes' if result.get('python_dependencies') else 'No'}")
    print(f"   Docker dependencies: {'Yes' if result.get('docker_dependencies') else 'No'}")
    print(f"   System dependencies: {'Yes' if result.get('system_dependencies') else 'No'}")
    
    return result


def test_tracker():
    """Test the dependency tracker."""
    print("\nTesting DependencyTracker...")
    
    # Track dependencies across the workspace
    tracker = DependencyTracker("/opt/openproject")
    repos = tracker.discover_repositories()
    
    print(f"✅ Discovered {len(repos)} repositories:")
    for repo in repos:
        print(f"   - {repo.name}")
        
    return repos


def main():
    """Run basic tests of the dependency manager."""
    print("🧪 Testing Dependency Manager Components\n")
    
    try:
        # Test analyzer
        analysis_result = test_analyzer()
        
        # Test tracker  
        discovered_repos = test_tracker()
        
        print(f"\n✅ All tests passed!")
        print(f"   Found {len(discovered_repos)} repositories in workspace")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()