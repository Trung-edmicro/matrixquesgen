"""
Phase-specific API endpoints for modular testing and maintenance
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
from typing import List, Optional
import json

from services.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
from services.phases.phase1_matrix_processing import MatrixMetadata
from services.phases.phase2_content_acquisition import ProcessedContent
from services.phases.phase3_content_mapping import ContentMappingService
from services.phases.phase4_alternative_question_generation import QuestionSet


# Create separate routers for each phase
phase1_router = APIRouter(prefix="/phase1", tags=["Phase 1 - Matrix Processing"])
phase2_router = APIRouter(prefix="/phase2", tags=["Phase 2 - Content Acquisition"])
phase3_router = APIRouter(prefix="/phase3", tags=["Phase 3 - Content Extraction"])
phase4_router = APIRouter(prefix="/phase4", tags=["Phase 4 - Question Generation"])
workflow_router = APIRouter(prefix="/workflow", tags=["Complete Workflow"])

# Initialize orchestrator
orchestrator = WorkflowOrchestrator()


# Phase 1 Endpoints
@phase1_router.post("/process-matrix", response_model=dict)
async def process_matrix_file_endpoint(file: UploadFile = File(...)):
    """Process a matrix Excel file and extract metadata"""
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"temp_{file.filename}")
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process matrix file
        metadata, lessons, drive_paths, matrix_output_path = orchestrator.execute_phase1_matrix_processing(temp_path)

        # Clean up temp file
        temp_path.unlink(missing_ok=True)

        return {
            "success": True,
            "metadata": {
                "subject": metadata.subject,
                "curriculum": metadata.curriculum,
                "grade": metadata.grade,
                "filename": metadata.filename
            },
            "lessons": [
                {
                    "chapter": lesson.chapter_number,
                    "lesson": lesson.lesson_number,
                    "name": lesson.lesson_name
                }
                for lesson in lessons
            ],
            "drive_paths": drive_paths
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matrix processing failed: {str(e)}")


@phase1_router.get("/matrix-info/{filename}", response_model=dict)
async def get_matrix_info(filename: str):
    """Get information about a matrix file without full processing"""
    try:
        file_path = Path(filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Matrix file not found")

        metadata = orchestrator.matrix_service.parse_matrix_filename(filename)
        if not metadata:
            raise HTTPException(status_code=400, detail="Invalid matrix filename format")

        return {
            "subject": metadata.subject,
            "curriculum": metadata.curriculum,
            "grade": metadata.grade
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting matrix info: {str(e)}")


# Phase 2 Endpoints
@phase2_router.post("/download-content", response_model=dict)
async def download_content_endpoint(
    subject: str,
    grade: str,
    chapter: str,
    lesson: str,
    drive_path: str,  # JSON string of list
    all_lessons: Optional[str] = None  # JSON string of lessons list
):
    """Download and process content for a specific lesson"""
    try:
        drive_path_list = json.loads(drive_path)
        all_lessons_list = json.loads(all_lessons) if all_lessons else None

        processed_content = orchestrator.content_service.process_content_for_lesson(
            subject, grade, chapter, lesson, drive_path_list, all_lessons_list
        )

        if not processed_content:
            raise HTTPException(status_code=404, detail="No content found")

        # Save processed content to content directory
        content_dir = Path("data/content")
        output_path = orchestrator.content_service.save_processed_content(
            processed_content, content_dir
        )

        return {
            "success": True,
            "output_path": str(output_path),
            "content_summary": {
                "sgk_count": len(processed_content.sgk),
                "sbt_count": len(processed_content.sbt),
                "tn_count": len(processed_content.tn),
                "ds_count": len(processed_content.ds)
            }
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid drive_path format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content download failed: {str(e)}")


@phase2_router.get("/content-files/{subject}/{grade}/{chapter}/{lesson}")
async def get_content_files(subject: str, grade: str, chapter: str, lesson: str):
    """Get list of content files for a lesson"""
    try:
        # Look for processed content files
        pattern = f"{subject}_{grade}_{chapter}_{lesson}_*.json"
        files = list(orchestrator.config.output_dir.glob(pattern))

        return {
            "files": [str(f) for f in files],
            "count": len(files)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting content files: {str(e)}")


# Phase 3 Endpoints
@phase3_router.post("/map-content-to-matrix", response_model=dict)
async def map_content_to_matrix_endpoint(matrix_json_path: str):
    """Map Phase 2 content into Phase 1 matrix structure"""
    try:
        matrix_file_path = Path(matrix_json_path)
        if not matrix_file_path.exists():
            raise HTTPException(status_code=404, detail="Matrix JSON file not found")

        # Initialize content mapping service
        mapping_service = ContentMappingService()

        # Map content to matrix
        result = mapping_service.map_content_to_matrix(matrix_file_path)

        return {
            "success": True,
            "enriched_matrix_path": str(result.enriched_matrix_path),
            "mapping_summary": {
                "lessons_mapped": result.lessons_mapped,
                "total_questions_mapped": result.total_questions_mapped
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content mapping failed: {str(e)}")


@phase3_router.get("/enriched-matrices")
async def get_enriched_matrices():
    """Get list of all enriched matrix files"""
    try:
        pattern = "*_enriched.json"
        files = list(orchestrator.config.output_dir.glob(pattern))

        matrices = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    matrices.append({
                        "file": str(file_path),
                        "subject": data.get("metadata", {}).get("subject"),
                        "grade": data.get("metadata", {}).get("grade"),
                        "total_lessons": len(data.get("lessons", [])),
                        "total_questions": sum(len(lesson.get("questions", {}).get("TN", [])) + len(lesson.get("questions", {}).get("DS", [])) for lesson in data.get("lessons", []))
                    })
            except Exception:
                continue

        return {
            "matrices": matrices,
            "count": len(matrices)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting enriched matrices: {str(e)}")


# Phase 4 Endpoints
@phase4_router.post("/generate-questions", response_model=dict)
async def generate_questions_endpoint(
    subject: str,
    grade: str,
    chapter: str,
    lesson: str,
    content: str,
    question_type: str = "TN",
    num_questions: int = 5
):
    """Generate questions from lesson content"""
    try:
        # Create a mock extracted lesson object
        class MockExtractedLesson:
            def __init__(self, subject, grade, chapter, lesson, content):
                self.subject = subject
                self.grade = grade
                self.chapter = chapter
                self.lesson = lesson
                self.content = content

        mock_lesson = MockExtractedLesson(subject, grade, chapter, lesson, content)

        question_set = orchestrator.question_service.process_question_generation(
            mock_lesson, question_type, num_questions
        )

        if not question_set:
            raise HTTPException(status_code=500, detail="Question generation failed")

        # Save question set
        output_path = orchestrator.question_service.save_question_set(
            question_set, orchestrator.config.output_dir
        )

        return {
            "success": True,
            "output_path": str(output_path),
            "question_summary": {
                "total_questions": question_set.total_questions,
                "question_type": question_type,
                "subject": question_set.subject,
                "grade": question_set.grade,
                "chapter": question_set.chapter,
                "lesson": question_set.lesson
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@phase4_router.get("/question-sets")
async def get_question_sets():
    """Get list of all generated question sets"""
    try:
        pattern = "questions_*.json"
        files = list(orchestrator.config.output_dir.glob(pattern))

        question_sets = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    question_sets.append({
                        "file": str(file_path),
                        "subject": metadata.get("subject"),
                        "grade": metadata.get("grade"),
                        "chapter": metadata.get("chapter"),
                        "lesson": metadata.get("lesson"),
                        "total_questions": metadata.get("total_questions"),
                        "generated_at": metadata.get("generated_at")
                    })
            except Exception:
                continue

        return {
            "question_sets": question_sets,
            "count": len(question_sets)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting question sets: {str(e)}")


# Complete Workflow Endpoint
@workflow_router.post("/execute-complete", response_model=dict)
async def execute_complete_workflow_endpoint(file: UploadFile = File(...)):
    """Execute the complete workflow from matrix file to questions"""
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"temp_{file.filename}")
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Execute complete workflow
        result = orchestrator.execute_complete_workflow(temp_path)

        # Clean up temp file
        temp_path.unlink(missing_ok=True)

        return {
            "success": result.success,
            "execution_time": result.execution_time,
            "summary": {
                "matrix_processed": result.matrix_metadata is not None,
                "contents_downloaded": len(result.processed_contents),
                "lessons_extracted": len(result.extracted_lessons),
                "question_sets_generated": len(result.question_sets)
            },
            "errors": result.errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@workflow_router.get("/status")
async def get_workflow_status():
    """Get current workflow status and available files"""
    try:
        # Count files in each category
        matrix_files = list(orchestrator.config.output_dir.glob("*.json"))
        processed_files = [f for f in matrix_files if "_extracted" not in f.name and "questions_" not in f.name]
        extracted_files = list(orchestrator.config.output_dir.glob("*_extracted.json"))
        question_files = list(orchestrator.config.output_dir.glob("questions_*.json"))

        return {
            "output_directory": str(orchestrator.config.output_dir),
            "files_count": {
                "processed_content": len(processed_files),
                "extracted_lessons": len(extracted_files),
                "question_sets": len(question_files)
            },
            "recent_files": {
                "processed": [str(f) for f in processed_files[-5:]],
                "extracted": [str(f) for f in extracted_files[-5:]],
                "questions": [str(f) for f in question_files[-5:]]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow status: {str(e)}")