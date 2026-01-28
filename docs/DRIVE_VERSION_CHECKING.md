# Tính năng Tự động Kiểm tra Phiên bản File từ Google Drive

## Tổng quan

Hệ thống tự động kiểm tra và cập nhật file từ Google Drive dựa trên thời gian chỉnh sửa (modified time). Tránh tải lại file không cần thiết, tiết kiệm bandwidth và thời gian.

## Cơ chế hoạt động

### 1. Lưu trữ Metadata

Mỗi file tải từ Google Drive sẽ có metadata được lưu tại:

```
data/.drive_metadata/<file_id>.json
```

**Nội dung metadata:**

```json
{
  "file_id": "1abc...xyz",
  "local_path": "data/content/HOAHOC_C12_3_10_content.json",
  "drive_name": "HOAHOC_C12_3_10_content.json",
  "drive_modified_time": "2026-01-20T10:30:00.000Z",
  "drive_size": "12345",
  "mime_type": "application/json",
  "last_checked": "2026-01-22T15:45:00.123456",
  "last_downloaded": "2026-01-20T14:20:00.123456"
}
```

### 2. Logic Kiểm tra Version

Khi gọi `download_file()` với `check_version=True`:

1. **File local không tồn tại** → Tải file mới
2. **Không có metadata** → Tải file và tạo metadata
3. **So sánh thời gian:**
   - Drive `modifiedTime` > Local `drive_modified_time` → Tải bản mới
   - Drive `modifiedTime` ≤ Local `drive_modified_time` → Skip, dùng file local

### 3. Kết quả trả về

```python
{
    'success': True,
    'file_name': 'example.json',
    'file_path': '/path/to/file',
    'status': 'up_to_date'|'downloaded',  # Trạng thái
    'modified_time': '2026-01-20T10:30:00.000Z',
    'message': 'File already up to date'
}
```

## API Usage

### 1. Download file với kiểm tra version (Mặc định)

```python
from services.core.google_drive_service import GoogleDriveService

drive_service = GoogleDriveService()
drive_service.authenticate()

# Tự động kiểm tra version
result = drive_service.download_file(
    file_id='1abc...xyz',
    output_path='data/output/file.json'
    # check_version=True (default)
)

if result['success']:
    if result['status'] == 'up_to_date':
        print("✓ File đã là bản mới nhất")
    else:
        print("✓ Đã tải bản mới")
```

### 2. Download file không kiểm tra version

```python
# Force download mặc dù file đã tồn tại
result = drive_service.download_file(
    file_id='1abc...xyz',
    output_path='data/output/file.json',
    check_version=False  # Bỏ qua kiểm tra version
)
```

### 3. Chỉ kiểm tra version (không download)

```python
# Kiểm tra xem file có cần cập nhật không
version_info = drive_service.check_file_version(
    file_id='1abc...xyz',
    local_path='data/output/file.json'
)

if version_info['success']:
    if version_info['needs_update']:
        print(f"⟳ Cần cập nhật: {version_info['reason']}")
        print(f"   Drive: {version_info['drive_modified_time']}")
        print(f"   Local: {version_info['local_modified_time']}")
    else:
        print(f"✓ File đã cập nhật")
```

### 4. Download toàn bộ folder với version checking

```python
result = drive_service.download_all_files_in_folder(
    folder_id='1def...uvw',
    output_dir='data/lesson_content',
    check_version=True  # Kiểm tra từng file
)

if result['success']:
    print(f"Tải mới: {result['total_downloaded']} files")
    print(f"Đã cập nhật: {result['total_up_to_date']} files")
    print(f"Tổng: {result['total_processed']} files")
```

## Integration trong ContentAcquisitionService

Tính năng đã được tích hợp tự động vào:

### 1. Download Lesson Content

```python
# File: phase2_content_acquisition.py
content_items = content_service.download_content_by_path(
    drive_path=['C12', 'HOAHOC', 'HOAHOC_KNTT_C12_3_10'],
    check_version=True  # Tự động kiểm tra version
)
```

### 2. Download Prompts

```python
# Trong download_prompts_from_drive()
# Tự động kiểm tra version cho từng prompt file
success = content_service.download_prompts_from_drive(
    grade='C12',
    subject='HOAHOC',
    curriculum='KNTT'
)
```

### 3. Output Logs

Khi chạy, bạn sẽ thấy logs:

```
🔄 Đang download prompts từ Drive (C12/HOAHOC/Prompts)...
  ✓ TN.txt (đã cập nhật)
  ✓ DS.txt (mới tải)
✓ Đã tải mới 1 prompts, 1 prompts đã cập nhật (2/2 tổng)
```

hoặc nếu tất cả đã cập nhật:

```
  ✓ TN.txt (đã cập nhật)
  ✓ DS.txt (đã cập nhật)
✓ Tất cả 2 prompts đã là phiên bản mới nhất
```

## Testing

### 1. Cấu hình Test

Thêm vào `.env`:

