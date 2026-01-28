# Tính năng Tự động Kiểm tra và Cập nhật File từ Google Drive

## Tóm tắt

Đã xây dựng thành công tính năng **tự động kiểm tra phiên bản file** từ Google Drive. Hệ thống sẽ:

- ✓ Lưu thông tin thời gian chỉnh sửa (metadata) của mỗi file tải xuống
- ✓ So sánh thời gian giữa file trên Drive và file local
- ✓ Chỉ tải file khi phát hiện có phiên bản mới
- ✓ Tự động sử dụng file local nếu đã là bản mới nhất

## Files đã thay đổi

### 1. `server/src/services/core/google_drive_service.py`

**Thêm mới:**

- `_get_metadata_path()` - Lấy đường dẫn file metadata
- `_save_file_metadata()` - Lưu metadata file (thời gian, tên, kích thước)
- `_load_file_metadata()` - Đọc metadata đã lưu
- `_check_if_file_needs_update()` - So sánh thời gian để quyết định có cần tải lại
- `check_file_version()` - API công khai để kiểm tra version

**Cập nhật:**

- `__init__()` - Thêm metadata directory management
- `download_file()` - Thêm tham số `check_version` và logic kiểm tra
- `download_all_files_in_folder()` - Thêm support cho version checking

**Cơ chế:**

```python
# Metadata được lưu tại: data/.drive_metadata/<file_id>.json
{
  "file_id": "...",
  "drive_modified_time": "2026-01-20T10:30:00.000Z",
  "local_path": "...",
  "last_downloaded": "..."
}

# So sánh: drive_time > saved_time → Tải lại file
```

### 2. `server/src/services/phases/phase2_content_acquisition.py`

**Cập nhật:**

- `download_content_by_path()` - Thêm tham số `check_version` (default: True)
- `download_prompts_from_drive()` - Thêm logs chi tiết về trạng thái download

**Tích hợp:**

- Tự động áp dụng version checking cho tất cả downloads
- Hiển thị rõ ràng file nào được tải mới, file nào đã cập nhật

### 3. Files mới

#### `test_drive_version.py`

Test suite đầy đủ cho tính năng version checking:

- Test download file lần đầu
- Test download lại file (nên skip)
- Test API check_file_version
- Test download folder với version checking
- Kiểm tra metadata files

#### `docs/DRIVE_VERSION_CHECKING.md`

Tài liệu chi tiết:

- Giải thích cơ chế hoạt động
- API usage examples
- Integration guide
- Best practices
- Troubleshooting

## Cách sử dụng

### 1. Basic Usage (Tự động)

```python
# Mặc định đã bật version checking
result = drive_service.download_file(file_id, output_path)

if result['status'] == 'up_to_date':
    print("✓ File đã là bản mới nhất")
else:
    print("✓ Đã tải bản mới")
```

### 2. Check version mà không download

```python
info = drive_service.check_file_version(file_id, local_path)

if info['needs_update']:
    print(f"Cần cập nhật: {info['reason']}")
```

### 3. Download folder

```python
result = drive_service.download_all_files_in_folder(
    folder_id,
    output_dir,
    check_version=True
)

print(f"Tải mới: {result['total_downloaded']}")
print(f"Đã cập nhật: {result['total_up_to_date']}")
```

## Lợi ích

### 1. Tiết kiệm Bandwidth

- Không tải lại file không cần thiết
- Đặc biệt quan trọng với file lớn

### 2. Tăng tốc độ

- Workflow chạy nhanh hơn khi skip download
- Giảm thời gian chờ

### 3. Tự động sync

- Luôn có bản mới nhất từ Drive
- Không cần check thủ công

### 4. Logging rõ ràng

```
🔄 Đang download prompts từ Drive (C12/HOAHOC/Prompts)...
  ✓ TN.txt (đã cập nhật)
  ✓ DS.txt (mới tải)
✓ Đã tải mới 1 prompts, 1 prompts đã cập nhật (2/2 tổng)
```

## Testing

