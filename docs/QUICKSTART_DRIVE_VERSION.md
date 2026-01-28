# 🚀 Quick Start - Drive Version Checking

## Tính năng mới

✅ **Tự động kiểm tra và cập nhật file từ Google Drive**

- Chỉ tải file khi có phiên bản mới trên Drive
- Sử dụng file local nếu đã là bản mới nhất
- Tiết kiệm bandwidth và thời gian

## Cách hoạt động

```
1. Download file lần đầu
   → Lưu metadata (thời gian chỉnh sửa)

2. Download lần sau
   → So sánh thời gian Drive vs Local
   → Nếu Drive mới hơn: Tải lại
   → Nếu đã cập nhật: Skip
```

## Sử dụng

### Tự động (đã tích hợp)

```python
# Mặc định đã bật version checking
drive_service.download_file(file_id, output_path)
```

### Log output

```
✓ File 'example.txt' đã là phiên bản mới nhất (local)
⟳ Phát hiện phiên bản mới của 'data.json' trên Drive, đang tải xuống...
```

### Check version không download

```python
info = drive_service.check_file_version(file_id, local_path)
if info['needs_update']:
    print("Cần cập nhật!")
```

## Chạy Demo

```bash
# Test suite
python test_drive_version.py

# Demo interactive
python demo_drive_version.py
```

### Cấu hình demo (optional)

Thêm vào `.env`:

```env
TEST_FILE_ID=your_file_id
TEST_FOLDER_ID=your_folder_id
```

## Metadata Storage

Files metadata được lưu tại:

```
data/.drive_metadata/<file_id>.json
```

Ví dụ:

```json
{
  "file_id": "1abc...xyz",
  "drive_modified_time": "2026-01-20T10:30:00.000Z",
  "local_path": "data/content/file.json",
  "last_downloaded": "2026-01-20T14:20:00.123456"
}
```

## Files mới

| File                                | Mô tả             |
| ----------------------------------- | ----------------- |
| `test_drive_version.py`             | Test suite đầy đủ |
| `demo_drive_version.py`             | Demo interactive  |
| `docs/DRIVE_VERSION_CHECKING.md`    | Tài liệu chi tiết |
| `FEATURE_DRIVE_VERSION_CHECKING.md` | Summary thay đổi  |
| `.env.example`                      | Template cấu hình |

## Files đã sửa

| File                            | Thay đổi                    |
| ------------------------------- | --------------------------- |
| `google_drive_service.py`       | Thêm version checking logic |
| `phase2_content_acquisition.py` | Tích hợp version check      |
| `README.md`                     | Update features             |

## Lợi ích

✅ **Tiết kiệm bandwidth** - Không tải lại file không cần  
✅ **Tăng tốc độ** - Skip downloads cho files đã cập nhật  
✅ **Tự động sync** - Luôn có bản mới nhất từ Drive  
✅ **Logging rõ ràng** - Biết được file nào được tải/skip

## Backward Compatible

✅ Tất cả code cũ vẫn hoạt động  
✅ Không breaking changes  
✅ Version checking mặc định bật

## Xem thêm

📖 **Chi tiết**: [DRIVE_VERSION_CHECKING.md](docs/DRIVE_VERSION_CHECKING.md)  
📋 **Summary**: [FEATURE_DRIVE_VERSION_CHECKING.md](FEATURE_DRIVE_VERSION_CHECKING.md)  
🔧 **Config**: [.env.example](.env.example)

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Date**: 2026-01-22
