from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path
import uuid
import json
import subprocess
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.core.google_drive_service import GoogleDriveService

router = APIRouter(
    prefix="/google-drive",
    tags=["google-drive"],
    responses={404: {"description": "Not found"}},
)


class DownloadRequest(BaseModel):
    file_id: str
    file_name: Optional[str] = None


class FolderListRequest(BaseModel):
    folder_id: str
    query: Optional[str] = None


class ProcessContentRequest(BaseModel):
    folder_id: str
    json_file_name: Optional[str] = "lesson_data_C12_1_1.json"


@router.post("/download")
async def download_file(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Tải xuống file từ Google Drive

    - **file_id**: ID của file trên Google Drive
    - **file_name**: Tên file tùy chọn khi lưu (optional)
    """
    try:
        # Khởi tạo service
        drive_service = GoogleDriveService()

        # Tạo đường dẫn tạm thời
        temp_dir = Path("data/temp")
        temp_dir.mkdir(exist_ok=True)

        # Tạo tên file ngẫu nhiên nếu không cung cấp
        if not request.file_name:
            request.file_name = f"downloaded_{uuid.uuid4().hex[:8]}"

        output_path = temp_dir / request.file_name

        # Tải xuống file
        result = drive_service.download_file(request.file_id, str(output_path))

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        # Trả về file
        background_tasks.add_task(cleanup_temp_file, output_path)

        return FileResponse(
            path=output_path,
            filename=result['file_name'],
            media_type='application/octet-stream'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tải file: {str(e)}")


@router.get("/file-info/{file_id}")
async def get_file_info(file_id: str):
    """
    Lấy thông tin file từ Google Drive

    - **file_id**: ID của file
    """
    try:
        drive_service = GoogleDriveService()
        result = drive_service.get_file_info(file_id)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        return result['file_info']

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy thông tin file: {str(e)}")


@router.post("/list-folder")
async def list_folder_files(request: FolderListRequest):
    """
    Liệt kê files trong folder Google Drive

    - **folder_id**: ID của folder
    - **query**: Query bổ sung (optional)
    """
    try:
        drive_service = GoogleDriveService()
        result = drive_service.list_files_in_folder(request.folder_id, request.query)

        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi liệt kê files: {str(e)}")


@router.post("/process-content")
async def process_content(request: ProcessContentRequest):
    """
    Xử lý nội dung từ Google Drive folder

    - **folder_id**: ID của folder cuối chứa files hoặc JSON
    - **json_file_name**: Tên file JSON mong đợi (optional, mặc định lesson_data_C12_1_1.json)
    """
    try:
        drive_service = GoogleDriveService()

        # Kiểm tra xem có file JSON không
        result = drive_service.list_files_in_folder(request.folder_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])

        files = result['files']
        json_file = None
        for file_info in files:
            if file_info['name'] == request.json_file_name:
                json_file = file_info
                break

        if json_file:
            # Download file JSON hiện có
            temp_dir = Path("data/temp")
            temp_dir.mkdir(exist_ok=True)
            output_path = temp_dir / request.json_file_name

            download_result = drive_service.download_file(json_file['id'], str(output_path))
            if not download_result['success']:
                raise HTTPException(status_code=400, detail=download_result['error'])

            # Đọc và trả về nội dung JSON
            with open(output_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)

            # Cleanup
            try:
                output_path.unlink()
            except:
                pass

            return {
                'status': 'downloaded_existing',
                'json_content': json_content
            }

        else:
            # Download tất cả files
            downloads_dir = "downloads"
            download_result = drive_service.download_all_files_in_folder(request.folder_id, downloads_dir)
            if not download_result['success']:
                raise HTTPException(status_code=400, detail=download_result['error'])

            # Chạy build_json_structure.py
            try:
                result = subprocess.run(
                    ['python', 'build_json_structure.py'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    cwd=os.getcwd()
                )
                if result.returncode != 0:
                    raise HTTPException(status_code=500, detail=f"Lỗi build JSON: {result.stderr}")

                # Đọc file JSON đã tạo
                json_file_path = "lesson_data_C12_1_1.json"
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    json_content = json.load(f)

                # Trả về JSON content (không upload do limitation của service account)
                return {
                    'status': 'created_new',
                    'json_content': json_content,
                    'message': 'JSON created successfully from downloaded files.'
                }

            except subprocess.CalledProcessError as e:
                raise HTTPException(status_code=500, detail=f"Lỗi chạy script: {e.stderr}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý content: {str(e)}")


class ProcessMatrixRequest(BaseModel):
    matrix_file_path: str
    output_json_path: Optional[str] = None


@router.post("/process-matrix")
async def process_matrix_file(request: ProcessMatrixRequest, background_tasks: BackgroundTasks):
    """
    Tự động process file ma trận để tạo JSON hoàn chỉnh từ Google Drive

    - **matrix_file_path**: Đường dẫn đến file ma trận Excel
    - **output_json_path**: Đường dẫn output JSON (optional, auto-generate nếu không cung cấp)
    """
    try:
        matrix_path = Path(request.matrix_file_path)
        if not matrix_path.exists():
            raise HTTPException(status_code=404, detail=f"File ma trận không tồn tại: {request.matrix_file_path}")

        # Import MatrixParser
        from services.core.matrix_parser import MatrixParser

        print(f"🔍 Processing matrix file: {request.matrix_file_path}")

        # Load và parse matrix
        parser = MatrixParser()
        parser.load_excel(str(matrix_path))

        # Tạo path tự động
        path = parser.generate_drive_path()
        print(f"📂 Generated path: {'/'.join(path)}")

        # Navigate để tìm folder cuối
        drive_service = GoogleDriveService()
        root_folder_id = os.getenv('ROOT_GDRIVE_FOLDER_ID')
        if not root_folder_id:
            raise HTTPException(status_code=500, detail="ROOT_GDRIVE_FOLDER_ID not configured")

        current_folder_id = root_folder_id

        # Navigate qua từng level
        for segment in path:
            print(f"📂 Looking for '{segment}' in current folder...")
            found = False

            files = drive_service.list_files_in_folder(current_folder_id)
            for file_info in files:
                if (file_info['mimeType'] == 'application/vnd.google-apps.folder' and
                    file_info['name'].lower() == segment.lower()):
                    current_folder_id = file_info['id']
                    print(f"✅ Found folder: {file_info['name']} (ID: {current_folder_id})")
                    found = True
                    break

            if not found:
                available_folders = [f['name'] for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
                raise HTTPException(
                    status_code=404,
                    detail=f"Folder '{segment}' not found. Available: {available_folders}"
                )

        # Đã đến folder cuối, process content
        print(f"\n🎯 Reached target folder: {'/'.join(path)}")
        print("🔄 Starting content processing...")

        # Download tất cả files trong folder
        downloads_dir = Path("downloads") / "_".join(path[:2])  # Lớp_Môn
        downloads_dir.mkdir(parents=True, exist_ok=True)

        files = drive_service.list_files_in_folder(current_folder_id)
        downloaded_files = []

        for file_info in files:
            if file_info['mimeType'] == 'application/vnd.google-apps.folder':
                continue  # Skip folders

            file_name = file_info['name']
            local_path = downloads_dir / file_name

            print(f"⬇️  Downloading: {file_name}")
            drive_service.download_file(file_info['id'], str(local_path))
            downloaded_files.append(str(local_path))

        # Process content từ downloaded files
        from services.build_json_structure import build_json_structure

        json_content = build_json_structure(
            downloads_dir=str(downloads_dir),
            subject=parser.subject or "UNKNOWN",
            grade=parser.grade or "UNKNOWN",
            topic=f"{path[3]}_{path[4]}" if len(path) > 4 else "unknown"
        )

        # Enrich JSON với thông tin từ matrix
        json_content['matrix_info'] = {
            'file_name': matrix_path.name,
            'subject': parser.subject,
            'curriculum': parser.curriculum,
            'grade': parser.grade,
            'chapter_number': path[3] if len(path) > 3 else None,
            'lesson_number': path[4] if len(path) > 4 else None,
            'generated_path': path
        }

        # Parse thêm thông tin từ matrix để enrich questions
        all_specs = parser.get_all_question_specs()
        json_content['matrix_questions'] = {
            'TN': [spec.__dict__ for spec in all_specs['TN']],
            'DS': [spec.__dict__ for spec in all_specs['DS']],
            'TLN': [spec.__dict__ for spec in all_specs['TLN']]
        }

        # Save JSON
        if request.output_json_path:
            output_path = Path(request.output_json_path)
        else:
            matrix_name = matrix_path.stem
            output_path = Path("data/output") / f"{matrix_name}_processed.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False, indent=2)

        # Cleanup downloaded files
        background_tasks.add_task(cleanup_temp_files, downloaded_files)

        return {
            "status": "success",
            "message": f"Processed matrix file successfully",
            "output_path": str(output_path),
            "generated_path": path,
            "json_content": json_content
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý matrix file: {str(e)}")


def cleanup_temp_file(file_path: Path):
    """
    Xóa file tạm thời sau khi download
    """
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Lỗi xóa file tạm: {e}")


def cleanup_temp_files(file_paths: list):
    """
    Xóa nhiều file tạm thời
    """
    for file_path in file_paths:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            print(f"Lỗi xóa file tạm {file_path}: {e}")