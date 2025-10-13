#!/usr/bin/env python3
"""
Simple dependency installer for OpenProject Config Manager.

Installs dependencies based on what's actually needed:
- Absolute/Ad-Hoc (required vs optional)
- Production/Developer (end-user vs development)
"""

import subprocess
import sys
import argparse
from pathlib import Path


def install_production_absolute():
    """Install core production dependencies (always needed)."""
    packages = [
        "click>=8.1.0",
        "rich>=13.0.0", 
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0"
    ]
    
    print("🔧 Installing core production dependencies...")
    return run_pip_install(packages)


def install_developer_absolute():
    """Install core development dependencies."""
    packages = [
        "pytest>=7.0.0",
        "pytest-json-report",
        "black>=23.0.0",
        "flake8>=6.0.0", 
        "mypy>=1.0.0"
    ]
    
    print("🛠️ Installing core development dependencies...")
    return run_pip_install(packages)


def install_production_adhoc(features=None):
    """Install optional production dependencies based on features."""
    if not features:
        features = []
    
    packages = []
    
    if "docker" in features:
        packages.append("docker>=7.0.0")
        print("  + Docker integration")
    
    if "http" in features or "external" in features:
        packages.append("requests>=2.31.0")
        print("  + HTTP/external service support")
    
    if "system" in features or "monitoring" in features:
        packages.extend(["psutil>=5.9.0", "netifaces>=0.11.0"])
        print("  + System monitoring and network discovery")
    
    if "ssl" in features or "crypto" in features:
        packages.append("cryptography>=41.0.0")
        print("  + SSL/cryptography support")
    
    if packages:
        print("🔌 Installing optional production dependencies...")
        return run_pip_install(packages)
    else:
        print("ℹ️ No optional production features requested")
        return True


def install_developer_adhoc(tools=None):
    """Install optional development dependencies based on tools."""
    if not tools:
        tools = []
    
    packages = []
    
    if "coverage" in tools:
        packages.extend(["pytest-cov>=4.0.0", "coverage"])
        print("  + Test coverage analysis")
    
    if "advanced-testing" in tools:
        packages.append("pytest-mock>=3.11.0")
        print("  + Advanced testing with mocks")
    
    if "security" in tools:
        packages.extend(["bandit>=1.7.0", "safety>=2.3.0"])
        print("  + Security analysis tools")
    
    if "docs" in tools:
        packages.append("sphinx>=5.0.0")
        print("  + Documentation generation")
    
    if packages:
        print("🔬 Installing optional development tools...")
        return run_pip_install(packages)
    else:
        print("ℹ️ No optional development tools requested")
        return True


def run_pip_install(packages):
    """Run pip install for a list of packages."""
    if not packages:
        return True
    
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Successfully installed {len(packages)} package(s)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        print(f"   Command: {' '.join(cmd)}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False


def install_from_pyproject():
    """Install using pyproject.toml (development setup)."""
    print("📦 Installing from pyproject.toml...")
    
    cmd = [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Development environment setup complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install from pyproject.toml: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Install dependencies for OpenProject Config Manager")
    
    parser.add_argument("--mode", choices=["production", "development", "minimal"], 
                       default="production", help="Installation mode")
    
    parser.add_argument("--features", nargs="*", 
                       choices=["docker", "http", "external", "system", "monitoring", "ssl", "crypto"],
                       help="Optional production features to enable")
    
    parser.add_argument("--dev-tools", nargs="*",
                       choices=["coverage", "advanced-testing", "security", "docs"], 
                       help="Optional development tools to install")
    
    parser.add_argument("--use-pyproject", action="store_true",
                       help="Install using pyproject.toml instead")
    
    args = parser.parse_args()
    
    print("🚀 OpenProject Config Manager - Dependency Installer")
    print("=" * 50)
    
    if args.use_pyproject:
        success = install_from_pyproject()
        sys.exit(0 if success else 1)
    
    success = True
    
    if args.mode in ["minimal", "production", "development"]:
        # Always install core production dependencies
        if not install_production_absolute():
            success = False
    
    if args.mode == "development":
        # Install core development dependencies
        if not install_developer_absolute():
            success = False
    
    # Install optional production features
    if args.features:
        if not install_production_adhoc(args.features):
            success = False
    
    # Install optional development tools
    if args.dev_tools:
        if not install_developer_adhoc(args.dev_tools):
            success = False
    
    if success:
        print("\n🎉 Dependency installation complete!")
        print("\nNext steps:")
        if args.mode == "development":
            print("  - Run tests: python run_ui_tests.py")
            print("  - Format code: black src tests")
            print("  - Check code: flake8 src tests")
        else:
            print("  - Use the configuration manager: config-manager configure")
    else:
        print("\n⚠️ Some dependencies failed to install")
        print("Check the errors above and try again")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()