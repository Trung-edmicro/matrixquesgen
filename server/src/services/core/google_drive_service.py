import os
import io
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import google.auth.exceptions


class GoogleDriveService:
    """
    Service để tương tác với Google Drive API
    """

    def __init__(self, credentials_path: Optional[str] = None, scopes: Optional[list] = None):
        """
        Khởi tạo Google Drive service

        Args:
            credentials_path: Đường dẫn đến file credentials JSON
            scopes: List các scopes cần thiết
        """
        self.credentials_path = credentials_path or os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
        self.scopes = scopes or ['https://www.googleapis.com/auth/drive']
        self.service = None
        self._authenticated = False
        
        # Đường dẫn lưu metadata file
        self.metadata_dir = Path(os.getenv('DATA_DIR', 'data')) / '.drive_metadata'
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def authenticate(self) -> bool:
        """
        Xác thực với Google Drive API

        Returns:
            bool: True nếu xác thực thành công
        """
        if self._authenticated and self.service:
            return True

        try:
            if not self.credentials_path or not Path(self.credentials_path).exists():
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.scopes
            )

            self.service = build('drive', 'v3', credentials=creds)
            self._authenticated = True
            return True

        except Exception as e:
            self._authenticated = False
            self.service = None
            print(f"❌ Lỗi xác thực Google Drive: {e}")
            return False

    def download_file(self, file_id: str, output_path: str, check_version: bool = True) -> Dict[str, Any]:
        """
        Tải xuống file từ Google Drive với kiểm tra version

        Args:
            file_id: ID của file trên Google Drive
            output_path: Đường dẫn lưu file local
            check_version: Có kiểm tra version trước khi tải không (default: True)

        Returns:
            Dict chứa thông tin kết quả
        """
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            # Lấy thông tin file từ Drive
            file_metadata = self.service.files().get(
                fileId=file_id, 
                fields='id,name,size,mimeType,modifiedTime'
            ).execute()
            
            file_name = file_metadata.get('name', 'downloaded_file')
            drive_modified_time = file_metadata.get('modifiedTime')
            
            # Kiểm tra xem có cần tải mới không
            if check_version and Path(output_path).exists():
                need_update = self._check_if_file_needs_update(file_id, output_path, drive_modified_time)
                
                if not need_update:
                    print(f"✓ File '{file_name}' đã là phiên bản mới nhất (local)")
                    return {
                        'success': True,
                        'file_name': file_name,
                        'file_path': output_path,
                        'file_size': file_metadata.get('size', 0),
                        'mime_type': file_metadata.get('mimeType', ''),
                        'modified_time': drive_modified_time,
                        'status': 'up_to_date',
                        'message': 'File already up to date'
                    }
                else:
                    print(f"⟳ Phát hiện phiên bản mới của '{file_name}' trên Drive, đang tải xuống...")

            # Tải xuống file
            request = self.service.files().get_media(fileId=file_id)

            # Tạo thư mục nếu chưa tồn tại
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with io.FileIO(output_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()

            # Lưu metadata
            self._save_file_metadata(file_id, output_path, file_metadata)
            
            return {
                'success': True,
                'file_name': file_name,
                'file_path': output_path,
                'file_size': file_metadata.get('size', 0),
                'mime_type': file_metadata.get('mimeType', ''),
                'modified_time': drive_modified_time,
                'status': 'downloaded',
                'message': 'File downloaded successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_metadata_path(self, file_id: str) -> Path:
        """
        Lấy đường dẫn file metadata cho một file Drive ID

        Args:
            file_id: ID của file trên Google Drive

        Returns:
            Path đến file metadata
        """
        return self.metadata_dir / f"{file_id}.json"

    def _save_file_metadata(self, file_id: str, local_path: str, drive_metadata: Dict[str, Any]) -> None:
        """
        Lưu metadata của file (thời gian chỉnh sửa, tên, etc.)

        Args:
            file_id: ID của file trên Google Drive
            local_path: Đường dẫn file local
            drive_metadata: Metadata từ Google Drive API
        """
        try:
            metadata = {
                'file_id': file_id,
                'local_path': local_path,
                'drive_name': drive_metadata.get('name'),
                'drive_modified_time': drive_metadata.get('modifiedTime'),
                'drive_size': drive_metadata.get('size'),
                'mime_type': drive_metadata.get('mimeType'),
                'last_checked': datetime.now().isoformat(),
                'last_downloaded': datetime.now().isoformat()
            }
            
            metadata_path = self._get_metadata_path(file_id)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save metadata for file {file_id}: {e}")

    def _load_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Đọc metadata đã lưu của file

        Args:
            file_id: ID của file trên Google Drive

        Returns:
            Dict chứa metadata hoặc None nếu không tìm thấy
        """
        try:
            metadata_path = self._get_metadata_path(file_id)
            if not metadata_path.exists():
                return None
                
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Warning: Could not load metadata for file {file_id}: {e}")
            return None

    def _check_if_file_needs_update(self, file_id: str, local_path: str, drive_modified_time: str) -> bool:
        """
        Kiểm tra xem file local có cần cập nhật không

        Args:
            file_id: ID của file trên Google Drive
            local_path: Đường dẫn file local
            drive_modified_time: Thời gian chỉnh sửa từ Drive (ISO format)

        Returns:
            True nếu cần tải lại file, False nếu file local đã mới nhất
        """
        try:
            # Kiểm tra file local có tồn tại không
            local_file = Path(local_path)
            if not local_file.exists():
                return True
            
            # Kiểm tra file có rỗng hay bị lỗi không
            file_size = local_file.stat().st_size
            if file_size == 0:
                # print(f"⚠️  File local '{local_file.name}' rỗng, cần tải lại")
                return True
            
            # Đọc metadata đã lưu
            metadata = self._load_file_metadata(file_id)
            if not metadata:
                # Không có metadata -> cần tải lại để lưu metadata
                return True
            
            # So sánh thời gian chỉnh sửa
            saved_modified_time = metadata.get('drive_modified_time')
            if not saved_modified_time:
                return True
            
            # Parse thời gian
            drive_time = datetime.fromisoformat(drive_modified_time.replace('Z', '+00:00'))
            saved_time = datetime.fromisoformat(saved_modified_time.replace('Z', '+00:00'))
            
            # Nếu file trên Drive mới hơn -> cần cập nhật
            if drive_time > saved_time:
                return True
            
            # Kiểm tra file size từ metadata có khớp không
            saved_size = metadata.get('drive_size')
            if saved_size and file_size != int(saved_size):
                print(f"⚠️  File size không khớp (local: {file_size}, expected: {saved_size}), cần tải lại")
                return True
            
            # File local đã là bản mới nhất và hợp lệ
            return False
            
        except Exception as e:
            print(f"Warning: Error checking file version for {file_id}: {e}")
            # Nếu có lỗi, để an toàn ta tải lại file
            return True

    def check_file_version(self, file_id: str, local_path: str) -> Dict[str, Any]:
        """
        Kiểm tra phiên bản file mà không tải xuống

        Args:
            file_id: ID của file trên Google Drive
            local_path: Đường dẫn file local

        Returns:
            Dict chứa thông tin version
        """
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            # Lấy thông tin file từ Drive
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id,name,modifiedTime,size'
            ).execute()

            drive_modified_time = file_metadata.get('modifiedTime')
            file_name = file_metadata.get('name')

            # Kiểm tra file local
            local_exists = Path(local_path).exists()
            
            if not local_exists:
                return {
                    'success': True,
                    'file_name': file_name,
                    'needs_update': True,
                    'reason': 'File does not exist locally',
                    'drive_modified_time': drive_modified_time
                }

            # Đọc metadata
            metadata = self._load_file_metadata(file_id)
            
            if not metadata:
                return {
                    'success': True,
                    'file_name': file_name,
                    'needs_update': True,
                    'reason': 'No metadata found',
                    'drive_modified_time': drive_modified_time
                }

            saved_modified_time = metadata.get('drive_modified_time')
            
            # So sánh thời gian
            drive_time = datetime.fromisoformat(drive_modified_time.replace('Z', '+00:00'))
            saved_time = datetime.fromisoformat(saved_modified_time.replace('Z', '+00:00'))
            
            needs_update = drive_time > saved_time
            
            return {
                'success': True,
                'file_name': file_name,
                'needs_update': needs_update,
                'drive_modified_time': drive_modified_time,
                'local_modified_time': saved_modified_time,
                'reason': 'Drive version is newer' if needs_update else 'Local file is up to date'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Lấy thông tin file từ Google Drive

        Args:
            file_id: ID của file

        Returns:
            Dict chứa thông tin file
        """
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            file_info = self.service.files().get(fileId=file_id, fields='*').execute()

            return {
                'success': True,
                'file_info': file_info
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_files_in_folder(self, folder_id: str, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Liệt kê files trong một folder

        Args:
            folder_id: ID của folder
            query: Query bổ sung (optional)

        Returns:
            Dict chứa list files
        """
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            base_query = f"'{folder_id}' in parents and trashed = false"
            if query:
                base_query += f" and {query}"

            # Retry logic for SSL errors
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    results = self.service.files().list(
                        q=base_query,
                        fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
                    ).execute()
                    break
                except Exception as api_error:
                    error_msg = str(api_error)
                    if 'SSL' in error_msg and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                        print(f"SSL error in list_files (attempt {attempt + 1}/{max_retries}): {error_msg}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise api_error

            files = results.get('files', [])

            return {
                'success': True,
                'files': files
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def upload_file(self, file_path: str, folder_id: str, file_name: Optional[str] = None, supports_all_drives: bool = True) -> Dict[str, Any]:
        """
        Upload file lên Google Drive

        Args:
            file_path: Đường dẫn file local
            folder_id: ID của folder đích trên Drive
            file_name: Tên file trên Drive (optional, mặc định lấy từ file_path)
            supports_all_drives: True để support Shared Drives

        Returns:
            Dict chứa thông tin kết quả
        """
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            from googleapiclient.http import MediaFileUpload

            if not file_name:
                file_name = Path(file_path).name

            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }

            media = MediaFileUpload(file_path, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink',
                supportsAllDrives=supports_all_drives
            ).execute()

            return {
                'success': True,
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_view_link': file.get('webViewLink')
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def is_shared_drive_folder(self, folder_id: str) -> bool:
        """
        Kiểm tra xem folder có phải thuộc Shared Drive hay không

        Args:
            folder_id: ID của folder

        Returns:
            bool: True nếu là Shared Drive
        """
        try:
            if not self.authenticate():
                return False

            # Lấy thông tin folder
            folder_info = self.service.files().get(
                fileId=folder_id,
                fields='driveId,shared'
            ).execute()

            # Nếu có driveId và khác với personal drive, thì là Shared Drive
            drive_id = folder_info.get('driveId')
            if drive_id and drive_id != folder_id:  # Shared Drives có driveId khác
                return True

            return False

        except Exception as e:
            print(f"Error checking if shared drive: {e}")
            return False

    def download_all_files_in_folder(self, folder_id: str, output_dir: str, check_version: bool = True) -> Dict[str, Any]:
        """
        Download tất cả files trong folder với kiểm tra version

        Args:
            folder_id: ID của folder
            output_dir: Thư mục lưu files local
            check_version: Có kiểm tra version trước khi tải không (default: True)

        Returns:
            Dict chứa thông tin kết quả
        """
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            # Tạo thư mục output
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # List files trong folder
            result = self.list_files_in_folder(folder_id)
            if not result['success']:
                return result

            files = result['files']
            if not files:
                return {
                    'success': True,
                    'message': 'Folder is empty',
                    'downloaded_files': [],
                    'up_to_date_files': [],
                    'skipped_folders': []
                }

            downloaded_files = []
            up_to_date_files = []
            skipped_folders = []
            
            for file_info in files:
                file_id = file_info['id']
                file_name = file_info['name']
                mime_type = file_info['mimeType']

                # Skip folders
                if mime_type == 'application/vnd.google-apps.folder':
                    skipped_folders.append(file_name)
                    continue

                output_path = Path(output_dir) / file_name

                # Download file với version check
                download_result = self.download_file(file_id, str(output_path), check_version=check_version)
                if download_result['success']:
                    file_entry = {
                        'file_name': file_name,
                        'file_path': str(output_path),
                        'file_id': file_id,
                        'modified_time': download_result.get('modified_time')
                    }
                    
                    if download_result.get('status') == 'up_to_date':
                        up_to_date_files.append(file_entry)
                    else:
                        downloaded_files.append(file_entry)
                else:
                    print(f"Failed to download {file_name}: {download_result['error']}")

            return {
                'success': True,
                'downloaded_files': downloaded_files,
                'up_to_date_files': up_to_date_files,
                'skipped_folders': skipped_folders,
                'total_downloaded': len(downloaded_files),
                'total_up_to_date': len(up_to_date_files),
                'total_processed': len(downloaded_files) + len(up_to_date_files)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }