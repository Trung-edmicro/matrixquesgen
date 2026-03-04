"""
Update API routes – exposes GitHub Releases check/download to the UI.
"""
import sys
import os
from pathlib import Path

# Ensure project root (where update.py / version.py live) is on sys.path.
# In a frozen PyInstaller exe, _MEIPASS is added automatically.
# In dev mode, add the project root explicitly.
if not getattr(sys, "frozen", False):
    _project_root = Path(__file__).parent.parent.parent.parent.parent  # routes -> api -> src -> server -> root
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

try:
    import update as _update_module
    _update_available = True
except ImportError:
    _update_available = False

try:
    from version import __version__, __app_name__
except ImportError:
    __version__ = "unknown"
    __app_name__ = "MatrixQuesGen"

router = APIRouter(prefix="/api/update", tags=["Update"])


@router.get("/version")
async def get_version():
    """Return current app version."""
    return {"version": __version__, "app_name": __app_name__}


@router.post("/check")
async def check_for_update(background_tasks: BackgroundTasks):
    """
    Trigger an async update check.
    Returns immediately; poll GET /api/update/status for results.
    """
    if not _update_available:
        return JSONResponse(
            {"error": "Update module not available (dev mode)"},
            status_code=503,
        )
    background_tasks.add_task(_update_module.check_update_async)
    _update_module._set_state(
        status="checking", progress=0, message="Đang kiểm tra phiên bản mới…", error=None
    )
    return {"message": "Đang kiểm tra cập nhật…"}


@router.post("/download")
async def download_update(background_tasks: BackgroundTasks):
    """
    Trigger async download + install of the latest release.
    Only valid after /check returned available=true.
    """
    if not _update_available:
        return JSONResponse(
            {"error": "Update module not available (dev mode)"},
            status_code=503,
        )
    state = _update_module.get_state()
    if state.get("status") not in ("available",):
        return JSONResponse(
            {"error": "No update available. Run /check first."},
            status_code=400,
        )
    background_tasks.add_task(_update_module.download_update_async)
    return {"message": "Đã bắt đầu tải bản cập nhật…"}


@router.get("/status")
async def get_update_status():
    """
    Poll this endpoint for current update progress.
    Returns state dict: status, progress, message, latest_version, changelog, error.
    """
    if not _update_available:
        return {
            "status": "unavailable",
            "progress": 0,
            "message": "Update module not available (dev mode)",
            "current_version": __version__,
        }
    state = _update_module.get_state()
    state["current_version"] = __version__
    return state
