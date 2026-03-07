"""
Runtime hook: ensure sys._MEIPASS is at the front of sys.path.
Runs before any user code in the frozen exe.
This guarantees that packages copied as .py source files to _MEIPASS
(uvicorn, fastapi, starlette, etc.) are found before anything else.
"""
import sys
import os

if hasattr(sys, '_MEIPASS') and sys._MEIPASS not in sys.path:
    sys.path.insert(0, sys._MEIPASS)
