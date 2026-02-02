"""
Phase 4 Alternative: Alternative Question Generation Service
Handles generating questions with new logic: combined NB/TH, separate VD, and DS with topic-based prompt selection
"""
import json
import os
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import existing services
from ..core.genai_client import GenAIClient
from ..generators.question_generator import QuestionGenerator, GeneratedEssayQuestion
from ..core.matrix_parser import MatrixParser, QuestionSpec, TrueFalseQuestionSpec

# Import rich content support
from services.core.rich_content import (
    ContentBlock, ContentType,
    text as text_block, mixed as mixed_block
)


@dataclass
class GeneratedQuestion:
    """Generated question structure"""
    id: str
    type: str  # 'multiple_choice', 'true_false', 'short_answer', etc.
    question: str
    correct_answer: str
    subject: str
    grade: str
    chapter: str
    lesson: str
    lesson_name: str  # Add lesson name
    generated_at: str
    options: Optional[Dict[str, str]] = None
    explanation: Optional[Union[str, Dict[str, str]]] = None
    difficulty: str = 'medium'
    question_code: Optional[str] = None  # Question code from matrix
    # For DS questions
    source_text: Optional[str] = None
    statements: Optional[Dict[str, Dict]] = None
    # DS metadata fields (source citation)
    source_citation: Optional[str] = None
    source_origin: Optional[str] = None
    source_type: Optional[str] = None
    pedagogical_approach: Optional[str] = None
    search_evidence: Optional[str] = None


@dataclass
class QuestionSet:
    """Set of generated questions for a lesson"""
    subject: str
    grade: str
    chapter: str
    lesson: str
    question_type: str
    questions: List[GeneratedQuestion]
    total_questions: int
    generated_at: str


