"""Convert favicon.ico from PNG to proper ICO format if needed."""
from PIL import Image
import os
import sys

src = "favicon.ico"
if not os.path.exists(src):
    print("No favicon.ico found, skipping")
    sys.exit(0)

with open(src, "rb") as f:
    magic = f.read(4)

if magic == b"\x00\x00\x01\x00":
    print("favicon.ico is already a valid ICO, skipping")
    sys.exit(0)

img = Image.open(src).convert("RGBA")
img.save(src, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("Converted favicon.ico to proper ICO format")
