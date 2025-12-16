# Hướng dẫn sử dụng Template từ File DOCX

## Tổng quan

Tính năng mới cho phép sử dụng **file DOCX đề mẫu** để AI tham khảo khi sinh câu hỏi mới. Câu hỏi từ đề mẫu sẽ được:

1. **Parse tự động** từ file DOCX
2. **Mapping** với các hàng trong ma trận
3. **Gán vào prompt** như template để AI học theo

## Workflow

```
File DOCX đề mẫu → Parse câu hỏi → Mapping với ma trận → Sinh câu hỏi mới
       ↓                 ↓                   ↓                    ↓
   demau.docx      24 câu hỏi        Gán template         AI tham khảo
                   NB/TH/VD          vào prompt           cấu trúc mẫu
```

## Cấu trúc file DOCX đề mẫu

### Format câu hỏi TN (Trắc nghiệm)

```
Câu 1 (NB). Nội dung câu hỏi ở đây?
A. Phương án A
B. Phương án B
C. Phương án C
D. Phương án D

Câu 2 (TH). Nội dung câu hỏi khác?
A. Phương án A
B. Phương án B
...
```

### Format câu hỏi DS (Đúng/Sai)

**Dạng 1: Tư liệu text**

```
Câu 1. Cho đoạn tư liệu sau:
Nội dung tư liệu ở đây...
Có thể nhiều đoạn văn.

(NB) a. Mệnh đề thứ nhất
(NB) b. Mệnh đề thứ hai
(TH) c. Mệnh đề thứ ba
(VD) d. Mệnh đề thứ tư
```

**Dạng 2: Tư liệu bảng**

```
Câu 4. Cho bảng thông tin sau:

[Bảng DOCX]
| Thời gian  | Nội dung                    |
|------------|----------------------------|
| 8/8/1967   | ASEAN được thành lập       |
| Năm 1971   | Tuyên bố về khu vực...     |

(NB) a. Sự kiện Việt Nam gia nhập ASEAN (1995)...
(NB) b. Quá trình phát triển từ ASEAN 5...
(TH) c. Hiến chương ASEAN được thông qua...
(VD) d. ASEAN được đánh giá là...
```

### Các pattern hợp lệ:

**Câu TN:**
✅ `Câu 1 (NB). Text`  
✅ `Câu 2 (TH): Text`  
✅ `Câu 3. Text` (không có level)  
✅ Phương án: `A.`, `B.`, `C.`, `D.`

**Câu DS:**
✅ `Câu 1. Cho đoạn tư liệu sau:`  
✅ `Câu 2. Cho bảng thông tin sau:`  
✅ Mệnh đề với level: `(NB) a.`, `(TH) b.`  
✅ Mệnh đề không level: `a.`, `b.`, `c.`, `d.`

❌ Không nhận diện: Câu không có số thứ tự, format khác

## Sử dụng trong Code

### 1. Parse câu hỏi từ DOCX (TN và DS)

```python
from services.question_parser import QuestionParser

# Tạo parser
parser = QuestionParser(verbose=True)

# Load file
parser.load_docx("path/to/demau.docx")

# Parse câu TN (Trắc nghiệm)
tn_questions = parser.parse_multiple_choice_questions()
print(f"Đã parse {len(tn_questions)} câu TN")

# Parse câu DS (Đúng/Sai)
ds_questions = parser.parse_true_false_questions()
print(f"Đã parse {len(ds_questions)} câu DS")

# Xem thống kê TN
stats = parser.get_statistics()
# {
#   'total_questions': 24,
#   'complete_questions': 24,
#   'by_level': {'NB': 11, 'TH': 9, 'VD': 3, 'Unknown': 1}
# }

# Xem chi tiết câu DS
for q in ds_questions:
    print(f"Câu {q['number']}: {q['has_table']} (bảng: {q.get('has_table', False)})")
    print(f"  Tư liệu: {q['source_text'][:100]}...")
    print(f"  Mệnh đề: {len(q['statements'])} câu")
```

### 2. Mapping với ma trận