class AlternativeQuestionGenerationService:
    """Alternative service for generating questions with new logic"""

    def __init__(self, ai_provider: str = "genai"):
        self.ai_provider = ai_provider
        # Base prompts directory
        if os.getenv('APP_DIR'):
            self.prompts_base_dir = Path(os.getenv('APP_DIR')) / "data" / "prompts"
        else:
            self.prompts_base_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "prompts"
        
        # Default prompts directory (will be updated by set_prompts_directory)
        self.prompts_dir = self.prompts_base_dir

        # Load model names from environment
        self.primary_model = os.getenv('GENAI_MODEL', 'gemini-3-pro-preview')
        self.fallback_model = os.getenv('GEMINI_FALLBACK_MODEL', 'gemini-2.5-pro')

        print(f"✓ Configured retry strategy:")
        print(f"   Primary model: {self.primary_model} (5 retries)")
        print(f"   Fallback model: {self.fallback_model} (3 retries)")

        # Initialize existing AI client
        self.genai_client = None
        self.question_generator = None
        self.matrix_parser = MatrixParser()  # Initialize matrix parser for sample questions

        if ai_provider == "genai":
            # Initialize GenAI client
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            api_key = os.getenv("GENAI_API_KEY")

            try:
                self.genai_client = GenAIClient(
                    project_id=project_id,
                    credentials_path=credentials_path,
                    api_key=api_key
                )
                
                # Try to find TN prompt file (TN2.txt or TN.txt)
                tn_prompt_path = None
                if (self.prompts_dir / "TN2.txt").exists():
                    tn_prompt_path = str(self.prompts_dir / "TN2.txt")
                    print(f"✓ Using TN2.txt for QuestionGenerator init")
                elif (self.prompts_dir / "TN.txt").exists():
                    tn_prompt_path = str(self.prompts_dir / "TN.txt")
                    print(f"✓ Using TN.txt for QuestionGenerator init")
                else:
                    print(f"⚠️ Neither TN.txt nor TN2.txt found in {self.prompts_dir}")
                    print(f"   QuestionGenerator will be initialized when set_prompts_directory() is called")
                
                if tn_prompt_path:
                    self.question_generator = QuestionGenerator(
                        ai_client=self.genai_client,
                        prompt_template_path=tn_prompt_path,
                        verbose=True,
                        matrix_parser=self.matrix_parser  # Add matrix_parser for sample questions
                    )
                    print(f"✓ QuestionGenerator initialized with {Path(tn_prompt_path).name}")
                else:
                    self.question_generator = None
                    
            except Exception as e:
                # print(f"❌ Failed to initialize GenAI client: {e}")
                # print(f"   Project ID: {project_id}")
                # print(f"   Credentials path: {credentials_path}")
                # print(f"   API key: {'***' if api_key else None}")
                self.genai_client = None
                self.question_generator = None

    def classify_lesson_topic_type(self, lesson_data: Dict) -> int:
        """
        Classify lesson topic type based on content analysis
        Returns:
        1: Only situation-based DS questions
        2: Only material-based DS questions
        3: Both types possible
        """
        lesson_name = lesson_data.get('lesson_name', '').lower()
        content = lesson_data.get('content', '').lower()

        # Keywords indicating situation-based topics
        situation_keywords = [
            'tình huống', 'thực tế', 'cuộc sống', 'xã hội', 'pháp luật',
            'kinh tế', 'quyền', 'nghĩa vụ', 'trách nhiệm', 'vi phạm',
            'hành vi', 'chủ thể', 'bảo vệ', 'thực thi'
        ]

        # Keywords indicating material/data-based topics
        material_keywords = [
            'chỉ số', 'thống kê', 'báo cáo', 'dữ liệu', 'số liệu',
            'tăng trưởng', 'phát triển', 'chính sách', 'quy hoạch',
            'kế hoạch', 'chi tiêu', 'thu nhập', 'ngân sách'
        ]

        situation_count = sum(1 for kw in situation_keywords if kw in content)
        material_count = sum(1 for kw in material_keywords if kw in content)

        # If predominantly situation-based
        if situation_count > material_count * 2:
            return 1
        # If predominantly material-based
        elif material_count > situation_count * 2:
            return 2
        # If mixed or balanced
        else:
            return 3

    def set_prompts_directory(self, subject: str, curriculum: str, grade: str):
        """
        Set prompts directory based on matrix metadata
        
        Args:
            subject: Subject name (e.g., "LICHSU")
            curriculum: Curriculum name (e.g., "KNTT")
            grade: Grade level (e.g., "C12")
        """
        prompts_subdir = f"{subject}_{curriculum}_{grade}"
        self.prompts_dir = self.prompts_base_dir / prompts_subdir
        
        if self.prompts_dir.exists():
            print(f"✓ Prompts directory set to: {self.prompts_dir}")
        else:
            print(f"⚠️ Prompts directory not found: {self.prompts_dir}")
            print(f"   Will fallback to base directory: {self.prompts_base_dir}")
            self.prompts_dir = self.prompts_base_dir
        
        # Re-initialize QuestionGenerator with new prompts directory
        if self.genai_client:
            try:
                # Try to find TN prompt file (TN2.txt or TN.txt)
                tn_prompt_path = None
                if (self.prompts_dir / "TN2.txt").exists():
                    tn_prompt_path = str(self.prompts_dir / "TN2.txt")
                    print(f"✓ Using TN2.txt for QuestionGenerator")
                elif (self.prompts_dir / "TN.txt").exists():
                    tn_prompt_path = str(self.prompts_dir / "TN.txt")
                    print(f"✓ Using TN.txt for QuestionGenerator")
                
                if tn_prompt_path:
                    self.question_generator = QuestionGenerator(
                        ai_client=self.genai_client,
                        prompt_template_path=tn_prompt_path,
                        verbose=True,
                        matrix_parser=self.matrix_parser
                    )
                    print(f"✓ QuestionGenerator re-initialized with {Path(tn_prompt_path).name}")
                else:
                    print(f"⚠️ Neither TN.txt nor TN2.txt found in {self.prompts_dir}")
                    self.question_generator = None
            except Exception as e:
                print(f"❌ Failed to re-initialize QuestionGenerator: {e}")
                self.question_generator = None

    def select_ds_prompt(self, lesson_data: Dict, existing_questions: List[GeneratedQuestion] = None) -> str:
        """
        Select appropriate DS prompt based on topic type and existing questions
        """
        if existing_questions is None:
            existing_questions = []
            
        topic_type = self.classify_lesson_topic_type(lesson_data)

        if topic_type == 1:
            # Only situation-based
            return str(self.prompts_dir / "DS_case.txt")
        elif topic_type == 2:
            # Only material-based
            return str(self.prompts_dir / "DS_học liệu AI gen.txt")
        else:
            # Type 3: Both possible, decide based on existing questions
            situation_count = sum(1 for q in existing_questions if q.type == "DS" and "tình huống" in (q.source_text or "").lower())
            material_count = sum(1 for q in existing_questions if q.type == "DS" and not ("tình huống" in (q.source_text or "").lower()))

            if situation_count > 2:
                # Too many situation, use material
                return str(self.prompts_dir / "DS_học liệu AI gen.txt")
            elif material_count > 1:
                # Too many material, use situation
                return str(self.prompts_dir / "DS_case.txt")
            else:
                # Default to situation for type 3
                return str(self.prompts_dir / "DS_case.txt")

    def process_question_generation(self, extracted_lesson: Any, question_type: str, num_questions: int = 5) -> Optional[QuestionSet]:
        """Process question generation with new logic"""
        try:
            if not self.question_generator:
                return None

            # Generate questions using new logic
            subject = extracted_lesson.subject
            grade = extracted_lesson.grade
            chapter = str(extracted_lesson.chapter)
            lesson = str(extracted_lesson.lesson)
            content = extracted_lesson.content

            # Get specs based on question type
            if question_type == "TN":
                specs = extracted_lesson.tn_specs
            elif question_type == "DS":
                specs = extracted_lesson.ds_specs
            else:
                specs = []

            if not specs:
                return None

            # Generate questions for each spec
            generated_questions = []
            for spec in specs[:num_questions]:  # Limit to num_questions
                try:
                    # Create QuestionSpec for the existing generator
                    codes = spec.get('code', [])
                    if isinstance(codes, list) and codes:
                        code_str = codes[0]  # Use first code
                    else:
                        code_str = f"C{len(generated_questions)+1}"

                    qspec = QuestionSpec(
                        question_codes=[code_str],
                        lesson_name=getattr(extracted_lesson, 'lesson_name', f"Chương {chapter} - Bài {lesson}"),
                        question_type=question_type,
                        cognitive_level=spec.get('level', 'medium'),
                        learning_outcome=spec.get('learning_outcome', ''),
                        num_questions=1,
                        competency_level=1,
                        row_index=0
                    )

                    # Generate question
                    questions = self.question_generator.generate_questions_for_spec(
                        spec=qspec,
                        content=content
                    )

                    for gen_q in questions:
                        question = GeneratedQuestion(
                            id=f"{subject}_{grade}_{chapter}_{lesson}_{question_type}_{gen_q.question_code}",
                            type=question_type,
                            question=gen_q.question_stem,
                            options=gen_q.options,
                            correct_answer=gen_q.correct_answer,
                            explanation=gen_q.explanation,
                            difficulty=gen_q.level,
                            subject=subject,
                            grade=grade,
                            chapter=chapter,
                            lesson=lesson,
                            lesson_name=extracted_lesson.lesson_name,
                            generated_at=datetime.now().isoformat()
                        )
                        generated_questions.append(question)

                except Exception as e:
                    print(f"❌ Error generating {question_type} for spec {spec}: {e}")
                    continue

            if generated_questions:
                return QuestionSet(
                    subject=subject,
                    grade=grade,
                    chapter=chapter,
                    lesson=lesson,
                    question_type=question_type,
                    questions=generated_questions,
                    total_questions=len(generated_questions),
                    generated_at=datetime.now().isoformat()
                )
            else:
                return None

        except Exception as e:
            print(f"ALTERNATIVE: Error in process_question_generation: {e}")
            return None

    def process_enriched_matrix_alternative(self, enriched_matrix_path: Path, question_types: List[str] = None) -> Optional[QuestionSet]:
        """
        Process enriched matrix with alternative logic:
        - Combine NB and TH levels into single request using TN2.txt
        - Use VD with separate prompt TN_VD_case2.txt
        - DS with topic-based prompt selection
        - Auto-retry missing questions until complete
        """
        print("ALTERNATIVE: Starting alternative question generation logic")
        print("   - TN: NB+TH combined using TN2.txt, VD separate using TN_VD_case2.txt")
        print("   - DS: Topic-based prompt selection (situation vs material)")
        print("   - TLN: Using TLN.txt prompt")
        print("   - TL: Using TLN.txt prompt with extended answer")
        print("   - Auto-retry missing questions")
        if question_types is None:
            question_types = ["TN", "DS", "TLN", "TL"]

        try:
            # Load enriched matrix JSON
            with open(enriched_matrix_path, 'r', encoding='utf-8') as f:
                matrix_data = json.load(f)
            
            # First pass: generate all questions
            question_set = self._generate_questions_from_matrix(matrix_data, question_types)
            
            if not question_set:
                return None
            
            # Check and retry missing questions
            max_retry_attempts = 3
            retry_attempt = 0
            
            while retry_attempt < max_retry_attempts:
                missing_info = self._check_missing_questions(matrix_data, question_set, question_types)
                
                if not missing_info['has_missing']:
                    print(f"✅ All questions generated successfully!")
                    break
                
                retry_attempt += 1
                print(f"\n⚠️ Missing questions detected (attempt {retry_attempt}/{max_retry_attempts}):")
                print(f"   Expected: TN={missing_info['expected']['TN']}, DS={missing_info['expected']['DS']}, "
                      f"TLN={missing_info['expected']['TLN']}, TL={missing_info['expected']['TL']}")
                print(f"   Generated: TN={missing_info['generated']['TN']}, DS={missing_info['generated']['DS']}, "
                      f"TLN={missing_info['generated']['TLN']}, TL={missing_info['generated']['TL']}")
                print(f"   Missing: TN={missing_info['missing']['TN']}, DS={missing_info['missing']['DS']}, "
                      f"TLN={missing_info['missing']['TLN']}, TL={missing_info['missing']['TL']}")
                
                # Generate missing questions
                additional_questions = self._generate_missing_questions(matrix_data, missing_info)
                
                if additional_questions:
                    # Merge with existing questions
                    question_set = self._merge_question_sets(question_set, additional_questions)
                    print(f"✅ Added {len(additional_questions)} missing questions")
                else:
                    print(f"❌ Failed to generate missing questions in attempt {retry_attempt}")
            
            # Deduplicate questions before returning
            question_set = self._deduplicate_questions(question_set)
            print(f"📊 Final count after deduplication: TN={len([q for q in question_set.questions if q.type == 'TN'])}, "
                  f"DS={len([q for q in question_set.questions if q.type == 'DS'])}, "
                  f"TLN={len([q for q in question_set.questions if q.type == 'TLN'])}, "
                  f"TL={len([q for q in question_set.questions if q.type == 'TL'])}")
                    
            return question_set

        except Exception as e:
            print(f"ALTERNATIVE: Error processing enriched matrix: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_questions_from_matrix(self, matrix_data: Dict, question_types: List[str]) -> Optional[QuestionSet]:
        """Generate questions from matrix data (original logic)"""
        try:
            all_questions = []
            generation_tasks = []

            # Create generation tasks for each lesson and spec
            for lesson_data in matrix_data['lessons']:
                chapter = lesson_data['chapter_number']
                lesson = lesson_data['lesson_number']
                content = lesson_data.get('content', '')
                supplementary = lesson_data.get('supplementary_material', '')

                # Generate questions for each requested type
                for question_type in question_types:
                    if question_type == "TN":
                        # Process TN specs with new logic: combine NB and TH
                        tn_specs = lesson_data.get('TN', {})

                        # Collect all NB and TH specs
                        nb_specs = []
                        th_specs = []
                        vd_specs = []

                        for level, specs in tn_specs.items():
                            if level.upper() == 'NB':
                                nb_specs.extend(specs)
                            elif level.upper() == 'TH':
                                th_specs.extend(specs)
                            elif level.upper() == 'VD':
                                vd_specs.extend(specs)
                        
                        # Debug: Log counts
                        print(f"📊 DEBUG TN specs for lesson {chapter}.{lesson}:")
                        print(f"   NB specs: {len(nb_specs)}")
                        print(f"   TH specs: {len(th_specs)}")
                        print(f"   VD specs: {len(vd_specs)}")
                        if vd_specs:
                            print(f"   VD spec codes: {[spec.get('code') for spec in vd_specs]}")

                        # Create individual TN_SINGLE tasks for each NB spec
                        for spec_data in nb_specs:
                            task = {
                                'type': 'TN_SINGLE',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary,
                                'spec_data': spec_data,
                                'level': 'NB'
                            }
                            generation_tasks.append(task)

                        # Create individual TN_SINGLE tasks for each TH spec
                        for spec_data in th_specs:
                            task = {
                                'type': 'TN_SINGLE',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary,
                                'spec_data': spec_data,
                                'level': 'TH'
                            }
                            generation_tasks.append(task)

                        # Create separate VD tasks
                        for spec_data in vd_specs:
                            print(f"🔧 DEBUG: Creating TN_VD task for lesson {chapter}.{lesson} with codes {spec_data.get('code')}")
                            task = {
                                'type': 'TN_VD',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary,
                                'spec_data': spec_data
                            }
                            generation_tasks.append(task)
                            print(f"✅ TN_VD task added to queue (total tasks now: {len(generation_tasks)})")

                    elif question_type == "DS":
                        # Process DS specs with topic-based prompt selection
                        ds_specs = lesson_data.get('DS', [])
                        topic_type = self.classify_lesson_topic_type(lesson_data)
                        
                        for spec_data in ds_specs:
                            # Transform statements array to expected_outcomes and cognitive_levels dicts
                            # This ensures compatibility with both old and new matrix formats
                            statements = spec_data.get('statements', [])
                            if statements and not spec_data.get('expected_outcomes'):
                                # New format: extract from statements array
                                expected_outcomes = {}
                                cognitive_levels = {}
                                for stmt in statements:
                                    label = stmt.get('label', '')
                                    if label:
                                        expected_outcomes[label] = stmt.get('learning_outcome', '')
                                        cognitive_levels[label] = stmt.get('cognitive_level', 'TH')
                                
                                spec_data['expected_outcomes'] = expected_outcomes
                                spec_data['cognitive_levels'] = cognitive_levels
                            
                            # Select prompt based on topic type and existing questions
                            # For now, we'll select based on lesson data only
                            selected_prompt = self.select_ds_prompt(lesson_data)
                            prompt_name = selected_prompt.split('/')[-1]
                            
                            task = {
                                'type': 'DS_TOPIC_BASED',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': spec_data.get('materials', ''),
                                'spec_data': spec_data,
                                'selected_prompt': selected_prompt
                            }
                            generation_tasks.append(task)

                    elif question_type == "TLN":
                        # Process TLN specs (Trả lời ngắn - Short answer)
                        tln_specs = lesson_data.get('TLN', {})
                        
                        # Collect specs by level
                        for level in ['NB', 'TH', 'VD']:
                            specs = tln_specs.get(level, [])
                            for spec_data in specs:
                                # Load TLN prompt
                                tln_prompt_path = self.prompts_dir / "TLN.txt"
                                if not tln_prompt_path.exists():
                                    tln_prompt_path = self.prompts_base_dir / "server" / "src" / "config" / "prompt" / "TLN.txt"
                                
                                task = {
                                    'type': 'TLN_SINGLE',
                                    'lesson_data': lesson_data,
                                    'chapter': chapter,
                                    'lesson': lesson,
                                    'content': content,
                                    'supplementary': supplementary,
                                    'spec_data': spec_data,
                                    'level': level,
                                    'prompt_path': str(tln_prompt_path)
                                }
                                generation_tasks.append(task)
                                print(f"✅ TLN_{level} task added to queue (total tasks now: {len(generation_tasks)})")

                    elif question_type == "TL":
                        # Process TL specs (Tự luận - Essay)
                        tl_specs = lesson_data.get('TL', {})
                        
                        # Collect specs by level
                        for level in ['NB', 'TH', 'VD']:
                            specs = tl_specs.get(level, [])
                            for spec_data in specs:
                                # Use TL prompt for essay questions with full structure
                                tl_prompt_path = self.prompts_dir / "TL.txt"
                                if not tl_prompt_path.exists():
                                    tl_prompt_path = self.prompts_base_dir / "server" / "src" / "config" / "prompt" / "TL.txt"
                                
                                task = {
                                    'type': 'TL_SINGLE',
                                    'lesson_data': lesson_data,
                                    'chapter': chapter,
                                    'lesson': lesson,
                                    'content': content,
                                    'supplementary': supplementary,
                                    'spec_data': spec_data,
                                    'level': level,
                                    'prompt_path': str(tl_prompt_path)
                                }
                                generation_tasks.append(task)
                                print(f"✅ TL_{level} task added to queue (total tasks now: {len(generation_tasks)})")


            # Execute generation tasks in parallel
            print(f"ALTERNATIVE: Starting parallel generation of {len(generation_tasks)} question tasks...")

            # Use fewer workers to avoid rate limiting (429 errors)
            max_workers = min(5, len(generation_tasks))  # Reduced from 10 to 3
            print(f"   Using {max_workers} parallel workers to avoid API rate limits")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit tasks with small delay to avoid burst
                future_to_task = {}
                for task in generation_tasks:
                    future_to_task[executor.submit(self._generate_alternative_question_task, task)] = task
                    time.sleep(0.2)  # Small delay between submissions

                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        generated_questions = future.result()
                        if generated_questions:
                            all_questions.extend(generated_questions)
                            task_type = task['type']
                            chapter = task['chapter']
                            lesson = task['lesson']
                            print(f"✅ ALTERNATIVE: Completed {task_type} task for lesson {chapter}.{lesson} - {len(generated_questions)} questions")
                    except Exception as e:
                        print(f"❌ ALTERNATIVE: Failed {task['type']} task for lesson {task['chapter']}.{task['lesson']}: {e}")

            # Convert to GeneratedQuestion format
            questions = []
            for gen_q in all_questions:
                if gen_q.question_type == "DS":  # DS question
                    # Convert DS to standard format
                    statements_text = "\n".join([f"{label}. {stmt['text']}" for label, stmt in gen_q.statements.items()])
                    question = GeneratedQuestion(
                        id=f"{matrix_data['metadata']['subject']}_{matrix_data['metadata']['grade']}_{gen_q.chapter_number}_{gen_q.lesson_number}_{gen_q.question_type}_{gen_q.question_code}",
                        type=gen_q.question_type,
                        question=statements_text,
                        options=None,
                        correct_answer="",
                        explanation=gen_q.explanation,  # dict
                        difficulty="mixed",
                        subject=matrix_data['metadata']['subject'],
                        grade=matrix_data['metadata']['grade'],
                        chapter=str(gen_q.chapter_number),
                        lesson=str(gen_q.lesson_number),
                        lesson_name=gen_q.lesson_name,
                        generated_at=datetime.now().isoformat(),
                        question_code=gen_q.question_code,  # Store code from matrix
                        source_text=gen_q.source_text,
                        statements=gen_q.statements,
                        # Add DS metadata fields
                        source_citation=gen_q.source_citation,
                        source_origin=gen_q.source_origin,
                        source_type=gen_q.source_type,
                        pedagogical_approach=gen_q.pedagogical_approach,
                        search_evidence=gen_q.search_evidence
                    )
                elif gen_q.question_type == "TL" or getattr(gen_q, 'question_type_main', None) == "TL":  # TL (Essay) question
                    # Convert TL to standard format - store full essay structure
                    question = GeneratedQuestion(
                        id=f"{matrix_data['metadata']['subject']}_{matrix_data['metadata']['grade']}_{gen_q.chapter_number}_{gen_q.lesson_number}_TL_{gen_q.question_code}",
                        type="TL",
                        question=gen_q.question_stem,
                        options=None,  # TL has no options
                        correct_answer=gen_q.sample_answer,  # Sample answer as correct answer
                        explanation={
                            "question_type": gen_q.question_type,
                            "historical_context": gen_q.historical_context,
                            "required_elements": gen_q.required_elements,
                            "answer_structure": gen_q.answer_structure,
                            "key_points": gen_q.key_points,
                            "scoring_rubric": gen_q.scoring_rubric
                        },
                        difficulty=gen_q.level,
                        subject=matrix_data['metadata']['subject'],
                        grade=matrix_data['metadata']['grade'],
                        chapter=str(gen_q.chapter_number),
                        lesson=str(gen_q.lesson_number),
                        lesson_name=gen_q.lesson_name,
                        generated_at=datetime.now().isoformat(),
                        question_code=gen_q.question_code
                    )
                else:  # TN or TLN question (both have question_stem structure)
                    question = GeneratedQuestion(
                        id=f"{matrix_data['metadata']['subject']}_{matrix_data['metadata']['grade']}_{gen_q.chapter_number}_{gen_q.lesson_number}_{gen_q.question_type}_{gen_q.question_code}",
                        type=gen_q.question_type,
                        question=gen_q.question_stem,
                        options=gen_q.options,  # TN has A/B/C/D, TLN has empty dict
                        correct_answer=gen_q.correct_answer,
                        explanation=gen_q.explanation,
                        difficulty=gen_q.level,
                        subject=matrix_data['metadata']['subject'],
                        grade=matrix_data['metadata']['grade'],
                        chapter=str(gen_q.chapter_number),
                        lesson=str(gen_q.lesson_number),
                        lesson_name=gen_q.lesson_name,
                        generated_at=datetime.now().isoformat()
                    )
                    # Store question_code as attribute for later use
                    question.question_code = gen_q.question_code
                questions.append(question)

            # Create question set
            if questions:
                question_set = self.create_question_set(questions)
                return question_set

            return None
            
        except Exception as e:
            print(f"Error in _generate_questions_from_matrix: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _check_missing_questions(self, matrix_data: Dict, question_set: QuestionSet, 
                                 question_types: List[str]) -> Dict:
        """
        Check if all expected questions are generated
        
        Returns:
            Dict with keys: has_missing, expected, generated, missing
        """
        # Count expected questions from matrix
        expected_counts = {'TN': 0, 'DS': 0, 'TLN': 0, 'TL': 0}
        
        for lesson_data in matrix_data['lessons']:
            for q_type in question_types:
                if q_type == 'TN':
                    tn_specs = lesson_data.get('TN', {})
                    for level, specs in tn_specs.items():
                        for spec in specs:
                            expected_counts['TN'] += spec.get('num', 1)
                            
                elif q_type == 'DS':
                    ds_specs = lesson_data.get('DS', [])
                    expected_counts['DS'] += len(ds_specs)
                            
                elif q_type == 'TLN':
                    tln_specs = lesson_data.get('TLN', {})
                    for level, specs in tln_specs.items():
                        for spec in specs:
                            expected_counts['TLN'] += spec.get('num', 1)
                            
                elif q_type == 'TL':
                    tl_specs = lesson_data.get('TL', {})
                    for level, specs in tl_specs.items():
                        for spec in specs:
                            expected_counts['TL'] += spec.get('num', 1)
        
        # Count generated questions
        generated_counts = {
            'TN': len([q for q in question_set.questions if q.type == 'TN']),
            'DS': len([q for q in question_set.questions if q.type == 'DS']),
            'TLN': len([q for q in question_set.questions if q.type == 'TLN']),
            'TL': len([q for q in question_set.questions if q.type == 'TL'])
        }
        
        # Calculate missing
        missing_counts = {
            q_type: max(0, expected_counts[q_type] - generated_counts[q_type])
            for q_type in ['TN', 'DS', 'TLN', 'TL']
        }
        
        has_missing = any(count > 0 for count in missing_counts.values())
        
        return {
            'has_missing': has_missing,
            'expected': expected_counts,
            'generated': generated_counts,
            'missing': missing_counts
        }
    
    def _generate_missing_questions(self, matrix_data: Dict, missing_info: Dict) -> List:
        """Generate only the missing questions"""
        missing_counts = missing_info['missing']
        all_missing_questions = []
        
        print(f"\n🔄 Generating missing questions...")
        
        for q_type, missing_count in missing_counts.items():
            if missing_count <= 0:
                continue
                
            print(f"   Generating {missing_count} missing {q_type} questions...")
            
            # Find lessons that need more questions
            for lesson_data in matrix_data['lessons']:
                if missing_count <= 0:
                    break
                    
                chapter = lesson_data['chapter_number']
                lesson = lesson_data['lesson_number']
                content = lesson_data.get('content', '')
                supplementary = lesson_data.get('supplementary_material', '')
                
                if q_type == 'TN':
                    # Generate missing TN questions
                    tn_specs = lesson_data.get('TN', {})
                    for level, specs in tn_specs.items():
                        if missing_count <= 0:
                            break
                        for spec in specs:
                            if missing_count <= 0:
                                break
                            task = {
                                'type': 'TN_SINGLE',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary,
                                'spec_data': spec,
                                'level': level
                            }
                            try:
                                questions = self._generate_alternative_question_task(task)
                                if questions:
                                    all_missing_questions.extend(questions)
                                    missing_count -= len(questions)
                            except Exception as e:
                                print(f"❌ Error generating missing TN: {e}")
                                
                elif q_type == 'DS':
                    # Generate missing DS questions - DS is stored as a list
                    ds_specs = lesson_data.get('DS', [])
                    for spec_data in ds_specs:
                        if missing_count <= 0:
                            break
                        
                        # Select prompt for this DS question
                        selected_prompt = self.select_ds_prompt(lesson_data)
                        
                        task = {
                            'type': 'DS_TOPIC_BASED',
                            'lesson_data': lesson_data,
                            'chapter': chapter,
                            'lesson': lesson,
                            'content': content,
                            'supplementary': spec_data.get('supplementary_materials', ''),
                            'spec_data': spec_data,
                            'selected_prompt': selected_prompt
                        }
                        try:
                            questions = self._generate_alternative_question_task(task)
                            if questions:
                                all_missing_questions.extend(questions)
                                missing_count -= len(questions)
                        except Exception as e:
                            print(f"❌ Error generating missing DS: {e}")
                                
                elif q_type == 'TLN':
                    # Generate missing TLN questions
                    tln_specs = lesson_data.get('TLN', {})
                    for level, specs in tln_specs.items():
                        if missing_count <= 0:
                            break
                        for spec in specs:
                            if missing_count <= 0:
                                break
                            task = {
                                'type': 'TLN_SINGLE',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary,
                                'spec_data': spec,
                                'level': level
                            }
                            try:
                                questions = self._generate_alternative_question_task(task)
                                if questions:
                                    all_missing_questions.extend(questions)
                                    missing_count -= len(questions)
                            except Exception as e:
                                print(f"❌ Error generating missing TLN: {e}")
                                
                elif q_type == 'TL':
                    # Generate missing TL questions
                    tl_specs = lesson_data.get('TL', {})
                    for level, specs in tl_specs.items():
                        if missing_count <= 0:
                            break
                        for spec in specs:
                            if missing_count <= 0:
                                break
                            task = {
                                'type': 'TL_SINGLE',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary,
                                'spec_data': spec,
                                'level': level
                            }
                            try:
                                questions = self._generate_alternative_question_task(task)
                                if questions:
                                    all_missing_questions.extend(questions)
                                    missing_count -= len(questions)
                            except Exception as e:
                                print(f"❌ Error generating missing TL: {e}")
        
        return all_missing_questions
    
    def _merge_question_sets(self, existing_set: QuestionSet, new_questions: List) -> QuestionSet:
        """Merge new questions into existing question set"""
        # Convert new questions to GeneratedQuestion format
        for gen_q in new_questions:
            if gen_q.question_type == "DS":
                question = GeneratedQuestion(
                    id=f"{existing_set.subject}_{existing_set.grade}_{gen_q.chapter_number}_{gen_q.lesson_number}_DS_{gen_q.question_code}",
                    type="DS",
                    question=None,
                    source_text=gen_q.source_text,
                    statements=gen_q.statements,
                    correct_answer=None,
                    explanation=gen_q.explanation,
                    difficulty=gen_q.level,
                    subject=existing_set.subject,
                    grade=existing_set.grade,
                    chapter=str(gen_q.chapter_number),
                    lesson=str(gen_q.lesson_number),
                    lesson_name=gen_q.lesson_name,
                    generated_at=datetime.now().isoformat(),
                    source_citation=getattr(gen_q, 'source_citation', None),
                    source_origin=getattr(gen_q, 'source_origin', None),
                    source_type=getattr(gen_q, 'source_type', None),
                    pedagogical_approach=getattr(gen_q, 'pedagogical_approach', None),
                    search_evidence=getattr(gen_q, 'search_evidence', None)
                )
            elif gen_q.question_type == "TL" or getattr(gen_q, 'question_type_main', None) == "TL":
                question = GeneratedQuestion(
                    id=f"{existing_set.subject}_{existing_set.grade}_{gen_q.chapter_number}_{gen_q.lesson_number}_TL_{gen_q.question_code}",
                    type="TL",
                    question=gen_q.question_stem,
                    options=None,
                    correct_answer=gen_q.correct_answer,
                    explanation=gen_q.explanation,
                    difficulty=gen_q.level,
                    subject=existing_set.subject,
                    grade=existing_set.grade,
                    chapter=str(gen_q.chapter_number),
                    lesson=str(gen_q.lesson_number),
                    lesson_name=gen_q.lesson_name,
                    generated_at=datetime.now().isoformat()
                )
            else:
                question = GeneratedQuestion(
                    id=f"{existing_set.subject}_{existing_set.grade}_{gen_q.chapter_number}_{gen_q.lesson_number}_{gen_q.question_type}_{gen_q.question_code}",
                    type=gen_q.question_type,
                    question=gen_q.question_stem,
                    options=gen_q.options,
                    correct_answer=gen_q.correct_answer,
                    explanation=gen_q.explanation,
                    difficulty=gen_q.level,
                    subject=existing_set.subject,
                    grade=existing_set.grade,
                    chapter=str(gen_q.chapter_number),
                    lesson=str(gen_q.lesson_number),
                    lesson_name=gen_q.lesson_name,
                    generated_at=datetime.now().isoformat()
                )
            question.question_code = gen_q.question_code
            existing_set.questions.append(question)
        
        # Update total count
        existing_set.total_questions = len(existing_set.questions)
        
        return existing_set

    def _generate_alternative_question_task(self, task: Dict) -> List:
        """Generate questions for a single alternative task with model fallback on 429 errors"""
        primary_retries = 5
        fallback_retries = 3
        total_max_retries = primary_retries + fallback_retries
        
        attempt = 0
        current_model = self.primary_model
        using_fallback = False
        
        while attempt < total_max_retries:
            try:
                # Switch to fallback model after primary retries exhausted
                if attempt >= primary_retries and not using_fallback:
                    current_model = self.fallback_model
                    using_fallback = True
                    print(f"🔄 Switching to fallback model: {current_model}")
                    # Update the model in genai_client and question_generator
                    if self.genai_client:
                        self.genai_client.model_name = current_model
                    if self.question_generator and self.question_generator.ai_client:
                        self.question_generator.ai_client.model_name = current_model
                task_type = task['type']
                lesson_data = task['lesson_data']
                chapter = task['chapter']
                lesson = task['lesson']
                content = task['content']
                supplementary = task['supplementary']

                generated_questions = []

                if task_type == "TN_SINGLE":
                    # Single TN generation (NB or TH) using TN2.txt
                    spec_data = task['spec_data']
                    level = task['level']

                    # Extract question codes from spec
                    codes = spec_data.get('code', [])
                    if isinstance(codes, list) and codes:
                        question_codes = codes
                    else:
                        question_codes = [f"{level}1"]  # Fallback

                    num_questions = spec_data.get('num', len(question_codes))

                    # Create spec
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,
                        cognitive_level=level,
                        question_type="TN",
                        num_questions=num_questions,
                        question_codes=question_codes,
                        learning_outcome=spec_data.get('learning_outcome', ''),
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Load TN2 prompt template
                    prompt_template = self.load_prompt_template("TN2.txt")
                    if not prompt_template:
                        return []

                    # Replace placeholders in template
                    if level == 'NB':
                        template_vars = {
                            "NUM_NB": num_questions,
                            "NUM_TH": 0,
                            "NB": "Nhận biết",
                            "TH": "Thông hiểu",
                            "EXPECTED_LEARNING_OUTCOME": spec.learning_outcome,
                            "LESSON_NAME": spec.lesson_name,
                            "CONTENT": content,
                            "QUESTION_TEMPLATE_NB": "\n".join(spec_data.get('question_template', [''])),
                            "QUESTION_TEMPLATE_TH": ""
                        }
                    else:  # TH
                        template_vars = {
                            "NUM_NB": 0,
                            "NUM_TH": num_questions,
                            "NB": "Nhận biết",
                            "TH": "Thông hiểu",
                            "EXPECTED_LEARNING_OUTCOME": spec.learning_outcome,
                            "LESSON_NAME": spec.lesson_name,
                            "CONTENT": content,
                            "QUESTION_TEMPLATE_NB": "",
                            "QUESTION_TEMPLATE_TH": "\n".join(spec_data.get('question_template', ['']))
                        }

                    for var, value in template_vars.items():
                        prompt_template = prompt_template.replace("{{" + var + "}}", str(value))

                    # Generate questions
                    generated = self.question_generator.generate_questions_with_custom_prompt(
                        prompt_template=prompt_template,
                        content=content,
                        num_questions=num_questions
                    )
                    # Add chapter and lesson info + ensure correct codes
                    for idx, q in enumerate(generated):
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                        # Use code from matrix if available
                        if idx < len(question_codes):
                            q.question_code = question_codes[idx]
                    generated_questions.extend(generated)

                elif task_type == "TN_VD":
                    # Extract spec_data from task
                    spec_data = task['spec_data']
                    
                    # Extract question codes and num from spec
                    question_codes = spec_data.get('code', ['VD1'])
                    if not isinstance(question_codes, list):
                        question_codes = [question_codes]
                    num_questions = spec_data.get('num', len(question_codes))
                    
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,
                        cognitive_level="VD",
                        question_type="TN",
                        num_questions=num_questions,
                        question_codes=question_codes,
                        learning_outcome=spec_data.get('learning_outcome', ''),
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Load TN_VD.txt template (or TN_VD_case2.txt if exists)
                    prompt_template = self.load_prompt_template("TN_VD_case2.txt")
                    if not prompt_template:
                        # Fallback to TN_VD.txt
                        print(f"   ℹ️  TN_VD_case2.txt not found, using TN_VD.txt instead")
                        prompt_template = self.load_prompt_template("TN_VD.txt")
                    if not prompt_template:
                        print(f"❌ ERROR: Neither TN_VD_case2.txt nor TN_VD.txt found for VD generation")
                        return []
                    
                    print(f"   ✓ Using prompt template for VD generation")

                    # Replace placeholders
                    template_vars = {
                        "NUM": num_questions,
                        "EXPECTED_LEARNING_OUTCOME": spec.learning_outcome,
                        "LESSON_NAME": spec.lesson_name,
                        "CONTENT": content,
                        "QUESTION_TEMPLATE": spec_data.get('question_template', [''])[0] if spec_data.get('question_template') else ''
                    }

                    for var, value in template_vars.items():
                        prompt_template = prompt_template.replace("{{" + var + "}}", str(value))

                    # Generate VD questions
                    generated = self.question_generator.generate_questions_with_custom_prompt(
                        prompt_template=prompt_template,
                        content=content,
                        num_questions=num_questions
                    )
                    
                    # Extract question codes from spec
                    question_codes = spec_data.get('code', ['VD1'])
                    if not isinstance(question_codes, list):
                        question_codes = [question_codes]
                    
                    # Add chapter, lesson info and correct codes
                    for idx, q in enumerate(generated):
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                        # Use code from matrix if available
                        if idx < len(question_codes):
                            q.question_code = question_codes[idx]
                    generated_questions.extend(generated)

                elif task_type == "DS_TOPIC_BASED":
                    # DS generation with topic-based prompt selection
                    spec_data = task['spec_data']
                    selected_prompt_path = task['selected_prompt']

                    # Load the selected prompt
                    prompt_template = self.load_prompt_template_from_path(selected_prompt_path)
                    if not prompt_template:
                        return []

                    # Create TrueFalseQuestionSpec
                    from ..core.matrix_parser import TrueFalseQuestionSpec
                    spec = TrueFalseQuestionSpec(
                        question_code=spec_data.get('question_code', spec_data.get('code', ['DS1'])[0]),
                        lesson_name=lesson_data['lesson_name'],
                        statements=[],  # Will be generated by AI
                        question_type="DS",
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary,
                        rich_content_types=spec_data.get('rich_content_types', None)
                    )

                    # Replace placeholders in DS prompt
                    template_vars = {
                        "NUM": 1,
                        "LESSON_NAME": spec.lesson_name,
                        "CONTENT": content,
                        "LEARNING_OUTCOME": spec_data.get('learning_outcome', ''),
                        "TEXTBOOK_CONTENT": content,
                        "QUESTION_TEMPLATE": spec_data.get('question_template', [''])[0] if spec_data.get('question_template') else '',
                        "COGNITIVE_LEVEL_A": spec_data.get('cognitive_levels', {}).get('a', 'NB'),
                        "COGNITIVE_LEVEL_B": spec_data.get('cognitive_levels', {}).get('b', 'TH'),
                        "COGNITIVE_LEVEL_C": spec_data.get('cognitive_levels', {}).get('c', 'TH'),
                        "COGNITIVE_LEVEL_D": spec_data.get('cognitive_levels', {}).get('d', 'VD'),
                        "EXPECTED_LEARNING_OUTCOME_A": spec_data.get('expected_outcomes', {}).get('a', ''),
                        "EXPECTED_LEARNING_OUTCOME_B": spec_data.get('expected_outcomes', {}).get('b', ''),
                        "EXPECTED_LEARNING_OUTCOME_C": spec_data.get('expected_outcomes', {}).get('c', ''),
                        "EXPECTED_LEARNING_OUTCOME_D": spec_data.get('expected_outcomes', {}).get('d', ''),
                        "EXPECTED_OUTCOME_A": spec_data.get('expected_outcomes', {}).get('a', ''),
                        "EXPECTED_OUTCOME_B": spec_data.get('expected_outcomes', {}).get('b', ''),
                        "EXPECTED_OUTCOME_C": spec_data.get('expected_outcomes', {}).get('c', ''),
                        "EXPECTED_OUTCOME_D": spec_data.get('expected_outcomes', {}).get('d', '')
                    }

                    for var, value in template_vars.items():
                        prompt_template = prompt_template.replace("{{" + var + "}}", str(value))

                    # Generate DS question
                    generated_ds = self.question_generator.generate_ds_with_custom_prompt(
                        prompt_template=prompt_template,
                        content=content,
                        question_code=spec.question_code,
                        rich_content_types=spec_data.get('rich_content_types', None)
                    )
                    if generated_ds:
                        generated_ds.chapter_number = int(chapter)
                        generated_ds.lesson_number = int(lesson)
                        generated_questions.append(generated_ds)

                elif task_type == "TLN_SINGLE":
                    # TLN generation (Trả lời ngắn - Short answer)
                    spec_data = task['spec_data']
                    level = task['level']
                    prompt_path = task['prompt_path']

                    # Load TLN prompt
                    prompt_template = self.load_prompt_template_from_path(prompt_path)
                    if not prompt_template:
                        return []

                    # Get number of questions and codes
                    num_questions = spec_data.get('num', 1)
                    question_codes = spec_data.get('code', [])
                    if not isinstance(question_codes, list):
                        question_codes = [question_codes]

                    # Create spec
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,
                        cognitive_level=level,
                        question_type="TLN",
                        num_questions=num_questions,
                        question_codes=question_codes,
                        learning_outcome=spec_data.get('learning_outcome', ''),
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Replace placeholders in prompt
                    template_vars = {
                        "NUM": num_questions,
                        "LESSON_NAME": spec.lesson_name,
                        "CONTENT": content,
                        "COGNITIVE_LEVEL": level,
                        "EXPECTED_LEARNING_OUTCOME": spec.learning_outcome,
                        "TEXTBOOK_CONTENT": content,
                        "QUESTION_TEMPLATE": spec_data.get('question_template', [''])[0] if spec_data.get('question_template') else ''
                    }

                    for var, value in template_vars.items():
                        prompt_template = prompt_template.replace("{{" + var + "}}", str(value))

                    # Generate TLN questions
                    generated = self.question_generator.generate_questions_with_custom_prompt(
                        prompt_template=prompt_template,
                        content=content,
                        num_questions=num_questions
                    )
                    
                    # Add chapter, lesson info and correct codes
                    for idx, q in enumerate(generated):
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                        q.question_type = "TLN"
                        # Use code from matrix if available
                        if idx < len(question_codes):
                            q.question_code = question_codes[idx]
                    generated_questions.extend(generated)

                elif task_type == "TL_SINGLE":
                    # TL generation (Tự luận - Essay)
                    spec_data = task['spec_data']
                    level = task['level']
                    prompt_path = task['prompt_path']

                    # Get number of questions and codes
                    num_questions = spec_data.get('num', 1)
                    question_codes = spec_data.get('code', [])
                    if not isinstance(question_codes, list):
                        question_codes = [question_codes]

                    # Create spec
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,
                        cognitive_level=level,
                        question_type="TL",
                        num_questions=num_questions,
                        question_codes=question_codes,
                        learning_outcome=spec_data.get('learning_outcome', ''),
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Get question template if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    # Generate TL questions using the new generate_tl_questions method
                    generated = self.question_generator.generate_tl_questions(
                        spec=spec,
                        prompt_template_path=prompt_path,
                        content=content,
                        question_template=question_template
                    )
                    
                    # Add chapter, lesson info and correct codes
                    for idx, q in enumerate(generated):
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                        q.question_type = "TL"
                        # Use code from matrix if available
                        if idx < len(question_codes):
                            q.question_code = question_codes[idx]
                    generated_questions.extend(generated)

                # Return generated questions after successful completion
                return generated_questions

            except Exception as e:
                error_message = str(e)
                task_type = task.get('type', 'UNKNOWN')
                chapter = task.get('chapter', '?')
                lesson = task.get('lesson', '?')
                
                # Check if it's a rate limit error (429)
                if '429' in error_message or 'RESOURCE_EXHAUSTED' in error_message:
                    attempt += 1
                    if attempt < total_max_retries:
                        # Exponential backoff with cap at 60 seconds
                        wait_time = min(5 * (2 ** min(attempt, 4)), 60) + random.uniform(0, 3)
                        
                        if attempt <= primary_retries:
                            print(f"⚠️ Rate limit (429) for {task_type} lesson {chapter}.{lesson} with {current_model}")
                            print(f"   🔄 Retry {attempt}/{primary_retries} with primary model - waiting {wait_time:.1f}s")
                        else:
                            fallback_attempt = attempt - primary_retries
                            print(f"⚠️ Rate limit (429) for {task_type} lesson {chapter}.{lesson} with {current_model}")
                            print(f"   🔄 Retry {fallback_attempt}/{fallback_retries} with fallback model - waiting {wait_time:.1f}s")
                        
                        time.sleep(wait_time)
                        continue  # Retry with current or fallback model
                    else:
                        print(f"❌ CRITICAL: All retries exhausted ({total_max_retries}) for {task_type} lesson {chapter}.{lesson}")
                        print(f"   Tried {primary_retries} times with {self.primary_model}")
                        print(f"   Tried {fallback_retries} times with {self.fallback_model}")
                        print(f"   ⚠️ This task will return EMPTY and cause missing questions!")
                        return []
                else:
                    # Other errors - only retry 3 times
                    attempt += 1
                    if attempt < 3:
                        wait_time = 2 ** attempt + random.uniform(0, 1)
                        print(f"⚠️ Error in {task_type} for lesson {chapter}.{lesson}: {e}")
                        print(f"   Retrying in {wait_time:.1f}s (attempt {attempt}/3)")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ CRITICAL: Max retries (3) reached for {task_type} lesson {chapter}.{lesson}")
                        print(f"   Error: {e}")
                        import traceback
                        traceback.print_exc()
                        return []
        
        # This line should never be reached but keep as safety
        print(f"⚠️ WARNING: Unexpected exit from retry loop for {task.get('type')} task")
        return []

    def load_prompt_template(self, template_name: str) -> Optional[str]:
        """Load prompt template by name"""
        prompt_file = self.prompts_dir / template_name
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # print(f"❌ Prompt template not found: {template_name}")
            return None
        except Exception as e:
            # print(f"❌ Error loading prompt template {template_name}: {e}")
            return None

    def load_prompt_template_from_path(self, template_path: str) -> Optional[str]:
        """Load prompt template from full path"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # print(f"❌ Prompt template not found: {template_path}")
            return None
        except Exception as e:
            # print(f"❌ Error loading prompt template {template_path}: {e}")
            return None

    def create_question_set(self, questions: List[GeneratedQuestion]) -> QuestionSet:
        """Create a question set from generated questions"""
        if not questions:
            return None

        # All questions should have same metadata
        first_q = questions[0]

        return QuestionSet(
            subject=first_q.subject,
            grade=first_q.grade,
            chapter=first_q.chapter,
            lesson=first_q.lesson,
            question_type=first_q.type,
            questions=questions,
            total_questions=len(questions),
            generated_at=datetime.now().isoformat()
        )

    def save_question_set(self, question_set: QuestionSet,
                        output_dir: Path = Path("data/questions"),
                        session_id: str = None,
                        matrix_file: str = None) -> Path:
        """Save question set to JSON file"""
        import uuid

        if session_id is None:
            session_id = str(uuid.uuid4())
        if matrix_file is None:
            matrix_file = f"{question_set.subject}_{question_set.grade}_matrix"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"questions_{question_set.subject}_{question_set.grade}_{question_set.chapter}_{question_set.lesson}_alternative.json"
        output_path = output_dir / filename

        # Group questions by type
        tn_questions = []
        ds_questions = []
        tln_questions = []
        tl_questions = []

        for q in question_set.questions:
            if q.type == "TN":
                # Extract question_code properly - check if it's stored in the question object first
                question_code = getattr(q, 'question_code', None) or q.id.split('_')[-1]
                tn_questions.append({
                    'question_code': question_code,
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'chapter_number': q.chapter,
                    'lesson_number': q.lesson,
                    'level': q.difficulty,
                    'question_stem': q.question,
                    'options': q.options,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation
                })
            elif q.type == "DS":
                if isinstance(q.explanation, dict):
                    explanation_dict = q.explanation
                else:
                    explanation_dict = json.loads(q.explanation) if q.explanation else {}
                # Ensure explanation has the correct structure with a, b, c, d keys
                normalized_explanation = {
                    "a": explanation_dict.get("a", ""),
                    "b": explanation_dict.get("b", ""),
                    "c": explanation_dict.get("c", ""),
                    "d": explanation_dict.get("d", "")
                }
                # Extract question_code properly
                question_code = getattr(q, 'question_code', None) or q.id.split('_')[-1]
                ds_question = {
                    'question_code': question_code,
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'chapter_number': q.chapter,
                    'lesson_number': q.lesson,
                    'level': q.difficulty,
                    'source_text': q.source_text,
                    'statements': q.statements,
                    'explanation': normalized_explanation
                }
                # Add metadata fields if available
                if q.source_citation:
                    ds_question['source_citation'] = q.source_citation
                if q.source_origin:
                    ds_question['source_origin'] = q.source_origin
                if q.source_type:
                    ds_question['source_type'] = q.source_type
                if q.pedagogical_approach:
                    ds_question['pedagogical_approach'] = q.pedagogical_approach
                if q.search_evidence:
                    ds_question['search_evidence'] = q.search_evidence
                ds_questions.append(ds_question)
            elif q.type == "TLN":
                tln_questions.append({
                    'question_code': getattr(q, 'question_code', None) or q.id.split('_')[-1],
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'chapter_number': q.chapter,
                    'lesson_number': q.lesson,
                    'level': q.difficulty,
                    'question_stem': q.question,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation
                })
            elif q.type == "TL":
                tl_questions.append({
                    'question_code': getattr(q, 'question_code', None) or q.id.split('_')[-1],
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'chapter_number': q.chapter,
                    'lesson_number': q.lesson,
                    'level': q.difficulty,
                    'question_stem': q.question,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation
                })

        set_dict = {
            'metadata': {
                'session_id': session_id,
                'total_questions': question_set.total_questions,
                'tn_count': len(tn_questions),
                'ds_count': len(ds_questions),
                'tln_count': len(tln_questions),
                'tl_count': len(tl_questions),
                'matrix_file': matrix_file,
                'generated_at': question_set.generated_at,
                'generation_method': 'alternative_logic',
                'status': 'completed'
            },
            'questions': {
                'TN': tn_questions,
                'DS': ds_questions,
                'TLN': tln_questions,
                'TL': tl_questions
            }
        }
    
    def _deduplicate_questions(self, question_set: QuestionSet) -> QuestionSet:
        """
        Remove duplicate questions based on question_code, lesson_name, and level
        Keep the first occurrence of each unique question
        """
        seen = set()
        unique_questions = []
        duplicates_removed = 0
        
        for question in question_set.questions:
            # Create a unique key for each question
            # Handle both GeneratedQuestion (from phase4, has 'id') and question_generator objects (have 'question_code')
            try:
                q_code = question.question_code if hasattr(question, 'question_code') else question.id
                q_lesson = question.lesson_name if hasattr(question, 'lesson_name') else question.lesson
                q_level = question.level if hasattr(question, 'level') else question.difficulty
                q_type = question.type if hasattr(question, 'type') else getattr(question, 'question_type', 'unknown')
            except AttributeError as e:
                print(f"⚠️ WARNING: Cannot extract dedup key from question: {e}")
                # Include all questions that can't be deduplicated
                unique_questions.append(question)
                continue
                
            key = (q_code, q_lesson, q_level, q_type)
            
            if key not in seen:
                seen.add(key)
                unique_questions.append(question)
            else:
                duplicates_removed += 1
                print(f"🗑️ Removed duplicate: {q_type} {q_code} - {q_lesson} ({q_level})")
        
        if duplicates_removed > 0:
            print(f"\n✅ Removed {duplicates_removed} duplicate questions")
        
        # Create new QuestionSet with unique questions
        return QuestionSet(
            subject=question_set.subject,
            grade=question_set.grade,
            chapter=question_set.chapter,
            lesson=question_set.lesson,
            question_type=question_set.question_type,
            questions=unique_questions,
            total_questions=len(unique_questions),
            generated_at=question_set.generated_at
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(set_dict, f, ensure_ascii=False, indent=2)

        return output_path