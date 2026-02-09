"""
Cross-Lesson DS Helper
Xử lý merge context từ nhiều bài cho câu hỏi Đúng/Sai (DS) có statements nằm ở nhiều bài khác nhau
"""

from typing import Dict, List, Optional, Any
import re


def find_all_ds_statements_across_lessons(
    matrix_data: Dict,
    question_code: str
) -> Dict[str, List[Dict]]:
    """
    Tìm tất cả statements của 1 câu DS across all lessons
    
    Args:
        matrix_data: Full matrix JSON data
        question_code: Mã câu (VD: "C1", "C2")
        
    Returns:
        Dict mapping lesson_key -> list of statements
        {
            "3_6": [{"label": "a", "cognitive_level": "NB", ...}, ...],
            "3_7": [{"label": "c", "cognitive_level": "VD", ...}, ...]
        }
    """
    result = {}
    
    lessons = matrix_data.get('lessons', [])
    
    for lesson in lessons:
        chapter_number = lesson.get('chapter_number', '0')
        lesson_number = lesson.get('lesson_number', '0')
        lesson_key = f"{chapter_number}_{lesson_number}"
        
        ds_specs = lesson.get('DS', [])
        
        for ds_spec in ds_specs:
            # Check if this spec belongs to our question_code
            spec_question_code = ds_spec.get('question_code', '')
            
            if spec_question_code.upper() == question_code.upper():
                statements = ds_spec.get('statements', [])
                if statements:
                    result[lesson_key] = statements
    
    return result


def merge_cross_lesson_ds_context(
    matrix_data: Dict,
    current_chapter: str,
    current_lesson: str,
    question_code: str,
    current_statements: List[Dict],
    current_lesson_data: Dict
) -> Optional[Dict]:
    """
    Merge context từ nhiều bài cho 1 câu DS
    
    Args:
        matrix_data: Full matrix JSON
        current_chapter: Chapter hiện tại
        current_lesson: Lesson hiện tại
        question_code: Mã câu (C1, C2, ...)
        current_statements: Statements hiện có ở bài hiện tại
        current_lesson_data: Lesson data hiện tại
        
    Returns:
        Dict chứa merged data:
        {
            "spec_data": {...},  # DS spec với đủ 4 statements
            "merged_lesson_data": {...},  # Lesson data merged
            "merged_content": "...",  # Content từ tất cả các bài
            "merged_supplementary": "...",  # Supplementary materials merged
            "source_lessons": ["3_6", "3_7", ...]  # Danh sách các bài đã merge
        }
    """
    # Find all statements across lessons
    all_statements_by_lesson = find_all_ds_statements_across_lessons(
        matrix_data, question_code
    )
    
    if not all_statements_by_lesson:
        return None
    
    # Collect all statements
    all_statements = []
    source_lessons = []
    merged_content_parts = []
    merged_supplementary_parts = []
    merged_learning_outcomes = set()
    
    current_lesson_key = f"{current_chapter}_{current_lesson}"
    
    # Find all lessons that contribute to this question
    lessons = matrix_data.get('lessons', [])
    lessons_by_key = {
        f"{l.get('chapter_number', '0')}_{l.get('lesson_number', '0')}": l
        for l in lessons
    }
    
    for lesson_key, statements in all_statements_by_lesson.items():
        source_lessons.append(lesson_key)
        all_statements.extend(statements)
        
        # Get lesson data
        lesson_data = lessons_by_key.get(lesson_key)
        if lesson_data:
            # Collect content
            content = lesson_data.get('content', '')
            if content:
                lesson_name = lesson_data.get('lesson_name', '')
                merged_content_parts.append(f"## {lesson_name}\n\n{content}")
            
            # Collect supplementary materials
            supp = lesson_data.get('supplementary_material', '')
            if supp:
                merged_supplementary_parts.append(supp)
            
            # Collect learning outcomes from statements
            for stmt in statements:
                lo = stmt.get('learning_outcome', '')
                if lo:
                    merged_learning_outcomes.add(lo)
    
    # Sort statements by label (a, b, c, d)
    all_statements.sort(key=lambda x: x.get('label', 'z'))
    
    # Verify we have exactly 4 statements with labels a, b, c, d
    labels = [s.get('label') for s in all_statements]
    if len(labels) != 4 or labels != ['a', 'b', 'c', 'd']:
        print(f"  ⚠️  DS {question_code}: Found {len(labels)} statements {labels}, expected ['a', 'b', 'c', 'd']")
        # Don't merge if not complete
        return None
    
    # Build merged spec_data
    merged_spec_data = {
        'question_code': question_code,
        'statements': all_statements,
        'question_type': 'DS',
        'code': [question_code],
        'num': 1,
        'learning_outcome': '\n\n'.join(merged_learning_outcomes) if merged_learning_outcomes else '',
        'question_template': []  # Will be populated if available
    }
    
    # Check for rich_content_types - take from any statement that has it
    for lesson_data_item in lessons_by_key.values():
        ds_specs = lesson_data_item.get('DS', [])
        for ds_spec in ds_specs:
            if ds_spec.get('question_code') == question_code and ds_spec.get('rich_content_types'):
                merged_spec_data['rich_content_types'] = ds_spec['rich_content_types']
                break
    
    # Build merged lesson data (use current as base, but merge content and supplementary)
    merged_lesson_data = current_lesson_data.copy()
    
    # Merge content from all source lessons
    merged_content = "\n\n---\n\n".join(merged_content_parts) if merged_content_parts else current_lesson_data.get('content', '')
    
    # Merge supplementary materials
    merged_supplementary = "\n\n---\n\n".join(merged_supplementary_parts) if merged_supplementary_parts else current_lesson_data.get('supplementary_material', '')
    
    # Update lesson name to indicate cross-lesson
    if len(source_lessons) > 1:
        lesson_names = []
        for lesson_key in sorted(source_lessons):
            lesson_data = lessons_by_key.get(lesson_key)
            if lesson_data:
                lesson_names.append(lesson_data.get('lesson_name', lesson_key))
        
        merged_lesson_data['lesson_name'] = f"Cross-lesson: {' + '.join(lesson_names)}"
    
    return {
        'spec_data': merged_spec_data,
        'merged_lesson_data': merged_lesson_data,
        'merged_content': merged_content,
        'merged_supplementary': merged_supplementary,
        'source_lessons': source_lessons
    }
