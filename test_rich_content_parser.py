"""
Test script for rich content type parsing from matrix
"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add server to path
sys.path.insert(0, str(Path(__file__).parent / 'server' / 'src'))

from services.core.matrix_parser import MatrixParser
from services.phases.phase1_matrix_processing import MatrixProcessingService
import json

def test_parse_question_cell():
    """Test parse_question_cell with rich content types"""
    parser = MatrixParser()
    
    test_cases = [
        ("1 (C3-[BK])", (1, ["C3"], {"C3": ["BK"]})),
        ("2 (C4-[BD],C5-[BK])", (2, ["C4", "C5"], {"C4": ["BD"], "C5": ["BK"]})),
        ("1 (C1-[BK,TT])", (1, ["C1"], {"C1": ["BK", "TT"]})),
        ("1 (C1-[LT])", (1, ["C1"], {"C1": ["LT"]})),
        ("2 (C1,2)", (2, ["C1", "C2"], {})),  # Old format, no rich types
        ("3", (3, [], {})),  # Just a number
    ]
    
    print("=" * 60)
    print("Testing parse_question_cell()")
    print("=" * 60)
    
    for cell_value, expected in test_cases:
        result = parser.parse_question_cell(cell_value)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{cell_value}'")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()

def test_matrix_processing():
    """Test full matrix processing with DIALY matrix"""
    print("=" * 60)
    print("Testing Full Matrix Processing")
    print("=" * 60)
    
    matrix_path = Path(r"E:\App\matrixquesgen\data\input\Ma trận_DIALY_KNTT_C12.xlsx")
    
    if not matrix_path.exists():
        print(f"✗ Matrix file not found: {matrix_path}")
        return
    
    print(f"Loading matrix: {matrix_path}")
    
    service = MatrixProcessingService()
    
    try:
        # Process matrix
        metadata, lessons, drive_paths, all_specs, true_false_specs = service.process_matrix_file(matrix_path)
        
        print(f"\n✓ Matrix processed successfully")
        print(f"  Subject: {metadata.subject}")
        print(f"  Curriculum: {metadata.curriculum}")
        print(f"  Grade: {metadata.grade}")
        print(f"  Lessons: {len(lessons)}")
        
        # Check for rich content types in specs
        print("\n" + "=" * 60)
        print("Checking for Rich Content Types in Question Specs")
        print("=" * 60)
        
        for question_type, specs in all_specs.items():
            print(f"\n{question_type} Questions:")
            rich_count = 0
            for spec in specs:
                # Show lesson info
                lesson_num = getattr(spec, 'lesson_number', None)
                if lesson_num is None:
                    lesson_match = re.search(r'Bài\s*(\d+)', spec.lesson_name, re.IGNORECASE)
                    lesson_num = int(lesson_match.group(1)) if lesson_match else None
                
                print(f"  Chapter: {spec.chapter_number}, Lesson: {lesson_num}, Codes: {spec.question_codes}")
                
                if hasattr(spec, 'rich_content_types') and spec.rich_content_types:
                    rich_count += 1
                    print(f"    ✓ Rich types: {spec.rich_content_types}")
            
            if rich_count == 0:
                print(f"  No rich content types found")
            else:
                print(f"  Total with rich types: {rich_count}/{len(specs)}")
        
        # Save to JSON and check output
        print("\n" + "=" * 60)
        print("Saving to JSON")
        print("=" * 60)
        
        output_path = service.save_matrix_data(metadata, lessons, all_specs, true_false_specs)
        print(f"✓ Saved to: {output_path}")
        
        # Load and check JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)
        
        print("\nChecking JSON for rich_content_types:")
        found_rich = False
        for lesson in matrix_data['lessons']:
            for q_type in ['TN', 'TLN', 'TL']:
                for level in ['NB', 'TH', 'VD']:
                    for item in lesson[q_type][level]:
                        if 'rich_content_types' in item:
                            found_rich = True
                            print(f"  ✓ {q_type}/{level}: {item['code']} -> {item['rich_content_types']}")
            
            for ds_item in lesson['DS']:
                if 'rich_content_types' in ds_item:
                    found_rich = True
                    print(f"  ✓ DS: {ds_item['question_code']} -> {ds_item['rich_content_types']}")
        
        if not found_rich:
            print("  ⚠ No rich_content_types found in JSON output")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parse_question_cell()
    print("\n" * 2)
    test_matrix_processing()
