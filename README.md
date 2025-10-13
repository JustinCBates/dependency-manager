# Dependency Manager

Centralized dependency management system for the OpenProject multi-repository ecosystem.

## 🎯 Purpose

This repository provides unified dependency management across all OpenProject repositories:
- **Centralized tooling** for dependency analysis and management
- **Cross-repository** dependency tracking and validation
- **Shared scripts** for installation, updates, and vulnerability scanning
- **Version management** and compatibility checking
- **Documentation** of the overall dependency landscape

## 🏗️ Architecture

```
dependency-manager/
├── src/dependency_manager/
│   ├── analyzers/          # Dependency analysis tools
│   ├── installers/         # Installation automation
│   ├── trackers/           # Cross-repo dependency tracking
│   └── validators/         # Compatibility and security validation
├── scripts/                # Shared dependency scripts
├── configs/                # Shared configuration templates
├── docs/                   # Dependency documentation
└── tools/                  # CLI utilities
```

## 🚀 Features

### Dependency Analysis
- **Multi-language support**: Python, JavaScript, Docker, system packages
- **Vulnerability scanning**: Security audit across all repositories
- **Version compatibility**: Check for conflicts between repositories
- **Dependency graphs**: Visualize the dependency landscape

### Cross-Repository Management
- **Unified updates**: Update dependencies across all repos
- **Consistency checking**: Ensure compatible versions
- **Shared configurations**: Common dependency patterns
- **Lock file management**: Coordinated version locking

### Automation Tools
- **Batch installation**: Install dependencies across all repos
- **Update automation**: Automated dependency updates with testing
- **CI/CD integration**: Integration with build pipelines
- **Notification system**: Alert on security vulnerabilities

## 📦 Usage

### CLI Interface
```bash
# Analyze dependencies across all repositories
dependency-manager analyze --all

# Check for vulnerabilities
dependency-manager audit --security

# Update dependencies in specific repos
dependency-manager update --repos config-manager,deploy-manager

# Generate dependency report
dependency-manager report --format html
```

### Python API
```python
from dependency_manager import RepositoryAnalyzer, DependencyTracker

# Analyze a single repository
analyzer = RepositoryAnalyzer("/path/to/repo")
report = analyzer.analyze()

# Track cross-repo dependencies
tracker = DependencyTracker()
conflicts = tracker.check_conflicts()
```

## 🔧 Installation

```bash
git clone https://github.com/JustinCBates/dependency-manager.git
cd dependency-manager
pip install -e .
```

## 📚 Repository Integration

Each repository maintains its own core dependency files:
- `pyproject.toml` - Python dependencies
- `package.json` - Node.js dependencies  
- `Dockerfile` - Container dependencies

The dependency-manager provides:
- Shared tooling and scripts
- Cross-repository analysis
- Centralized vulnerability scanning
- Version compatibility checking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add dependency management functionality
4. Test across multiple OpenProject repositories
5. Submit a pull request

---

**Part of the OpenProject multi-repository ecosystem**