```python
from services.question_parser import QuestionMatrixMapper

# Tạo ma trận
matrix_rows = [
    {
        'question_codes': ['C1'],
        'knowledge_content': 'Hội nghị I-an-ta',
        'cognitive_level': 'NB',
        'expected_outcome': 'Nêu được...',
        'num_questions': 1
    },
    # ... more rows
]

# Mapping
mapper = QuestionMatrixMapper(verbose=True)

# Chế độ 1: Theo thứ tự (câu 1 → hàng 1, câu 2 → hàng 2)
mapped_order = mapper.map_by_order(questions, matrix_rows)

# Chế độ 2: Thông minh (ưu tiên cùng level)
mapped_smart = mapper.map_questions_to_matrix(questions, matrix_rows)

# Kết quả: mỗi row sẽ có thêm field 'question_template'
for row in mapped_smart:
    print(row['question_template'])
    # "Câu 1 (NB). Từ ngày 4-2 đến 11-2-1945...
    # A. Thành lập tổ chức Liên hợp quốc.
    # B. Thông qua Hiến chương...
    # ..."
```

### 3. Sinh câu hỏi với template

```python
from services.template_generator import QuestionGeneratorWithTemplate

# Tạo generator với template
gen = QuestionGeneratorWithTemplate(verbose=True)

# Load template DOCX
gen.load_template_docx("demau.docx")

# Mapping với ma trận
mapped_rows = gen.map_template_to_matrix(
    matrix_rows,
    mapping_mode='smart'  # hoặc 'order'
)

# Sinh câu hỏi (cần có QuestionGenerator đã khởi tạo)
from services.question_generator import QuestionGenerator
from services.genai_client import VertexAIClient

ai_client = VertexAIClient(...)
generator = QuestionGenerator(ai_client, "path/to/prompt/TN.txt")

# Sinh với template
questions = gen.generate_with_template(
    generator=generator,
    matrix_rows=matrix_rows,
    mapping_mode='smart'
)
```

### 4. Sử dụng hàm tiện ích

```python
from services.question_parser import parse_questions_from_docx, map_questions_to_matrix

# Parse nhanh
questions = parse_questions_from_docx("demau.docx", verbose=True)

# Mapping nhanh
mapped = map_questions_to_matrix(
    questions=questions,
    matrix_rows=matrix_rows,
    mapping_mode='smart',
    verbose=True
)
```

## Chế độ Mapping

### 1. Mode: `order` (Theo thứ tự)

Mapping tuần tự: Câu 1 → Hàng 1, Câu 2 → Hàng 2, ...

**Ưu điểm:**

- Đơn giản, dễ hiểu
- Phù hợp khi đề mẫu và ma trận có cùng thứ tự

**Nhược điểm:**

- Không quan tâm đến level
- Câu NB có thể map vào hàng VD

### 2. Mode: `smart` (Thông minh)

Mapping ưu tiên cùng level: Tìm câu NB cho hàng NB, câu TH cho hàng TH, ...

**Ưu điểm:**

- Template phù hợp về độ khó
- AI sinh câu đúng cấp độ hơn

**Nhược điểm:**

- Phức tạp hơn một chút

## Ví dụ thực tế

### File: demau.docx

```
Câu 1 (NB). Từ ngày 4-2 đến 11-2-1945, tại Hội nghị I-an-ta...?
A. Thành lập tổ chức Liên hợp quốc.
B. Thông qua Hiến chương Liên hợp quốc.
C. Ra bản Tuyên bố Liên hợp quốc.
D. Thành lập Hội đồng Bảo an Liên hợp quốc.

Câu 2 (NB). Một trong những nguyên tắc hoạt động của Liên hợp quốc là
A. tôn trọng các nghĩa vụ quốc tế và luật pháp quốc tế.
B. đe dọa vũ lực và sử dụng vũ lực trong quan hệ quốc tế.
...
```

### Ma trận

| Câu | Nội dung         | Level |
| --- | ---------------- | ----- |
| C1  | Hội nghị I-an-ta | NB    |
| C2  | Nguyên tắc LHQ   | TH    |
| C3  | Vai trò LHQ      | VD    |

### Kết quả mapping (smart mode)

- **C1 (NB)** ← Câu 1 (NB) từ DOCX ✓ Level khớp
- **C2 (TH)** ← Câu 4 (TH) từ DOCX ✓ Level khớp
- **C3 (VD)** ← Câu 19 (VD) từ DOCX ✓ Level khớp

### Prompt gửi đến AI

