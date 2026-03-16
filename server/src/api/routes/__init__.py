"""
API routes
"""

# Explicit imports for PyInstaller to detect and bundle all route modules
from . import generate
from . import questions
from . import export
from . import google_drive
from . import regenerate
from . import images

__all__ = [
    'generate',
    'questions', 
    'export',
    'google_drive',
    'regenerate',
    'images'
]
