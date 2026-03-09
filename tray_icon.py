"""
System Tray Icon for MatrixQuesGen
Provides a system tray icon with right-click menu to show logs, open app, and exit.
"""
import os
import sys
import logging
import webbrowser
import threading
import subprocess
from pathlib import Path
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    _TRAY_AVAILABLE = True
except Exception:
    # PIL or pystray not available (not bundled in this build)
    Icon = Menu = MenuItem = None
    Image = ImageDraw = None
    _TRAY_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_default_icon():
    """Create a simple default icon if no icon file is available"""
    # Create a 64x64 icon with a simple "M" letter
    width = 64
    height = 64
    color1 = (52, 152, 219)  # Blue
    color2 = (255, 255, 255)  # White
    
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    
    # Draw a simple "M" shape
    dc.rectangle([10, 10, 54, 54], fill=color1, outline=color2, width=3)
    dc.text((20, 20), "M", fill=color2)
    
    return image


class TrayIcon:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.log_file = self.base_dir / "logs" / "app.log"
        self.icon = None
        self.server_url = "http://localhost:8000"
        
    def get_icon_image(self):
        """Load icon image or create default.
        In a frozen one-file exe, favicon.ico lives in _MEIPASS, not APP_DIR.
        Check both locations.
        """
        candidates = [self.base_dir / "favicon.ico"]
        if getattr(sys, 'frozen', False):
            candidates.insert(0, Path(sys._MEIPASS) / "favicon.ico")
        for icon_path in candidates:
            if icon_path.exists():
                try:
                    img = Image.open(icon_path)
                    img.load()  # force decode now so errors surface here
                    return img.convert('RGBA')
                except Exception as e:
                    logger.warning(f"Could not load icon {icon_path}: {e}")
        return create_default_icon()
    
    def open_app(self, icon=None, item=None):
        """Open the application in browser"""
        webbrowser.open(self.server_url)
    
    def show_logs(self, icon=None, item=None):
        """Open logs file in notepad"""
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_file.write_text("No logs yet.\n")
        try:
            if sys.platform == "win32":
                os.startfile(str(self.log_file))
            else:
                subprocess.run(['xdg-open', str(self.log_file)])
        except Exception as e:
            logger.error(f"Error opening log file: {e}")
    
    def open_logs_folder(self, icon=None, item=None):
        """Open logs folder in explorer"""
        logs_folder = self.base_dir / "logs"
        logs_folder.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(logs_folder))
            else:
                subprocess.run(['xdg-open', str(logs_folder)])
        except Exception as e:
            logger.error(f"Error opening logs folder: {e}")

    def open_data_folder(self, icon=None, item=None):
        """Open data folder in explorer"""
        data_folder = self.base_dir / "data"
        data_folder.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(data_folder))
            else:
                subprocess.run(['xdg-open', str(data_folder)])
        except Exception as e:
            logger.error(f"Error opening data folder: {e}")
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        if icon:
            icon.stop()
        os._exit(0)
    
    def create_menu(self):
        """Create the context menu"""
        return Menu(
            MenuItem("Mở Ứng Dụng", self.open_app, default=True),
            MenuItem("Xem Logs", self.show_logs),
            MenuItem("Mở Thư Mục Logs", self.open_logs_folder),
            MenuItem("Mở Thư Mục Data", self.open_data_folder),
            Menu.SEPARATOR,
            MenuItem("Thoát", self.quit_app)
        )
    
    def run(self):
        """Start the tray icon (must be called in its own thread)."""
        if not _TRAY_AVAILABLE:
            logger.warning("pystray/PIL not available — system tray icon disabled")
            return
        try:
            icon_image = self.get_icon_image()
            logger.info(f"Tray icon image size: {icon_image.size}")
            self.icon = Icon(
                "MatrixQuesGen",
                icon_image,
                "MatrixQuesGen - Quản lý sinh câu hỏi",
                self.create_menu()
            )
            logger.info("Tray icon created, starting message loop...")
            self.icon.run()
        except Exception as e:
            import traceback
            logger.error(f"Tray icon failed: {e}")
            logger.error(traceback.format_exc())


def start_tray_icon(base_dir):
    """Start tray icon in a separate daemon thread."""
    tray = TrayIcon(base_dir)
    thread = threading.Thread(target=tray.run, daemon=True, name="tray-icon")
    thread.start()
    return tray
