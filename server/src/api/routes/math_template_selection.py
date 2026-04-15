"""
API routes for Math subject question template selection workflow
This allows users to select question templates between phase 3 and phase 4
"""

import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
from services.phases.phase4_question_generation import QuestionGenerationService, GeneratedQuestion, QuestionSet

router = APIRouter(prefix="/api/math-template", tags=["Math Templates"])


# Helper functions
def _get_app_dir() -> Path:
    """Get APP_DIR with lazy loading to ensure env var is set"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    return Path(__file__).parent.parent.parent.parent


def _get_sessions_dir() -> Path:
    """Get sessions directory path with lazy loading"""
    sessions_dir = _get_app_dir() / "data" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def _get_matrix_dir() -> Path:
    """Get matrix directory path"""
    matrix_dir = _get_app_dir() / "data" / "matrix"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    return matrix_dir


def _get_questions_dir() -> Path:
    """Get questions directory path with lazy loading"""
    questions_dir = _get_app_dir() / "data" / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)
    return questions_dir


# Request/Response models
class EnrichedMatrixResponse(BaseModel):
    """Response containing enriched matrix data for template selection"""
    session_id: str
    metadata: dict
    lessons: List[dict]
    needs_template_selection: bool  # True if subject is Math and has question_templates


class TemplateSelection(BaseModel):
    """Template selection for a single question"""
    lesson_index: int  # Index of lesson in lessons array
    question_type: str  # "TN", "DS", "TLN", "TL"
    level: Optional[str] = None  # "NB", "TH", "VD" for TN/TLN/TL
    question_index: int  # Index within the level/type array
    selected_template: str  # The selected template text
    is_custom: bool = False  # True if user provided custom template
    is_random: bool = False  # True if system randomly selected


class SaveTemplatesRequest(BaseModel):
    """Request to save selected templates and continue to phase 4"""
    session_id: str
    selections: List[TemplateSelection]


@router.get("/{session_id}/enriched-matrix", response_model=EnrichedMatrixResponse)
async def get_enriched_matrix_for_selection(session_id: str):
    """
    Get enriched matrix data after phase 3 for template selection
    Only applicable for Math subject
    """
    try:
        # Load session data to get matrix file info
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Get enriched matrix path from session
        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(
                status_code=404, 
                detail="Enriched matrix not found. Phase 3 may not be completed."
            )
        
        # Load enriched matrix
        enriched_path = Path(enriched_matrix_path)
        if not enriched_path.exists():
            raise HTTPException(status_code=404, detail=f"Enriched matrix file not found: {enriched_path}")
        
        with open(enriched_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)
        
        metadata = matrix_data.get('metadata', {})
        subject = metadata.get('subject', '').upper()
        
        # Check if this is Math subject and has question templates
        needs_selection = False
        if subject == 'TOAN':
            # Check if any question has question_template array with items
            for lesson in matrix_data.get('lessons', []):
                # Check TN questions
                for level in ['NB', 'TH', 'VD']:
                    tn_questions = lesson.get('TN', {}).get(level, [])
                    for q in tn_questions:
                        if q.get('question_template') and len(q['question_template']) > 0:
                            needs_selection = True
                            break
                
                # Check DS questions
                ds_questions = lesson.get('DS', [])
                for q in ds_questions:
                    if q.get('question_template') and len(q['question_template']) > 0:
                        needs_selection = True
                        break
                
                # Check TLN questions
                for level in ['NB', 'TH', 'VD']:
                    tln_questions = lesson.get('TLN', {}).get(level, [])
                    for q in tln_questions:
                        if q.get('question_template') and len(q['question_template']) > 0:
                            needs_selection = True
                            break
                
                # Check TL questions
                for level in ['NB', 'TH', 'VD']:
                    tl_questions = lesson.get('TL', {}).get(level, [])
                    for q in tl_questions:
                        if q.get('question_template') and len(q['question_template']) > 0:
                            needs_selection = True
                            break
                
                if needs_selection:
                    break
        
        return EnrichedMatrixResponse(
            session_id=session_id,
            metadata=metadata,
            lessons=matrix_data.get('lessons', []),
            needs_template_selection=needs_selection
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading enriched matrix: {str(e)}")


@router.post("/{session_id}/save-selections")
async def save_template_selections(session_id: str, request: SaveTemplatesRequest):
    """
    Save template selections and update enriched matrix
    """
    try:
        # Load session data
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(status_code=404, detail="Enriched matrix not found")
        
        # Load enriched matrix
        enriched_path = Path(enriched_matrix_path)
        with open(enriched_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)
        
        # Apply selections
        for selection in request.selections:
            lesson = matrix_data['lessons'][selection.lesson_index]
            
            if selection.question_type == "TN":
                question = lesson['TN'][selection.level][selection.question_index]
            elif selection.question_type == "DS":
                question = lesson['DS'][selection.question_index]
            elif selection.question_type == "TLN":
                question = lesson['TLN'][selection.level][selection.question_index]
            elif selection.question_type == "TL":
                question = lesson['TL'][selection.level][selection.question_index]
            else:
                continue
            
            # Update question_template to be a single selected template (string)
            # instead of an array
            question['selected_question_template'] = selection.selected_template
            question['template_is_custom'] = selection.is_custom
            question['template_is_random'] = selection.is_random
        
        # Save updated enriched matrix
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, ensure_ascii=False, indent=2)
        
        # Update session to mark templates as selected
        session_data['templates_selected'] = True
        session_data['templates_selected_at'] = datetime.now().isoformat()
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "Templates saved successfully",
            "selections_count": len(request.selections)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error saving selections: {str(e)}")


@router.post("/{session_id}/continue-to-phase4")
async def continue_to_phase4(session_id: str, background_tasks: BackgroundTasks):
    """
    Continue to phase 4 after templates have been selected
    """
    try:
        # Load session data
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Check if templates were selected
        if not session_data.get('templates_selected'):
            raise HTTPException(
                status_code=400, 
                detail="Templates not selected. Please select templates first."
            )
        
        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(status_code=404, detail="Enriched matrix not found")
        
        # Add background task to run phase 4
        background_tasks.add_task(
            run_phase4_with_templates,
            session_id,
            enriched_matrix_path
        )
        
        return {
            "success": True,
            "message": "Phase 4 started",
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error continuing to phase 4: {str(e)}")


def run_phase4_with_templates(session_id: str, enriched_matrix_path: str):
    """
    Background task to run phase 4 with selected templates
    """
    session_file = _get_sessions_dir() / f"{session_id}.json"
    
    def update_session(data: dict):
        """Helper to update session file"""
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    try:
        # Load session data
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Update status
        session_data['status'] = 'processing'
        session_data['current_phase'] = 'phase4_question_generation'
        session_data['progress'] = 80
        update_session(session_data)
        
        # Run Phase 4
        import logging
        _log = logging.getLogger(__name__)
        _log.info(f"[{session_id}] Starting Phase 4 with selected templates")
        
        # Get subject, curriculum, grade from session metadata (Phase 1 output)
        # This has the CORRECT values from the original matrix processing
        session_metadata = session_data.get('metadata', {})
        subject = session_metadata.get("subject", "")
        curriculum = session_metadata.get("curriculum", "KNTT")
        grade = session_metadata.get("grade", "")
        
        # Fallback: try matrix_metadata if metadata is empty
        if not subject or not grade:
            matrix_metadata = session_data.get('matrix_metadata', {})
            subject = subject or matrix_metadata.get("subject", "")
            curriculum = curriculum or matrix_metadata.get("curriculum", "KNTT")
            grade = grade or matrix_metadata.get("grade", "")
        
        if not subject or not grade:
            raise Exception(f"Cannot determine subject and grade from session data. Available keys: {list(session_data.keys())}")
        
        print(f"📝 Phase 4 Configuration:")
        print(f"   Subject: {subject}")
        print(f"   Curriculum: {curriculum}")
        print(f"   Grade: {grade}")
        
        # Download prompts from Drive before generating questions
        _log.info(f"→ Downloading prompts from Google Drive ({grade}/{subject}/Prompts)...")
        try:
            from services.phases.phase2_content_acquisition import ContentAcquisitionService
            content_service = ContentAcquisitionService()
            
            prompts_downloaded = content_service.download_prompts_from_drive(
                grade=grade,
                subject=subject,
                curriculum=curriculum
            )
            if prompts_downloaded:
                _log.info("✓ Prompts downloaded successfully")
            else:
                _log.warning("⚠️ Could not download prompts from Drive - using local fallback")
        except Exception as e:
            _log.warning(f"⚠️ Error downloading prompts: {e}")
            _log.warning("   Will try to use local prompts if available")
        
        # Initialize question generation service
        question_service = QuestionGenerationService()
        
        # Set prompts directory based on subject/curriculum/grade
        question_service.set_prompts_directory(subject, curriculum, grade)
        
        # Generate questions from enriched matrix with selected templates
        question_set = question_service.process_enriched_matrix(
            Path(enriched_matrix_path),
            question_types=["TN", "DS", "TLN", "TL"]
        )
        
        if not question_set:
            raise Exception("No questions generated from enriched matrix")
        
        # Save questions
        questions_file = _get_questions_dir() / f"questions_{session_id}.json"
        
        # Flatten questions
        generated_tn = [q for q in question_set.questions if q.type == "TN"]
        generated_ds = [q for q in question_set.questions if q.type == "DS"]
        generated_tln = [q for q in question_set.questions if q.type == "TLN"]
        generated_tl = [q for q in question_set.questions if q.type == "TL"]
        
        output_data = {
            "metadata": {
                "session_id": session_id,
                "subject": subject,
                "grade": grade,
                "curriculum": curriculum,
                "matrix_file": session_metadata.get("filename", "unknown"),
                "total_questions": len(question_set.questions),
                "tn_count": len(generated_tn),
                "ds_count": len(generated_ds),
                "tln_count": len(generated_tln),
                "tl_count": len(generated_tl),
                "generated_at": datetime.now().isoformat(),
                "status": "completed"
            },
            "questions": {
                "TN": [
                    {
                        "question_code": q.id.split('_')[-1],
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "options": q.options,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tn
                ],
                "DS": [
                    {
                        "question_code": q.id.split('_')[-1],
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "source_text": q.source_text,
                        "statements": q.statements,
                        "explanation": q.explanation
                    }
                    for q in generated_ds
                ],
                "TLN": [
                    {
                        "question_code": q.id.split('_')[-1],
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tln
                ],
                "TL": [
                    {
                        "question_code": q.id.split('_')[-1],
                        "question_type": q.type,
                        "lesson_name": q.lesson_name,
                        "chapter_number": q.chapter,
                        "lesson_number": q.lesson,
                        "level": q.difficulty,
                        "question_stem": q.question,
                        "correct_answer": q.correct_answer,
                        "explanation": q.explanation
                    }
                    for q in generated_tl
                ]
            }
        }
        
        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Update session
        session_data.update({
            'current_phase': 'completed',
            'progress': 100,
            'status': 'completed',
            'total_questions': len(question_set.questions),
            'tn_count': len(generated_tn),
            'ds_count': len(generated_ds),
            'tln_count': len(generated_tln),
            'tl_count': len(generated_tl),
            'results_file': str(questions_file.name)
        })
        update_session(session_data)
        
        _log.info(f"✅ Phase 4 completed! Generated {len(question_set.questions)} questions")
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        import logging
        logging.getLogger(__name__).error(
            f"[{session_id}] Phase 4 failed: {error_msg}\n{error_trace}"
        )
        
        # Save error to session
        session_data = {
            "session_id": session_id,
            "status": "failed",
            "error": error_msg,
            "error_trace": error_trace,
            "current_phase": "phase4_question_generation",
            "progress": 80,
            "generated_at": datetime.now().isoformat()
        }
        update_session(session_data)
