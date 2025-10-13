#!/usr/bin/env python3
"""
Dependency Migration Tool - Consolidate shared dependency scripts.

Migrates dependency management scripts from multiple repositories
into the centralized dependency-manager system.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class DependencyMigrator:
    """Migrate and consolidate dependency management across repositories."""
    
    def __init__(self, workspace_path: str = "/opt/openproject"):
        self.workspace_path = Path(workspace_path)
        self.dependency_manager_path = self.workspace_path / "external" / "dependency-manager"
        self.migration_log = []
        
    def discover_dependency_scripts(self) -> Dict[str, List[Path]]:
        """Discover all dependency-related scripts across repositories."""
        scripts = {
            "install_scripts": [],
            "check_scripts": [],
            "requirement_files": [],
            "setup_scripts": [],
            "other_scripts": []
        }
        
        # Search patterns
        patterns = {
            "install_scripts": ["**/install_deps*", "**/install-deps*", "**/install_*deps*"],
            "check_scripts": ["**/check_deps*", "**/check-deps*", "**/deps_check*"],
            "requirement_files": ["**/requirements*.txt", "**/deps*.txt"],
            "setup_scripts": ["**/setup_deps*", "**/setup-deps*", "**/deps_setup*"],
            "other_scripts": ["**/manage_deps*", "**/deps_*", "**/dependency_*"]
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                for file_path in self.workspace_path.glob(pattern):
                    if file_path.exists() and file_path.is_file():
                        # Skip files already in dependency-manager
                        if "dependency-manager" not in str(file_path):
                            scripts[category].append(file_path)
                            
        return scripts
        
    def analyze_script_content(self, script_path: Path) -> Dict[str, Any]:
        """Analyze a script to understand its purpose and dependencies."""
        analysis = {
            "path": str(script_path),
            "type": "unknown",
            "language": script_path.suffix.lower(),
            "dependencies": [],
            "functionality": [],
            "repository": None
        }
        
        # Determine repository
        parts = script_path.parts
        if "external" in parts:
            repo_index = parts.index("external") + 1
            if repo_index < len(parts):
                analysis["repository"] = parts[repo_index]
        else:
            analysis["repository"] = "main"
            
        try:
            with open(script_path, 'r') as f:
                content = f.read()
                
            # Analyze content based on language
            if script_path.suffix in ['.py']:
                analysis.update(self._analyze_python_script(content))
            elif script_path.suffix in ['.sh', '.bash']:
                analysis.update(self._analyze_shell_script(content))
            elif script_path.suffix in ['.txt']:
                analysis.update(self._analyze_requirements_file(content))
                
        except Exception as e:
            analysis["error"] = str(e)
            
        return analysis
        
    def _analyze_python_script(self, content: str) -> Dict[str, Any]:
        """Analyze Python script content."""
        analysis = {
            "type": "python",
            "dependencies": [],
            "functionality": []
        }
        
        # Look for import statements
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                analysis["dependencies"].append(line)
                
        # Look for pip install commands
        if 'pip install' in content:
            analysis["functionality"].append("pip_installer")
        if 'subprocess' in content and ('install' in content or 'pip' in content):
            analysis["functionality"].append("subprocess_installer")
        if 'requirements' in content.lower():
            analysis["functionality"].append("requirements_handler")
        if 'virtual' in content.lower() or 'venv' in content.lower():
            analysis["functionality"].append("virtualenv_manager")
            
        return analysis
        
    def _analyze_shell_script(self, content: str) -> Dict[str, Any]:
        """Analyze shell script content."""
        analysis = {
            "type": "shell", 
            "dependencies": [],
            "functionality": []
        }
        
        # Look for command usage
        if 'docker' in content.lower():
            analysis["functionality"].append("docker_handler")
        if 'pip install' in content:
            analysis["functionality"].append("pip_installer")
        if 'apt install' in content or 'yum install' in content:
            analysis["functionality"].append("system_installer")
        if 'command_exists' in content or 'which ' in content:
            analysis["functionality"].append("dependency_checker")
        if 'git' in content.lower():
            analysis["functionality"].append("git_handler")
            
        return analysis
        
    def _analyze_requirements_file(self, content: str) -> Dict[str, Any]:
        """Analyze requirements file content."""
        analysis = {
            "type": "requirements",
            "dependencies": [],
            "functionality": ["dependency_list"]
        }
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                analysis["dependencies"].append(line)
                
        return analysis
        
    def create_migration_plan(self) -> Dict[str, Any]:
        """Create a comprehensive migration plan."""
        scripts = self.discover_dependency_scripts()
        migration_plan = {
            "discovered_scripts": len(sum(scripts.values(), [])),
            "categories": {},
            "consolidation_strategy": {},
            "actions": []
        }
        
        for category, script_list in scripts.items():
            if script_list:
                migration_plan["categories"][category] = []
                for script_path in script_list:
                    analysis = self.analyze_script_content(script_path)
                    migration_plan["categories"][category].append(analysis)
                    
        # Plan consolidation strategy
        migration_plan["consolidation_strategy"] = {
            "install_scripts": "Merge into dependency_installer.py enhanced functionality",
            "check_scripts": "Integrate into repository_analyzer.py validation",
            "requirement_files": "Parse and integrate into unified lockfile system",
            "setup_scripts": "Consolidate into CLI setup commands",
            "other_scripts": "Evaluate for integration or deprecation"
        }
        
        # Plan specific actions
        migration_plan["actions"] = [
            {
                "action": "backup_existing_scripts",
                "description": "Create backup of all discovered scripts before migration"
            },
            {
                "action": "enhance_dependency_installer", 
                "description": "Add functionality from scattered install scripts"
            },
            {
                "action": "enhance_repository_analyzer",
                "description": "Add validation logic from check scripts"
            },
            {
                "action": "create_unified_setup",
                "description": "Create single setup command for all repositories"
            },
            {
                "action": "update_documentation",
                "description": "Update docs to reflect centralized dependency management"
            },
            {
                "action": "deprecate_old_scripts",
                "description": "Mark old scripts as deprecated with migration notices"
            }
        ]
        
        return migration_plan
        
    def backup_scripts(self, scripts: Dict[str, List[Path]]) -> Path:
        """Create backup of existing scripts before migration."""
        backup_dir = self.dependency_manager_path / "migration_backup"
        backup_dir.mkdir(exist_ok=True)
        
        for category, script_list in scripts.items():
            if script_list:
                category_backup = backup_dir / category
                category_backup.mkdir(exist_ok=True)
                
                for script_path in script_list:
                    # Create unique backup name
                    repo_name = self._get_repo_name(script_path)
                    backup_name = f"{repo_name}_{script_path.name}"
                    backup_path = category_backup / backup_name
                    
                    shutil.copy2(script_path, backup_path)
                    self.migration_log.append(f"Backed up: {script_path} -> {backup_path}")
                    
        return backup_dir
        
    def _get_repo_name(self, script_path: Path) -> str:
        """Get repository name from script path."""
        parts = script_path.parts
        if "external" in parts:
            repo_index = parts.index("external") + 1
            if repo_index < len(parts):
                return parts[repo_index]
        return "main"
        
    def create_deprecation_notices(self, scripts: Dict[str, List[Path]]):
        """Create deprecation notices for old scripts."""
        notice_template = """#!/bin/bash
