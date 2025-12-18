"""
API routes for PDF upload and processing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import shutil
from pathlib import Path
import os

from ...services.pdf_processing_service import PDFProcessingService


router = APIRouter(prefix="/pdf", tags=["PDF Processing"])

# Initialize service
pdf_service = PDFProcessingService()


@router.post("/upload")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    matrix_file_path: Optional[str] = Form(None),
    sheet_name: str = Form("Sử 12")
):
    """
    Upload and process PDF files
    
    Args:
        files: List of PDF files to upload
        matrix_file_path: Path to matrix Excel file (optional)
        sheet_name: Sheet name in matrix file
        
    Returns:
        Processing results
    """
    try:
        # Validate files are PDFs
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is not a PDF"
                )
        
        # Save uploaded files
        uploaded_paths = []
        uploads_dir = pdf_service.uploads_dir
        
        for file in files:
            file_path = uploads_dir / file.filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_paths.append(str(file_path))
        
        # Default matrix file if not provided
        if matrix_file_path is None:
            base_dir = Path(__file__).parent.parent.parent.parent.parent
            matrix_file_path = str(base_dir / "data" / "07. SỬ 12. ma trận KSCL lần 1 (1).xlsx")
        
        # Check if matrix file exists
        if not os.path.exists(matrix_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Matrix file not found: {matrix_file_path}"
            )
        
        # Process PDFs
        results = pdf_service.process_multiple_pdfs(
            pdf_files=uploaded_paths,
            matrix_file=matrix_file_path,
            sheet_name=sheet_name
        )
        
        # Save content mapping
        mapping_file = pdf_service.save_content_mapping()
        
        return JSONResponse(content={
            "success": True,
            "message": "PDFs processed successfully",
            "summary": results['summary'],
            "matching": {
                "matched_count": len(results['matching']['matched']),
                "unmatched_pdfs": [Path(p).name for p in results['matching']['unmatched_pdfs']],
                "missing_lessons": results['matching']['missing_lessons']
            },
            "processing": [
                {
                    "lesson_name": r['lesson_name'],
                    "pdf_file": Path(r['pdf_path']).name,
                    "success": r['success'],
                    "is_text_based": r.get('is_text_based'),
                    "content_length": len(r.get('content', '')) if r['success'] else 0,
                    "error": r.get('error')
                }
                for r in results['processing']
            ],
            "mapping_file": mapping_file
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{lesson_name}")
async def get_lesson_content(lesson_name: str):
    """
    Get extracted content for a specific lesson
    
    Args:
        lesson_name: Name of the lesson
        
    Returns:
        Lesson content
    """
    content = pdf_service.get_content_for_lesson(lesson_name)
    
    if content is None:
        raise HTTPException(
            status_code=404,
            detail=f"No content found for lesson: {lesson_name}"
        )
    
    return JSONResponse(content={
        "success": True,
        "lesson_name": lesson_name,
        "content": content,
        "content_length": len(content),
        "pdf_file": str(pdf_service.pdf_files_map.get(lesson_name, ''))
    })


@router.get("/mapping")
async def get_content_mapping():
    """
    Get all lesson-content mappings
    
    Returns:
        All mappings
    """
    return JSONResponse(content={
        "success": True,
        "total_lessons": len(pdf_service.pdf_content_map),
        "lessons": list(pdf_service.pdf_content_map.keys()),
        "mapping": {
            lesson_name: {
                "pdf_file": str(pdf_service.pdf_files_map.get(lesson_name, '')),
                "content_length": len(content)
            }
            for lesson_name, content in pdf_service.pdf_content_map.items()
        }
    })


@router.delete("/clear")
async def clear_uploads():
    """
    Clear uploaded files and reset service
    
    Returns:
        Success message
    """
    try:
        # Clear uploaded files
        for file in pdf_service.uploads_dir.glob("*.pdf"):
            file.unlink()
        
        # Reset service
        pdf_service.pdf_content_map.clear()
        pdf_service.pdf_files_map.clear()
        
        return JSONResponse(content={
            "success": True,
            "message": "All uploads cleared"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
