# api/routes/solute.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
from pathlib import Path
import uuid

router = APIRouter(
    prefix="/api",
    tags=["Solute"]
)

# Giả sử bạn sẽ viết service xử lý ở đây
from services.english_generator_service.english_generator_service import solve_english_exam


@router.post("/solute-english-exam")
async def solute_english_exam(
    pdf_files: List[UploadFile] = File(...)
):
    """
    Nhận PDF đề tiếng Anh → trả về JSON lời giải
    """

    if not pdf_files:
        raise HTTPException(status_code=400, detail="Không có file PDF")

    try:
        # Tạo thư mục temp
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)

        file_paths = []

        # Save files
        for pdf in pdf_files:
            file_id = str(uuid.uuid4())
            file_path = temp_dir / f"{file_id}_{pdf.filename}"

            with open(file_path, "wb") as f:
                content = await pdf.read()
                f.write(content)

            file_paths.append(str(file_path))

        # 🚀 Gọi service xử lý
        result = solve_english_exam(file_paths)

        return {
            "status": "completed",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))