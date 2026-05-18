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
from ..ai.math_template_filter_service import MathTemplateFilterService
from ..ai.history_material_filter_service import HistoryMaterialFilterService
from ..core.genai_client import GenAIClient
from config.settings import Config


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

    def __init__(self, genai_client: Optional[GenAIClient] = None):
        self.content_dir = Path("data/content")
        self.matrix_dir = Path("data/matrix")
        
        # Initialize Math template filter service and History material filter service
        if genai_client:
            self.math_filter_service = MathTemplateFilterService(genai_client)
            self.history_material_filter_service = HistoryMaterialFilterService(genai_client)
        else:
            # Dùng factory create_ai_client() để tôn trọng cài đặt AI provider
            # (Gemini hoặc OpenAI tuỳ lựa chọn người dùng)
            try:
                from ..core.ai_provider_settings import create_ai_client
                default_client = create_ai_client()
                self.math_filter_service = MathTemplateFilterService(default_client)
                self.history_material_filter_service = HistoryMaterialFilterService(default_client)
            except Exception as e:
                print(f"⚠️ Failed to initialize AI client for Math/History filtering: {e}")
                self.math_filter_service = MathTemplateFilterService(None)
                self.history_material_filter_service = HistoryMaterialFilterService(None)

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
            content_file = self._find_content_file(subject, grade, chapter_num, lesson_num)
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
                questions_mapped = self._map_lesson_content(lesson_data, content_file, subject)
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

        # Fix curriculum in metadata before saving enriched matrix
        # Ensure it defaults to KNTT if empty or invalid
        if 'metadata' in matrix_data:
            curriculum = matrix_data['metadata'].get('curriculum', '')
            if not curriculum or len(curriculum) > 10:  # If it's a session ID or empty, replace with KNTT
                matrix_data['metadata']['curriculum'] = Config.DEFAULT_CURRICULUM
                print(f"✓ Fixed curriculum in enriched matrix metadata to: {Config.DEFAULT_CURRICULUM}")

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

    def _find_content_file(self, subject: str, grade: str, chapter_num: int, lesson_num: int) -> Optional[Path]:
        """Find the Phase 2 content file for a specific lesson
        
        Args:
            subject: Subject code (e.g., 'TOAN', 'HOAHOC')
            grade: Grade code (e.g., 'C10', 'C11')
            chapter_num: Chapter number
            lesson_num: Lesson number
            
        Returns:
            Path to content file or None if not found
            
        Patterns:
        - Current Phase 2 cache: SUBJECT_GRADE_CHAPTER_LESSON_content.json
          e.g., TOAN_C12_1_1_content.json
        - Legacy cache with curriculum: SUBJECT_CURRICULUM_GRADE_CHAPTER_LESSON_content.json
          e.g., TOAN_KNTT_C12_1_1_content.json
        """
        # First try the exact filename produced by Phase 2.
        exact_filename = f"{subject}_{grade}_{chapter_num}_{lesson_num}_content.json"
        exact_file = self.content_dir / exact_filename
        if exact_file.exists():
            print(f"✅ Found exact content file for {subject} {grade} lesson {chapter_num}.{lesson_num}: {exact_file.name}")
            return exact_file

        # Then try the legacy format that includes curriculum between subject and grade.
        legacy_pattern = f"{subject}_*_{grade}_{chapter_num}_{lesson_num}_content.json"
        legacy_files = sorted(self.content_dir.glob(legacy_pattern))
        if legacy_files:
            print(f"✅ Found legacy content file for {subject} {grade} lesson {chapter_num}.{lesson_num}: {legacy_files[0].name}")
            return legacy_files[0]

        # Last-resort search is intentionally grade-safe. Older logic used
        # SUBJECT_*_CHAPTER_LESSON and could pick C10 content for a C12 matrix.
        fallback_pattern = f"{subject}_*_{chapter_num}_{lesson_num}_content.json"
        fallback_files = sorted(self.content_dir.glob(fallback_pattern))
        rejected_files = []

        for fallback_file in fallback_files:
            name_parts = fallback_file.stem.split('_')
            if len(name_parts) < 5:
                rejected_files.append(fallback_file.name)
                continue

            file_subject = name_parts[0]
            file_grade = name_parts[-4]
            file_chapter = name_parts[-3]
            file_lesson = name_parts[-2]

            if (
                file_subject == subject
                and file_grade == grade
                and file_chapter == str(chapter_num)
                and file_lesson == str(lesson_num)
            ):
                print(f"⚠️  Using grade-safe fallback content file for {subject} {grade} lesson {chapter_num}.{lesson_num}: {fallback_file.name}")
                return fallback_file

            rejected_files.append(fallback_file.name)

        if rejected_files:
            print(f"⚠️  Rejected fallback content files for {subject} {grade} lesson {chapter_num}.{lesson_num} due to grade mismatch: {rejected_files}")
        
        # If still not found
        print(f"❌ Content file not found for {subject} {grade} lesson {chapter_num}.{lesson_num}")
        return None

    def _map_lesson_content(self, lesson_data: Dict, content_file: Path, subject: str = 'TOAN') -> int:
        """Map content from Phase 2 file into lesson data
        
        Args:
            lesson_data: Lesson data from Phase 1 matrix
            content_file: Path to Phase 2 content file
            subject: Subject code (e.g., 'TOAN', 'HOAHOC')
                     For TOAN: maps ALL available templates
                     For other subjects: limits to 5 templates per question
        """
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

            # Determine if we should map all templates (TOAN) or limit to 5 (other subjects)
            map_all_templates = (subject.upper() == 'TOAN')
            is_toan = (subject.upper() == 'TOAN')

            # Map TN questions
            tn_data = data.get('TN', {})
            if tn_data and 'TN' in lesson_data:
                if is_toan and 'raw_questions' in tn_data:
                    # For TOAN: use AI filtering on raw_questions
                    questions_mapped += self._map_toan_questions_with_ai_filtering(
                        lesson_data['TN'], 
                        tn_data.get('raw_questions', []),
                        'TN'
                    )
                else:
                    # For other subjects: use random selection
                    questions_mapped += self._map_tn_questions(lesson_data['TN'], tn_data, map_all_templates)

            # Map TLN questions
            tln_data = data.get('TLN', {})
            if tln_data and 'TLN' in lesson_data:
                if is_toan and 'raw_questions' in tln_data:
                    # For TOAN: use AI filtering
                    questions_mapped += self._map_toan_questions_with_ai_filtering(
                        lesson_data['TLN'],
                        tln_data.get('raw_questions', []),
                        'TLN'
                    )
                else:
                    # For other subjects: use random selection
                    questions_mapped += self._map_tn_questions(lesson_data['TLN'], tln_data, map_all_templates)

            # Map TL questions
            tl_data = data.get('TL', {})
            if tl_data and 'TL' in lesson_data:
                if is_toan and 'raw_questions' in tl_data:
                    # For TOAN: use AI filtering
                    questions_mapped += self._map_toan_questions_with_ai_filtering(
                        lesson_data['TL'],
                        tl_data.get('raw_questions', []),
                        'TL'
                    )
                else:
                    # For other subjects: use random selection
                    questions_mapped += self._map_tn_questions(lesson_data['TL'], tl_data, map_all_templates)

            # Map DS questions (with AI material filter for supported subjects)
            ds_data = data.get('DS', {})
            if 'DS' in lesson_data and lesson_data['DS']:
                questions_mapped += self._map_ds_questions(
                    lesson_data['DS'],
                    ds_data.get('questions', []),
                    ds_data.get('material', []),
                    map_all_templates,
                    subject=subject,
                    lesson_name=lesson_data.get('lesson_name', '')
                )

            return questions_mapped

        except Exception as e:
            print(f"Error mapping content from {content_file}: {e}")
            return 0

    def _map_tn_questions(self, tn_specs: Dict, tn_content: Dict, map_all: bool = False) -> int:
        """Map TN questions with template selection
        
        Args:
            tn_specs: Question specifications from Phase 1 matrix
            tn_content: Content data from Phase 2 file
            map_all: If True, map ALL templates (for TOAN)
                     If False, limit to 5 templates per question
        """
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
                    available = available_questions[level]
                    if available:
                        if map_all:
                            # For TOAN: include ALL available templates
                            selected = list(available)
                        else:
                            # For other subjects: limit to 5 templates
                            num_to_sample = min(5, len(available))
                            if len(available) >= num_to_sample:
                                selected = random.sample(available, num_to_sample)
                            else:
                                selected = list(available)
                        spec['question_template'] = selected
                        questions_mapped += len(selected)

        return questions_mapped

    def _map_ds_questions(
        self,
        ds_specs: List,
        ds_questions: List,
        ds_materials: List,
        map_all: bool = False,
        subject: str = '',
        lesson_name: str = ''
    ) -> int:
        """Map DS questions with template selection

        Args:
            ds_specs: Question specifications from Phase 1 matrix
            ds_questions: Question data from Phase 2 file
            ds_materials: Material data from Phase 2 file (from Drive content)
            map_all: If True, map ALL templates (for TOAN)
                     If False, limit to 5 templates per question
            subject: Subject code (e.g., 'LICHSU'). Used to decide AI material filtering.
            lesson_name: Lesson name for AI context.
        """
        questions_mapped = 0

        if not ds_specs:
            return 0

        # Determine if this subject needs AI material filtering
        use_material_filter = Config.should_filter_material(subject) if subject else False

        # For each DS spec, select questions based on subject
        # For TOAN: select ALL questions, For others: limit to 5
        for spec in ds_specs:
            # Map questions
            if 'question_template' in spec and ds_questions:
                if map_all:
                    # For TOAN: include ALL available questions
                    selected_questions = list(ds_questions)
                else:
                    # For other subjects: limit to 5 questions
                    num_to_sample = min(5, len(ds_questions))
                    if len(ds_questions) >= num_to_sample:
                        selected_questions = random.sample(ds_questions, num_to_sample)
                    else:
                        selected_questions = list(ds_questions)
                spec['question_template'] = selected_questions
                questions_mapped += len(selected_questions)

            # Map materials (replace supplementary_materials with materials)
            if 'supplementary_materials' in spec:
                del spec['supplementary_materials']  # Remove old field

            # Only map materials from Drive content if not already set in spec from matrix
            existing_materials = spec.get('materials', '')
            if existing_materials:
                # Keep existing materials from matrix, don't override from Drive content
                pass
            elif ds_materials:
                if use_material_filter:
                    # Use AI to filter best matching materials from Drive content
                    question_code = spec.get('question_code', spec.get('code', ['DS'])[0])
                    statements = spec.get('statements', [])
                    filtered = self.history_material_filter_service.filter_materials(
                        lesson_name=lesson_name,
                        question_code=question_code,
                        statements=statements,
                        materials_list=ds_materials
                    )
                    spec['materials'] = filtered  # Store as list[str]
                    spec['materials_pool'] = ds_materials  # Full pool for "load more" feature
                    print(f"   ✓ AI filtered materials for DS {question_code}: {len(filtered)} selected")
                else:
                    # Default: random pick one material
                    selected_material = random.choice(ds_materials)
                    spec['materials'] = selected_material
            else:
                spec['materials'] = ""

        return questions_mapped

    def _map_toan_questions_with_ai_filtering(
        self, 
        question_specs: Dict,
        raw_questions: List[str],
        question_type: str
    ) -> int:
        """Map TOAN questions using AI filtering
        
        Args:
            question_specs: Question specifications (dict with NB/TH/VD levels)
            raw_questions: Raw questions list from Phase 2 (all levels mixed)
            question_type: Type of question (TN, TLN, TL)
        
        Returns:
            Number of questions mapped
        """
        questions_mapped = 0

        try:
            if not raw_questions:
                print(f"   No raw questions to filter for {question_type}")
                return 0

            print(f"\n🤖 AI Filtering for {question_type} - {len(raw_questions)} raw questions")

            # For each level (NB, TH, VD), filter questions for each spec
            for level in ['NB', 'TH', 'VD']:
                if level not in question_specs:
                    continue

                level_specs = question_specs[level]
                
                for spec in level_specs:
                    learning_outcome = spec.get('learning_outcome', '')
                    
                    if not learning_outcome:
                        print(f"   ⚠️  No learning outcome for {question_type}-{level}, skipping AI filter")
                        # Fallback: use first 5 questions
                        spec['question_template'] = raw_questions[:5]
                        questions_mapped += len(spec['question_template'])
                        continue

                    # Call AI filtering service
                    filtered_questions = self.math_filter_service.filter_question_templates(
                        question_type=question_type,
                        cognitive_level=level,
                        expected_learning_outcome=learning_outcome,
                        question_list=raw_questions
                    )

                    # Map filtered questions to spec
                    spec['question_template'] = filtered_questions
                    questions_mapped += len(filtered_questions)

            return questions_mapped

        except Exception as e:
            print(f"❌ Error in AI filtering for {question_type}: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: assign first 5 raw questions to each spec
            for level in ['NB', 'TH', 'VD']:
                if level not in question_specs:
                    continue
                for spec in question_specs[level]:
                    spec['question_template'] = raw_questions[:5]
                    questions_mapped += 5
            
            return questions_mapped