### Chạy Test Suite

```bash
python test_drive_version.py
```

### Cần cấu hình trong .env

```env
# Optional: để test đầy đủ
TEST_FILE_ID=<your_file_id>
TEST_FOLDER_ID=<your_folder_id>
```

### Test Cases

1. ✓ Download file lần đầu → status='downloaded'
2. ✓ Download lại file → status='up_to_date'
3. ✓ Check version API → needs_update=False
4. ✓ Metadata được tạo và lưu đúng
5. ✓ Download folder với multiple files

## Backward Compatibility

✓ **Không breaking changes** - Tất cả code cũ vẫn hoạt động:

```python
# Code cũ vẫn chạy (check_version=True by default)
drive_service.download_file(file_id, path)

# Muốn tắt version checking
drive_service.download_file(file_id, path, check_version=False)
```

## Performance Impact

- **Minimal overhead**: Chỉ thêm 1 API call để get file metadata
- **Significant savings**: Skip download cho files đã cập nhật
- **Network**: Giảm bandwidth usage đáng kể

### Benchmark (ước tính)

| Scenario                  | Trước          | Sau                  |
| ------------------------- | -------------- | -------------------- |
| 10 prompts không đổi      | ~2MB download  | ~10KB metadata check |
| 50 lesson files không đổi | ~50MB download | ~50KB metadata check |
| Time saved                | -              | ~80-90%              |

## Edge Cases đã xử lý

1. ✓ File local bị xóa → Tải lại tự động
2. ✓ Metadata bị mất → Tải lại và tạo metadata mới
3. ✓ File Drive bị xóa → Giữ nguyên file local, báo lỗi
4. ✓ Lỗi khi check version → Tải lại file để đảm bảo an toàn
5. ✓ Timezone issues → Sử dụng ISO format với timezone

## Known Limitations

1. **Không support conflict resolution**: Nếu file local bị edit, sẽ bị ghi đè
   - Workaround: Sử dụng version control cho files quan trọng

2. **Metadata không được backup**: Nếu xóa folder `.drive_metadata`, cần download lại
   - Workaround: Thêm `.drive_metadata` vào git (nếu cần)

3. **Không check file content**: Chỉ dựa vào modified time
   - Acceptable: Drive API đảm bảo modified time chính xác

## Future Enhancements

### Phase 2

- [ ] Batch version checking (check nhiều files một lúc)
- [ ] Parallel downloads cho files cần update
- [ ] Cache statistics và reporting

### Phase 3

- [ ] Web UI để xem sync status
- [ ] Manual trigger sync cho specific files
- [ ] Conflict resolution UI

### Phase 4

- [ ] Smart sync scheduling (cron jobs)
- [ ] Incremental backup của metadata
- [ ] Delta sync (chỉ tải phần thay đổi)

## Migration Guide

Không cần migration - Tính năng tự động hoạt động cho:

- ✓ Tất cả downloads trong ContentAcquisitionService
- ✓ Download prompts
- ✓ Download lesson content
- ✓ Manual downloads qua GoogleDriveService

**Chỉ cần**: Chạy workflow như bình thường, hệ thống sẽ tự động:

1. Lần đầu: Download và lưu metadata
2. Lần sau: Check version và chỉ tải khi cần

## Support

### Documentation

- [DRIVE_VERSION_CHECKING.md](docs/DRIVE_VERSION_CHECKING.md) - Tài liệu chi tiết
- [GOOGLE_DRIVE_INTEGRATION.md](docs/GOOGLE_DRIVE_INTEGRATION.md) - Google Drive API

### Testing

- [test_drive_version.py](test_drive_version.py) - Test suite

### Issues

Nếu gặp vấn đề:

1. Check logs để xem status messages
2. Kiểm tra metadata files tại `data/.drive_metadata/`
3. Chạy test suite để verify
4. Force download với `check_version=False` nếu cần

---

**Version**: 1.0.0  
**Date**: 2026-01-22  
**Author**: GitHub Copilot  
**Status**: ✅ Production Ready
