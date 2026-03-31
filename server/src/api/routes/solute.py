# api/routes/solute.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
from pathlib import Path
import uuid

from fastapi.responses import FileResponse
from services.solute_exam_service.solute_english_exam_service import solve_english_exam
from services.solute_exam_service.docx_export_exam_service import export_soluted_english_exam_from_data
routerSolute = APIRouter(
    prefix="/api",
    tags=["Solute"]
)

# Giả sử bạn sẽ viết service xử lý ở đây
from services.solute_exam_service.solute_english_exam_service import solve_english_exam


@routerSolute.post("/export-soluted-english-exam")
async def export_soluted_english_exam(payload: dict):
    file_path = "output_exam.docx"

    export_soluted_english_exam_from_data(payload, file_path)

    return FileResponse(
        file_path,
        filename="Soluted_English_Exam.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# @routerSolute.post("/export-soluted-standard-english-exam")
# async def export_soluted_standard_english_exam(payload: dict):

#     file_path = "output_standard_exam.docx"

#     export_soluted_standard_english_exam_from_data(payload, file_path)

#     return FileResponse(
#         file_path,
#         filename="Soluted_Standard_English_Exam.docx",
#         media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#     )



@routerSolute.post("/solute-english-exam")
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
        result = await solve_english_exam(file_paths)

        print(f">>>>>>> debug result {result}")

        return {
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

