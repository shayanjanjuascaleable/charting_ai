"""
Path utilities for backend module.
Provides centralized path definitions for the project structure.
"""
from pathlib import Path

# Project root: parent of backend/ directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directory paths
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"


def data_path(*parts):
    """
    Helper function to construct paths within the data directory.
    
    Args:
        *parts: Path components to join
        
    Returns:
        Path: Absolute path within data directory
        
    Example:
        data_path('charting_ai.db') -> BACKEND_DIR/data/charting_ai.db
        data_path('backups', 'old.db') -> BACKEND_DIR/data/backups/old.db
    """
    return DATA_DIR.joinpath(*parts)

