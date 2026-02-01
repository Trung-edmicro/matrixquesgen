"""
Test configuration for source display
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config

# Test các môn học
subjects = ["LICHSU", "GDKTPL", "HOA", "LY"]

print("Kiểm tra cấu hình hiển thị source theo môn học:")
print("=" * 60)

for subject in subjects:
    should_display = Config.should_display_source(subject)
    status = "✅ Hiển thị source" if should_display else "❌ Không hiển thị source"
    print(f"{subject:15} -> {status}")

print("\nDanh sách môn hiển thị source:")
print(Config.SUBJECTS_WITH_SOURCE_DISPLAY)
