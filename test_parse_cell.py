"""
Minimal test script for rich content type parsing
Tests only the parse_question_cell logic
"""
import re
from typing import Tuple, List, Dict

def parse_question_cell(cell_value) -> Tuple[int, List[str], Dict[str, List[str]]]:
    """
    Parse question cell from matrix to extract:
    1. Number of questions
    2. Question codes
    3. Rich content types per question code
    
    Examples:
        "1 (C3-[BK])" -> (1, ["C3"], {"C3": ["BK"]})
        "2 (C4-[BD],C5-[BK])" -> (2, ["C4","C5"], {"C4":["BD"], "C5":["BK"]})
        "1 (C1-[BK,TT])" -> (1, ["C1"], {"C1": ["BK","TT"]})
        "2 (C1,2)" -> (2, ["C1","C2"], {})  # Old format
    """
    if not isinstance(cell_value, str):
        cell_value = str(cell_value)
    
    cell_value = cell_value.strip()
    
    if not cell_value or cell_value == 'nan':
        return 0, [], {}
    
    # Try to extract number and content in parentheses
    match = re.match(r'(\d+)\s*\((.*?)\)', cell_value)
    
    if match:
        num_questions = int(match.group(1))
        content = match.group(2).strip()
        
        question_codes = []
        rich_content_types = {}
        
        # Check if content has rich type annotations [BK], [BD], etc
        if '[' in content and ']' in content:
            # New format with rich content types: "C3-[BK]" or "C4-[BD],C5-[BK]"
            # Split by comma, but be careful with commas inside brackets
            parts = []
            current = ""
            bracket_depth = 0
            
            for char in content:
                if char == '[':
                    bracket_depth += 1
                elif char == ']':
                    bracket_depth -= 1
                elif char == ',' and bracket_depth == 0:
                    if current.strip():
                        parts.append(current.strip())
                    current = ""
                    continue
                current += char
            
            if current.strip():
                parts.append(current.strip())
            
            # Parse each part: "C3-[BK]" or "C3-[BK,TT]"
            for part in parts:
                # Pattern: C3-[BK] or C3-[BK,TT]
                part_match = re.match(r'([A-Z]\d+)\s*-\s*\[(.*?)\]', part, re.IGNORECASE)
                if part_match:
                    code = part_match.group(1).upper()
                    types_str = part_match.group(2)
                    # Split types by comma
                    types = [t.strip().upper() for t in types_str.split(',') if t.strip()]
                    
                    question_codes.append(code)
                    rich_content_types[code] = types
        else:
            # Old format: "C1,2" or "C1, C2"
            # Split by comma
            parts = [p.strip() for p in content.split(',')]
            
            for part in parts:
                if part.upper().startswith('C'):
                    question_codes.append(part.upper())
                else:
                    # Assume it's a number to be prefixed with C
                    if part.isdigit():
                        question_codes.append(f"C{part}")
        
        return num_questions, question_codes, rich_content_types
    
    # If no parentheses, might just be a number
    if cell_value.isdigit():
        return int(cell_value), [], {}
    
    return 0, [], {}

def test_parse_question_cell():
    """Test parse_question_cell with rich content types"""
    
    test_cases = [
        ("1 (C3-[BK])", (1, ["C3"], {"C3": ["BK"]})),
        ("2 (C4-[BD],C5-[BK])", (2, ["C4", "C5"], {"C4": ["BD"], "C5": ["BK"]})),
        ("1 (C1-[BK,TT])", (1, ["C1"], {"C1": ["BK", "TT"]})),
        ("1 (C3-[LT])", (1, ["C3"], {"C3": ["LT"]})),
        ("2 (C1,2)", (2, ["C1", "C2"], {})),  # Old format, no rich types
        ("3", (3, [], {})),  # Just a number
        ("1 (C1-[HA])", (1, ["C1"], {"C1": ["HA"]})),  # Image type
        ("2 (C1-[BD,BK],C2-[LT])", (2, ["C1", "C2"], {"C1": ["BD", "BK"], "C2": ["LT"]})),
    ]
    
    print("=" * 60)
    print("Testing parse_question_cell()")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for cell_value, expected in test_cases:
        result = parse_question_cell(cell_value)
        status = "✓" if result == expected else "✗"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Input: '{cell_value}'")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        if result != expected:
            print(f"  MISMATCH!")
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

if __name__ == "__main__":
    test_parse_question_cell()
