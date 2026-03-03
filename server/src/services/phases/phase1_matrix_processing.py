"""
Phase 1: Matrix Processing Service
Handles parsing matrix Excel files and extracting metadata
"""

import pandas as pd
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..core.matrix_parser import MatrixParser


@dataclass
class MatrixMetadata:
    """Metadata extracted from matrix file"""
    subject: str
    curriculum: str
    grade: str
    filename: str
    file_path: Path


@dataclass
class LessonInfo:
    """Lesson information from matrix content"""
    chapter_number: str
    lesson_number: str
    lesson_name: str
    content: str


class MatrixProcessingService:
    """Service for processing matrix Excel files and extracting question specs"""

    def __init__(self):
        self.matrix_parser = MatrixParser()
        # Support both formats: Ma trận_SUBJECT_CURRICULUM_GRADE.xlsx and sessionId_Ma trận_SUBJECT_CURRICULUM_GRADE.xlsx
        self.matrix_pattern = re.compile(
            r'(?:[a-f0-9-]+_)?Ma trận_([A-Z]+)_([A-Z]+)_([A-Z0-9]+)\.xlsx', 
            re.IGNORECASE
        )

    def parse_matrix_filename(self, filename: str) -> Optional[MatrixMetadata]:
        """Parse matrix filename to extract subject, curriculum, grade"""
        match = self.matrix_pattern.match(filename)
        if not match:
            return None

        subject, curriculum, grade = match.groups()
        return MatrixMetadata(
            subject=subject.upper(),
            curriculum=curriculum.upper(),
            grade=grade.upper(),
            filename=filename,
            file_path=Path(filename)
        )

    def load_matrix_file(self, file_path: Path) -> pd.DataFrame:
        """Load matrix Excel file into DataFrame"""
        try:
            return pd.read_excel(file_path, header=None)
        except Exception as e:
            raise ValueError(f"Failed to load matrix file {file_path}: {e}")

    def extract_lesson_info(self, df: pd.DataFrame) -> List[LessonInfo]:
        """Extract lesson information from matrix DataFrame"""
        lessons = []

        # Matrix structure (updated to match MatrixParser):
        # Column 2: "Tên Chủ đề - Chương" - contains chapter info (may be empty for some subjects)
        # Column 3: "Tên Bài" - contains lesson info

        current_chapter = None

        for idx, row in df.iterrows():
            # Skip header rows
            if idx < 2:
                continue

            # Check for chapter info in column 2 (index 2)
            chapter_text = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else ""

            # Check for lesson info in column 3 (index 3)
            lesson_text = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ""

            # Extract chapter number from chapter text
            # Support both "Chủ đề" (LICHSU) and "Chương" (HOAHOC, VATLY) and Roman numerals
            if chapter_text:
                # Try "Chủ đề X" or "Chương X" pattern (Arabic numbers)
                chapter_match = re.search(r'(?:Chủ đề|Chương)\s*(\d+)', chapter_text, re.IGNORECASE)
                if not chapter_match:
                    # Try Roman numerals pattern: "Chương I", "Chương II", etc.
                    roman_match = re.search(r'(?:Chủ đề|Chương)\s*([IVXLCDM]+)', chapter_text, re.IGNORECASE)
                    if roman_match:
                        # Convert Roman to Arabic
                        roman_str = roman_match.group(1).upper()
                        roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                        arabic_num = 0
                        prev_value = 0
                        for char in reversed(roman_str):
                            value = roman_map.get(char, 0)
                            if value < prev_value:
                                arabic_num -= value
                            else:
                                arabic_num += value
                            prev_value = value
                        current_chapter = str(arabic_num)
                else:
                    current_chapter = chapter_match.group(1)

            # Extract lesson info from lesson text
            if lesson_text and "Bài" in lesson_text:
                # If no chapter info found in column 2, use "0" as default
                # This handles subjects that don't have explicit chapter structure
                if not current_chapter:
                    current_chapter = "0"  # Default to chapter 0 if no explicit chapter
                lesson_match = re.search(r'Bài\s*(\d+)', lesson_text, re.IGNORECASE)
                if lesson_match and current_chapter:
                    lesson_num = lesson_match.group(1)

                    lessons.append(LessonInfo(
                        chapter_number=current_chapter,
                        lesson_number=lesson_num,
                        lesson_name=lesson_text,
                        content=lesson_text
                    ))

        # Deduplicate lessons based on chapter_number and lesson_number
        # Keep the first occurrence (usually has the most standard lesson name)
        seen = set()
        unique_lessons = []
        for lesson in lessons:
            key = (lesson.chapter_number, lesson.lesson_number)
            if key not in seen:
                seen.add(key)
                unique_lessons.append(lesson)

        return unique_lessons

    def generate_drive_paths(self, metadata: MatrixMetadata, lessons: List[LessonInfo]) -> List[str]:
        """Generate Google Drive folder paths for content download"""
        paths = []

        for lesson in lessons:
            # Generate path in format: [grade, subject, subject_curriculum_grade_chapter_lesson]
            path = [
                metadata.grade,
                metadata.subject,
                f"{metadata.subject}_{metadata.curriculum}_{metadata.grade}_{lesson.chapter_number}_{lesson.lesson_number}"
            ]
            paths.append(path)

        return paths

    def process_matrix_file(self, file_path: Path) -> Tuple[MatrixMetadata, List[LessonInfo], List[str]]:
        """Complete matrix processing pipeline"""
        # Parse filename
        metadata = self.parse_matrix_filename(file_path.name)
        if not metadata:
            raise ValueError(f"Invalid matrix filename format: Ma trận_Mã Môn_Bộ_Mã Khối.xlsx (Ví dụ: Ma trận_LICHSU_KNTT_C12.xlsx)")

        # Load matrix with MatrixParser to get question specs
        self.matrix_parser.load_excel(str(file_path))
        all_specs = self.matrix_parser.get_all_question_specs()
        true_false_specs = self.matrix_parser.group_true_false_questions()
        
        # Parse rich content types from "Loại" sheet
        rich_content_type_definitions = self.matrix_parser.parse_rich_content_types_sheet()

        # Extract lesson info from matrix
        df = self.load_matrix_file(file_path)
        lessons = self.extract_lesson_info(df)

        if not lessons:
            raise ValueError(f"No lesson information found in matrix file: {file_path}")

        # Generate drive paths
        drive_paths = self.generate_drive_paths(metadata, lessons)

        return metadata, lessons, drive_paths, all_specs, true_false_specs, rich_content_type_definitions

    def _expand_rich_content_types(self, rich_types: Dict[str, List[str]], 
                                   definitions: Dict[str, Dict[str, str]]) -> Dict[str, List[Dict]]:
        """Expand rich content type codes to full definitions
        
        Args:
            rich_types: {"C3": ["BK", "BD"]}
            definitions: {"BK": {"name": "Bảng khảo", "description": ""}}
        
        Returns:
            {"C3": [{"code": "BK", "name": "Bảng khảo", "description": ""}, ...]}
        """
        if not definitions:
            return rich_types
        
        expanded = {}
        for code, types in rich_types.items():
            expanded[code] = []
            for type_code in types:
                if type_code in definitions:
                    expanded[code].append({
                        'code': type_code,
                        'name': definitions[type_code]['name'],
                        'description': definitions[type_code]['description']
                    })
                else:
                    # If definition not found, just use the code
                    expanded[code].append({
                        'code': type_code,
                        'name': type_code,
                        'description': ''
                    })
        return expanded
    
    def save_matrix_data(self, metadata: MatrixMetadata, lessons: List[LessonInfo],
                        all_specs: Dict[str, List], true_false_specs: List,
                        rich_content_type_definitions: Dict[str, Dict[str, str]] = None,
                        output_dir: Path = Path("data/matrix")) -> Path:
        """Save matrix processing results to JSON file with question specs"""
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"matrix_{metadata.subject}_{metadata.curriculum}_{metadata.grade}.json"
        output_path = output_dir / filename

        # Create lesson data with question specs
        lessons_data = []
        for lesson in lessons:
            lesson_data = {
                'chapter_number': lesson.chapter_number,
                'lesson_number': lesson.lesson_number,
                'lesson_name': lesson.lesson_name,
                'content': '',
                'supplementary_material': '',
                'TN': {'NB': [], 'TH': [], 'VD': []},
                'DS': [],
                'TLN': {'NB': [], 'TH': [], 'VD': []},
                'TL': {'NB': [], 'TH': [], 'VD': []}
            }

            # Add TN specs for this lesson
            if 'TN' in all_specs:
                for spec in all_specs['TN']:
                    # Extract lesson number from lesson_name if not available in spec
                    spec_lesson_num = getattr(spec, 'lesson_number', None)
                    if spec_lesson_num is None:
                        # Try to extract from lesson_name (e.g., "Bài 1" -> 1)
                        lesson_match = re.search(r'Bài\s*(\d+)', spec.lesson_name, re.IGNORECASE)
                        spec_lesson_num = int(lesson_match.group(1)) if lesson_match else None

                    if spec.chapter_number == int(lesson.chapter_number) and spec_lesson_num == int(lesson.lesson_number):
                        level_key = spec.cognitive_level
                        if level_key in lesson_data['TN']:
                            tn_item = {
                                'num': spec.num_questions,
                                'code': spec.question_codes,
                                'learning_outcome': spec.learning_outcome,
                                'question_template': []
                            }
                            # Add rich_content_types if available (expanded with definitions)
                            if hasattr(spec, 'rich_content_types') and spec.rich_content_types:
                                tn_item['rich_content_types'] = self._expand_rich_content_types(
                                    spec.rich_content_types, rich_content_type_definitions or {}
                                )
                            lesson_data['TN'][level_key].append(tn_item)

            # Add DS specs for this lesson
            # Process DS statements - keep only statements that belong to this lesson
            if 'DS' in all_specs:
                # Group DS specs by question code
                from collections import defaultdict
                ds_by_code = defaultdict(list)
                ds_rich_types = {}  # Track rich content types per question code
                
                for spec in all_specs['DS']:
                    # Extract lesson number
                    spec_lesson_num = getattr(spec, 'lesson_number', None)
                    if spec_lesson_num is None:
                        lesson_match = re.search(r'Bài\s*(\d+)', spec.lesson_name, re.IGNORECASE)
                        spec_lesson_num = int(lesson_match.group(1)) if lesson_match else None
                    
                    if spec.chapter_number == int(lesson.chapter_number) and spec_lesson_num == int(lesson.lesson_number):
                        # Store rich content types if available
                        if hasattr(spec, 'rich_content_types') and spec.rich_content_types:
                            for code, types in spec.rich_content_types.items():
                                base_match = re.match(r'(C\d+)([A-D])?', code, re.IGNORECASE)
                                if base_match:
                                    base_code = base_match.group(1).upper()
                                    if base_code not in ds_rich_types:
                                        ds_rich_types[base_code] = {}
                                    ds_rich_types[base_code][code] = types
                        
                        # Extract base question code and statement label from each code
                        for code in spec.question_codes:
                            base_match = re.match(r'(C\d+)([A-D])?', code, re.IGNORECASE)
                            if base_match:
                                base_code = base_match.group(1).upper()
                                label = base_match.group(2).lower() if base_match.group(2) else None
                                
                                if label:  # Only process if it has a statement label
                                    ds_by_code[base_code].append({
                                        'label': label,
                                        'cognitive_level': spec.cognitive_level,
                                        'learning_outcome': spec.learning_outcome,
                                        'statement_code': code.upper(),
                                        'supplementary_materials': spec.supplementary_materials
                                    })
                
                # Add grouped statements for each question code found in this lesson
                for question_code, statements in ds_by_code.items():
                    ds_item = {
                        'question_code': question_code,
                        'statements': statements,
                        'supplementary_materials': statements[0]['supplementary_materials'] if statements else '',
                        'question_template': []
                    }
                    # Aggregate rich_content_types from all statements into a single list for the question
                    if question_code in ds_rich_types:
                        # Collect all unique rich content types from all statements
                        aggregated_types = []
                        seen_codes = set()
                        
                        for stmt_code, types in ds_rich_types[question_code].items():
                            for type_code in types:
                                if type_code not in seen_codes:
                                    seen_codes.add(type_code)
                                    aggregated_types.append(type_code)
                        
                        # Expand with definitions at question level (not statement level)
                        if aggregated_types:
                            ds_item['rich_content_types'] = self._expand_rich_content_types(
                                {question_code: aggregated_types}, 
                                rich_content_type_definitions or {}
                            )
                    lesson_data['DS'].append(ds_item)

            # Add TLN specs for this lesson
            if 'TLN' in all_specs:
                for spec in all_specs['TLN']:
                    # Extract lesson number from lesson_name if not available in spec
                    spec_lesson_num = getattr(spec, 'lesson_number', None)
                    if spec_lesson_num is None:
                        # Try to extract from lesson_name (e.g., "Bài 1" -> 1)
                        lesson_match = re.search(r'Bài\s*(\d+)', spec.lesson_name, re.IGNORECASE)
                        spec_lesson_num = int(lesson_match.group(1)) if lesson_match else None

                    if spec.chapter_number == int(lesson.chapter_number) and spec_lesson_num == int(lesson.lesson_number):
                        level_key = spec.cognitive_level
                        if level_key in lesson_data['TLN']:
                            tln_item = {
                                'num': spec.num_questions,
                                'code': spec.question_codes,
                                'learning_outcome': spec.learning_outcome,
                                'question_template': []
                            }
                            # Add rich_content_types if available (expanded with definitions)
                            if hasattr(spec, 'rich_content_types') and spec.rich_content_types:
                                tln_item['rich_content_types'] = self._expand_rich_content_types(
                                    spec.rich_content_types, rich_content_type_definitions or {}
                                )
                            lesson_data['TLN'][level_key].append(tln_item)

            # Add TL specs for this lesson
            if 'TL' in all_specs:
                for spec in all_specs['TL']:
                    # Extract lesson number from lesson_name if not available in spec
                    spec_lesson_num = getattr(spec, 'lesson_number', None)
                    if spec_lesson_num is None:
                        # Try to extract from lesson_name (e.g., "Bài 1" -> 1)
                        lesson_match = re.search(r'Bài\s*(\d+)', spec.lesson_name, re.IGNORECASE)
                        spec_lesson_num = int(lesson_match.group(1)) if lesson_match else None

                    if spec.chapter_number == int(lesson.chapter_number) and spec_lesson_num == int(lesson.lesson_number):
                        level_key = spec.cognitive_level
                        if level_key in lesson_data['TL']:
                            tl_item = {
                                'num': spec.num_questions,
                                'code': spec.question_codes,
                                'learning_outcome': spec.learning_outcome,
                                'question_template': []
                            }
                            # Add rich_content_types if available (expanded with definitions)
                            if hasattr(spec, 'rich_content_types') and spec.rich_content_types:
                                tl_item['rich_content_types'] = self._expand_rich_content_types(
                                    spec.rich_content_types, rich_content_type_definitions or {}
                                )
                            lesson_data['TL'][level_key].append(tl_item)

            lessons_data.append(lesson_data)

        matrix_data = {
            'metadata': {
                'subject': metadata.subject,
                'curriculum': metadata.curriculum,
                'grade': metadata.grade,
                'filename': metadata.filename
            },
            'rich_content_type_definitions': rich_content_type_definitions if rich_content_type_definitions else {},
            'lessons': lessons_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, ensure_ascii=False, indent=2)

        return output_path