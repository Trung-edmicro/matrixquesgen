"""Debug script to check why rich_content_types not saved"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'server' / 'src'))

from services.core.matrix_parser import MatrixParser

# Load matrix
parser = MatrixParser()
parser.load_excel(r"E:\App\matrixquesgen\data\input\Ma trận_DIALY_KNTT_C12.xlsx")

# Get TN specs
all_specs = parser.get_all_question_specs()

print("TN Specs with rich content types:")
for spec in all_specs['TN']:
    print(f"\n  Lesson: {spec.lesson_name}")
    print(f"  Chapter: {spec.chapter_number}")
    print(f"  Codes: {spec.question_codes}")
    print(f"  Has rich_content_types attr: {hasattr(spec, 'rich_content_types')}")
    if hasattr(spec, 'rich_content_types'):
        print(f"  rich_content_types: {spec.rich_content_types}")
