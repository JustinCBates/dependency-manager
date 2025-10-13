#!/usr/bin/env python3
"""
Dependency Manager CLI - Command Line Interface for Multi-Repository Dependency Management.

Provides unified commands for analyzing, tracking, installing, and validating 
dependencies across multiple repositories in the OpenProject workspace.
"""

import argparse
import sys
import json
from pathlib import Path

from .analyzers import RepositoryAnalyzer
from .trackers import DependencyTracker
from .installers import DependencyInstaller
from .validators import DependencyValidator


def analyze_command(args):
    """Analyze dependencies in repositories."""
    if args.repository:
        # Analyze single repository
        analyzer = RepositoryAnalyzer(args.repository)
        result = analyzer.analyze()
        
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            analyzer.generate_report()
    else:
        # Analyze all repositories
        tracker = DependencyTracker(args.workspace)
        repos = tracker.discover_repositories()
        
        for repo_path in repos:
            print(f"\n{'='*60}")
            print(f"Analyzing: {repo_path.name}")
            print('='*60)
            
            analyzer = RepositoryAnalyzer(str(repo_path))
            if args.format == "json":
                result = analyzer.analyze()
                print(json.dumps(result, indent=2))
            else:
                analyzer.generate_report()


def track_command(args):
    """Track dependencies across repositories."""
    tracker = DependencyTracker(args.workspace)
    
    if args.conflicts:
        conflicts = tracker.find_version_conflicts()
        if conflicts:
            print("Version Conflicts Found:")
            for dep_name, usages in conflicts.items():
                print(f"\n{dep_name}:")
                for usage in usages:
                    print(f"  {usage['repository']}: {usage['requirement']}")
        else:
            print("✅ No version conflicts found")
            
    elif args.shared:
        shared = tracker.find_shared_dependencies()
        if shared:
            print("Shared Dependencies:")
            for dep_name, repos in shared.items():
                print(f"  {dep_name}: {', '.join(repos)}")
        else:
            print("No shared dependencies found")
            
    else:
        # Full tracking report
        report = tracker.generate_report(args.format)
        print(report)


def install_command(args):
    """Install dependencies across repositories."""
    installer = DependencyInstaller(args.workspace)
    
    if args.lockfile:
        success = installer.install_from_lockfile(args.lockfile)
    else:
        features = args.features.split(',') if args.features else None
        success = installer.install_dependencies(
            include_dev=args.dev,
            include_optional=args.optional,
            include_system=args.system,
            features=features,
            upgrade=args.upgrade
        )
        
    if success:
        if args.save_lockfile:
            installer.save_lockfile()
        print("✅ Installation completed successfully")
    else:
        print("❌ Installation failed")
        sys.exit(1)


def validate_command(args):
    """Validate dependencies for security and compatibility."""
    validator = DependencyValidator(args.workspace)
    
    if args.security:
        result = validator.check_security_vulnerabilities()
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            vuln_count = result.get("total_vulnerabilities", 0)
            if vuln_count > 0:
                print(f"🚨 Found {vuln_count} security vulnerabilities")
            else:
                print("✅ No known security vulnerabilities")
                
    elif args.licenses:
        result = validator.check_license_compatibility(args.target_license)
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            issues = result.get("total_issues", 0)
            if issues > 0:
                print(f"⚠️ Found {issues} license compatibility issues")
            else:
                print("✅ All licenses are compatible")
                
    elif args.outdated:
        result = validator.check_outdated_packages()
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            total = result.get("total_outdated", 0)
            if total > 0:
                print(f"📦 Found {total} outdated packages")
                major = len(result.get("major_updates", []))
                minor = len(result.get("minor_updates", []))
                patch = len(result.get("patch_updates", []))
                print(f"  Major updates: {major}")
                print(f"  Minor updates: {minor}")
                print(f"  Patch updates: {patch}")
            else:
                print("✅ All packages are up to date")
    else:
        # Full validation report
        report = validator.generate_validation_report(args.format)
        print(report)


