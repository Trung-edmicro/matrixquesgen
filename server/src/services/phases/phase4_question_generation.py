"""
Phase 4: Question Generation Service
Handles generating questions from extracted lesson content
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
from ..core.content_validator import clean_all_questions
from ..generators.question_generator import QuestionGenerator
from ..core.matrix_parser import MatrixParser, QuestionSpec, TrueFalseQuestionSpec

# Import rich content support
from data.rich_content import (
    ContentBlock, ContentType,
    text as text_block, mixed as mixed_block
)


@dataclass
class GeneratedQuestion:
    """Generated question structure with rich content support"""
    id: str
    type: str  # 'multiple_choice', 'true_false', 'short_answer', etc.
    question: Union[str, Dict[str, Any]]  # Support both simple text and rich content
    correct_answer: Union[str, Dict[str, Any]]
    subject: str
    grade: str
    chapter: str
    lesson: str
    lesson_name: str
    generated_at: str
    options: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None
    explanation: Optional[Union[str, Dict[str, Any]]] = None
    difficulty: str = 'medium'
    # For DS questions
    source_text: Optional[Union[str, Dict[str, Any]]] = None
    statements: Optional[Dict[str, Dict]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling rich content serialization"""
        result = {
            'id': self.id,
            'type': self.type,
            'question': self._serialize_content(self.question),
            'correct_answer': self._serialize_content(self.correct_answer),
            'subject': self.subject,
            'grade': self.grade,
            'chapter': self.chapter,
            'lesson': self.lesson,
            'lesson_name': self.lesson_name,
            'generated_at': self.generated_at,
            'difficulty': self.difficulty
        }
        
        if self.options:
            result['options'] = {k: self._serialize_content(v) for k, v in self.options.items()}
        if self.explanation:
            result['explanation'] = self._serialize_content(self.explanation)
        if self.source_text:
            result['source_text'] = self._serialize_content(self.source_text)
        if self.statements:
            result['statements'] = self.statements
            
        return result
    
    @staticmethod
    def _serialize_content(content: Union[str, Dict, ContentBlock]) -> Union[str, Dict]:
        """Serialize content to JSON-compatible format"""
        if isinstance(content, ContentBlock):
            return content.to_dict()
        elif isinstance(content, dict) and isinstance(content.values().__iter__().__next__(), (ContentBlock, dict)):
            return {k: GeneratedQuestion._serialize_content(v) for k, v in content.items()}
        return content


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


