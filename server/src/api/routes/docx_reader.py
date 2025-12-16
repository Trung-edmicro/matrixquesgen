from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import os
from typing import Optional, Dict, Any

from services.docx_reader import DocxReader, read_docx, read_docx_text

router = APIRouter(prefix="/docx", tags=["docx"])


@router.post("/read")
async def read_docx_file(file: UploadFile = File(...)):
    """
    Đọc và trích xuất nội dung từ file DOCX được upload
    
    Args:
        file: File DOCX được upload
        
    Returns:
        Dict: Toàn bộ nội dung document bao gồm text, paragraphs, tables, structure
    """
    # Kiểm tra file extension
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="File phải có định dạng .docx"
        )
    
    try:
        # Lưu file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Đọc file
        reader = DocxReader(verbose=True)
        reader.load_document(tmp_file_path)
        result = reader.extract_all()
        
        # Xóa file tạm
        os.unlink(tmp_file_path)
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "data": result
        })
        
    except Exception as e:
        # Xóa file tạm nếu có lỗi
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đọc file: {str(e)}"
        )


@router.post("/read/text")
async def read_docx_text_only(file: UploadFile = File(...)):
    """
    Đọc chỉ text từ file DOCX được upload
    
    Args:
        file: File DOCX được upload
        
    Returns:
        Dict: Nội dung text của document
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="File phải có định dạng .docx"
        )
    
    try:
        # Lưu file tạm
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Đọc text
        text = read_docx_text(tmp_file_path)
        
        # Xóa file tạm
        os.unlink(tmp_file_path)
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "text": text,
            "length": len(text)
        })
        
    except Exception as e:
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đọc file: {str(e)}"
        )


@router.post("/read/structure")
async def read_docx_structure(file: UploadFile = File(...)):
    """
    Đọc cấu trúc của file DOCX
    
    Args:
        file: File DOCX được upload
        
    Returns:
        Dict: Thông tin cấu trúc document
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="File phải có định dạng .docx"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        reader = DocxReader(verbose=True)
        reader.load_document(tmp_file_path)
        structure = reader.get_structure()
        
        os.unlink(tmp_file_path)
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "structure": structure
        })
        
    except Exception as e:
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đọc file: {str(e)}"
        )


@router.post("/read/tables")
async def read_docx_tables(file: UploadFile = File(...)):
    """
    Đọc các bảng từ file DOCX
    
    Args:
        file: File DOCX được upload
        
    Returns:
        Dict: Danh sách các bảng trong document
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="File phải có định dạng .docx"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        reader = DocxReader(verbose=True)
        reader.load_document(tmp_file_path)
        tables = reader.get_tables()
        
        os.unlink(tmp_file_path)
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "total_tables": len(tables),
            "tables": tables
        })
        
    except Exception as e:
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đọc file: {str(e)}"
        )


@router.post("/search")
async def search_in_docx(
    file: UploadFile = File(...),
    keyword: str = "",
    case_sensitive: bool = False
):
    """
    Tìm kiếm text trong file DOCX
    
    Args:
        file: File DOCX được upload
        keyword: Từ khóa cần tìm
        case_sensitive: Phân biệt hoa thường
        
    Returns:
        Dict: Danh sách các đoạn văn chứa từ khóa
    """
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="File phải có định dạng .docx"
        )
    
    if not keyword:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng cung cấp từ khóa tìm kiếm"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        reader = DocxReader(verbose=True)
        reader.load_document(tmp_file_path)
        results = reader.search_text(keyword, case_sensitive)
        
        os.unlink(tmp_file_path)
        
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            "keyword": keyword,
            "case_sensitive": case_sensitive,
            "total_found": len(results),
            "results": results
        })
        
    except Exception as e:
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tìm kiếm: {str(e)}"
        )


@router.get("/read-local")
async def read_local_docx_file(file_path: str):
    """
    Đọc file DOCX từ đường dẫn local trên server
    
    Args:
        file_path: Đường dẫn đầy đủ đến file DOCX
        
    Returns:
        Dict: Toàn bộ nội dung document
    """
    try:
        # Kiểm tra file tồn tại
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"File không tồn tại: {file_path}"
            )
        
        if not file_path.endswith('.docx'):
            raise HTTPException(
                status_code=400,
                detail="File phải có định dạng .docx"
            )
        
        # Đọc file
        result = read_docx(file_path, verbose=True)
        
        return JSONResponse(content={
            "success": True,
            "file_path": file_path,
            "data": result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đọc file: {str(e)}"
        )
