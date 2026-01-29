"""Test rich content types trong prompt builder"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'server' / 'src'))

from services.generators.prompt_builder_service import PromptBuilderService
from services.core.matrix_parser import MatrixParser

# Load enriched matrix
matrix_path = Path("data/matrix/enriched_matrix_DIALY_KNTT_C12.json")
with open(matrix_path, 'r', encoding='utf-8') as f:
    matrix_data = json.load(f)

print("=" * 60)
print("Testing Rich Content Types in Prompt Builder")
print("=" * 60)

# Find a lesson with TN questions that have rich_content_types
for lesson in matrix_data['lessons']:
    for level in ['NB', 'TH', 'VD']:
        for item in lesson['TN'][level]:
            if 'rich_content_types' in item:
                print(f"\nFound TN question with rich types:")
                print(f"  Lesson: {lesson['lesson_name']}")
                print(f"  Level: {level}")
                print(f"  Codes: {item['code']}")
                print(f"  Rich types: {json.dumps(item['rich_content_types'], ensure_ascii=False, indent=4)}")
                
                # Create a mock QuestionSpec to test formatting
                from services.core.matrix_parser import QuestionSpec
                
                spec = QuestionSpec(
                    lesson_name=lesson['lesson_name'],
                    competency_level=1,
                    cognitive_level=level,
                    question_type='TN',
                    num_questions=item['num'],
                    question_codes=item['code'],
                    learning_outcome=item['learning_outcome'],
                    row_index=0,
                    chapter_number=int(lesson['chapter_number']),
                    supplementary_materials='',
                    rich_content_types=item['rich_content_types']
                )
                
                # Test formatter
                builder = PromptBuilderService(prompt_dir="data/prompts/DIALY_KNTT_C12")
                rich_str = builder._format_rich_content_types(spec)
                
                print(f"\nFormatted for prompt:")
                print(rich_str)
                print("\n" + "=" * 60)
                break
        else:
            continue
        break
    else:
        continue
    break

# Find TLN with rich types
print("\nSearching for TLN with rich types...")
for lesson in matrix_data['lessons']:
    for level in ['NB', 'TH', 'VD']:
        for item in lesson['TLN'][level]:
            if 'rich_content_types' in item:
                print(f"\nFound TLN question with rich types:")
                print(f"  Lesson: {lesson['lesson_name']}")
                print(f"  Level: {level}")
                print(f"  Codes: {item['code']}")
                print(f"  Rich types: {json.dumps(item['rich_content_types'], ensure_ascii=False, indent=4)}")
                
                # Test formatter
                from services.core.matrix_parser import QuestionSpec
                spec = QuestionSpec(
                    lesson_name=lesson['lesson_name'],
                    competency_level=1,
                    cognitive_level=level,
                    question_type='TLN',
                    num_questions=item['num'],
                    question_codes=item['code'],
                    learning_outcome=item['learning_outcome'],
                    row_index=0,
                    chapter_number=int(lesson['chapter_number']),
                    supplementary_materials='',
                    rich_content_types=item['rich_content_types']
                )
                
                rich_str = builder._format_rich_content_types(spec)
                print(f"\nFormatted for prompt:")
                print(rich_str)
                print("\n" + "=" * 60)
                break
        else:
            continue
        break
    else:
        continue
    break