class QuestionGenerationService:
    """Service for generating questions from lesson content using existing GenAI infrastructure"""

    def __init__(self, ai_provider: str = "genai"):
        self.ai_provider = ai_provider
        # Base prompts directory
        if os.getenv('APP_DIR'):
            self.prompts_base_dir = Path(os.getenv('APP_DIR')) / "data" / "prompts"
        else:
            self.prompts_base_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "prompts"
        
        # Default prompts directory (will be updated by set_prompts_directory)
        self.prompts_dir = self.prompts_base_dir

        # Initialize existing AI client
        self.genai_client = None
        self.question_generator = None
        self.matrix_parser = MatrixParser()  # Initialize matrix parser for sample questions
        
        # Track primary and fallback models for retry logic
        self.primary_model = "gemini-3-pro-preview"  # Default primary model
        self.fallback_model = "gemini-2.5-pro"  # Fallback model for rate limits

        if ai_provider == "genai":
            # Initialize GenAI client
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "matrixquesgen")
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            api_key = os.getenv("GENAI_API_KEY")

            try:
                self.genai_client = GenAIClient(
                    project_id=project_id,
                    credentials_path=credentials_path,
                    api_key=api_key
                )
                # Update primary_model from actual client
                if self.genai_client and self.genai_client.model_name:
                    self.primary_model = self.genai_client.model_name
                # Don't initialize QuestionGenerator here - will be done when prompts directory is set
                print("✅ Initialized GenAI client for question generation service")
                print(f"✓ Configured retry strategy:")
                print(f"   Primary model: {self.primary_model} (5 retries)")
                print(f"   Fallback model: {self.fallback_model} (3 retries)")
            except Exception as e:
                print(f"❌ Failed to initialize GenAI client: {e}")
                print(f"   Project ID: {project_id}")
                print(f"   Credentials path: {credentials_path}")
                print(f"   API key: {'***' if api_key else None}")
                self.genai_client = None
                self.question_generator = None

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
        
        # Initialize QuestionGenerator now that we have the correct prompts directory
        if self.genai_client and not self.question_generator:
            try:
                # Try to find TN prompt file (TN2.txt or TN.txt)
                tn_prompt_path = None
                if (self.prompts_dir / "TN2.txt").exists():
                    tn_prompt_path = str(self.prompts_dir / "TN2.txt")
                    print(f"✓ Using TN2.txt for QuestionGenerator init")
                elif (self.prompts_dir / "TN.txt").exists():
                    tn_prompt_path = str(self.prompts_dir / "TN.txt")
                    print(f"✓ Using TN.txt for QuestionGenerator init")
                
                if tn_prompt_path:
                    self.question_generator = QuestionGenerator(
                        ai_client=self.genai_client,
                        prompt_template_path=tn_prompt_path,
                        verbose=True,
                        matrix_parser=self.matrix_parser
                    )
                    print(f"✓ QuestionGenerator initialized with {Path(tn_prompt_path).name}")
                else:
                    print(f"⚠️ Neither TN.txt nor TN2.txt found in {self.prompts_dir}")
                    print(f"   QuestionGenerator will not be initialized")
                    self.question_generator = None
            except Exception as e:
                print(f"❌ Failed to initialize QuestionGenerator: {e}")

    def process_question_generation(self, extracted_lesson: Any, question_type: str, num_questions: int = 5) -> Optional[QuestionSet]:
        """Process question generation for an extracted lesson"""
        try:
            if not self.question_generator:
                print("❌ Question generator not initialized")
                return None

            # Generate questions using lesson content and specs
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
                print(f"⚠️  No {question_type} specs found for lesson {chapter}.{lesson}")
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
            print(f"❌ Error in process_question_generation: {e}")
            return None

    def load_prompt_template(self, question_type: str) -> Optional[str]:
        """Load prompt template for specific question type"""
        prompt_file = self.prompts_dir / f"{question_type}.txt"
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Prompt template not found for question type: {question_type}")
            return None
        except Exception as e:
            print(f"❌ Error loading prompt template {prompt_file}: {e}")
            return None

    def generate_questions(self, content: str, subject: str, grade: str,
                         chapter: str, lesson: str, question_type: str = "TN",
                         num_questions: int = 5, difficulty: str = "medium") -> List[GeneratedQuestion]:
        """Generate questions from lesson content using existing infrastructure"""
        try:
            if not self.question_generator:
                print("❌ Question generator not initialized")
                return []

            # Create QuestionSpec for the existing generator
            spec = QuestionSpec(
                question_codes=[f"C{i+1}" for i in range(num_questions)],
                lesson_name=f"Chương {chapter} - Bài {lesson}",
                question_type=question_type,
                cognitive_level=difficulty,
                learning_outcome=f"Học sinh hiểu và nắm vững nội dung bài học Chương {chapter} Bài {lesson}",
                num_questions=num_questions,
                competency_level=1,  # Default competency level
                row_index=0  # Default row index
            )

            # Generate questions using existing infrastructure
            generated_questions = self.question_generator.generate_questions_for_spec(
                spec=spec,
                content=content
            )

            # Convert to our GeneratedQuestion format
            questions = []
            for gen_q in generated_questions:
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
                    generated_at=datetime.now().isoformat()
                )
                questions.append(question)

            return questions

        except Exception as e:
            print(f"❌ Error generating questions: {e}")
            return []

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
        """Save question set to JSON file with rich content support"""
        import uuid
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        if matrix_file is None:
            matrix_file = f"{question_set.subject}_{question_set.grade}_matrix"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"questions_{question_set.subject}_{question_set.grade}_{question_set.chapter}_{question_set.lesson}.json"
        output_path = output_dir / filename

        # Group questions by type
        tn_questions = []
        ds_questions = []
        tln_questions = []
        tl_questions = []
        
        for q in question_set.questions:
            # Use to_dict() if available, otherwise manually serialize
            if hasattr(q, 'to_dict'):
                q_dict = q.to_dict()
            else:
                # Backward compatibility: manual serialization
                q_dict = {
                    'question_code': q.id.split('_')[-1],
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'question_stem': q.question if q.type != "DS" else None,
                    'source_text': q.source_text if q.type == "DS" else None,
                    'statements': q.statements if q.type == "DS" else None,
                    'options': q.options,
                    'correct_answer': q.correct_answer,
                    'explanation': q.explanation
                }
                # Remove None values
                q_dict = {k: v for k, v in q_dict.items() if v is not None}
            
            # Categorize by type
            if q.type == "TN":
                tn_questions.append({
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'question_stem': q_dict.get('question_stem', q.question),
                    'options': q_dict.get('options', q.options),
                    'correct_answer': q_dict.get('correct_answer', q.correct_answer),
                    'explanation': q_dict.get('explanation', q.explanation)
                })
            elif q.type == "DS":
                # Handle DS explanation normalization
                explanation = q_dict.get('explanation', q.explanation)
                if isinstance(explanation, dict):
                    explanation_dict = explanation
                else:
                    explanation_dict = json.loads(explanation) if explanation else {}
                normalized_explanation = {
                    "a": explanation_dict.get("a", ""),
                    "b": explanation_dict.get("b", ""),
                    "c": explanation_dict.get("c", ""),
                    "d": explanation_dict.get("d", "")
                }
                ds_questions.append({
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'source_text': q_dict.get('source_text', q.source_text),
                    'statements': q_dict.get('statements', q.statements),
                    'explanation': normalized_explanation
                })
            elif q.type == "TLN":
                tln_questions.append({
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'question_stem': q_dict.get('question_stem', q.question),
                    'correct_answer': q_dict.get('correct_answer', q.correct_answer),
                    'explanation': q_dict.get('explanation', q.explanation)
                })
            elif q.type == "TL":
                tl_questions.append({
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'question_stem': q_dict.get('question_stem', q.question),
                    'correct_answer': q_dict.get('correct_answer', q.correct_answer),
                    'explanation': q_dict.get('explanation', q.explanation)
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
                'status': 'completed',
                'content_version': '2.0',
                'supports_rich_content': True
            },
            'questions': {
                'TN': tn_questions,
                'DS': ds_questions,
                'TLN': tln_questions,
                'TL': tl_questions
            }
        }
        
        # Clean và validate rich content
        try:
            set_dict = clean_all_questions(set_dict)
            print("✅ Đã clean và validate rich content")
        except Exception as e:
            print(f"⚠️ Warning khi clean rich content: {e}")
            # Tiếp tục save ngay cả khi có lỗi

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(set_dict, f, ensure_ascii=False, indent=2)

        return output_path

    def process_enriched_matrix(self, enriched_matrix_path: Path, question_types: List[str] = None) -> Optional[QuestionSet]:
        """Process enriched matrix JSON and generate questions using multi-threading
        
        Args:
            enriched_matrix_path: Path to enriched matrix JSON file
            question_types: List of question types to generate (e.g., ["TN", "DS", "TLN", "TL"]). If None, generates all types.
        """
        if question_types is None:
            question_types = ["TN", "DS", "TLN", "TL"]
            
        try:
            # Load enriched matrix JSON
            with open(enriched_matrix_path, 'r', encoding='utf-8') as f:
                matrix_data = json.load(f)

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
                        # Process TN specs
                        tn_specs = lesson_data.get('TN', {})
                        for level, specs in tn_specs.items():
                            if not specs:
                                continue

                            for spec_data in specs:
                                # Create task for TN generation
                                task = {
                                    'type': 'TN',
                                    'lesson_data': lesson_data,
                                    'chapter': chapter,
                                    'lesson': lesson,
                                    'content': content,
                                    'supplementary': supplementary,
                                    'level': level,
                                    'spec_data': spec_data
                                }
                                generation_tasks.append(task)

                    elif question_type == "DS":
                        # Process DS specs
                        ds_specs = lesson_data.get('DS', [])
                        # print(f"DEBUG: Lesson {chapter}.{lesson} has {len(ds_specs)} DS specs")
                        for spec_data in ds_specs:
                            # print(f"DEBUG: Creating DS task for spec: {spec_data.get('question_code', 'unknown')}")
                            # Create task for DS generation
                            task = {
                                'type': 'DS',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': spec_data.get('materials', ''),
                                'spec_data': spec_data
                            }
                            generation_tasks.append(task)

                    elif question_type == "TLN":
                        # Process TLN specs
                        tln_specs = lesson_data.get('TLN', {})
                        for level, specs in tln_specs.items():
                            if not specs:
                                continue

                            for spec_data in specs:
                                # Create task for TLN generation
                                task = {
                                    'type': 'TLN',
                                    'lesson_data': lesson_data,
                                    'chapter': chapter,
                                    'lesson': lesson,
                                    'content': content,
                                    'supplementary': supplementary,
                                    'level': level,
                                    'spec_data': spec_data
                                }
                                generation_tasks.append(task)

                    elif question_type == "TL":
                        # Process TL specs (Tự luận - Essay)
                        tl_specs = lesson_data.get('TL', {})
                        for level, specs in tl_specs.items():
                            if not specs:
                                continue

                            for spec_data in specs:
                                # Create task for TL generation
                                task = {
                                    'type': 'TL',
                                    'lesson_data': lesson_data,
                                    'chapter': chapter,
                                    'lesson': lesson,
                                    'content': content,
                                    'supplementary': supplementary,
                                    'level': level,
                                    'spec_data': spec_data
                                }
                                generation_tasks.append(task)

            # Execute generation tasks in parallel
            print(f"Starting parallel generation of {len(generation_tasks)} question tasks...")
            
            # Giảm workers để tránh rate limit 429
            max_workers = min(5, len(generation_tasks))
            print(f"   Using {max_workers} parallel workers to avoid API rate limits")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(self._generate_question_task, task): task
                    for task in generation_tasks
                }

                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        generated_questions = future.result()
                        if generated_questions:
                            all_questions.extend(generated_questions)
                            print(f"✅ Completed {task['type']} task for lesson {task['chapter']}.{task['lesson']} - {len(generated_questions)} questions")
                    except Exception as e:
                        print(f"❌ Failed {task['type']} task for lesson {task['chapter']}.{task['lesson']}: {e}")

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
                        source_text=gen_q.source_text,
                        statements=gen_q.statements
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
                questions.append(question)

            # Create question set
            if questions:
                question_set = self.create_question_set(questions)
                return question_set

            return None

        except Exception as e:
            print(f"❌ Error processing enriched matrix: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_question_task(self, task: Dict) -> List:
        """Generate questions for a single task with retry logic and fallback model"""
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

                if task_type == "TN":
                    level = task['level']
                    spec_data = task['spec_data']

                    # Create QuestionSpec from enriched data
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,  # Default
                        cognitive_level=level,
                        question_type="TN",
                        num_questions=spec_data['num'],
                        question_codes=spec_data['code'],
                        learning_outcome=spec_data['learning_outcome'],
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Use question templates if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    # Generate questions
                    generated = self.question_generator.generate_questions_for_spec(
                        spec=spec,
                        content=content,
                        question_template=question_template
                    )
                    # Add chapter and lesson info to generated questions
                    for q in generated:
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                    generated_questions.extend(generated)

                elif task_type == "DS":
                    spec_data = task['spec_data']

                    # Get question template from enriched data
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    # Parse statements from enriched data (if available)
                    statements = []
                    if 'statements' in spec_data:
                        for stmt in spec_data['statements']:
                            from ..core.matrix_parser import StatementSpec
                            statements.append(StatementSpec(
                                statement_code=f"{spec_data.get('question_code', 'DS1')}{stmt['label'].upper()}",
                                label=stmt['label'],
                                cognitive_level=stmt['cognitive_level'],
                                learning_outcome=stmt.get('learning_outcome', ''),
                                supplementary_materials=supplementary
                            ))

                    # Create TrueFalseQuestionSpec from enriched data
                    from ..core.matrix_parser import TrueFalseQuestionSpec
                    spec = TrueFalseQuestionSpec(
                        question_code=spec_data.get('question_code', spec_data.get('code', ['DS1'])[0]),
                        lesson_name=lesson_data['lesson_name'],
                        statements=statements,
                        question_type="DS",
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Generate DS questions
                    generated_ds = self.question_generator.generate_true_false_question(
                        tf_spec=spec,
                        prompt_template_path=str(self.prompts_dir / "DS.txt"),
                        content=content,
                        question_template=question_template
                    )
                    # Add chapter and lesson info to generated DS question
                    generated_ds.chapter_number = int(chapter)
                    generated_ds.lesson_number = int(lesson)
                    generated_questions.append(generated_ds)

                elif task_type == "TLN":
                    level = task['level']
                    spec_data = task['spec_data']

                    # Create QuestionSpec for TLN
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,  # Default
                        cognitive_level=level,
                        question_type="TLN",
                        num_questions=spec_data['num'],
                        question_codes=spec_data['code'],
                        learning_outcome=spec_data['learning_outcome'],
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Use question templates if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    # Generate TLN questions using TLN prompt
                    generated = self.question_generator.generate_tln_questions(
                        spec=spec,
                        prompt_template_path=str(self.prompts_dir / "TLN.txt"),
                        content=content,
                        question_template=question_template
                    )
                    # Add chapter and lesson info to generated questions
                    for q in generated:
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                    generated_questions.extend(generated)

                elif task_type == "TL":
                    level = task['level']
                    spec_data = task['spec_data']

                    # Create QuestionSpec for TL (Tự luận - Essay)
                    from ..core.matrix_parser import QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=lesson_data['lesson_name'],
                        competency_level=1,  # Default
                        cognitive_level=level,
                        question_type="TL",
                        num_questions=spec_data['num'],
                        question_codes=spec_data['code'],
                        learning_outcome=spec_data['learning_outcome'],
                        row_index=0,
                        chapter_number=int(chapter),
                        supplementary_materials=supplementary
                    )

                    # Use question templates if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    # Generate TL questions using TL prompt (essay questions with full structure)
                    generated = self.question_generator.generate_tl_questions(
                        spec=spec,
                        prompt_template_path=str(self.prompts_dir / "TL.txt"),
                        content=content,
                        question_template=question_template
                    )
                    # Add chapter and lesson info to generated questions
                    for q in generated:
                        q.chapter_number = int(chapter)
                        q.lesson_number = int(lesson)
                        q.question_type = "TL"  # Override to TL
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
                        print(f"   Last error: {error_message}")
                        return []
        
        # Should not reach here
        return []

