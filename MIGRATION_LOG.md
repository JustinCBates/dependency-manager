# Dependency Management Migration Report

## Summary
- **Total scripts discovered**: 8
- **Repositories affected**: 2
- **Script categories**: 3

### Install Scripts
- `/opt/openproject/external/config-manager/dependencies/install_deps.py` (config-manager) - pip_installer, subprocess_installer
- `/opt/openproject/external/config-manager/dependencies/install_deps.py.deprecated` (config-manager) - 
- `/opt/openproject/external/config-manager/dependencies/install_deps.py` (config-manager) - pip_installer, subprocess_installer
- `/opt/openproject/external/config-manager/dependencies/install_deps.py.deprecated` (config-manager) - 

### Check Scripts
- `/opt/openproject/dependencies/check_deps.sh.deprecated` (main) - 
- `/opt/openproject/dependencies/check_deps.sh` (main) - docker_handler, system_installer, dependency_checker, git_handler

### Other Scripts
- `/opt/openproject/external/config-manager/src/openproject_config_manager.egg-info/dependency_links.txt` (config-manager) - dependency_list
- `/opt/openproject/external/config-manager/src/openproject_config_manager.egg-info/dependency_links.txt.deprecated` (config-manager) - 

## Consolidation Strategy

**Install Scripts**: Merge into dependency_installer.py enhanced functionality

**Check Scripts**: Integrate into repository_analyzer.py validation

**Other Scripts**: Evaluate for integration or deprecation

## Migration Actions

1. **Backup Existing Scripts**
   Create backup of all discovered scripts before migration

2. **Enhance Dependency Installer**
   Add functionality from scattered install scripts

3. **Enhance Repository Analyzer**
   Add validation logic from check scripts

4. **Create Unified Setup**
   Create single setup command for all repositories

5. **Update Documentation**
   Update docs to reflect centralized dependency management

6. **Deprecate Old Scripts**
   Mark old scripts as deprecated with migration notices


## Migration Log

- Backed up: /opt/openproject/external/config-manager/dependencies/install_deps.py -> /opt/openproject/external/dependency-manager/migration_backup/install_scripts/config-manager_install_deps.py
- Backed up: /opt/openproject/external/config-manager/dependencies/install_deps.py -> /opt/openproject/external/dependency-manager/migration_backup/install_scripts/config-manager_install_deps.py
- Backed up: /opt/openproject/dependencies/check_deps.sh -> /opt/openproject/external/dependency-manager/migration_backup/check_scripts/main_check_deps.sh
- Backed up: /opt/openproject/external/config-manager/src/openproject_config_manager.egg-info/dependency_links.txt -> /opt/openproject/external/dependency-manager/migration_backup/other_scripts/config-manager_dependency_links.txt
- Created deprecation notice: /opt/openproject/external/config-manager/dependencies/install_deps.py.deprecated
- Created deprecation notice: /opt/openproject/external/config-manager/dependencies/install_deps.py.deprecated
- Created deprecation notice: /opt/openproject/dependencies/check_deps.sh.deprecated
- Created deprecation notice: /opt/openproject/external/config-manager/src/openproject_config_manager.egg-info/dependency_links.txt.deprecated
