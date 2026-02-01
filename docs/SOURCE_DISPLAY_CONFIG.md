# Cấu hình hiển thị nguồn tư liệu (Source) theo môn học

## Tổng quan

Hệ thống hỗ trợ cấu hình hiển thị hoặc ẩn nguồn tư liệu (source_text) trong câu hỏi Đúng/Sai (DS) theo từng môn học.

## Cấu hình

### Server (Backend)

**File:** `server/src/config/__init__.py`

```python
# Danh sách các môn học HIỂN THỊ source trong câu hỏi DS
SUBJECTS_WITH_SOURCE_DISPLAY = [
    "LICHSU",  # Lịch sử cần hiển thị nguồn tư liệu
    # Thêm các môn khác cần hiển thị source vào đây
]
```

**Cách thêm môn mới cần hiển thị source:**

Thêm mã môn học (viết HOA) vào danh sách `SUBJECTS_WITH_SOURCE_DISPLAY`.

Ví dụ:

```python
SUBJECTS_WITH_SOURCE_DISPLAY = [
    "LICHSU",
    "DIA",     # Thêm môn Địa lý
    "GDCD",    # Thêm môn GDCD
]
```

### Cách hoạt động

1. **API Response** (`/api/questions/{session_id}`)
   - Kiểm tra môn học trong metadata
   - Nếu môn KHÔNG nằm trong danh sách `SUBJECTS_WITH_SOURCE_DISPLAY`:
     - Tự động loại bỏ các field: `source_text`, `source_citation`, `source_origin`, `source_type`

2. **Export DOCX** (`/api/export/{session_id}`)
   - Kiểm tra môn học trong metadata
   - Nếu môn KHÔNG hiển thị source:
     - Bỏ qua phần "Cho đoạn tư liệu sau"
     - Không xuất source_text và source_citation vào file DOCX

3. **Client (Frontend)**
   - Kiểm tra môn học từ metadata
   - Nếu môn KHÔNG hiển thị source:
     - Ẩn phần tư liệu trên UI
     - Ẩn source citation và origin badge

## Ví dụ

### LICHSU (Lịch sử) - Hiển thị source

```json
{
  "question_code": "C1",
  "question_type": "DS",
  "source_text": "Ngày 2-9-1945, tại Quảng trường Ba Đình...",
  "source_citation": "SGK Lịch sử 12, trang 45",
  "statements": {
    "a": { "text": "...", "correct_answer": true }
  }
}
```

➡️ Hiển thị đầy đủ source_text và source_citation

### GDKTPL - Không hiển thị source

```json
{
  "question_code": "C1",
  "question_type": "DS",
  "source_text": "...", // Bị loại bỏ khi trả về API
  "statements": {
    "a": { "text": "...", "correct_answer": true }
  }
}
```

➡️ Không hiển thị source_text, chỉ hiển thị statements

## Test

Chạy script test:

```bash
cd server
python test_source_config.py
```

Kết quả mẫu:

```
Kiểm tra cấu hình hiển thị source theo môn học:
============================================================
LICHSU          -> ✅ Hiển thị source
GDKTPL          -> ❌ Không hiển thị source
HOA             -> ❌ Không hiển thị source
LY              -> ❌ Không hiển thị source
```

## Lưu ý

- Mã môn học phải viết HOA (uppercase)
- Mặc định tất cả môn KHÔNG hiển thị source (trừ môn trong danh sách)
- Cấu hình áp dụng cho cả API, Export DOCX và UI
- Không cần restart server sau khi thay đổi cấu hình (chỉ cần reload module)