```env
# File ID để test version checking
TEST_FILE_ID=1abc...xyz

# Folder ID để test download folder
TEST_FOLDER_ID=1def...uvw
```

### 2. Chạy Test Suite

```bash
python test_drive_version.py
```

Test suite sẽ kiểm tra:

- ✓ Download file lần đầu
- ✓ Download lại file (nên skip)
- ✓ Kiểm tra API check_file_version
- ✓ Kiểm tra metadata file
- ✓ Download folder với version checking

### 3. Test Manual

```python
from services.core.google_drive_service import GoogleDriveService

drive = GoogleDriveService()
drive.authenticate()

# Test 1: Download lần đầu
r1 = drive.download_file('file_id', 'test.txt')
print(r1['status'])  # Expected: 'downloaded'

# Test 2: Download lại ngay (chưa thay đổi)
r2 = drive.download_file('file_id', 'test.txt')
print(r2['status'])  # Expected: 'up_to_date'

# Test 3: Check version
info = drive.check_file_version('file_id', 'test.txt')
print(info['needs_update'])  # Expected: False
```

## Lợi ích

### 1. Tiết kiệm Bandwidth

- Không tải lại file khi không cần
- Đặc biệt hữu ích cho file lớn

### 2. Tăng tốc độ xử lý

- Skip download cho file đã cập nhật
- Workflow chạy nhanh hơn

### 3. Sync tự động

- Phát hiện ngay khi file trên Drive được cập nhật
- Tự động tải bản mới nhất

### 4. Logging rõ ràng

- Biết được file nào được tải mới
- File nào đã cập nhật

## Xử lý Edge Cases

### 1. Metadata bị mất/hỏng

```python
# Hệ thống tự động tải lại file và tạo metadata mới
# Không gây lỗi
```

### 2. File local bị xóa

```python
# Hệ thống phát hiện và tải lại file
# Tạo lại metadata
```

### 3. Lỗi trong quá trình check

```python
# Default: tải lại file để đảm bảo an toàn
# Log warning để debug
```

### 4. File trên Drive bị xóa

```python
# API sẽ trả về error
# File local vẫn tồn tại (không bị xóa)
```

## Best Practices

### 1. Luôn sử dụng version checking

```python
# ✓ GOOD
result = drive_service.download_file(file_id, path)

# ✗ BAD (trừ khi có lý do đặc biệt)
result = drive_service.download_file(file_id, path, check_version=False)
```

### 2. Check version trước khi xử lý nhiều

```python
# Nếu cần check nhiều files
for file_id, local_path in files_to_check:
    info = drive_service.check_file_version(file_id, local_path)
    if info['needs_update']:
        # Chỉ download files cần cập nhật
        drive_service.download_file(file_id, local_path)
```

### 3. Xử lý kết quả đúng cách

```python
result = drive_service.download_file(file_id, path)

if result['success']:
    if result['status'] == 'downloaded':
        # File mới được tải, có thể cần xử lý lại
        process_file(result['file_path'])
    elif result['status'] == 'up_to_date':
        # File đã có, có thể dùng cache
        use_cached_result(result['file_path'])
```

### 4. Cleanup metadata định kỳ

```python
# Có thể xóa metadata của files không còn dùng
from pathlib import Path

metadata_dir = Path('data/.drive_metadata')
for metadata_file in metadata_dir.glob('*.json'):
    # Check và cleanup nếu cần
    pass
```

## Troubleshooting

### Vấn đề: File luôn bị tải lại

**Nguyên nhân:**

- Metadata bị xóa
- Thời gian không khớp do timezone

**Giải pháp:**

```python
# Check metadata
metadata = drive._load_file_metadata(file_id)
print(metadata)

# Check thời gian
info = drive.check_file_version(file_id, local_path)
print(info['drive_modified_time'])
print(info['local_modified_time'])
```

### Vấn đề: File không được cập nhật

**Nguyên nhân:**

- Metadata lỗi thời
- File Drive chưa sync

**Giải pháp:**

```python
# Force download
drive.download_file(file_id, path, check_version=False)

# Hoặc xóa metadata
metadata_path = drive._get_metadata_path(file_id)
metadata_path.unlink()
```

### Vấn đề: Error khi parse thời gian

**Nguyên nhân:**

- Format thời gian từ Drive thay đổi

**Giải pháp:**

- Check logs
- Update parsing logic nếu cần

## Changelog

### Version 1.0.0 (2026-01-22)

- ✓ Thêm metadata storage system
- ✓ Implement version checking logic
- ✓ Integrate vào ContentAcquisitionService
- ✓ Support folder download với version check
- ✓ Thêm comprehensive test suite
- ✓ Logging và status reporting

## Future Enhancements

### 1. Cache Management

- Tự động cleanup metadata cũ
- Giới hạn kích thước cache

### 2. Advanced Sync

- Batch version checking
- Parallel downloads cho file cần update

### 3. Web UI

- Hiển thị trạng thái sync
- Manual trigger sync

### 4. Statistics

- Track download stats
- Bandwidth savings report
