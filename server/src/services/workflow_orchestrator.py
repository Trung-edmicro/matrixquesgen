"""
Workflow Orchestrator
Coordinates the execution of all phases in the matrix-to-questions pipeline
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .phases.phase1_matrix_processing import MatrixProcessingService, MatrixMetadata, LessonInfo
from .phases.phase2_content_acquisition import ContentAcquisitionService, ProcessedContent
from .phases.phase3_content_mapping import ContentMappingService, ContentMappingResult
from .phases.phase4_alternative_question_generation import AlternativeQuestionGenerationService, QuestionSet
from .phases.phase4_question_generation import QuestionGenerationService
from .core.google_drive_service import GoogleDriveService


@dataclass
class WorkflowConfig:
    """Configuration for the workflow"""
    max_concurrent_downloads: int = 1  # Reduced from 3 to avoid SSL issues
    max_concurrent_generations: int = 2
    enable_caching: bool = True
    output_dir: Path = Path("data/output")
    ai_provider: str = "genai"
    question_types: List[str] = None

    def __post_init__(self):
        if self.question_types is None:
            self.question_types = ["TN", "DS", "TLN", "TL"]


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    success: bool
    matrix_metadata: Optional[MatrixMetadata] = None
    processed_contents: List[ProcessedContent] = None
    extracted_lessons: List[Any] = None
    question_sets: List[QuestionSet] = None
    errors: List[str] = None
    execution_time: float = 0.0

    def __post_init__(self):
        if self.processed_contents is None:
            self.processed_contents = []
        if self.question_sets is None:
            self.question_sets = []
        if self.errors is None:
            self.errors = []


class WorkflowOrchestrator:
    """Orchestrates the complete matrix-to-questions workflow"""

    def __init__(self, config: WorkflowConfig = None, progress_callback=None):
        self.config = config or WorkflowConfig()
        self.progress_callback = progress_callback

        # Initialize services
        self.drive_service = GoogleDriveService()
        self.matrix_service = MatrixProcessingService()
        self.content_service = ContentAcquisitionService(self.drive_service)
        
        # Initialize both question generation services
        self.alternative_question_service = AlternativeQuestionGenerationService(self.config.ai_provider)
        self.standard_question_service = QuestionGenerationService(self.config.ai_provider)
        self.question_service = None  # Will be set based on available prompts

        # Store metadata from phase1 for use in later phases
        self.matrix_metadata: Optional[MatrixMetadata] = None

        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def execute_phase1_matrix_processing(self, matrix_file_path: Path) -> Tuple[MatrixMetadata, List[LessonInfo], List[str], Path]:
        """Execute Phase 1: Matrix Processing"""
        metadata, lessons, drive_paths, all_specs, true_false_specs, rich_content_type_definitions = self.matrix_service.process_matrix_file(matrix_file_path)

        # Store metadata for use in later phases
        self.matrix_metadata = metadata

        # Save matrix data to organized directory
        matrix_output_path = self.matrix_service.save_matrix_data(
            metadata, lessons, all_specs, true_false_specs, rich_content_type_definitions
        )

        return metadata, lessons, drive_paths, matrix_output_path

    def execute_phase2_content_enrichment(self, matrix_json_path: Path, metadata: MatrixMetadata,
                                        lessons: List[LessonInfo], drive_paths: List[str]) -> List[ProcessedContent]:
        """Execute Phase 2: Content Acquisition - download and save content for each lesson"""
        print("Phase 2: Downloading content for lessons...")

        # Prepare all_lessons data for smart folder finding
        all_lessons_data = [
            {
                'chapter': str(lesson.chapter_number),
                'lesson': str(lesson.lesson_number),
                'name': lesson.lesson_name
            }
            for lesson in lessons
        ]

        # Validate all drive paths exist using smart folder finding
        print("Validating lesson folders on Google Drive...")
        missing_lessons = []
        for lesson in lessons:
            folder_id = self.content_service.find_lesson_folder_smart(
                grade=metadata.grade,
                subject=metadata.subject,
                chapter=str(lesson.chapter_number),
                lesson=str(lesson.lesson_number),
                all_lessons=all_lessons_data
            )
            if folder_id is None:
                missing_lessons.append(f"Chương {lesson.chapter_number}, Bài {lesson.lesson_number}: {lesson.lesson_name}")
        
        if missing_lessons:
            error_msg = "Missing required lesson folders on Google Drive:\n"
            error_msg += "\n".join(f"- {lesson}" for lesson in missing_lessons)
            error_msg += "\n\nPlease check Google Drive structure and folder naming conventions."
            raise Exception(error_msg)

        processed_contents = []

        # Download content for each lesson
        for lesson, drive_path in zip(lessons, drive_paths):
            print(f"Processing lesson {lesson.chapter_number}.{lesson.lesson_number}: {lesson.lesson_name}")

            # Check if content file already exists and is valid
            existing_content = self._check_existing_content_file(
                metadata.subject, metadata.grade, str(lesson.chapter_number), str(lesson.lesson_number)
            )
            
            if existing_content:
                print(f"Using existing content file for lesson {lesson.chapter_number}.{lesson.lesson_number}")
                processed_contents.append(existing_content)
                continue

            processed_content = self._download_lesson_content(
                metadata.subject, metadata.grade, str(lesson.chapter_number), 
                str(lesson.lesson_number), drive_path, all_lessons_data
            )

            if processed_content:
                processed_contents.append(processed_content)
            else:
                print(f"No content downloaded for lesson {lesson.chapter_number}.{lesson.lesson_number}")

        print(f"Downloaded content for {len(processed_contents)} out of {len(lessons)} lessons")
        return processed_contents

    def execute_phase3_content_mapping(self, matrix_json_path: Path) -> ContentMappingResult:
        """Execute Phase 3: Content Mapping - map Phase 2 content into Phase 1 matrix"""
        print("Phase 3: Mapping content to matrix...")

        # Initialize content mapping service
        mapping_service = ContentMappingService()

        # Map content to matrix
        result = mapping_service.map_content_to_matrix(matrix_json_path)

        print(f"Content mapping completed: {result.lessons_mapped} lessons mapped, {result.total_questions_mapped} questions mapped")
        print(f"Enriched matrix saved to: {result.enriched_matrix_path}")

        return result
    
    def _detect_prompt_type(self, prompts_dir: Path) -> str:
        """Detect which prompt files are available and return 'alternative' or 'standard'
        
        Alternative prompts: TN2.txt, TN_VD_case2.txt, DS_case.txt (topic-based)
        Standard prompts: TN.txt, DS.txt
        """
        if not prompts_dir.exists():
            return 'standard'  # Default to standard
        
        # Check for alternative prompts
        has_tn2 = (prompts_dir / "TN2.txt").exists()
        has_tn_vd_case2 = (prompts_dir / "TN_VD_case2.txt").exists()
        has_tn_vd = (prompts_dir / "TN_VD.txt").exists()  # Check for TN_VD.txt as well
        has_ds_case = (prompts_dir / "DS_case.txt").exists()
        
        # Check for standard prompts
        has_tn = (prompts_dir / "TN.txt").exists()
        has_ds = (prompts_dir / "DS.txt").exists()
        
        # If we have alternative prompts (TN2 or TN_VD_case2 or TN_VD), use alternative
        if has_tn2 or has_tn_vd_case2 or has_tn_vd:
            print(f"✓ Detected ALTERNATIVE prompts (TN2: {has_tn2}, TN_VD_case2: {has_tn_vd_case2}, TN_VD: {has_tn_vd}, DS_case: {has_ds_case})")
            return 'alternative'
        
        # If we have standard prompts, use standard
        if has_tn or has_ds:
            print(f"✓ Detected STANDARD prompts (TN: {has_tn}, DS: {has_ds})")
            return 'standard'
        
        # Default to standard if no prompts found
        print("⚠️ No prompts detected, defaulting to STANDARD mode")
        return 'standard'
    
    def execute_phase4_question_generation(self, enriched_matrix_path: Path) -> Optional[QuestionSet]:
        """Execute Phase 4: Question Generation using enriched matrix (like CLI phase4)"""
        print("Phase 4: Generating questions from enriched matrix...")
        
        # Download prompts from Drive before generating questions
        if self.matrix_metadata:
            print(f"\n→ Downloading prompts from Google Drive ({self.matrix_metadata.grade}/{self.matrix_metadata.subject})...")
            try:
                prompts_downloaded = self.content_service.download_prompts_from_drive(
                    grade=self.matrix_metadata.grade,
                    subject=self.matrix_metadata.subject,
                    curriculum=self.matrix_metadata.curriculum
                )
                if prompts_downloaded:
                    print("✓ Prompts ready\n")
                else:
                    print("⚠️ Could not download prompts from Drive\n")
            except Exception as e:
                print(f"⚠️ Error downloading prompts: {e}\n")
            
            # Set prompts directory for both services (before detection)
            self.alternative_question_service.set_prompts_directory(
                subject=self.matrix_metadata.subject,
                curriculum=self.matrix_metadata.curriculum,
                grade=self.matrix_metadata.grade
            )
            self.standard_question_service.set_prompts_directory(
                subject=self.matrix_metadata.subject,
                curriculum=self.matrix_metadata.curriculum,
                grade=self.matrix_metadata.grade
            )
            
            # Check if prompts exist (either Drive or local)
            prompts_dir = self.standard_question_service.prompts_dir
            has_prompts = False
            
            # Check for standard prompts
            tn_path = prompts_dir / "TN.txt"
            ds_path = prompts_dir / "DS.txt"
            
            # Check for alternative prompts
            tn2_path = prompts_dir / "TN2.txt"
            tn_vd_case2_path = prompts_dir / "TN_VD_case2.txt"
            ds_case_path = prompts_dir / "DS_case.txt"
            
            if tn_path.exists() or ds_path.exists() or tn2_path.exists() or tn_vd_case2_path.exists() or ds_case_path.exists():
                has_prompts = True
            
            if not has_prompts:
                error_msg = f"Missing prompts for {self.matrix_metadata.subject}!\n\n"
                error_msg += f"Prompts không tồn tại trên Google Drive.\n\n"
                raise Exception(error_msg)
        else:
            print("⚠️ No matrix metadata available, skipping prompt download\n")

        # Detect which prompts are available and select appropriate service
        prompts_dir = self.alternative_question_service.prompts_dir
        prompt_type = self._detect_prompt_type(prompts_dir)
        
        if prompt_type == 'alternative':
            print("→ Using ALTERNATIVE Phase 4 logic (TN2/VD_case2/DS_case)\n")
            self.question_service = self.alternative_question_service
            method = 'alternative'
        else:
            print("→ Using STANDARD Phase 4 logic (TN/DS)\n")
            self.question_service = self.standard_question_service
            method = 'standard'

        try:
            # Use the appropriate method based on prompt type
            if method == 'alternative':
                question_set = self.question_service.process_enriched_matrix_alternative(
                    enriched_matrix_path, 
                    self.config.question_types
                )
            else:
                question_set = self.question_service.process_enriched_matrix(
                    enriched_matrix_path, 
                    self.config.question_types
                )
            
            if question_set:
                print(f"Generated {question_set.total_questions} questions from enriched matrix")
                return question_set
            else:
                print("No questions generated from enriched matrix")
                return None
                
        except Exception as e:
            print(f"Error in phase 4 question generation: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _validate_drive_paths(self, drive_paths: List[str]) -> List[tuple]:
        """Validate that all drive paths exist on Google Drive
        Returns list of (missing_path, available_folders) tuples for missing paths
        """
        missing_folders = []
        
        for drive_path_str in drive_paths:
            drive_path = drive_path_str if isinstance(drive_path_str, list) else drive_path_str.split(',')
            
            # Try to navigate to the path
            folder_id = self.content_service.find_folder_by_path(drive_path)
            
            if folder_id is None:
                # Path doesn't exist, get available folders at the last valid level
                available_folders = self._get_available_folders_at_path(drive_path)
                missing_folders.append((drive_path_str, available_folders))
        
        return missing_folders

    def _get_available_folders_at_path(self, drive_path: List[str]) -> List[str]:
        """Get available folders at the deepest valid level of the path"""
        try:
            current_folder_id = self.content_service.root_folder_id
            
            # Navigate as far as possible
            for i, component in enumerate(drive_path):
                result = self.drive_service.list_files_in_folder(
                    current_folder_id,
                    query="mimeType='application/vnd.google-apps.folder'"
                )
                
                if not result['success']:
                    return []
                
                folders = result['files']
                target_folder = None
                for folder in folders:
                    if folder['name'] == component:
                        target_folder = folder
                        break
                
                if not target_folder:
                    # Return available folders at current level
                    return [f['name'] for f in folders]
                
                current_folder_id = target_folder['id']
            
            # If we reach here, path exists
            return []
            
        except Exception as e:
            print(f"Error checking available folders: {e}")
            return []

    def _check_existing_content_file(self, subject: str, grade: str, chapter: str, lesson: str) -> Optional[ProcessedContent]:
        """Check if content file already exists and return ProcessedContent if valid"""
        content_dir = Path("data/content")
        content_filename = f"{subject}_{grade}_{chapter}_{lesson}_content.json"
        content_file_path = content_dir / content_filename
        
        if not content_file_path.exists():
            return None
            
        try:
            with open(content_file_path, 'r', encoding='utf-8') as f:
                content_data = json.load(f)
            
            # Validate content structure
            if not self._validate_content_structure(content_data, subject, grade, chapter, lesson):
                print(f"⚠️  Existing content file {content_filename} has invalid structure, will re-download")
                return None
                
            # Create ProcessedContent from existing file
            processed_content = ProcessedContent(
                subject=subject,
                grade=grade,
                topic=f"{chapter}.{lesson}",
                data=content_data
            )
            
            return processed_content
            
        except Exception as e:
            print(f"⚠️  Error reading existing content file {content_filename}: {e}")
            return None

    def _validate_content_structure(self, content_data: dict, subject: str, grade: str, chapter: str, lesson: str) -> bool:
        """Validate that content file has the expected structure"""
        try:
            # Check basic structure
            if 'data' not in content_data:
                return False
                
            data = content_data['data']
            if 'content' not in data:
                return False
                
            content = data['content']
            # Check if has SGK, SGV or SBT content
            sgk_content = content.get('SGK', '')
            sgv_content = content.get('SGV', '')
            sbt_content = content.get('SBT', '')

            if not sgk_content and not sgv_content and not sbt_content:
                return False
                
            # Check metadata matches
            if 'metadata' in content_data:
                metadata = content_data['metadata']
                if metadata.get('subject') != subject or metadata.get('grade') != grade:
                    return False
                    
            return True
            
        except Exception:
            return False

    def _download_lesson_content(self, subject: str, grade: str, chapter: str, lesson: str, 
                                drive_path: str, all_lessons: List[Dict] = None) -> Optional[ProcessedContent]:
        try:
            drive_path_list = drive_path if isinstance(drive_path, list) else drive_path.split(',')
            
            processed_content = self.content_service.process_content_for_lesson(
                subject, grade, chapter, lesson, drive_path_list, all_lessons
            )
            
            if processed_content:
                # Save to content directory for Phase 2
                content_dir = Path("data/content")
                output_path = self.content_service.save_processed_content(processed_content, content_dir)
                print(f"💾 Saved processed content to {output_path}")
            
            return processed_content
        except Exception as e:
            print(f"Error in _download_lesson_content: {e}")
            return None

    def execute_complete_workflow(self, matrix_file_path: Path) -> WorkflowResult:
        """Execute the complete workflow from matrix file to questions"""
        start_time = time.time()
        result = WorkflowResult(success=False)

        try:
            # Phase 1: Matrix Processing
            if self.progress_callback:
                self.progress_callback('phase1_matrix_processing', 10)
            metadata, lessons, drive_paths, matrix_output_path = self.execute_phase1_matrix_processing(matrix_file_path)
            result.matrix_metadata = metadata

            # Phase 2: Content Acquisition
            if self.progress_callback:
                self.progress_callback('phase2_content_acquisition', 30)
            processed_contents = self.execute_phase2_content_enrichment(matrix_output_path, metadata, lessons, drive_paths)
            result.processed_contents = processed_contents

            # Phase 3: Content Mapping
            if self.progress_callback:
                self.progress_callback('phase3_content_mapping', 50)
            mapping_result = self.execute_phase3_content_mapping(matrix_output_path)
            result.extracted_lessons = mapping_result.extracted_lessons

            # Phase 4: Question Generation using enriched matrix
            if self.progress_callback:
                self.progress_callback('phase4_question_generation', 80)
            question_set = self.execute_phase4_question_generation(mapping_result.enriched_matrix_path)
            result.question_sets = [question_set] if question_set else []

            if self.progress_callback:
                self.progress_callback('saving_results', 95)

            result.success = True

        except Exception as e:
            result.errors.append(str(e))
            print(f"❌ Workflow failed: {e}")

        finally:
            result.execution_time = time.time() - start_time
            print(f"Execution time: {result.execution_time:.2f} seconds")
        return result

    def execute_single_phase(self, phase: int, **kwargs) -> Any:
        """Execute a single phase with given parameters"""
        if phase == 1:
            return self.execute_phase1_matrix_processing(kwargs['matrix_file_path'])
        elif phase == 2:
            return self.execute_phase2_content_enrichment(
                kwargs['matrix_json_path'], kwargs['metadata'], kwargs['lessons'], kwargs['drive_paths']
            )
        elif phase == 3:
            return self.execute_phase3_content_extraction(kwargs['processed_contents'])
        elif phase == 4:
            return self.execute_phase4_question_generation(kwargs['enriched_matrix_path'])
        else:
            raise ValueError(f"Invalid phase number: {phase}")