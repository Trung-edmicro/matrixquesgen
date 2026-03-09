"""
Auto-update module for MatrixQuesGen
Checks for updates from GitHub Releases and downloads/installs new setup.exe
"""
import sys
import os
import requests
import subprocess
import tempfile
import logging
import threading
from pathlib import Path
from typing import Callable, Optional
from version import __version__, __app_name__

# GitHub repository info — fall back to the published repo if env var is not set
_GITHUB_REPO_DEFAULT = "Trung-edmicro/matrixquesgen"


def _github_api_url() -> str:
    """Build the GitHub API URL at call-time so env vars loaded after import are respected."""
    repo = os.getenv("GITHUB_REPO") or _GITHUB_REPO_DEFAULT
    return f"https://api.github.com/repos/{repo}/releases/latest"

# Global progress state (for API polling)
_update_state = {
    "status": "idle",       # idle | checking | available | downloading | installing | up_to_date | error
    "progress": 0,          # 0-100
    "message": "",
    "latest_version": None,
    "changelog": "",
    "download_url": None,
    "error": None,
}

_update_lock = threading.Lock()


def _set_state(**kwargs):
    with _update_lock:
        _update_state.update(kwargs)


def get_state() -> dict:
    with _update_lock:
        return dict(_update_state)


class Updater:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_dir = (
            Path(sys.executable).parent
            if getattr(sys, "frozen", False)
            else Path(__file__).parent
        )
        self.temp_dir = Path(tempfile.gettempdir()) / "matrixquesgen_update"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_for_update(self) -> dict:
        """Check if a newer version is available on GitHub Releases."""
        _set_state(status="checking", progress=0, message="Dang kiem tra phien ban moi...", error=None)
        try:
            headers = {"Accept": "application/vnd.github+json"}
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"Bearer {github_token}"

            response = requests.get(_github_api_url(), headers=headers, timeout=15)
            response.raise_for_status()
            release = response.json()

            latest_version = release["tag_name"].lstrip("v")
            current_version = __version__

            download_url = self._get_setup_download_url(release)

            if self._is_newer(latest_version, current_version):
                self.logger.info(f"New version available: {latest_version}")
                _set_state(
                    status="available",
                    progress=0,
                    message=f"Co phien ban moi: v{latest_version}",
                    latest_version=latest_version,
                    changelog=release.get("body", ""),
                    download_url=download_url,
                )
                return {
                    "available": True,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "changelog": release.get("body", ""),
                    "download_url": download_url,
                }
            else:
                _set_state(
                    status="up_to_date",
                    progress=100,
                    message="Application is using the latest version.",
                    latest_version=latest_version,
                )
                return {
                    "available": False,
                    "current_version": current_version,
                    "latest_version": latest_version,
                }

        except Exception as exc:
            self.logger.error(f"Check for update failed: {exc}")
            _set_state(status="error", message=str(exc), error=str(exc))
            return {"available": False, "error": str(exc)}

    def download_and_install(
        self,
        download_url: Optional[str] = None,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> bool:
        """Download new setup installer and run it silently."""
        state = get_state()
        url = download_url or state.get("download_url")
        if not url:
            _set_state(status="error", message="Khong tim thay URL tai xuong.", error="No download URL")
            return False

        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            latest_version = state.get("latest_version", "new")
            installer_path = self.temp_dir / f"{__app_name__}_Setup_{latest_version}.exe"

            _set_state(status="downloading", progress=0, message="Dang tai ban cap nhat...")
            self.logger.info(f"Downloading update from {url}")

            headers = {}
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"Bearer {github_token}"

            response = requests.get(url, headers=headers, stream=True, timeout=120)
            response.raise_for_status()

            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(installer_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = int(downloaded * 100 / total)
                            mb_done = downloaded // 1024 // 1024
                            mb_total = total // 1024 // 1024
                            msg = f"Dang tai... {mb_done} MB / {mb_total} MB"
                            _set_state(progress=pct, message=msg)
                            if on_progress:
                                on_progress(pct, msg)

            _set_state(progress=100, message="Tai xong, dang cai dat...", status="installing")
            self.logger.info(f"Download complete: {installer_path}")

            # Launch installer with /FORCECLOSEAPPLICATIONS so it can replace
            # the running exe without showing the "close applications" dialog.
            # Give the UI a moment to show the "installing" status, then exit
            # this process so the installer can overwrite MatrixQuesGen.exe.
            subprocess.Popen(
                [str(installer_path), "/SILENT", "/FORCECLOSEAPPLICATIONS"],
                creationflags=getattr(subprocess, "DETACHED_PROCESS", 8),
            )
            _set_state(message="Trinh cai dat da khoi dong. Ung dung dang tu dong tat de cap nhat...")

            # Shut down this process after a short delay so the browser tab
            # has time to read the final status before the server disappears.
            def _exit_after_delay():
                import time
                time.sleep(2)
                os._exit(0)

            threading.Thread(target=_exit_after_delay, daemon=True).start()
            return True

        except Exception as exc:
            self.logger.error(f"Download/install failed: {exc}")
            _set_state(status="error", message=str(exc), error=str(exc))
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        def parse(v: str):
            try:
                return [int(x) for x in v.split(".")]
            except Exception:
                return [0]

        l_parts = parse(latest)
        c_parts = parse(current)
        max_len = max(len(l_parts), len(c_parts))
        l_parts += [0] * (max_len - len(l_parts))
        c_parts += [0] * (max_len - len(c_parts))
        return l_parts > c_parts

    @staticmethod
    def _get_setup_download_url(release_data: dict) -> Optional[str]:
        """Prefer *_Setup*.exe or *_Installer*.exe asset."""
        assets = release_data.get("assets", [])
        for asset in assets:
            name = asset["name"].lower()
            if asset["name"].endswith(".exe") and ("setup" in name or "install" in name):
                return asset["browser_download_url"]
        for asset in assets:
            if asset["name"].endswith(".exe"):
                return asset["browser_download_url"]
        return None


# ---------------------------------------------------------------------------
# Convenience functions for background thread usage
# ---------------------------------------------------------------------------

_updater_singleton = None


def _get_updater() -> Updater:
    global _updater_singleton
    if _updater_singleton is None:
        _updater_singleton = Updater()
    return _updater_singleton


def check_update_async():
    """Run check_for_update in background thread."""
    def _run():
        _get_updater().check_for_update()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def download_update_async():
    """Run download_and_install in background thread."""
    def _run():
        _get_updater().download_and_install()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def check_and_update():
    updater = Updater()
    info = updater.check_for_update()
    if info.get("available"):
        print(f"New version available: {info['latest_version']} (current: {__version__})")
        print("Downloading update...")
        ok = updater.download_and_install()
        print("Update installer started." if ok else "Update failed.")
        return ok
    else:
        print(f"Up to date (v{__version__}).")
        return False


if __name__ == "__main__":
    check_and_update()