# DEPRECATED: This script has been migrated to the centralized dependency-manager
# 
# New location: /opt/openproject/external/dependency-manager
# New command: dependency-manager {command}
#
# Please use the new centralized system:
#   cd /opt/openproject/external/dependency-manager
#   python3 -m dependency_manager.cli {command}
#
# This script will be removed in a future version.

echo "⚠️  DEPRECATED: This script has been replaced by the centralized dependency-manager"
echo "📍 New location: /opt/openproject/external/dependency-manager"
echo "🚀 New command: dependency-manager {command}"
echo ""
echo "Please update your workflows to use the new system."
echo "See README.md in dependency-manager for migration guide."
exit 1
"""
        
        python_notice_template = '''#!/usr/bin/env python3
"""
DEPRECATED: This script has been migrated to the centralized dependency-manager

New location: /opt/openproject/external/dependency-manager
New command: dependency-manager {command}

Please use the new centralized system:
    cd /opt/openproject/external/dependency-manager
    python3 -m dependency_manager.cli {command}

This script will be removed in a future version.
"""

import sys

print("⚠️  DEPRECATED: This script has been replaced by the centralized dependency-manager")
print("📍 New location: /opt/openproject/external/dependency-manager") 
print("🚀 New command: dependency-manager {command}")
print("")
print("Please update your workflows to use the new system.")
print("See README.md in dependency-manager for migration guide.")
sys.exit(1)
'''
        
        for category, script_list in scripts.items():
            for script_path in script_list:
                if script_path.suffix == '.py':
                    notice_content = python_notice_template.format(
                        command=self._suggest_command(script_path.name)
                    )
                else:
                    notice_content = notice_template.format(
                        command=self._suggest_command(script_path.name)
                    )
                    
                # Create .deprecated file alongside original
                deprecated_path = script_path.with_suffix(script_path.suffix + '.deprecated')
                with open(deprecated_path, 'w') as f:
                    f.write(notice_content)
                    
                self.migration_log.append(f"Created deprecation notice: {deprecated_path}")
                
    def _suggest_command(self, script_name: str) -> str:
        """Suggest new dependency-manager command for old script."""
        name_lower = script_name.lower()
        
        if 'install' in name_lower:
            return 'install'
        elif 'check' in name_lower:
            return 'validate'
        elif 'setup' in name_lower:
            return 'create-venv'
        else:
            return 'analyze'
            
    def generate_migration_report(self) -> str:
        """Generate comprehensive migration report."""
        scripts = self.discover_dependency_scripts()
        migration_plan = self.create_migration_plan()
        
        report = "# Dependency Management Migration Report\n\n"
        
        # Summary
        total_scripts = sum(len(script_list) for script_list in scripts.values())
        report += f"## Summary\n"
        report += f"- **Total scripts discovered**: {total_scripts}\n"
        report += f"- **Repositories affected**: {len(set(self._get_repo_name(s) for script_list in scripts.values() for s in script_list))}\n"
        report += f"- **Script categories**: {len([k for k, v in scripts.items() if v])}\n\n"
        
        # Scripts by category
        for category, script_list in scripts.items():
            if script_list:
                report += f"### {category.replace('_', ' ').title()}\n"
                for script_path in script_list:
                    analysis = self.analyze_script_content(script_path)
                    repo = analysis.get('repository', 'unknown')
                    functionality = ', '.join(analysis.get('functionality', []))
                    report += f"- `{script_path}` ({repo}) - {functionality}\n"
                report += "\n"
                
        # Consolidation strategy
        report += "## Consolidation Strategy\n\n"
        for category, strategy in migration_plan["consolidation_strategy"].items():
            if scripts.get(category):
                report += f"**{category.replace('_', ' ').title()}**: {strategy}\n\n"
                
        # Actions required
        report += "## Migration Actions\n\n"
        for i, action in enumerate(migration_plan["actions"], 1):
            report += f"{i}. **{action['action'].replace('_', ' ').title()}**\n"
            report += f"   {action['description']}\n\n"
            
        return report
        
    def execute_migration(self, dry_run: bool = True) -> bool:
        """Execute the complete migration process."""
        print("🚀 Starting dependency management migration...")
        
        # Discover scripts
        scripts = self.discover_dependency_scripts()
        total_scripts = sum(len(script_list) for script_list in scripts.values())
        
        if total_scripts == 0:
            print("✅ No additional scripts found to migrate")
            return True
            
        print(f"📋 Found {total_scripts} scripts to migrate")
        
        if dry_run:
            print("🔍 DRY RUN: Showing what would be done...")
            migration_plan = self.create_migration_plan()
            
            for action in migration_plan["actions"]:
                print(f"   • {action['action']}: {action['description']}")
                
            print("\nRun with --execute to perform actual migration")
            return True
            
        # Execute actual migration
        try:
            # 1. Backup existing scripts
            backup_dir = self.backup_scripts(scripts)
            print(f"✅ Backed up scripts to: {backup_dir}")
            
            # 2. Create deprecation notices
            self.create_deprecation_notices(scripts)
            print("✅ Created deprecation notices")
            
            # 3. Log migration
            with open(self.dependency_manager_path / "MIGRATION_LOG.md", 'w') as f:
                f.write(self.generate_migration_report())
                f.write("\n## Migration Log\n\n")
                for log_entry in self.migration_log:
                    f.write(f"- {log_entry}\n")
                    
            print("✅ Migration completed successfully")
            print(f"📄 See MIGRATION_LOG.md for details")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate dependency management scripts")
    parser.add_argument("--workspace", default="/opt/openproject", 
                       help="Workspace path")
    parser.add_argument("--execute", action="store_true",
                       help="Execute migration (default is dry run)")
    parser.add_argument("--report-only", action="store_true",
                       help="Generate report only")
    
    args = parser.parse_args()
    
    migrator = DependencyMigrator(args.workspace)
    
    if args.report_only:
        print(migrator.generate_migration_report())
        return
        
    success = migrator.execute_migration(dry_run=not args.execute)
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()