```
# GỢI Ý CÂU HỎI MẪU
"Câu 1 (NB). Từ ngày 4-2 đến 11-2-1945, tại Hội nghị I-an-ta...?
A. Thành lập tổ chức Liên hợp quốc.
B. Thông qua Hiến chương Liên hợp quốc.
C. Ra bản Tuyên bố Liên hợp quốc.
D. Thành lập Hội đồng Bảo an Liên hợp quốc."
```

AI sẽ tham khảo cấu trúc này để sinh câu hỏi mới về "Hội nghị I-an-ta".

## Test & Demo

### Chạy test parser

```bash
cd E:\App\matrixquesgen\server\src
python test_question_parser.py
```

Kết quả:

- ✓ Parse 24 câu hỏi
- ✓ Phân loại theo level
- ✓ Test mapping

### Chạy demo workflow

```bash
python demo_template_workflow.py
```

Demo đầy đủ:

1. Load DOCX template
2. Tạo ma trận
3. Mapping (cả 2 mode)
4. Hiển thị kết quả
5. Preview prompt

## API Integration

### Endpoint đã tích hợp

```http
POST /api/generate
Content-Type: multipart/form-data

file: matrix.xlsx (required)
template_docx: demau.docx (optional)
max_workers: 5
min_interval: 0.2
```

**Workflow khi có template_docx:**

1. Parse câu TN và DS từ DOCX
2. Mapping với ma trận:
   - **TN**: C1→Câu 1, C12→Câu 12 (code mapping)
   - **DS**: C1→Câu 1, DS1→Câu 1 (hỗ trợ cả 2 format)
3. Gán template vào prompt ({{QUESTION_TEMPLATE}})
4. AI sinh câu mới theo template

**Nếu không có template_docx:**

- Sinh câu hỏi bình thường (không có template)

**Response:**

```json
{
  "session_id": "uuid-xxx",
  "status": "processing",
  "message": "Đã bắt đầu sinh câu hỏi..."
}
```

**Kiểm tra tiến độ:**

```http
GET /api/generate/{session_id}/progress

Response:
{
  "session_id": "uuid-xxx",
  "status": "completed",
  "progress": 100,
  "total_questions": 28,
  "template_info": {
    "total_tn_parsed": 24,
    "total_ds_parsed": 4,
    "tn_mapped_count": 24,
    "ds_mapped_count": 4,
    "mapping_mode": "code"
  }
}
```

### Tính năng đặc biệt DS

✅ **Hỗ trợ bảng trong tư liệu**:

- Pattern: `"Câu 4. Cho bảng thông tin sau:"`
- Tự động đọc bảng DOCX
- Format thành text: `Thời gian | Nội dung`

✅ **Hỗ trợ level cho mệnh đề**:

- Format: `(NB) a.`, `(TH) b.`, `(VD) c.`
- Giữ nguyên level khi gán vào prompt

## Lưu ý kỹ thuật

### Format DOCX phải đúng

- Câu hỏi phải có format: `Câu X (LEVEL). Text`
- Phương án: `A.`, `B.`, `C.`, `D.`
- Mỗi câu phải đủ 4 phương án

### Xử lý thiếu template

Nếu số câu trong DOCX < số hàng ma trận:

- Các hàng đầu sẽ có template
- Các hàng sau sẽ không có template (sinh bình thường)

### Performance

- Parse DOCX: ~1-2s cho file 24 câu
- Mapping: <100ms
- Tổng overhead: ~2s (chấp nhận được)

## Các file liên quan

```
server/src/
├── services/
│   ├── docx_reader.py          # Đọc DOCX
│   ├── question_parser.py      # Parse câu hỏi từ DOCX
│   ├── template_generator.py   # Tích hợp template vào generation
│   └── question_generator.py   # Sinh câu hỏi (đã update)
├── test_question_parser.py     # Test parser
├── demo_template_workflow.py   # Demo workflow
└── config/prompt/
    └── TN.txt                  # Prompt có biến {{QUESTION_TEMPLATE}}
```

## Tương lai

- [x] Support file DOCX dạng Đúng/Sai (DS) ✅
- [x] Support bảng trong tư liệu DS ✅
- [x] API endpoint để upload DOCX ✅
- [ ] Validation template DOCX trước khi parse
- [ ] Cache parsed questions để tránh parse lại
- [ ] UI để preview mapping result
