# HỖ TRỢ NHIỀU MẪU MA TRẬN

## Tổng quan

Hệ thống đã được cập nhật để hỗ trợ 2 mẫu ma trận khác nhau:

### **Mẫu 1: Ma trận đơn giản**

- Chỉ có 1 sheet duy nhất chứa ma trận
- Cần file docx đề mẫu để tham khảo khi generate câu hỏi
- Phù hợp với workflow hiện tại

### **Mẫu 2: Ma trận + Ngân hàng câu hỏi mẫu**

- Có 2 sheets:
  - Sheet "Ma trận": Cấu trúc giống Mẫu 1
  - Sheet "Câu hỏi mẫu": Chứa ngân hàng câu hỏi mẫu sẵn
- **KHÔNG** cần file docx đề mẫu
- Hệ thống sẽ random chọn câu hỏi mẫu từ ngân hàng

---

## Cấu trúc file Mẫu 2

### Sheet "Ma trận"

Cấu trúc **GIỐNG HOÀN TOÀN** với Mẫu 1:

| Cột   | Nội dung                              |
| ----- | ------------------------------------- |
| 1     | STT                                   |
| 2     | Thành phần năng lực                   |
| 3     | Tên chương - Bài                      |
| 4     | Đặc tả ma trận                        |
| 5-7   | TN (Nhận biết, Thông hiểu, Vận dụng)  |
| 8-10  | DS (Nhận biết, Thông hiểu, Vận dụng)  |
| 11-13 | TLN (Nhận biết, Thông hiểu, Vận dụng) |
| 14-15 | Tài liệu bổ sung (tùy chọn)           |

### Sheet "Câu hỏi mẫu"

| Cột | Nội dung                                           |
| --- | -------------------------------------------------- |
| 0   | STT (số thứ tự câu hỏi mẫu)                        |
| 1   | Bài (tên bài học)                                  |
| 2   | Dạng câu hỏi (Trắc nghiệm, Đúng Sai, Trả lời ngắn) |
| 3   | Cấp độ (Nhận biết, Thông hiểu, Vận dụng)           |
| 4   | Câu hỏi (nội dung đầy đủ bao gồm cả đáp án)        |

**Lưu ý:**

- Đối với câu **Đúng/Sai**: Cột "Cấp độ" có thể để trống (vì 4 mệnh đề có thể có cấp độ khác nhau)
- Mỗi câu hỏi mẫu là một câu hoàn chỉnh với đáp án
- Có thể có nhiều câu hỏi mẫu cho cùng 1 loại (bài, dạng, cấp độ)

---

## Ví dụ Mapping

### Trong sheet "Ma trận" (hàng 2)

```
Bài 6. Cách mạng tháng Tám - 1945
- Cột 5 (TN-NB): 1 (C1)
- Cột 7 (TN-VD): 1 (C2)
```

### Trong sheet "Câu hỏi mẫu"

```
STT 1-8: 8 câu mẫu cho C1 (Bài 6, TN, Nhận biết)
STT 9-14: 6 câu mẫu cho C2 (Bài 6, TN, Vận dụng)
```

### Khi generate

- Cần generate 1 câu C1 → Random chọn 1 trong 8 câu mẫu (STT 1-8)
- Cần generate 1 câu C2 → Random chọn 1 trong 6 câu mẫu (STT 9-14)

---

## API Sử dụng

### 1. Load ma trận

```python
from services.matrix_parser import MatrixParser

parser = MatrixParser()
parser.load_excel(file_path)  # Tự động phát hiện template
```

### 2. Kiểm tra có ngân hàng câu hỏi mẫu không

```python
if parser.has_sample_questions():
    print("Có ngân hàng câu hỏi mẫu")
else:
    print("Không có - cần file docx đề mẫu")
```

### 3. Lấy câu hỏi mẫu