def create_venv_command(args):
    """Create a unified virtual environment."""
    installer = DependencyInstaller(args.workspace)
    success = installer.create_virtual_environment(force_recreate=args.force)
    
    if success:
        print("✅ Virtual environment created successfully")
    else:
        print("❌ Failed to create virtual environment")
        sys.exit(1)


def lockfile_command(args):
    """Manage dependency lockfiles."""
    installer = DependencyInstaller(args.workspace)
    
    if args.generate:
        success = installer.save_lockfile(args.filename)
        if success:
            print(f"✅ Lockfile saved to {args.filename}")
        else:
            print("❌ Failed to generate lockfile")
            sys.exit(1)
    elif args.install:
        success = installer.install_from_lockfile(args.filename)
        if success:
            print("✅ Dependencies installed from lockfile")
        else:
            print("❌ Failed to install from lockfile")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dependency Manager for Multi-Repository OpenProject Environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dependency-manager analyze --repository ./my-repo
  dependency-manager track --conflicts
  dependency-manager install --dev --save-lockfile
  dependency-manager validate --security
  dependency-manager create-venv --force
        """
    )
    
    parser.add_argument("--workspace", default=".", 
                       help="Path to workspace directory (default: current directory)")
    parser.add_argument("--format", choices=["json", "summary"], default="summary",
                       help="Output format")
                       
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository dependencies")
    analyze_parser.add_argument("--repository", help="Specific repository to analyze")
    
    # Track command
    track_parser = subparsers.add_parser("track", help="Track dependencies across repositories")
    track_parser.add_argument("--conflicts", action="store_true", 
                             help="Show only version conflicts")
    track_parser.add_argument("--shared", action="store_true",
                             help="Show only shared dependencies")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install dependencies")
    install_parser.add_argument("--dev", action="store_true",
                               help="Include development dependencies")
    install_parser.add_argument("--optional", action="store_true",
                               help="Include optional dependencies")
    install_parser.add_argument("--system", action="store_true",
                               help="Include system dependencies (Docker, Git, etc.)")
    install_parser.add_argument("--features", 
                               help="Comma-separated list of features to install (docker,http,ssl,etc.)")
    install_parser.add_argument("--upgrade", action="store_true",
                               help="Upgrade existing packages")
    install_parser.add_argument("--lockfile", help="Install from specific lockfile")
    install_parser.add_argument("--save-lockfile", action="store_true",
                               help="Save lockfile after installation")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate dependencies")
    validate_parser.add_argument("--security", action="store_true",
                                help="Check for security vulnerabilities")
    validate_parser.add_argument("--licenses", action="store_true",
                                help="Check license compatibility")
    validate_parser.add_argument("--target-license", default="MIT",
                                help="Target license for compatibility check")
    validate_parser.add_argument("--outdated", action="store_true",
                                help="Check for outdated packages")
    
    # Create virtual environment command
    venv_parser = subparsers.add_parser("create-venv", 
                                       help="Create unified virtual environment")
    venv_parser.add_argument("--force", action="store_true",
                            help="Force recreate if environment exists")
    
    # Lockfile command
    lockfile_parser = subparsers.add_parser("lockfile", help="Manage dependency lockfiles")
    lockfile_parser.add_argument("--generate", action="store_true",
                                help="Generate lockfile from current environment")
    lockfile_parser.add_argument("--install", action="store_true",
                                help="Install from lockfile")
    lockfile_parser.add_argument("--filename", default="dependencies.lock.json",
                                help="Lockfile filename")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # Execute command
    try:
        if args.command == "analyze":
            analyze_command(args)
        elif args.command == "track":
            track_command(args)
        elif args.command == "install":
            install_command(args)
        elif args.command == "validate":
            validate_command(args)
        elif args.command == "create-venv":
            create_venv_command(args)
        elif args.command == "lockfile":
            lockfile_command(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.format == "json":
            print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()