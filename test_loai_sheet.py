"""Test parsing sheet Loại"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'server' / 'src'))

from services.core.matrix_parser import MatrixParser

# Load matrix
parser = MatrixParser()
parser.load_excel(r"E:\App\matrixquesgen\data\input\Ma trận_DIALY_KNTT_C12.xlsx")

# Parse sheet "Loại"
rich_types = parser.parse_rich_content_types_sheet()

print("\n" + "="*60)
print("Rich Content Type Definitions:")
print("="*60)
for code, info in rich_types.items():
    print(f"\n{code}:")
    print(f"  Tên: {info['name']}")
    print(f"  Mô tả: {info['description']}")
