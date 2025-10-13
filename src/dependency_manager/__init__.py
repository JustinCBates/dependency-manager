"""
Dependency Manager for OpenProject Multi-Repository Environment.

A comprehensive tool for managing dependencies across multiple repositories
with unified analysis, tracking, installation, and validation capabilities.
"""

__version__ = "0.1.0"
__author__ = "OpenProject Team"

from .analyzers import RepositoryAnalyzer
from .trackers import DependencyTracker
from .installers import DependencyInstaller
from .validators import DependencyValidator

__all__ = [
    "RepositoryAnalyzer",
    "DependencyTracker", 
    "DependencyInstaller",
    "DependencyValidator"
]