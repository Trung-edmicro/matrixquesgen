"""
API routes for History (LICHSU) subject DS material selection workflow.
Allows users to confirm/pick materials for DS questions between Phase 3 and Phase 4.
Pattern mirrors math_template_selection.py.
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, ValidationError
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/api/history-material", tags=["History Material Selection"])


# ── Question format normalization ──────────────────────────────────────────────

def _normalize_question(q) -> dict:
    """Convert GeneratedQuestion (alternative format) to standard format.

    GeneratedQuestion fields: id, type, question, difficulty, chapter, lesson, ...
    Standard format fields:   question_code, question_type, level, question_stem,
                               chapter_number, lesson_number, ...
    """
    # Extract question_code from dedicated field or from id (e.g. "LICHSU_C12_3_7_TN_C4" → "C4")
    question_code = (
        getattr(q, 'question_code', None)
        or (q.id.split('_')[-1] if getattr(q, 'id', None) else '?')
    )

    q_type = getattr(q, 'type', getattr(q, 'question_type', ''))
    chapter_number = str(getattr(q, 'chapter', getattr(q, 'chapter_number', '')))
    lesson_number = str(getattr(q, 'lesson', getattr(q, 'lesson_number', '')))
    lesson_name = getattr(q, 'lesson_name', '')

    if q_type == 'DS':
        return {
            'question_code': question_code,
            'question_type': 'DS',
            'lesson_name': lesson_name,
            'chapter_number': chapter_number,
            'lesson_number': lesson_number,
            'source_text': getattr(q, 'source_text', None),
            'statements': getattr(q, 'statements', None),
            'explanation': getattr(q, 'explanation', {}),
        }

    elif q_type == 'TL':
        explanation = getattr(q, 'explanation', {}) or {}
        return {
            'question_code': question_code,
            'question_type': 'TL',
            'lesson_name': lesson_name,
            'chapter_number': chapter_number,
            'lesson_number': lesson_number,
            'level': getattr(q, 'difficulty', getattr(q, 'level', '')),
            'question_stem': getattr(q, 'question', getattr(q, 'question_stem', None)),
            'answer_structure': explanation.get('answer_structure', {}) if isinstance(explanation, dict) else {},
            'sub_questions': explanation.get('sub_questions') if isinstance(explanation, dict) else None,
        }

    else:  # TN, TLN
        return {
            'question_code': question_code,
            'question_type': q_type,
            'lesson_name': lesson_name,
            'chapter_number': chapter_number,
            'lesson_number': lesson_number,
            'level': getattr(q, 'difficulty', getattr(q, 'level', '')),
            'question_stem': getattr(q, 'question', getattr(q, 'question_stem', None)),
            'options': getattr(q, 'options', None),
            'correct_answer': getattr(q, 'correct_answer', ''),
            'explanation': getattr(q, 'explanation', ''),
        }


# ── Lazy path helpers ──────────────────────────────────────────────────────────

def _get_app_dir() -> Path:
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    return Path(__file__).parent.parent.parent.parent


def _get_project_root() -> Path:
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    return Path(__file__).parent.parent.parent.parent.parent


def _get_sessions_dir() -> Path:
    d = _get_app_dir() / "data" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Pydantic models ───────────────────────────────────────────────────────────

class EnrichedMatrixForMaterialResponse(BaseModel):
    session_id: str
    metadata: dict
    lessons: List[dict]


class MaterialSelection(BaseModel):
    """Material selection for a single DS question."""
    lesson_index: int
    question_index: int           # Index within lesson.DS array
    question_code: str            # DS question_code
    selected_material: Optional[str] = None  # The verbatim chosen material text


class SaveMaterialSelectionsRequest(BaseModel):
    session_id: str
    selections: List[MaterialSelection]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{session_id}/enriched-matrix", response_model=EnrichedMatrixForMaterialResponse)
async def get_enriched_matrix_for_material_selection(session_id: str):
    """
    Return the enriched matrix after Phase 3 so the frontend can show
    DS questions with their AI-filtered materials list[str].
    """
    try:
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(status_code=404, detail="Enriched matrix not found (Phase 3 not completed)")

        enriched_path = Path(enriched_matrix_path)
        if not enriched_path.is_absolute():
            enriched_path = _get_project_root() / enriched_matrix_path
        if not enriched_path.exists():
            raise HTTPException(status_code=404, detail=f"Enriched matrix file not found: {enriched_path}")

        with open(enriched_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)

        return EnrichedMatrixForMaterialResponse(
            session_id=session_id,
            metadata=matrix_data.get('metadata', {}),
            lessons=matrix_data.get('lessons', [])
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading enriched matrix: {str(e)}")


@router.post("/{session_id}/save-selections")
async def save_material_selections(session_id: str, request: Request):
    """
    Save user's material selection for each DS question.
    Overwrites question['materials'] with the chosen single string so that
    Phase 4 (_resolve_materials) works without any extra changes.
    """
    try:
        raw_body = await request.body()
        try:
            body_dict = json.loads(raw_body)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

        try:
            save_request = SaveMaterialSelectionsRequest(**body_dict)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=f"Validation error: {e.json()}")

        # Load session
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(status_code=404, detail="Enriched matrix not found")

        enriched_path = Path(enriched_matrix_path)
        if not enriched_path.is_absolute():
            enriched_path = _get_project_root() / enriched_matrix_path

        with open(enriched_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)

        # Apply selections: replace list[str] materials with the single chosen str
        for sel in save_request.selections:
            try:
                lesson = matrix_data['lessons'][sel.lesson_index]
                ds_list = lesson.get('DS', [])
                question = ds_list[sel.question_index]
            except (IndexError, KeyError):
                continue  # Ignore out-of-range (shouldn't happen)

            if question and sel.selected_material is not None:
                question['materials'] = sel.selected_material
            elif question and sel.selected_material is None:
                # User skipped — keep existing (list) or collapse to first item
                existing = question.get('materials', '')
                if isinstance(existing, list):
                    question['materials'] = existing[0] if existing else ''

        # Save updated enriched matrix
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, ensure_ascii=False, indent=2)

        # Mark selections as done in session
        session_data['materials_selected'] = True
        session_data['materials_selected_at'] = datetime.now().isoformat()
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "message": "Material selections saved successfully",
            "selections_count": len(save_request.selections)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error saving material selections: {str(e)}")


# ── Pydantic model for more-materials ─────────────────────────────────────────

class MoreMaterialsRequest(BaseModel):
    """Request additional AI-filtered materials for a single DS question."""
    lesson_index: int
    question_index: int
    question_code: str
    already_shown: List[str] = []   # materials already visible in UI (to exclude)


@router.post("/{session_id}/more-materials")
async def get_more_materials(session_id: str, body: MoreMaterialsRequest):
    """
    Return up to 3 additional AI-filtered materials for a DS question.
    Uses materials_pool stored in enriched matrix and excludes already-shown ones.
    """
    try:
        # Load enriched matrix
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(status_code=404, detail="Enriched matrix not found")

        enriched_path = Path(enriched_matrix_path)
        if not enriched_path.is_absolute():
            enriched_path = _get_project_root() / enriched_matrix_path
        if not enriched_path.exists():
            raise HTTPException(status_code=404, detail="Enriched matrix file not found")

        with open(enriched_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)

        # Locate the question
        try:
            lesson = matrix_data['lessons'][body.lesson_index]
            question = lesson['DS'][body.question_index]
        except (IndexError, KeyError):
            raise HTTPException(status_code=404, detail="Question not found in enriched matrix")

        # Full pool stored by Phase 3
        pool: List[str] = question.get('materials_pool', [])
        if not pool:
            return {"new_materials": [], "message": "Không còn tư liệu nào trong kho để lọc thêm"}

        # Exclude already-shown items (exact match)
        already_shown_set = set(body.already_shown)
        remaining = [m for m in pool if m not in already_shown_set]

        if not remaining:
            return {"new_materials": [], "message": "Đã hiển thị toàn bộ tư liệu trong kho"}

        # AI filter on remaining pool
        try:
            from services.core.ai_provider_settings import create_ai_client
            from services.ai.history_material_filter_service import HistoryMaterialFilterService

            svc = HistoryMaterialFilterService(create_ai_client())
        except Exception:
            from services.ai.history_material_filter_service import HistoryMaterialFilterService
            svc = HistoryMaterialFilterService(None)

        lesson_name = lesson.get('lesson_name', '')
        statements = question.get('statements', [])
        new_filtered = svc.filter_materials(
            lesson_name=lesson_name,
            question_code=body.question_code,
            statements=statements,
            materials_list=remaining
        )

        # Clamp to 3 new results
        new_filtered = new_filtered[:3]

        print(f"✅ more-materials: {len(new_filtered)} new for DS {body.question_code} (pool remaining: {len(remaining)})")
        return {"new_materials": new_filtered}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching more materials: {str(e)}")


@router.post("/{session_id}/continue-to-phase4")
async def continue_to_phase4_after_material(session_id: str, background_tasks: BackgroundTasks):
    """
    Continue to Phase 4 after material selections have been saved.
    """
    import logging
    _log = logging.getLogger(__name__)
    _log.info(f"[{session_id}] 🔥 continue_to_phase4_after_material CALLED")
    print(f"\n🔥 continue_to_phase4_after_material CALLED for session {session_id}")
    
    try:
        session_file = _get_sessions_dir() / f"{session_id}.json"
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        if not session_data.get('materials_selected'):
            raise HTTPException(
                status_code=400,
                detail="Materials not selected. Please save material selections first."
            )

        enriched_matrix_path = session_data.get('enriched_matrix_path')
        if not enriched_matrix_path:
            raise HTTPException(status_code=404, detail="Enriched matrix not found")

        background_tasks.add_task(
            _run_phase4_after_material_selection,
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
        raise HTTPException(status_code=500, detail=f"Error starting Phase 4: {str(e)}")


# ── Background task ───────────────────────────────────────────────────────────

def _run_phase4_after_material_selection(session_id: str, enriched_matrix_path: str):
    """Background task: run Phase 4 after user confirmed material selections."""
    import logging
    _log = logging.getLogger(__name__)
    _log.info(f"[{session_id}] Starting Phase 4 (after material selection)")

    session_file = _get_sessions_dir() / f"{session_id}.json"

    def update_session(data: dict):
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        session_data['status'] = 'processing'
        session_data['current_phase'] = 'phase4_question_generation'
        session_data['progress'] = 80
        update_session(session_data)

        # Resolve subject / curriculum / grade from session metadata
        session_metadata = session_data.get('metadata', {})
        subject = session_metadata.get("subject", "")
        curriculum = session_metadata.get("curriculum", "KNTT")
        grade = session_metadata.get("grade", "")

        if not subject or not grade:
            matrix_metadata = session_data.get('matrix_metadata', {})
            subject = subject or matrix_metadata.get("subject", "")
            curriculum = curriculum or matrix_metadata.get("curriculum", "KNTT")
            grade = grade or matrix_metadata.get("grade", "")

        if not subject or not grade:
            raise Exception(
                f"Cannot determine subject/grade from session. Keys: {list(session_data.keys())}"
            )

        # Download prompts from Google Drive before generating
        _log.info(f"Downloading prompts from Drive ({grade}/{subject}/Prompts)...")
        try:
            from services.core.google_drive_service import GoogleDriveService
            from services.phases.phase2_content_acquisition import ContentAcquisitionService
            drive_service = GoogleDriveService()
            content_service = ContentAcquisitionService(drive_service)
            content_service.download_prompts_from_drive(
                grade=grade, subject=subject, curriculum=curriculum
            )
        except Exception as e:
            _log.warning(f"Could not download prompts from Drive: {e}")

        # Run Phase 4
        from services.workflow_orchestrator import WorkflowOrchestrator, WorkflowConfig
        from services.core.ai_provider_settings import get_ai_provider

        def _on_progress(phase, progress):
            session_data['current_phase'] = phase
            session_data['progress'] = progress
            update_session(session_data)

        orchestrator = WorkflowOrchestrator(
            config=WorkflowConfig(
                ai_provider=get_ai_provider(),
                question_types=["TN", "DS", "TLN", "TL"],
                max_concurrent_generations=5
            ),
            progress_callback=_on_progress
        )

        # Set prompts directory with metadata before Phase 4
        # (needed because we create a new orchestrator without matrix_metadata from Phase 1)
        orchestrator.standard_question_service.set_prompts_directory(
            subject=subject,
            curriculum=curriculum,
            grade=grade
        )
        orchestrator.alternative_question_service.set_prompts_directory(
            subject=subject,
            curriculum=curriculum,
            grade=grade
        )

        enriched_path = Path(enriched_matrix_path)
        if not enriched_path.is_absolute():
            enriched_path = _get_project_root() / enriched_matrix_path

        question_set = orchestrator.execute_phase4_question_generation(str(enriched_path))

        # ── Gather generated questions ────────────────────────────────────────
        generated_tn, generated_ds, generated_tln, generated_tl = [], [], [], []
        if question_set:
            for q in question_set.questions:
                if q.type == "TN":
                    generated_tn.append(q)
                elif q.type == "DS":
                    generated_ds.append(q)
                elif q.type == "TLN":
                    generated_tln.append(q)
                elif q.type == "TL":
                    generated_tl.append(q)

        questions_dir = _get_app_dir() / "data" / "questions"
        questions_dir.mkdir(parents=True, exist_ok=True)
        questions_file = questions_dir / f"questions_{session_id}.json"

        total_count = len(generated_tn) + len(generated_ds) + len(generated_tln) + len(generated_tl)
        output_data = {
            "metadata": {
                "session_id": session_id,
                "subject": subject,
                "grade": grade,
                "curriculum": curriculum,
                "matrix_file": session_metadata.get("filename", ""),
                "total_questions": total_count,
                "tn_count": len(generated_tn),
                "ds_count": len(generated_ds),
                "tln_count": len(generated_tln),
                "tl_count": len(generated_tl),
                "generated_at": datetime.now().isoformat(),
                "status": "completed"
            },
            "questions": {
                "TN": [_normalize_question(q) for q in generated_tn],
                "DS": [_normalize_question(q) for q in generated_ds],
                "TLN": [_normalize_question(q) for q in generated_tln],
                "TL": [_normalize_question(q) for q in generated_tl],
            },
        }

        with open(questions_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        session_data.update({
            "status": "completed",
            "current_phase": "completed",
            "progress": 100,
            "results_file": questions_file.name,
            "total_questions": total_count
        })
        update_session(session_data)
        _log.info(f"[{session_id}] Phase 4 completed — {total_count} questions generated")

    except Exception as e:
        import traceback
        traceback.print_exc()
        _log.error(f"[{session_id}] Phase 4 failed: {e}")
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            session_data.update({
                "status": "failed",
                "current_phase": "failed",
                "error": str(e)
            })
            update_session(session_data)
        except Exception:
            pass
