"""
Phase 4: Question Generation Service
Handles generating questions from extracted lesson content
"""

import json
import os
import time
import random
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import existing services
from ..core.genai_client import GenAIClient
from ..core.content_validator import clean_all_questions
from config.settings import Config
from ..generators.question_generator import QuestionGenerator, GeneratedEssayQuestion
from ..core.matrix_parser import MatrixParser, QuestionSpec, TrueFalseQuestionSpec

# Import rich content support
from services.core.rich_content import (
    ContentBlock, ContentType,
    text as text_block, mixed as mixed_block
)
from .cross_lesson_ds_helper import merge_cross_lesson_ds_context

# Import image workflow for HA_MH/HA_TL support
from ..generators.image_workflow_service import ImageWorkflowService


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
    # DS metadata fields (source citation)
    source_citation: Optional[str] = None
    source_origin: Optional[str] = None
    source_type: Optional[str] = None
    pedagogical_approach: Optional[str] = None
    search_evidence: Optional[str] = None
    
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
        self.image_workflow_service = None  # Will be initialized when genai_client is ready
        
        # Track primary and fallback models for retry logic
        self.primary_model = Config.VERTEX_AI_MODEL
        self.fallback_model = Config.VERTEX_AI_FALLBACK_MODEL

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
                
                # Initialize ImageWorkflowService
                try:
                    self.image_workflow_service = ImageWorkflowService(
                        ai_client=self.genai_client,
                        image_save_dir=None,  # Will use default: server/data/images
                        prompts_dir=None  # Will be set when set_prompts_directory is called
                    )
                    print("✅ Initialized ImageWorkflowService for HA_MH/HA_TL support")
                except Exception as img_err:
                    print(f"⚠️ Failed to initialize ImageWorkflowService: {img_err}")
                    print("   Image-based questions (HA_MH/HA_TL) will not be available")
                    self.image_workflow_service = None
                
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
        
        # Update ImageWorkflowService prompts_dir if initialized
        if self.image_workflow_service:
            try:
                self.image_workflow_service.description_service.prompts_dir = self.prompts_dir
                print("✓ Updated ImageWorkflowService prompts_dir")
            except Exception as e:
                print(f"⚠️ Could not update ImageWorkflowService prompts_dir: {e}")
        
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
                
                if not tn_prompt_path:
                    # Fallback: try tier-specific TN files (3-tier prompt system)
                    for tier_name in ("TN_NB.txt", "TN_TH.txt", "TN_VD.txt"):
                        candidate = self.prompts_dir / tier_name
                        if candidate.exists():
                            tn_prompt_path = str(candidate)
                            print(f"✓ Using {tier_name} as fallback for QuestionGenerator init")
                            break

                if not tn_prompt_path:
                    # Last resort: any .txt file in prompts_dir
                    txts = sorted(self.prompts_dir.glob("*.txt"))
                    if txts:
                        tn_prompt_path = str(txts[0])
                        print(f"✓ Using {txts[0].name} as last-resort fallback for QuestionGenerator init")

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

    def _get_prompt_path(self, question_type: str, rich_content_types: Optional[Dict[str, Any]] = None,
                         cognitive_level: str = "") -> Path:
        """
        Get prompt template path with type-specific fallback logic

        Priority order:
            1. {QTYPE}_{type_code}.txt      (e.g. TN_BD.txt  – rich content tier-1)
            2. {QTYPE}_{LEVEL}.txt          (e.g. TN_NB.txt  – cognitive level tier-2)
            3. {QTYPE}2.txt / {QTYPE}.txt   (e.g. TN2.txt / TN.txt – generic)
        """
        # Generic fallback — TN prefers TN2.txt
        if question_type == "TN" and (self.prompts_dir / "TN2.txt").exists():
            generic_prompt = self.prompts_dir / "TN2.txt"
        else:
            generic_prompt = self.prompts_dir / f"{question_type}.txt"

        # ── Priority 1: rich-content type-specific file ───────────────────
        if rich_content_types and isinstance(rich_content_types, dict):
            try:
                question_code_key = next(iter(rich_content_types.keys()))
                type_array = rich_content_types[question_code_key]
                if isinstance(type_array, list) and len(type_array) > 0:
                    type_obj = type_array[0]
                    if isinstance(type_obj, dict) and 'code' in type_obj:
                        type_code = type_obj['code']
                        # Full code (e.g. TN_HA_MH.txt)
                        candidate = self.prompts_dir / f"{question_type}_{type_code}.txt"
                        if candidate.exists():
                            return candidate
                        # Stripped suffix (e.g. TN_HA.txt)
                        if '_' in type_code:
                            primary_type = type_code.split('_')[0]
                            candidate = self.prompts_dir / f"{question_type}_{primary_type}.txt"
                            if candidate.exists():
                                return candidate
            except (StopIteration, AttributeError, KeyError, IndexError, TypeError) as e:
                print(f"  ⚠️ Could not extract type code from rich_content_types: {e}")

        # ── Priority 2: cognitive-level tier-2 file (e.g. TN_NB.txt) ────
        if cognitive_level:
            level_candidate = self.prompts_dir / f"{question_type}_{cognitive_level}.txt"
            if level_candidate.exists():
                return level_candidate

        # ── Priority 3: generic fallback ─────────────────────────────────
        return generic_prompt
    
    def _has_image_requirements(self, spec) -> Optional[str]:
        """
        Check if spec requires image generation (HA_MH or HA_TL)
        
        Args:
            spec: QuestionSpec or dict with rich_content_types
            
        Returns:
            'HA_MH', 'HA_TL', or None
        """
        # Get rich_content_types from spec
        if hasattr(spec, 'rich_content_types'):
            rich_types = spec.rich_content_types
        elif isinstance(spec, dict) and 'rich_content_types' in spec:
            rich_types = spec['rich_content_types']
        else:
            return None
        
        if not rich_types:
            return None
        
        # Check all question codes for HA_MH or HA_TL
        for code, types_list in rich_types.items():
            if not isinstance(types_list, list):
                continue
            
            for type_obj in types_list:
                type_code = None
                if isinstance(type_obj, dict):
                    type_code = type_obj.get('code', '')
                elif isinstance(type_obj, str):
                    type_code = type_obj
                
                if type_code:
                    if type_code == 'HA_MH':
                        return 'HA_MH'
                    elif type_code == 'HA_TL':
                        return 'HA_TL'
                    elif type_code == 'HA':  # Generic HA defaults to HA_MH
                        return 'HA_MH'
        
        return None

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
                    
                    # Copy rich_content_types from spec to QuestionSpec if exists
                    if 'rich_content_types' in spec:
                        qspec.rich_content_types = spec['rich_content_types']
                        # Debug: Show what type is being processed
                        image_type = self._has_image_requirements(qspec)
                        if image_type:
                            print(f"  🖼️ Detected {image_type} for {code_str}")

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
    
    def check_prompt_availability(self, question_types: List[str]) -> Dict[str, bool]:
        """Check which prompt templates are available.

        A question type is considered available if ANY of the following exist:
          - {QTYPE}.txt          (e.g. TN.txt  — flat/legacy)
          - {QTYPE}2.txt         (e.g. TN2.txt — alternative)
          - {QTYPE}_*.txt        (e.g. TN_NB.txt — 3-tier)
        """
        availability = {}
        for q_type in question_types:
            # Flat file
            if (self.prompts_dir / f"{q_type}.txt").exists():
                availability[q_type] = True
            # Alternative file (e.g. TN2.txt)
            elif (self.prompts_dir / f"{q_type}2.txt").exists():
                availability[q_type] = True
            # Any tier-based file (e.g. TN_NB.txt, TL_VD.txt)
            elif any(self.prompts_dir.glob(f"{q_type}_*.txt")):
                availability[q_type] = True
            else:
                availability[q_type] = False
        return availability

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
                ds_question = {
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'source_text': q_dict.get('source_text', q.source_text),
                    'statements': q_dict.get('statements', q.statements),
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
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'question_stem': q_dict.get('question_stem', q.question),
                    'correct_answer': q_dict.get('correct_answer', q.correct_answer),
                    'explanation': q_dict.get('explanation', q.explanation)
                })
            elif q.type == "TL":
                _tl_exp = q_dict.get('explanation', q.explanation)
                _tl_sub = _tl_exp.get('sub_questions') if isinstance(_tl_exp, dict) else None
                _tl_entry = {
                    'question_code': q_dict.get('question_code', q.id.split('_')[-1]),
                    'question_type': q.type,
                    'lesson_name': q.lesson_name,
                    'level': q.difficulty,
                    'question_stem': q_dict.get('question_stem', q.question),
                    'correct_answer': q_dict.get('correct_answer', q.correct_answer),
                    'explanation': _tl_exp,
                }
                if _tl_sub:
                    _tl_entry['sub_questions'] = _tl_sub
                tl_questions.append(_tl_entry)

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
        """Process enriched matrix JSON and generate questions using multi-threading with auto-retry for missing questions
        
        Args:
            enriched_matrix_path: Path to enriched matrix JSON file
            question_types: List of question types to generate (e.g., ["TN", "DS", "TLN", "TL"]). If None, generates all types.
        """
        if question_types is None:
            question_types = ["TN", "DS", "TLN", "TL"]
        
        # Check prompt availability and filter out unavailable types
        prompt_availability = self.check_prompt_availability(question_types)
        available_types = [q_type for q_type in question_types if prompt_availability[q_type]]
        unavailable_types = [q_type for q_type in question_types if not prompt_availability[q_type]]
        
        if unavailable_types:
            print(f"\n⚠️  System does not have prompt templates for: {', '.join(unavailable_types)}")
            print(f"   These question types will be skipped (not generated)")
            print(f"   Available question types: {', '.join(available_types) if available_types else 'None'}")
        
        if not available_types:
            print(f"\n❌ ERROR: No prompt templates available for any requested question type")
            return None
        
        # Use only available types for generation
        question_types = available_types
            
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
            
            # Track unavailable question types for informative messages
            self._unavailable_question_types = unavailable_types
            
            while retry_attempt < max_retry_attempts:
                missing_info = self._check_missing_questions(matrix_data, question_set, question_types)
                
                if not missing_info['has_missing']:
                    print(f"✅ All questions generated successfully!")
                    if unavailable_types:
                        print(f"   Note: {', '.join(unavailable_types)} were skipped (no prompt template)")
                    break
                
                retry_attempt += 1
                print(f"\n⚠️ Missing questions detected (attempt {retry_attempt}/{max_retry_attempts}):")
                print(f"   Expected: TN={missing_info['expected']['TN']}, DS={missing_info['expected']['DS']}, "
                      f"TLN={missing_info['expected']['TLN']}, TL={missing_info['expected']['TL']}")
                print(f"   Generated: TN={missing_info['generated']['TN']}, DS={missing_info['generated']['DS']}, "
                      f"TLN={missing_info['generated']['TLN']}, TL={missing_info['generated']['TL']}")
                print(f"   Missing: TN={missing_info['missing']['TN']}, DS={missing_info['missing']['DS']}, "
                      f"TLN={missing_info['missing']['TLN']}, TL={missing_info['missing']['TL']}")
                
                # Show missing question codes
                missing_codes = missing_info.get('missing_codes', {})
                for q_type in ['TN', 'DS', 'TLN', 'TL']:
                    codes = missing_codes.get(q_type, set())
                    if codes:
                        codes_str = ', '.join(sorted(codes))
                        print(f"   Missing {q_type} codes: {codes_str}")
                
                if unavailable_types:
                    print(f"   Note: {', '.join(unavailable_types)} are not counted (no prompt template)")
                
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
                  f"TL={len([q for q in question_set.questions if q.type == 'TL'])}", flush=True)
                    
            return question_set

        except Exception as e:
            print(f"❌ Error processing enriched matrix: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_questions_from_matrix(self, matrix_data: Dict, question_types: List[str]) -> Optional[QuestionSet]:
        """Generate questions from matrix data (original logic)"""
        try:
            all_questions = []
            generation_tasks = []
            
            # Track DS question_code đã tạo task để tránh duplicate
            processed_ds_codes = set()

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
                            # Get question_code to check for duplicates
                            question_code = spec_data.get('question_code', spec_data.get('code', ['DS1'])[0])
                            
                            # Skip if this DS question_code has already been processed
                            # (handles cross-lesson DS where same code appears in multiple lessons)
                            if question_code in processed_ds_codes:
                                # print(f"DEBUG: Skipping DS {question_code} in lesson {chapter}.{lesson} (already processed)")
                                continue
                            
                            # Mark this question_code as processed
                            processed_ds_codes.add(question_code)
                            # print(f"DEBUG: Creating DS task for spec: {question_code} in lesson {chapter}.{lesson}")
                            
                            # Determine supplementary based on rich_content_types
                            # - If no rich_content_types (text only): use spec materials
                            # - If has rich_content_types (BD/BK/HA): use lesson supplementary_material
                            rich_content_types = spec_data.get('rich_content_types', {})
                            if rich_content_types:
                                # Has rich content (BD/BK/HA) -> use supplementary_material
                                supplementary_for_ds = supplementary
                            else:
                                # No rich content (text only) -> use spec materials
                                supplementary_for_ds = spec_data.get('materials', '')
                            
                            # Create task for DS generation (only once per question_code)
                            task = {
                                'type': 'DS',
                                'lesson_data': lesson_data,
                                'chapter': chapter,
                                'lesson': lesson,
                                'content': content,
                                'supplementary': supplementary_for_ds,
                                'spec_data': spec_data,
                                'matrix_data': matrix_data  # Add matrix_data for cross-lesson DS
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
            print(f"Starting parallel generation of {len(generation_tasks)} question tasks...", flush=True)
            
            # Giảm workers để tránh rate limit 429
            max_workers = min(5, len(generation_tasks))
            print(f"   Using {max_workers} parallel workers to avoid API rate limits", flush=True)
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
                            # Get codes for better logging
                            spec_data = task.get('spec_data', {})
                            codes = spec_data.get('code', spec_data.get('question_code', []))
                            codes_str = ', '.join(codes) if isinstance(codes, list) else str(codes)
                            print(f"✅ Completed {task['type']} {codes_str} for lesson {task['chapter']}.{task['lesson']} - {len(generated_questions)} questions", flush=True)
                    except Exception as e:
                        print(f"❌ Failed {task['type']} task for lesson {task['chapter']}.{task['lesson']}: {e}", flush=True)

            # ── Merge TL sub-questions split across multiple levels ───────────
            # When sub-items (a, b, c) come from different cognitive-level rows
            # (e.g. C2a at TH, C2b at VD), phase4 generates them as separate
            # GeneratedEssayQuestion objects.  Reunite them into one question
            # per code so the output has a single C2 with all sub_questions.
            merged_all_questions = []
            tl_by_key: Dict = {}  # (chapter, lesson, code) -> GeneratedEssayQuestion
            LEVEL_ORDER = {'NB': 0, 'TH': 1, 'VD': 2, 'VDC': 3}

            for gen_q in all_questions:
                is_tl = (
                    getattr(gen_q, 'question_type_main', None) == 'TL'
                    or getattr(gen_q, 'question_type', None) == 'TL'
                )
                has_sub = bool(getattr(gen_q, 'sub_questions', None))

                if is_tl and has_sub:
                    key = (
                        getattr(gen_q, 'chapter_number', 0),
                        getattr(gen_q, 'lesson_number', 0),
                        gen_q.question_code,
                    )
                    if key in tl_by_key:
                        existing = tl_by_key[key]
                        # Append new sub_questions (preserving order a → b → c)
                        existing.sub_questions = (existing.sub_questions or []) + (gen_q.sub_questions or [])
                        # Upgrade cognitive level to the higher one
                        existing_ord = LEVEL_ORDER.get(existing.level, 0)
                        new_ord = LEVEL_ORDER.get(gen_q.level, 0)
                        if new_ord > existing_ord:
                            existing.level = gen_q.level
                    else:
                        tl_by_key[key] = gen_q
                else:
                    merged_all_questions.append(gen_q)

            # Add merged TL questions (preserving original order by first-seen)
            for gen_q in all_questions:
                is_tl = (
                    getattr(gen_q, 'question_type_main', None) == 'TL'
                    or getattr(gen_q, 'question_type', None) == 'TL'
                )
                has_sub = bool(getattr(gen_q, 'sub_questions', None))
                if is_tl and has_sub:
                    key = (
                        getattr(gen_q, 'chapter_number', 0),
                        getattr(gen_q, 'lesson_number', 0),
                        gen_q.question_code,
                    )
                    merged = tl_by_key.pop(key, None)
                    if merged is not None:  # only add once (pop removes it)
                        merged_all_questions.append(merged)

            all_questions = merged_all_questions
            # ── End TL merge ─────────────────────────────────────────────────

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
                    _tl_sub_questions = getattr(gen_q, 'sub_questions', None)
                    _tl_explanation: Dict = {
                        "question_type": gen_q.question_type,
                        "answer_structure": gen_q.answer_structure,
                    }
                    if _tl_sub_questions:
                        _tl_explanation["sub_questions"] = _tl_sub_questions
                    question = GeneratedQuestion(
                        id=f"{matrix_data['metadata']['subject']}_{matrix_data['metadata']['grade']}_{gen_q.chapter_number}_{gen_q.lesson_number}_TL_{gen_q.question_code}",
                        type="TL",
                        question=gen_q.question_stem,
                        options=None,  # TL has no options
                        correct_answer="",  # TL has no fixed answer
                        explanation=_tl_explanation,
                        difficulty=gen_q.level,
                        subject=matrix_data['metadata']['subject'],
                        grade=matrix_data['metadata']['grade'],
                        chapter=str(gen_q.chapter_number),
                        lesson=str(gen_q.lesson_number),
                        lesson_name=gen_q.lesson_name,
                        generated_at=datetime.now().isoformat()
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
            print(f"Error in _generate_questions_from_matrix: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _check_missing_questions(self, matrix_data: Dict, question_set: QuestionSet, 
                                 question_types: List[str]) -> Dict:
        """
        Check if all expected questions are generated
        
        Returns:
            Dict with keys: has_missing, expected, generated, missing, missing_codes
        """
        # Count expected questions from matrix AND track question codes
        expected_counts = {'TN': 0, 'DS': 0, 'TLN': 0, 'TL': 0}
        expected_codes = {'TN': set(), 'DS': set(), 'TLN': set(), 'TL': set()}
        
        for lesson_data in matrix_data['lessons']:
            for q_type in question_types:
                if q_type == 'TN':
                    tn_specs = lesson_data.get('TN', {})
                    for level, specs in tn_specs.items():
                        for spec in specs:
                            expected_counts['TN'] += spec.get('num', 1)
                            # Track each question code
                            for code in spec.get('code', []):
                                expected_codes['TN'].add(code)
                            
                elif q_type == 'DS':
                    ds_specs = lesson_data.get('DS', [])
                    for ds_spec in ds_specs:
                        # Track DS question code (set deduplicates cross-lesson splits)
                        code = ds_spec.get('question_code', '')
                        if code:
                            expected_codes['DS'].add(code)
                            
                elif q_type == 'TLN':
                    tln_specs = lesson_data.get('TLN', {})
                    for level, specs in tln_specs.items():
                        for spec in specs:
                            expected_counts['TLN'] += spec.get('num', 1)
                            # Track each question code
                            for code in spec.get('code', []):
                                expected_codes['TLN'].add(code)
                            
                elif q_type == 'TL':
                    tl_specs = lesson_data.get('TL', {})
                    for level, specs in tl_specs.items():
                        for spec in specs:
                            expected_counts['TL'] += spec.get('num', 1)
                            # Track each question code
                            for code in spec.get('code', []):
                                expected_codes['TL'].add(code)
        
        # DS expected = unique question_codes (cross-lesson splits count as 1 question)
        expected_counts['DS'] = len(expected_codes['DS'])

        # TL expected = unique question_codes (sub-items a/b share same code and are merged into 1 question)
        expected_counts['TL'] = len(expected_codes['TL'])

        # Count generated questions AND track generated codes
        generated_counts = {
            'TN': len([q for q in question_set.questions if q.type == 'TN']),
            'DS': len([q for q in question_set.questions if q.type == 'DS']),
            'TLN': len([q for q in question_set.questions if q.type == 'TLN']),
            'TL': len([q for q in question_set.questions if q.type == 'TL'])
        }
        
        # Track generated question codes
        generated_codes = {'TN': set(), 'DS': set(), 'TLN': set(), 'TL': set()}
        for q in question_set.questions:
            # Extract question code from id (format: SUBJECT_GRADE_CHAPTER_LESSON_TYPE_CODE)
            try:
                parts = q.id.split('_')
                if len(parts) >= 6:
                    code = parts[-1]  # Last part is question code
                    generated_codes[q.type].add(code)
            except:
                pass
        
        # Calculate missing counts and missing codes
        missing_counts = {
            q_type: max(0, expected_counts[q_type] - generated_counts[q_type])
            for q_type in ['TN', 'DS', 'TLN', 'TL']
        }
        
        # Find missing question codes
        missing_codes = {
            q_type: expected_codes[q_type] - generated_codes[q_type]
            for q_type in ['TN', 'DS', 'TLN', 'TL']
        }
        
        has_missing = any(count > 0 for count in missing_counts.values())
        
        return {
            'has_missing': has_missing,
            'expected': expected_counts,
            'generated': generated_counts,
            'missing': missing_counts,
            'missing_codes': missing_codes
        }
    
    def _generate_missing_questions(self, matrix_data: Dict, missing_info: Dict) -> List:
        """Generate only the missing questions based on missing codes"""
        missing_codes = missing_info.get('missing_codes', {})
        all_missing_questions = []
        
        print(f"\n🔄 Generating missing questions...")
        
        for q_type in ['TN', 'DS', 'TLN', 'TL']:
            codes_to_generate = missing_codes.get(q_type, set())
            if not codes_to_generate:
                continue
                
            codes_str = ', '.join(sorted(codes_to_generate))
            print(f"   Generating missing {q_type}: {codes_str}")
            
            # Find lessons that contain the missing question codes
            for lesson_data in matrix_data['lessons']:
                if not codes_to_generate:
                    break
                    
                chapter = lesson_data['chapter_number']
                lesson = lesson_data['lesson_number']
                content = lesson_data.get('content', '')
                supplementary = lesson_data.get('supplementary_material', '')
                
                if q_type == 'TN':
                    # Generate missing TN questions
                    tn_specs = lesson_data.get('TN', {})
                    for level, specs in tn_specs.items():
                        if not codes_to_generate:
                            break
                        for spec_data in specs:
                            # Check if this spec contains any missing codes
                            spec_codes = set(spec_data.get('code', []))
                            codes_in_this_spec = spec_codes & codes_to_generate
                            
                            if not codes_in_this_spec:
                                continue  # Skip this spec, no missing codes
                            
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
                            try:
                                questions = self._generate_question_task(task)
                                if questions:
                                    all_missing_questions.extend(questions)
                                    # Remove generated codes from missing set
                                    codes_to_generate -= codes_in_this_spec
                                    print(f"      ✓ Generated {q_type} {', '.join(sorted(codes_in_this_spec))}")
                            except Exception as e:
                                print(f"      ❌ Error generating {q_type} {', '.join(sorted(codes_in_this_spec))}: {e}")
                                
                elif q_type == 'DS':
                    # Generate missing DS questions
                    ds_specs = lesson_data.get('DS', [])
                    for spec_data in ds_specs:
                        if not codes_to_generate:
                            break
                        
                        # Check if this DS code is missing
                        ds_code = spec_data.get('question_code', '')
                        if ds_code not in codes_to_generate:
                            continue  # Skip, not missing
                        
                        task = {
                            'type': 'DS',
                            'lesson_data': lesson_data,
                            'chapter': chapter,
                            'lesson': lesson,
                            'content': content,
                            'supplementary': spec_data.get('materials', ''),
                            'spec_data': spec_data,
                            'matrix_data': matrix_data
                        }
                        try:
                            questions = self._generate_question_task(task)
                            if questions:
                                all_missing_questions.extend(questions)
                                codes_to_generate.discard(ds_code)
                                print(f"      ✓ Generated {q_type} {ds_code}")
                        except Exception as e:
                            print(f"      ❌ Error generating {q_type} {ds_code}: {e}")
                                
                elif q_type == 'TLN':
                    # Generate missing TLN questions
                    tln_specs = lesson_data.get('TLN', {})
                    for level, specs in tln_specs.items():
                        if not codes_to_generate:
                            break
                        for spec_data in specs:
                            # Check if this spec contains any missing codes
                            spec_codes = set(spec_data.get('code', []))
                            codes_in_this_spec = spec_codes & codes_to_generate
                            
                            if not codes_in_this_spec:
                                continue  # Skip this spec, no missing codes
                            
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
                            try:
                                questions = self._generate_question_task(task)
                                if questions:
                                    all_missing_questions.extend(questions)
                                    codes_to_generate -= codes_in_this_spec
                                    print(f"      ✓ Generated {q_type} {', '.join(sorted(codes_in_this_spec))}")
                            except Exception as e:
                                print(f"      ❌ Error generating {q_type} {', '.join(sorted(codes_in_this_spec))}: {e}")
                                
                elif q_type == 'TL':
                    # Generate missing TL questions
                    tl_specs = lesson_data.get('TL', {})
                    for level, specs in tl_specs.items():
                        if not codes_to_generate:
                            break
                        for spec_data in specs:
                            # Check if this spec contains any missing codes
                            spec_codes = set(spec_data.get('code', []))
                            codes_in_this_spec = spec_codes & codes_to_generate
                            
                            if not codes_in_this_spec:
                                continue  # Skip this spec, no missing codes
                            
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
                            try:
                                questions = self._generate_question_task(task)
                                if questions:
                                    all_missing_questions.extend(questions)
                                    codes_to_generate -= codes_in_this_spec
                                    print(f"      ✓ Generated {q_type} {', '.join(sorted(codes_in_this_spec))}")
                            except Exception as e:
                                print(f"      ❌ Error generating {q_type} {', '.join(sorted(codes_in_this_spec))}: {e}")
        
        return all_missing_questions
    
    def _merge_question_sets(self, existing_set: QuestionSet, new_questions: List) -> QuestionSet:
        """Merge new questions into existing question set"""
        # Convert new questions to GeneratedQuestion format
        for gen_q in new_questions:
            if gen_q.question_type == "DS":
                statements_text = "\n".join([f"{label}. {stmt['text']}" for label, stmt in gen_q.statements.items()])
                question = GeneratedQuestion(
                    id=f"{existing_set.subject}_{existing_set.grade}_{gen_q.chapter_number}_{gen_q.lesson_number}_{gen_q.question_type}_{gen_q.question_code}",
                    type=gen_q.question_type,
                    question=statements_text,
                    options=None,
                    correct_answer="",
                    explanation=gen_q.explanation,
                    difficulty="mixed",
                    subject=existing_set.subject,
                    grade=existing_set.grade,
                    chapter=str(gen_q.chapter_number),
                    lesson=str(gen_q.lesson_number),
                    lesson_name=gen_q.lesson_name,
                    generated_at=datetime.now().isoformat(),
                    source_text=gen_q.source_text,
                    statements=gen_q.statements,
                    source_citation=gen_q.source_citation,
                    source_origin=gen_q.source_origin,
                    source_type=gen_q.source_type,
                    pedagogical_approach=gen_q.pedagogical_approach,
                    search_evidence=gen_q.search_evidence
                )
            elif gen_q.question_type == "TL" or getattr(gen_q, 'question_type_main', None) == "TL":
                question = GeneratedQuestion(
                    id=f"{existing_set.subject}_{existing_set.grade}_{gen_q.chapter_number}_{gen_q.lesson_number}_TL_{gen_q.question_code}",
                    type="TL",
                    question=gen_q.question_stem,
                    options=None,
                    correct_answer="",
                    explanation={
                        "question_type": gen_q.question_type,
                        "answer_structure": gen_q.answer_structure
                    },
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
            existing_set.questions.append(question)
        
        # Update total count
        existing_set.total_questions = len(existing_set.questions)
        
        return existing_set

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
                matrix_data = task.get('matrix_data', None)  # Get matrix_data for cross-lesson DS

                generated_questions = []

                if task_type == "TN":
                    level = task['level']
                    spec_data = task['spec_data']

                    # Use question templates if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    rich_content_types = spec_data.get('rich_content_types', None)
                    codes = spec_data.get('code', [])

                    # When rich content is present and multiple questions are requested,
                    # generate one question at a time to prevent the AI from mixing up
                    # shared chart/table data across different questions.
                    if rich_content_types and len(codes) > 1:
                        print(f"  ℹ️ TN {', '.join(codes)}: rich_content detected with {len(codes)} codes → generating one-by-one")
                        generated = []
                        from ..core.matrix_parser import QuestionSpec
                        for code in codes:
                            single_rich_types = {code: rich_content_types[code]} if code in rich_content_types else None
                            spec_single = QuestionSpec(
                                lesson_name=lesson_data['lesson_name'],
                                competency_level=1,
                                cognitive_level=level,
                                question_type="TN",
                                num_questions=1,
                                question_codes=[code],
                                learning_outcome=spec_data['learning_outcome'],
                                row_index=0,
                                chapter_number=int(chapter),
                                supplementary_material=supplementary,
                                rich_content_types=single_rich_types
                            )
                            single_prompt_path = self._get_prompt_path("TN", single_rich_types, cognitive_level=level)
                            print(f"  → TN {code}: Using prompt {single_prompt_path.name}")
                            image_type = self._has_image_requirements(spec_single)
                            if image_type == 'HA_TL':
                                print(f"  📊 Processing HA_TL workflow for {code}...")
                                single_gen = self._process_ha_tl_workflow(
                                    spec=spec_single,
                                    prompt_path=single_prompt_path,
                                    content=content,
                                    question_template=question_template
                                )
                            elif image_type == 'HA_MH':
                                print(f"  🖼️ Processing HA_MH workflow (parallel) for {code}...")
                                single_gen = self.question_generator.generate_questions_for_spec(
                                    spec=spec_single,
                                    prompt_template_path=str(single_prompt_path),
                                    content=content,
                                    question_template=question_template
                                )
                                single_gen = self._process_ha_mh_workflow(
                                    spec=spec_single,
                                    content=content,
                                    questions=single_gen
                                )
                            else:
                                single_gen = self.question_generator.generate_questions_for_spec(
                                    spec=spec_single,
                                    prompt_template_path=str(single_prompt_path),
                                    content=content,
                                    question_template=question_template
                                )
                            generated.extend(single_gen)
                    else:
                        # No rich content or single question — use original batch flow
                        from ..core.matrix_parser import QuestionSpec
                        spec = QuestionSpec(
                            lesson_name=lesson_data['lesson_name'],
                            competency_level=1,  # Default
                            cognitive_level=level,
                            question_type="TN",
                            num_questions=spec_data['num'],
                            question_codes=codes,
                            learning_outcome=spec_data['learning_outcome'],
                            row_index=0,
                            chapter_number=int(chapter),
                            supplementary_material=supplementary,
                            rich_content_types=rich_content_types
                        )

                        # Get prompt path with type-specific fallback
                        prompt_path = self._get_prompt_path("TN", rich_content_types, cognitive_level=level)

                        # Log with question codes for identification
                        codes_str = ', '.join(codes) if codes else 'TN'
                        print(f"  → TN {codes_str}: Using prompt {prompt_path.name}")

                        # Check if this is HA_TL (need to generate image first, then question)
                        image_type = self._has_image_requirements(spec)

                        if image_type == 'HA_TL':
                            # HA_TL: Sequential workflow (Mô tả → Ảnh → Câu hỏi có ảnh)
                            print(f"  📊 Processing HA_TL workflow...")
                            generated = self._process_ha_tl_workflow(
                                spec=spec,
                                prompt_path=prompt_path,
                                content=content,
                                question_template=question_template
                            )
                        elif image_type == 'HA_MH':
                            # HA_MH: Parallel workflow (Sinh câu hỏi trước, ảnh song song)
                            print(f"  🖼️ Processing HA_MH workflow (parallel)...")
                            # B2.2: Sinh câu hỏi (độc lập)
                            generated = self.question_generator.generate_questions_for_spec(
                                spec=spec,
                                prompt_template_path=str(prompt_path),
                                content=content,
                                question_template=question_template
                            )
                            # B2.1 + B3: Sinh ảnh song song và merge
                            generated = self._process_ha_mh_workflow(
                                spec=spec,
                                content=content,
                                questions=generated
                            )
                        else:
                            # No image workflow
                            generated = self.question_generator.generate_questions_for_spec(
                                spec=spec,
                                prompt_template_path=str(prompt_path),
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
                    question_code = spec_data.get('question_code', spec_data.get('code', ['DS1'])[0])
                    
                    # Check if this DS question needs cross-lesson merge (< 4 statements)
                    current_statements = spec_data.get('statements', [])
                    
                    if len(current_statements) < 4 and matrix_data:
                        # Try to merge with statements from other lessons
                        print(f"  \u23f3 DS {question_code}: Only {len(current_statements)} statements, searching across lessons...")
                        
                        merged_result = merge_cross_lesson_ds_context(
                            matrix_data=matrix_data,
                            current_chapter=chapter,
                            current_lesson=lesson,
                            question_code=question_code,
                            current_statements=current_statements,
                            current_lesson_data=lesson_data
                        )
                        
                        if merged_result and len(merged_result['spec_data'].get('statements', [])) == 4:
                            # Use merged data
                            spec_data = merged_result['spec_data']
                            lesson_data = merged_result['merged_lesson_data']
                            content = merged_result['merged_content']
                            supplementary = merged_result['merged_supplementary']
                            
                            source_lessons_str = ", ".join(merged_result['source_lessons'])
                            print(f"  \u2713 DS {question_code}: Merged from lessons: {source_lessons_str}")
                        else:
                            print(f"  \u26a0\ufe0f  DS {question_code}: Could not find complete statements (need 4), skipping...")
                            return []  # Exit function - cannot process this DS question
                    elif len(current_statements) < 4:
                        # No matrix_data available for merge, skip incomplete question
                        print(f"  \u26a0\ufe0f  DS {question_code}: Only {len(current_statements)} statements, no matrix_data for merge, skipping...")
                        return []  # Exit function - cannot process this DS question

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
                                materials=supplementary
                            ))

                    # Create TrueFalseQuestionSpec from enriched data
                    from ..core.matrix_parser import TrueFalseQuestionSpec
                    spec = TrueFalseQuestionSpec(
                        question_code=spec_data.get('question_code', spec_data.get('code', ['DS1'])[0]),
                        lesson_name=lesson_data['lesson_name'],
                        statements=statements,
                        question_type="DS",
                        chapter_number=int(chapter),
                        supplementary_material=lesson_data.get('supplementary_material', ''),
                        materials=spec_data.get('materials', ''),
                        rich_content_types=spec_data.get('rich_content_types', None)
                    )

                    # Get prompt path with type-specific fallback
                    prompt_path = self._get_prompt_path("DS", spec_data.get('rich_content_types'))
                    
                    # Log with question code for identification
                    ds_code = spec_data.get('question_code', spec_data.get('code', ['DS'])[0])
                    print(f"  → DS {ds_code}: Using prompt {prompt_path.name}")

                    # Check if this is HA_TL (need to generate image first)
                    image_type = self._has_image_requirements(spec)
                    
                    if image_type == 'HA_TL':
                        # HA_TL: Sequential workflow
                        print(f"  📊 Processing HA_TL workflow for DS...")
                        generated_ds = self._process_ha_tl_workflow_ds(
                            spec=spec,
                            prompt_path=prompt_path,
                            content=content,
                            question_template=question_template
                        )
                    elif image_type == 'HA_MH':
                        # HA_MH: Parallel workflow
                        print(f"  🖼️ Processing HA_MH workflow for DS (parallel)...")
                        # Generate question first
                        generated_ds = self.question_generator.generate_true_false_question(
                            tf_spec=spec,
                            prompt_template_path=str(prompt_path),
                            content=content,
                            question_template=question_template
                        )
                        # Process image in parallel and merge
                        generated_ds = self._process_ha_mh_workflow_ds(
                            spec=spec,
                            content=content,
                            question=generated_ds
                        )
                    else:
                        # No image workflow
                        generated_ds = self.question_generator.generate_true_false_question(
                            tf_spec=spec,
                            prompt_template_path=str(prompt_path),
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

                    # Use question templates if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    rich_content_types_tln = spec_data.get('rich_content_types', None)
                    codes_tln = spec_data.get('code', [])

                    # When rich content is present and multiple questions are requested,
                    # generate one question at a time to prevent mixing up chart/table data.
                    if rich_content_types_tln and len(codes_tln) > 1:
                        print(f"  ℹ️ TLN {', '.join(codes_tln)}: rich_content detected with {len(codes_tln)} codes → generating one-by-one")
                        generated = []
                        from ..core.matrix_parser import QuestionSpec
                        for code in codes_tln:
                            single_rich_types_tln = {code: rich_content_types_tln[code]} if code in rich_content_types_tln else None
                            spec_single_tln = QuestionSpec(
                                lesson_name=lesson_data['lesson_name'],
                                competency_level=1,
                                cognitive_level=level,
                                question_type="TLN",
                                num_questions=1,
                                question_codes=[code],
                                learning_outcome=spec_data['learning_outcome'],
                                row_index=0,
                                chapter_number=int(chapter),
                                supplementary_material=supplementary,
                                rich_content_types=single_rich_types_tln
                            )
                            single_prompt_path_tln = self._get_prompt_path("TLN", single_rich_types_tln, cognitive_level=level)
                            print(f"  → TLN {code}: Using prompt {single_prompt_path_tln.name}")
                            single_gen_tln = self.question_generator.generate_tln_questions(
                                spec=spec_single_tln,
                                prompt_template_path=str(single_prompt_path_tln),
                                content=content,
                                question_template=question_template
                            )
                            generated.extend(single_gen_tln)
                    else:
                        # No rich content or single question — use original batch flow
                        from ..core.matrix_parser import QuestionSpec
                        spec = QuestionSpec(
                            lesson_name=lesson_data['lesson_name'],
                            competency_level=1,  # Default
                            cognitive_level=level,
                            question_type="TLN",
                            num_questions=spec_data['num'],
                            question_codes=codes_tln,
                            learning_outcome=spec_data['learning_outcome'],
                            row_index=0,
                            chapter_number=int(chapter),
                            supplementary_material=supplementary,
                            rich_content_types=rich_content_types_tln
                        )

                        # Get prompt path with type-specific fallback
                        prompt_path = self._get_prompt_path("TLN", rich_content_types_tln, cognitive_level=level)

                        # Log with question codes for identification
                        codes_str = ', '.join(codes_tln) if codes_tln else 'TLN'
                        print(f"  → TLN {codes_str}: Using prompt {prompt_path.name}")

                        # Generate TLN questions using TLN prompt
                        generated = self.question_generator.generate_tln_questions(
                            spec=spec,
                            prompt_template_path=str(prompt_path),
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
                    
                    # Validate rich_content_types before creating spec
                    rich_types = spec_data.get('rich_content_types', None)
                    if rich_types is not None and not isinstance(rich_types, dict):
                        print(f"⚠️ WARNING: Invalid rich_content_types type for TL: {type(rich_types)}, setting to None")
                        rich_types = None
                    
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
                        supplementary_material=supplementary,
                        rich_content_types=rich_types,
                        sub_items=spec_data.get('sub_items', None),
                    )

                    # Use question templates if available
                    question_template = ""
                    if spec_data.get('question_template'):
                        question_template = '\n'.join(spec_data['question_template'])

                    # Get prompt path with type-specific fallback
                    prompt_path = self._get_prompt_path("TL", rich_types, cognitive_level=level)
                    
                    # Log with question codes for identification
                    codes_str = ', '.join(spec_data['code']) if spec_data.get('code') else 'TL'
                    print(f"  → TL {codes_str}: Using prompt {prompt_path.name}")

                    # Generate TL questions using TL prompt (essay questions with full structure)
                    generated = self.question_generator.generate_tl_questions(
                        spec=spec,
                        prompt_template_path=str(prompt_path),
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
                    # Check if it's a missing prompt template error - don't retry
                    if 'Không thể đọc prompt template' in error_message or \
                       ('No such file or directory' in error_message and '.txt' in error_message):
                        print(f"⚠️  SKIPPING {task_type} for lesson {chapter}.{lesson}: Prompt template not found")
                        print(f"   System does not have prompt template for {task_type} question type")
                        print(f"   This is expected behavior - will not retry")
                        return []  # Return empty, don't retry
                    
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
    
    def _process_ha_mh_workflow(self, spec, content: str, questions: List) -> List:
        """
        Process HA_MH workflow: PARALLEL (Ảnh minh họa)
        
        Flow:
        B1. Sinh mô tả hình ảnh minh họa (illustrative_image.txt)
        B2. Song song:
            - Sinh ảnh từ mô tả → lưu local
            - Câu hỏi đã sinh rồi (passed in)
        B3. Merge ảnh vào câu hỏi
        
        Args:
            spec: QuestionSpec
            content: Nội dung SGK
            questions: Câu hỏi đã sinh (từ QuestionGenerator)
            
        Returns:
            List of questions với ảnh đã merge
        """
        if not self.image_workflow_service:
            print("  ⚠️ ImageWorkflowService not initialized, skipping image generation")
            return questions
        
        try:
            # B1: Sinh mô tả hình ảnh minh họa
            print("    Step 1: Generate illustrative image description...")
            desc_result = self.image_workflow_service.description_service.generate_illustrative_description(
                subject=spec.lesson_name.split('.')[0] if hasattr(spec, 'lesson_name') else '',
                class_level=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                chapter=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=spec.learning_outcome if hasattr(spec, 'learning_outcome') else ''
            )
            
            print(f"    ✓ Description: {desc_result.description[:80]}...")
            
            # B2: Song song - sinh ảnh (câu hỏi đã có)
            print("    Step 2: Generate image (parallel with question already done)...")
            
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                image_future = executor.submit(
                    self._generate_and_save_image,
                    description=desc_result.description,
                    image_type='HA_MH'
                )
                image_result = image_future.result()
            
            print(f"    ✓ Image saved: {image_result['image_path']}")
            
            # B3: Merge ảnh vào câu hỏi
            print("    Step 3: Merge image into questions...")
            merged_questions = self._merge_images_into_questions(
                questions=questions,
                images=[image_result],
                image_description=desc_result.description
            )
            
            print("    ✓ HA_MH workflow completed!")
            return merged_questions
            
        except Exception as e:
            print(f"    ❌ Error in HA_MH workflow: {e}")
            print(f"    Continuing with original questions...")
            return questions
    
    def _process_ha_tl_workflow(self, spec, prompt_path: Path, content: str, question_template: str) -> List:
        """
        Process HA_TL workflow: SEQUENTIAL (Ảnh tư liệu)
        
        Flow:
        B1. Sinh mô tả hình ảnh chi tiết (data_source_image.txt)
        B2. Sinh ảnh từ mô tả → lưu local
        B3. Sinh câu hỏi GỬI KÈM ảnh (QuestionGenerator với ảnh)
        B4. Merge ảnh vào câu hỏi
        
        Args:
            spec: QuestionSpec
            prompt_path: Path to prompt template
            content: Nội dung SGK
            question_template: Question template string
            
        Returns:
            List of questions với ảnh đã merge
        """
        if not self.image_workflow_service:
            print("  ⚠️ ImageWorkflowService not initialized, using default generation")
            return self.question_generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )
        
        try:
            # B1: Sinh mô tả hình ảnh CHI TIẾT
            print("    Step 1: Generate detailed data source description...")
            desc_result = self.image_workflow_service.description_service.generate_data_source_description(
                subject=spec.lesson_name.split('.')[0] if hasattr(spec, 'lesson_name') else '',
                class_level=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                chapter=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=spec.learning_outcome if hasattr(spec, 'learning_outcome') else ''
            )
            
            print(f"    ✓ Description: {desc_result.description[:80]}...")
            
            # B2: Sinh ảnh từ mô tả
            print("    Step 2: Generate image from description...")
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_TL'
            )
            
            print(f"    ✓ Image saved: {image_result['image_path']}")
            
            # B3: Sinh câu hỏi (KHÔNG gửi image_path vì API không hỗ trợ)
            # AI sẽ output [IMAGE_PLACEHOLDER] trong schema
            print("    Step 3: Generate questions (AI will use [IMAGE_PLACEHOLDER])...")
            questions = self.question_generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )
            
            # B4: Merge ảnh vào placeholder
            print("    Step 4: Merge image into placeholders...")
            merged_questions = self._merge_images_into_questions(
                questions=questions,
                images=[image_result],
                image_description=desc_result.description
            )
            
            print("    ✓ HA_TL workflow completed!")
            return merged_questions
            
        except Exception as e:
            print(f"    ❌ Error in HA_TL workflow: {e}")
            print(f"    Falling back to default generation...")
            return self.question_generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )
    
    def _process_ha_mh_workflow_ds(self, spec, content: str, question) -> Any:
        """Process HA_MH workflow for DS questions"""
        if not self.image_workflow_service:
            return question
        
        try:
            # Similar to TN but for single DS question
            desc_result = self.image_workflow_service.description_service.generate_illustrative_description(
                subject='',
                class_level='',
                chapter='',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=''
            )
            
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_MH'
            )
            
            # Merge into single question
            merged = self._merge_image_into_single_question(
                question=question,
                image=image_result,
                image_description=desc_result.description
            )
            
            return merged
        except Exception as e:
            print(f"    ❌ Error in DS HA_MH workflow: {e}")
            return question
    
    def _process_ha_tl_workflow_ds(self, spec, prompt_path: Path, content: str, question_template: str) -> Any:
        """Process HA_TL workflow for DS questions"""
        if not self.image_workflow_service:
            return self.question_generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )
        
        try:
            # B1: Sinh mô tả
            desc_result = self.image_workflow_service.description_service.generate_data_source_description(
                subject='',
                class_level='',
                chapter='',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=''
            )
            
            # B2: Sinh ảnh
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_TL'
            )
            
            # B3: Sinh câu hỏi (KHÔNG gửi image_path vì API không hỗ trợ)
            # AI sẽ output [IMAGE_PLACEHOLDER] trong schema
            question = self.question_generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )
            
            # B4: Merge ảnh vào placeholder
            merged = self._merge_image_into_single_question(
                question=question,
                image=image_result,
                image_description=desc_result.description
            )
            
            return merged
        except Exception as e:
            print(f"    ❌ Error in DS HA_TL workflow: {e}")
            return self.question_generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )
    
    def _generate_and_save_image(self, description: str, image_type: str) -> Dict[str, Any]:
        """
        Generate image và lưu vào local
        
        Args:
            description: Mô tả hình ảnh
            image_type: 'HA_MH' hoặc 'HA_TL'
            
        Returns:
            Dict với keys: image_path, image_data, description
        """
        from ..core.image_generation import ImageGenerator
        
        # Initialize ImageGenerator
        image_gen = ImageGenerator(num_images=1, aspect_ratio="16:9")
        
        # Generate image
        print(f"      Generating {image_type} image...")
        image_bytes_list = image_gen.generate(
            prompt=description,
            num_images=1,
            aspect_ratio="16:9"
        )
        
        if not image_bytes_list or len(image_bytes_list) == 0:
            raise Exception("Image generation returned empty")
        
        # Save to E:\App\matrixquesgen\server\data\images
        image_id = str(uuid.uuid4())[:8]
        
        if os.getenv('APP_DIR'):
            images_dir = Path(os.getenv('APP_DIR')) / "server" / "data" / "images"
        else:
            images_dir = Path(__file__).parent.parent.parent.parent.parent / "server" / "data" / "images"
        
        images_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{image_type.lower()}_{image_id}.png"
        
        # Write image bytes
        with open(image_path, 'wb') as f:
            f.write(image_bytes_list[0])
        
        return {
            'image_path': str(image_path),
            'image_data': image_bytes_list[0],
            'description': description,
            'image_type': image_type
        }
    
    def _merge_images_into_questions(self, questions: List, images: List[Dict], image_description: str) -> List:
        """
        Merge images vào questions tại vị trí [IMAGE_PLACEHOLDER]
        
        Args:
            questions: List of generated questions
            images: List of image results
            image_description: Description của hình ảnh
            
        Returns:
            List of questions với ảnh đã merge
        """
        if not images:
            return questions
        
        image_result = images[0]  # Use first image
        
        for question in questions:
            # Merge into question_stem hoặc source_text
            # QuestionGenerator returns objects with 'question_stem' (TN/TLN) or 'source_text' (DS)
            if hasattr(question, 'question_stem'):
                question.question_stem = self._replace_placeholder_in_content(
                    content_obj=question.question_stem,
                    image_path=image_result['image_path'],
                    image_description=image_description
                )
            
            if hasattr(question, 'question') and question.question:
                question.question = self._replace_placeholder_in_content(
                    content_obj=question.question,
                    image_path=image_result['image_path'],
                    image_description=image_description
                )
            
            if hasattr(question, 'source_text') and question.source_text:
                question.source_text = self._replace_placeholder_in_content(
                    content_obj=question.source_text,
                    image_path=image_result['image_path'],
                    image_description=image_description
                )
        
        return questions
    
    def _merge_image_into_single_question(self, question, image: Dict, image_description: str):
        """Merge image into a single question (for DS)"""
        if hasattr(question, 'source_text') and question.source_text:
            question.source_text = self._replace_placeholder_in_content(
                content_obj=question.source_text,
                image_path=image['image_path'],
                image_description=image_description
            )
        return question
    
    def _replace_placeholder_in_content(self, content_obj: Any, image_path: str, image_description: str) -> Any:
        """
        Replace [IMAGE_PLACEHOLDER] in a content object with actual image
        
        Args:
            content_obj: Content object (dict with type/content or string)
            image_path: Path to generated image file
            image_description: Description of the image
            
        Returns:
            Updated content object with image replacing placeholder
        """
        # If it's a string, just return it
        if isinstance(content_obj, str):
            return content_obj
        
        # If it's not a dict, return as is
        if not isinstance(content_obj, dict):
            return content_obj
        
        content_type = content_obj.get('type')
        content_data = content_obj.get('content')
        metadata = content_obj.get('metadata', {})
        
        # Only process if content is array (for type='image' or 'mixed')
        if not isinstance(content_data, list):
            return content_obj
        
        # Convert absolute image path to API URL
        filename = Path(image_path).name if image_path else None
        image_url = f"/api/images/file/{filename}" if filename else image_path
        
        # Find and replace [IMAGE_PLACEHOLDER]
        new_content = []
        for item in content_data:
            if item == '[IMAGE_PLACEHOLDER]':
                # Replace with actual image object
                new_content.append({
                    "type": "image",
                    "content": image_url,
                    "metadata": {
                        "caption": metadata.get('caption', image_description),
                        "generated": True,
                        "description": image_description
                    }
                })
            else:
                new_content.append(item)
        
        # Update content with replaced placeholders
        content_obj['content'] = new_content
        return content_obj
    
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