```python
sample = parser.get_sample_question(
    lesson_name="Bài 6. Cách mạng tháng Tám - 1945",
    question_type="TN",  # TN, DS, hoặc TLN
    cognitive_level="NB"  # NB, TH, VD, VDC
)

if sample:
    print(f"Câu hỏi mẫu: {sample.content}")
```

### 4. Parse ma trận như bình thường

```python
# Parse TN
tn_specs = parser.parse_matrix("TN")

# Parse DS
ds_specs = parser.parse_matrix("DS")

# Parse TLN
tln_specs = parser.parse_matrix("TLN")
```

---

## Classes mới

### 1. `SampleQuestionBank`

- **File:** `server/src/services/sample_question_bank.py`
- **Chức năng:** Quản lý ngân hàng câu hỏi mẫu
- **Methods:**
  - `load_from_excel(file_path, sheet_name)`: Load câu hỏi từ sheet
  - `find_samples(lesson, type, level, count)`: Tìm nhiều câu mẫu
  - `get_random_sample(lesson, type, level)`: Lấy 1 câu mẫu ngẫu nhiên
  - `has_samples()`: Kiểm tra có câu hỏi không
  - `print_statistics()`: In thống kê

### 2. `MatrixTemplateDetector`

- **File:** `server/src/services/matrix_template_detector.py`
- **Chức năng:** Phát hiện template ma trận
- **Methods:**
  - `detect(file_path)`: Phát hiện template và trả về metadata
  - `print_detection_result()`: In kết quả phát hiện

### 3. `MatrixParser` (đã update)

- **File:** `server/src/services/matrix_parser.py`
- **Thay đổi:**
  - Tự động phát hiện template khi load file
  - Tự động load ngân hàng câu hỏi mẫu nếu có
  - Thêm methods `has_sample_questions()` và `get_sample_question()`

---

## Workflow sử dụng

### Với Mẫu 1 (Ma trận đơn giản)

1. Upload file Excel ma trận
2. Upload file docx đề mẫu
3. Hệ thống parse ma trận
4. Generate câu hỏi dựa trên đề mẫu trong docx

### Với Mẫu 2 (Ma trận + Câu hỏi mẫu)

1. Upload file Excel ma trận (có sheet "Câu hỏi mẫu")
2. **KHÔNG** cần upload file docx
3. Hệ thống tự động:
   - Parse ma trận từ sheet "Ma trận"
   - Load ngân hàng câu hỏi từ sheet "Câu hỏi mẫu"
4. Generate câu hỏi bằng cách random chọn từ ngân hàng

---

## Lợi ích của Mẫu 2

1. **Không cần file docx đề mẫu**

   - Giảm bước upload
   - Đơn giản hóa workflow

2. **Nhiều câu hỏi mẫu cho mỗi loại**

   - Đa dạng hóa câu hỏi
   - Tránh trùng lặp

3. **Quản lý tập trung**

   - Tất cả trong 1 file Excel
   - Dễ cập nhật, bảo trì

4. **Random tự động**
   - Hệ thống tự động chọn câu mẫu
   - Đảm bảo phân bố đều

---

## Testing

Chạy test với cả 2 mẫu:

```bash
python test_matrix_parser_both_templates.py
```

---

## Tương thích ngược

✅ **Hoàn toàn tương thích** với code hiện tại:

- Mẫu 1 vẫn hoạt động bình thường
- API không thay đổi phá vỡ
- Chỉ thêm features mới

---

## Next Steps

1. **Update UI:** Thêm hướng dẫn về Mẫu 2 trong frontend
2. **Tích hợp:** Kết nối với QuestionGenerator để sử dụng câu mẫu
3. **Documentation:** Cập nhật docs cho user

---

## Files liên quan

- `server/src/services/sample_question_bank.py` - Ngân hàng câu hỏi mẫu
- `server/src/services/matrix_template_detector.py` - Phát hiện template
- `server/src/services/matrix_parser.py` - Parser chính (đã update)
- `test_matrix_parser_both_templates.py` - Script test
- `data/input/Ma trận (Mẫu 2).xlsx` - File mẫu 2 tham khảo
