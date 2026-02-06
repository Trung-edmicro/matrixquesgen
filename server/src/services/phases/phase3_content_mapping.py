"""
Phase 3: Content Mapping Service
Maps content from Phase 2 JSON files into Phase 1 matrix structure
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .phase1_matrix_processing import MatrixMetadata, LessonInfo


@dataclass
class ExtractedLesson:
    """Lesson with extracted content and specs"""
    subject: str
    grade: str
    chapter: int
    lesson: int
    lesson_name: str
    content: str
    tn_specs: List[Dict]
    ds_specs: List[Dict]


@dataclass
class ContentMappingResult:
    """Result of content mapping operation"""
    enriched_matrix_path: Path
    lessons_mapped: int
    total_questions_mapped: int
    extracted_lessons: List[ExtractedLesson]


class ContentMappingService:
    """Service for mapping Phase 2 content into Phase 1 matrix structure"""

    def __init__(self):
        self.content_dir = Path("data/content")
        self.matrix_dir = Path("data/matrix")

    def map_content_to_matrix(self, matrix_json_path: Path) -> ContentMappingResult:
        """Map content from Phase 2 JSON files into the matrix JSON"""
        print(f"🔗 Mapping content to matrix: {matrix_json_path}")

        # Load matrix JSON
        with open(matrix_json_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)

        # Get metadata
        metadata = matrix_data.get('metadata', {})
        subject = metadata.get('subject', 'Unknown')
        grade = metadata.get('grade', 'Unknown')

        lessons_mapped = 0
        total_questions_mapped = 0
        extracted_lessons = []

        # Deduplicate lessons by chapter_number and lesson_number
        seen_lessons = {}  # Key: (chapter, lesson), Value: merged lesson data
        
        for lesson_data in matrix_data['lessons']:
            chapter_num = int(lesson_data['chapter_number']) if isinstance(lesson_data['chapter_number'], str) else lesson_data['chapter_number']
            lesson_num = int(lesson_data['lesson_number']) if isinstance(lesson_data['lesson_number'], str) else lesson_data['lesson_number']
            lesson_key = (chapter_num, lesson_num)
            
            if lesson_key not in seen_lessons:
                # First occurrence, store it
                seen_lessons[lesson_key] = lesson_data.copy()
            else:
                # Duplicate found, merge question specs
                existing = seen_lessons[lesson_key]
                
                # Merge TN specs
                for q_type in ['TN', 'DS', 'TLN']:
                    if q_type not in lesson_data:
                        continue
                        
                    if q_type not in existing:
                        existing[q_type] = lesson_data[q_type]
                    elif isinstance(lesson_data[q_type], dict):
                        # TN/TLN structure: merge by level
                        for level, specs in lesson_data[q_type].items():
                            if level not in existing[q_type]:
                                existing[q_type][level] = specs
                            else:
                                # Merge specs, avoiding duplicate codes
                                existing_codes = set()
                                for spec in existing[q_type][level]:
                                    existing_codes.update(spec.get('code', []))
                                
                                for spec in specs:
                                    new_codes = [c for c in spec.get('code', []) if c not in existing_codes]
                                    if new_codes:
                                        existing[q_type][level].append(spec)
                                        existing_codes.update(new_codes)
                    elif isinstance(lesson_data[q_type], list):
                        # DS structure: merge list, avoiding duplicate codes
                        existing_codes = set()
                        for spec in existing[q_type]:
                            existing_codes.update(spec.get('code', []))
                        
                        for spec in lesson_data[q_type]:
                            new_codes = [c for c in spec.get('code', []) if c not in existing_codes]
                            if new_codes:
                                existing[q_type].append(spec)
                                existing_codes.update(new_codes)
        
        # Update matrix with deduplicated lessons
        matrix_data['lessons'] = list(seen_lessons.values())

        # Process each unique lesson
        for lesson_data in matrix_data['lessons']:
            # Convert to int if string
            chapter_num = int(lesson_data['chapter_number']) if isinstance(lesson_data['chapter_number'], str) else lesson_data['chapter_number']
            lesson_num = int(lesson_data['lesson_number']) if isinstance(lesson_data['lesson_number'], str) else lesson_data['lesson_number']
            lesson_name = lesson_data.get('lesson_name', f"Lesson {lesson_num}")

            # Find corresponding Phase 2 content file
            content_file = self._find_content_file(chapter_num, lesson_num)
            content = ""
            if content_file:
                # Load content
                try:
                    with open(content_file, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)
                    data = content_data.get('data', {})
                    sgk_content = data.get('content', {}).get('SGK', '')
                    # sgv_content = data.get('content', {}).get('SGV', '')
                    # sbt_content = data.get('content', {}).get('SBT', '')
                    sgv_content = ''
                    sbt_content = ''
                    content_parts = [c for c in [sgk_content, sgv_content, sbt_content] if c]
                    content = "\n\n".join(content_parts)
                except Exception as e:
                    print(f"⚠️  Error loading content for lesson {chapter_num}.{lesson_num}: {e}")

            # Map content to specs if content file exists
            questions_mapped = 0
            if content_file:
                questions_mapped = self._map_lesson_content(lesson_data, content_file)
                if questions_mapped > 0:
                    lessons_mapped += 1
                    total_questions_mapped += questions_mapped

            # Create extracted lesson
            tn_specs = self._extract_specs_from_lesson(lesson_data, 'TN')
            ds_specs = self._extract_specs_from_lesson(lesson_data, 'DS')
            
            extracted_lesson = ExtractedLesson(
                subject=subject,
                grade=grade,
                chapter=chapter_num,
                lesson=lesson_num,
                lesson_name=lesson_name,
                content=content,
                tn_specs=tn_specs,
                ds_specs=ds_specs
            )
            extracted_lessons.append(extracted_lesson)

        # Save enriched matrix
        enriched_path = matrix_json_path.parent / f"enriched_{matrix_json_path.name}"
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, ensure_ascii=False, indent=2)

        return ContentMappingResult(
            enriched_matrix_path=enriched_path,
            lessons_mapped=lessons_mapped,
            total_questions_mapped=total_questions_mapped,
            extracted_lessons=extracted_lessons
        )

    def _extract_specs_from_lesson(self, lesson_data: Dict, question_type: str) -> List[Dict]:
        """Extract specs from lesson data for given question type"""
        specs = []
        if question_type not in lesson_data:
            return specs
            
        type_data = lesson_data[question_type]
        
        # Handle different structures
        if isinstance(type_data, list):
            # DS structure: direct list of specs
            for spec in type_data:
                if isinstance(spec, dict):
                    specs.append(spec.copy())
        elif isinstance(type_data, dict):
            # TN/TLN structure: dict with levels (NB, TH, VD)
            for level, level_specs in type_data.items():
                if isinstance(level_specs, list):
                    for spec in level_specs:
                        if isinstance(spec, dict):
                            spec_copy = spec.copy()
                            spec_copy['level'] = level  # Add level info
                            specs.append(spec_copy)
        
        return specs

    def _find_content_file(self, chapter_num: int, lesson_num: int) -> Optional[Path]:
        """Find the Phase 2 content file for a specific lesson"""
        # Pattern: LICHSU_KNTT_C12_3_6_content.json
        pattern = f"*_{chapter_num}_{lesson_num}_content.json"

        matching_files = list(self.content_dir.glob(pattern))
        if matching_files:
            return matching_files[0]  # Take the first match

        return None

    def _map_lesson_content(self, lesson_data: Dict, content_file: Path) -> int:
        """Map content from Phase 2 file into lesson data"""
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content_data = json.load(f)

            questions_mapped = 0

            # Extract content data
            data = content_data.get('data', {})

            # Map SGK, SGV and SBT content
            sgk_content = data.get('content', {}).get('SGK', '')
            # sgv_content = data.get('content', {}).get('SGV', '')
            # sbt_content = data.get('content', {}).get('SBT', '')
            sgv_content = ''
            sbt_content = ''

            combined_content = []
            if sgk_content:
                combined_content.append(sgk_content)
            if sgv_content:
                combined_content.append(sgv_content)
            if sbt_content:
                combined_content.append(sbt_content)

            lesson_data['content'] = '\n\n'.join(combined_content) if combined_content else lesson_data.get('content', '')

            # Map supplementary_material from Phase 2 data (for TN/TLN/TL and DS with rich content)
            supplementary_material = data.get('supplementary_material', '')
            if supplementary_material:
                lesson_data['supplementary_material'] = supplementary_material
                print(f"   ✓ Mapped supplementary_material: {len(supplementary_material)} chars")

            # Map TN questions with random selection
            tn_data = data.get('TN', {})
            if tn_data and 'TN' in lesson_data:
                questions_mapped += self._map_tn_questions(lesson_data['TN'], tn_data)

            # Map TLN questions with random selection
            tln_data = data.get('TLN', {})
            if tln_data and 'TLN' in lesson_data:
                questions_mapped += self._map_tn_questions(lesson_data['TLN'], tln_data)

            # Map TL questions with random selection
            tl_data = data.get('TL', {})
            if tl_data and 'TL' in lesson_data:
                questions_mapped += self._map_tn_questions(lesson_data['TL'], tl_data)

            # Map DS questions with random selection
            ds_data = data.get('DS', {})
            if 'DS' in lesson_data and lesson_data['DS']:
                questions_mapped += self._map_ds_questions(lesson_data['DS'], ds_data.get('questions', []), ds_data.get('material', []))

            return questions_mapped

        except Exception as e:
            print(f"Error mapping content from {content_file}: {e}")
            return 0

    def _map_tn_questions(self, tn_specs: Dict, tn_content: Dict) -> int:
        """Map TN questions with random selection"""
        questions_mapped = 0

        # Collect all available questions by level
        available_questions = {'NB': [], 'TH': [], 'VD': []}

        for level in ['NB', 'TH', 'VD']:
            if level in tn_content:
                available_questions[level].extend(tn_content[level])

        # Map to specs
        for level, level_specs in tn_specs.items():
            if level not in available_questions or not available_questions[level]:
                continue

            for spec in level_specs:
                if 'question_template' in spec:
                    num_questions = spec.get('num', 1)
                    available = available_questions[level]
                    if available:
                        if len(available) == 1:
                            # Only one question available, use it for all required
                            selected = [available[0]] * num_questions
                        elif len(available) >= num_questions:
                            # Enough unique questions, select without replacement
                            selected = random.sample(available, num_questions)
                        else:
                            # Not enough unique questions, allow duplicates
                            selected = random.choices(available, k=num_questions)
                        spec['question_template'] = selected
                        questions_mapped += len(selected)

        return questions_mapped

    def _map_ds_questions(self, ds_specs: List, ds_questions: List, ds_materials: List) -> int:
        """Map DS questions with random selection"""
        questions_mapped = 0

        if not ds_specs:
            return 0

        # For each DS spec, randomly select one question and one material if available
        for spec in ds_specs:
            # Map questions
            if 'question_template' in spec and ds_questions:
                selected_question = random.choice(ds_questions)
                spec['question_template'] = [selected_question]
                questions_mapped += 1

            # Map materials (replace supplementary_materials with materials)
            if 'supplementary_materials' in spec:
                del spec['supplementary_materials']  # Remove old field

            if ds_materials:
                selected_material = random.choice(ds_materials)
                spec['materials'] = selected_material
            else:
                spec['materials'] = ""

        return questions_mapped