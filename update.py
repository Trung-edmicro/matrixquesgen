"""
Auto-update module for MatrixQuesGen
Checks for updates from GitHub Releases and downloads new version
"""
import sys
import os
import json
import requests
import subprocess
import tempfile
import logging
from pathlib import Path
from version import __version__, __app_name__

# GitHub repository info
# Replace with your actual GitHub repo
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class Updater:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        self.temp_dir = Path(tempfile.gettempdir()) / "matrixquesgen_update"

    def check_for_update(self):
        """Check if there's a newer version available"""
        try:
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            latest_version = release_data['tag_name'].lstrip('v')
            current_version = __version__

            if self._is_newer_version(latest_version, current_version):
                self.logger.info(f"New version available: {latest_version} (current: {current_version})")
                return {
                    'available': True,
                    'version': latest_version,
                    'url': self._get_download_url(release_data),
                    'changelog': release_data.get('body', '')
                }
            else:
                self.logger.info("Application is up to date")
                return {'available': False}

        except Exception as e:
            self.logger.error(f"Failed to check for updates: {e}")
            return {'available': False, 'error': str(e)}

    def _is_newer_version(self, latest, current):
        """Compare version strings"""
        def parse_version(v):
            return [int(x) for x in v.split('.')]

        try:
            latest_parts = parse_version(latest)
            current_parts = parse_version(current)

            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return latest_parts > current_parts
        except:
            return False

    def _get_download_url(self, release_data):
        """Get the download URL for the exe file"""
        for asset in release_data.get('assets', []):
            if asset['name'].endswith('.exe'):
                return asset['browser_download_url']
        return None

    def download_and_install(self, update_info):
        """Download and install the update"""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)

            # Download the new exe
            url = update_info['url']
            if not url:
                raise Exception("No download URL found")

            self.logger.info(f"Downloading update from {url}")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            exe_path = self.temp_dir / f"{__app_name__}_{update_info['version']}.exe"
            with open(exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Create update script
            update_script = self._create_update_script(exe_path, update_info['version'])
            self.logger.info("Update downloaded successfully")

            # Run update script
            subprocess.Popen([sys.executable, update_script], creationflags=subprocess.CREATE_NO_WINDOW)
            return True

        except Exception as e:
            self.logger.error(f"Failed to download/install update: {e}")
            return False

    def _create_update_script(self, new_exe_path, new_version):
        """Create a script to replace the current exe and restart"""
        script_content = f'''
import sys
import os
import time
import shutil
import subprocess
from pathlib import Path

def main():
    current_exe = Path(r"{sys.executable}")
    new_exe = Path(r"{new_exe_path}")
    backup_exe = current_exe.with_suffix('.bak')

    try:
        # Wait for current process to exit
        time.sleep(2)

        # Backup current exe
        if current_exe.exists():
            shutil.copy2(current_exe, backup_exe)

        # Replace exe
        shutil.move(str(new_exe), str(current_exe))

        # Start new version
        subprocess.Popen([str(current_exe)], creationflags=subprocess.CREATE_NO_WINDOW)

        print(f"Updated to version {new_version}")

    except Exception as e:
        print(f"Update failed: {{e}}")
        # Restore backup if exists
        if backup_exe.exists():
            shutil.move(str(backup_exe), str(current_exe))

if __name__ == "__main__":
    main()
'''

        script_path = self.temp_dir / "update_runner.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return script_path

def check_and_update():
    """Main function to check and perform update"""
    updater = Updater()
    update_info = updater.check_for_update()

    if update_info.get('available'):
        print(f"New version available: {update_info['version']}")
        print("Downloading update...")

        if updater.download_and_install(update_info):
            print("Update downloaded. Application will restart.")
            return True
        else:
            print("Update failed.")
            return False
    else:
        print("No updates available.")
        return False

if __name__ == "__main__":
    check_and_update()