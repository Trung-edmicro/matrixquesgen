# api/routes/solute.py

import json
import os

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from pathlib import Path
import uuid
from fastapi.responses import FileResponse
from services.solute_exam_service.solute_english_exam_service import solve_english_exam, solve_literature_exam, solve_other_exam, solve_geography_exam, solve_math_exam, solve_history_exam
from services.solute_exam_service.docx_export_exam_service import export_soluted_english_exam_from_data, export_soluted_standard_english_exam_from_data
from services.solute_exam_service.docx_export_generic_service import DocxExportService

routerSolute = APIRouter(
    prefix="/api",
    tags=["Solute"]
)

# Giả sử bạn sẽ viết service xử lý ở đây
from services.solute_exam_service.solute_english_exam_service import solve_english_exam


def delete_temp_file(path: str):
    try:
        file = Path(path)
        if file.exists():
            file.unlink()
            print(f">>>>>>> deleted temp file: {path}")
    except Exception as e:
        print(f">>>>>>> failed to delete {path}: {e}")

@routerSolute.post("/export-soluted-english-exam")
async def export_soluted_english_exam(payload: dict):
    file_path = "output_exam.docx"

    export_soluted_english_exam_from_data(payload, file_path)

    return FileResponse(
        file_path,
        filename="Soluted_English_Exam.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@routerSolute.post("/export-soluted-standard-english-exam")
async def export_soluted_standard_english_exam(payload: dict):

    file_path = "output_standard_exam.docx"

    export_soluted_standard_english_exam_from_data(payload, file_path)

    return FileResponse(
        file_path,
        filename="Soluted_Standard_English_Exam.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@routerSolute.post("/export-soluted-math-exam")
async def export_soluted_math_exam(payload: dict):
    try:
        # 1. Trích xuất dữ liệu thực tế từ payload
        # Theo cấu trúc JSON bạn gửi: {"results": [{...}]}
        if "results" in payload and len(payload["results"]) > 0:
            exam_data = payload["results"][0]
        else:
            exam_data = payload # Trường hợp payload là object trực tiếp

        # 2. Định nghĩa đường dẫn file tạm
        filepath = "output_math_exam.docx"
        
        # 3. Khởi tạo Service và tạo file
        exporter = DocxExportService()
        exporter.create_standard_docx(exam_data, filepath)

        # 4. Kiểm tra file có tồn tại không
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Could not create docx file")

        # 5. Trả về file cho frontend
        return FileResponse(
            path=filepath,
            filename="Soluted_Math_Exam.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print(f"Error exporting docx: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@routerSolute.post("/export-soluted-geography-exam")
async def export_soluted_geography_exam(payload: dict):
    try:
        # 1. Trích xuất dữ liệu thực tế từ payload
        # Theo cấu trúc JSON bạn gửi: {"results": [{...}]}
        if "results" in payload and len(payload["results"]) > 0:
            exam_data = payload["results"][0]
        else:
            exam_data = payload # Trường hợp payload là object trực tiếp

        # 2. Định nghĩa đường dẫn file tạm
        filepath = "output_geography_exam.docx"
        
        # 3. Khởi tạo Service và tạo file
        exporter = DocxExportService()
        exporter.create_standard_docx(exam_data, filepath)

        # 4. Kiểm tra file có tồn tại không
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Could not create docx file")

        # 5. Trả về file cho frontend
        return FileResponse(
            path=filepath,
            filename="Soluted_Geography_Exam.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print(f"Error exporting docx: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@routerSolute.post("/export-soluted-other-exam")
async def export_soluted_other_exam(payload: dict):
    try:
        # 1. Trích xuất dữ liệu thực tế từ payload
        # Theo cấu trúc JSON bạn gửi: {"results": [{...}]}
        if "results" in payload and len(payload["results"]) > 0:
            exam_data = payload["results"][0]
        else:
            exam_data = payload # Trường hợp payload là object trực tiếp

        # 2. Định nghĩa đường dẫn file tạm
        filepath = "output_exam.docx"
        
        # 3. Khởi tạo Service và tạo file
        exporter = DocxExportService()
        exporter.create_standard_docx(exam_data, filepath)

        # 4. Kiểm tra file có tồn tại không
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Could not create docx file")

        # 5. Trả về file cho frontend
        return FileResponse(
            path=filepath,
            filename="Soluted_Exam.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print(f"Error exporting docx: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@routerSolute.post("/export-soluted-literature-exam")
async def export_soluted_literature_exam(payload: dict):
    try:
        # 1. Trích xuất dữ liệu thực tế từ payload
        # Theo cấu trúc JSON bạn gửi: {"results": [{...}]}
        if "results" in payload and len(payload["results"]) > 0:
            exam_data = payload["results"][0]
        else:
            exam_data = payload # Trường hợp payload là object trực tiếp

        # 2. Định nghĩa đường dẫn file tạm
        filepath = "output_literature_exam.docx"
        
        # 3. Khởi tạo Service và tạo file
        exporter = DocxExportService()
        exporter.create_literature_docx(exam_data, filepath)

        # 4. Kiểm tra file có tồn tại không
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="Could not create docx file")

        # 5. Trả về file cho frontend
        return FileResponse(
            path=filepath,
            filename="Soluted_Literature_Exam.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print(f"Error exporting docx: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@routerSolute.post("/solute-exam")
async def solute_exam(
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
        result = await solve_other_exam(file_paths)

        print(f">>>>>>> debug result {result}")

        return {
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # ✅ Luôn xóa file temp dù thành công hay lỗi
        for path in file_paths:
            try:
                file = Path(path)
                if file.exists():
                    file.unlink()
                    print(f">>>>>>> deleted temp file: {path}")
            except Exception as cleanup_error:
                print(f">>>>>>> failed to delete {path}: {cleanup_error}")

@routerSolute.post("/solute-history-exam")
async def solute_history_exam(
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
        result = await solve_history_exam(file_paths)

        print(f">>>>>>> debug result {result}")

        return {
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # ✅ Luôn xóa file temp dù thành công hay lỗi
        for path in file_paths:
            try:
                file = Path(path)
                if file.exists():
                    file.unlink()
                    print(f">>>>>>> deleted temp file: {path}")
            except Exception as cleanup_error:
                print(f">>>>>>> failed to delete {path}: {cleanup_error}")


@routerSolute.post("/solute-math-exam")
async def solute_math_exam(
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
        result = await solve_math_exam(file_paths)

        print(f">>>>>>> debug result {result}")

        return {
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # ✅ Luôn xóa file temp dù thành công hay lỗi
        for path in file_paths:
            try:
                file = Path(path)
                if file.exists():
                    file.unlink()
                    print(f">>>>>>> deleted temp file: {path}")
            except Exception as cleanup_error:
                print(f">>>>>>> failed to delete {path}: {cleanup_error}")

@routerSolute.post("/solute-geography-exam")
async def solute_geography_exam(
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
        result = await solve_geography_exam(file_paths)

        print(f">>>>>>> debug result {result}")

        return {
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # ✅ Luôn xóa file temp dù thành công hay lỗi
        for path in file_paths:
            try:
                file = Path(path)
                if file.exists():
                    file.unlink()
                    print(f">>>>>>> deleted temp file: {path}")
            except Exception as cleanup_error:
                print(f">>>>>>> failed to delete {path}: {cleanup_error}")

@routerSolute.post("/solute-literature-exam")
async def solute_literature_exam(
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
        result = await solve_literature_exam(file_paths)

        print(f">>>>>>> debug result {result}")

        return {
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # ✅ Luôn xóa file temp dù thành công hay lỗi
        for path in file_paths:
            try:
                file = Path(path)
                if file.exists():
                    file.unlink()
                    print(f">>>>>>> deleted temp file: {path}")
            except Exception as cleanup_error:
                print(f">>>>>>> failed to delete {path}: {cleanup_error}")



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
    
    finally:
        # ✅ Luôn xóa file temp dù thành công hay lỗi
        for path in file_paths:
            try:
                file = Path(path)
                if file.exists():
                    file.unlink()
                    print(f">>>>>>> deleted temp file: {path}")
            except Exception as cleanup_error:
                print(f">>>>>>> failed to delete {path}: {cleanup_error}")

