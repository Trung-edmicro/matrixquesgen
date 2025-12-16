# Chức năng đọc file DOCX

## Tổng quan

Module đọc và trích xuất nội dung từ file DOCX, hỗ trợ:

- Đọc text, paragraphs, bảng
- Phân tích cấu trúc document
- Tìm kiếm text
- API endpoints để xử lý file upload và file local

## Cấu trúc

```
server/src/
├── services/
│   └── docx_reader.py          # Service đọc DOCX
├── api/routes/
│   └── docx_reader.py          # API endpoints
├── test_docx_reader.py         # Test đọc file trực tiếp
└── test_docx_api.py            # Test API endpoints
```

## Service: DocxReader

### Sử dụng cơ bản

```python
from services.docx_reader import DocxReader

# Tạo reader
reader = DocxReader(verbose=True)

# Tải file
reader.load_document("path/to/file.docx")

# Lấy toàn bộ nội dung
data = reader.extract_all()
```

### Các phương thức chính

#### 1. load_document(file_path)

Tải file DOCX vào memory.

```python
reader.load_document("demau.docx")
```

#### 2. get_text()

Lấy toàn bộ text.

```python
text = reader.get_text()
print(f"Độ dài: {len(text)} ký tự")
```

#### 3. get_paragraphs()

Lấy danh sách các đoạn văn với format chi tiết.

```python
paragraphs = reader.get_paragraphs()
for para in paragraphs:
    print(f"{para['index']}: {para['text']}")
    print(f"Style: {para['style']}")
    # Truy cập runs (text với format riêng)
    for run in para['runs']:
        print(f"  {run['text']} - Bold: {run['bold']}")
```

#### 4. get_tables()

Lấy tất cả bảng trong document.

```python
tables = reader.get_tables()
for table in tables:
    print(f"Bảng {table['index']}: {table['rows']}x{table['cols']}")
    # Truy cập dữ liệu cell
    for row in table['data']:
        for cell in row:
            print(f"[{cell['row']},{cell['col']}]: {cell['text']}")
```

#### 5. get_structure()

Phân tích cấu trúc document.

```python
structure = reader.get_structure()
print(f"Đoạn văn: {structure['total_paragraphs']}")
print(f"Bảng: {structure['total_tables']}")
print(f"Tiêu đề: {len(structure['headings'])}")
```

#### 6. search_text(keyword, case_sensitive)

Tìm kiếm text trong document.

```python
results = reader.search_text("câu hỏi", case_sensitive=False)
for result in results:
    print(f"Tìm thấy tại đoạn {result['index']}: {result['text']}")
```

#### 7. extract_all()

Trích xuất toàn bộ nội dung.

```python
all_data = reader.extract_all()
# Chứa: structure, text, paragraphs, tables
```

### Hàm tiện ích

```python
from services.docx_reader import read_docx, read_docx_text

# Đọc toàn bộ
data = read_docx("file.docx", verbose=True)

# Chỉ lấy text
text = read_docx_text("file.docx")
```

## API Endpoints

### Base URL

```
http://localhost:8000/docx
```

### 1. POST /docx/read

Upload và đọc toàn bộ file DOCX.

**Request:**

```bash
curl -X POST http://localhost:8000/docx/read \
  -F "file=@demau.docx"
```

**Response:**

```json
{
  "success": true,
  "filename": "demau.docx",
  "data": {
    "structure": {...},
    "text": "...",
    "paragraphs": [...],
    "tables": [...]
  }
}
```

### 2. POST /docx/read/text

Upload và chỉ lấy text.

**Request:**

```bash
curl -X POST http://localhost:8000/docx/read/text \
  -F "file=@demau.docx"
```

**Response:**

```json
{
  "success": true,
  "filename": "demau.docx",
  "text": "...",
  "length": 14512
}
```

### 3. POST /docx/read/structure

Lấy cấu trúc document.

**Request:**

```bash
curl -X POST http://localhost:8000/docx/read/structure \
  -F "file=@demau.docx"
```

**Response:**

```json
{
  "success": true,
  "filename": "demau.docx",
  "structure": {
    "file_name": "demau.docx",
    "total_paragraphs": 153,
    "total_tables": 1,
    "headings": [],
    "sections": 1
  }
}
```

### 4. POST /docx/read/tables

Lấy các bảng từ document.

**Request:**

```bash
curl -X POST http://localhost:8000/docx/read/tables \
  -F "file=@demau.docx"
```

**Response:**

```json
{
  "success": true,
  "filename": "demau.docx",
  "total_tables": 1,
  "tables": [
    {
      "index": 0,
      "rows": 7,
      "cols": 2,
      "data": [[...]]
    }
  ]
}
```

### 5. POST /docx/search

Tìm kiếm text trong document.

**Request:**

```bash
curl -X POST "http://localhost:8000/docx/search?keyword=câu&case_sensitive=false" \
  -F "file=@demau.docx"
```

**Response:**

```json
{
  "success": true,
  "filename": "demau.docx",
  "keyword": "câu",
  "case_sensitive": false,
  "total_found": 30,
  "results": [
    {
      "index": 0,
      "text": "...",
      "style": "Normal"
    }
  ]
}
```

### 6. GET /docx/read-local

Đọc file từ đường dẫn local trên server.

**Request:**

```bash
curl -X GET "http://localhost:8000/docx/read-local?file_path=E:/App/matrixquesgen/data/input/demau.docx"
```

**Response:**

```json
{
  "success": true,
  "file_path": "E:/App/matrixquesgen/data/input/demau.docx",
  "data": {...}
}
```

## Test

### Test Service (đọc file trực tiếp)

```bash
cd E:\App\matrixquesgen\server\src
python test_docx_reader.py
```

Kết quả sẽ hiển thị:

- Cấu trúc document
- Text preview
- Danh sách paragraphs
- Bảng
- Kết quả tìm kiếm

### Test API Endpoints

1. **Chạy server:**

```bash
cd E:\App\matrixquesgen\server\src\api
python main-api.py
```

2. **Chạy test (terminal khác):**

```bash
cd E:\App\matrixquesgen\server\src
python test_docx_api.py
```

Test sẽ kiểm tra:

- ✓ Đọc file local
- ✓ Upload và đọc file
- ✓ Đọc chỉ text
- ✓ Đọc cấu trúc
- ✓ Đọc bảng
- ✓ Tìm kiếm
- ✓ API docs

### Test thủ công với Swagger UI

Truy cập: http://localhost:8000/docs

Tại đây bạn có thể:

- Xem chi tiết tất cả endpoints
- Test upload file trực tiếp
- Xem request/response schema

## Ví dụ sử dụng

### Python Script

```python
from services.docx_reader import DocxReader

# Đọc file demau.docx
reader = DocxReader(verbose=True)
reader.load_document(r"E:\App\matrixquesgen\data\input\demau.docx")

# Lấy cấu trúc
structure = reader.get_structure()
print(f"File có {structure['total_paragraphs']} đoạn văn")
print(f"File có {structure['total_tables']} bảng")

# Tìm câu hỏi
questions = reader.search_text("Câu", case_sensitive=False)
print(f"Tìm thấy {len(questions)} câu hỏi")

# Lấy bảng đầu tiên
tables = reader.get_tables()
if tables:
    first_table = tables[0]
    print(f"Bảng có {first_table['rows']} hàng, {first_table['cols']} cột")
```

### JavaScript/Fetch API

```javascript
// Upload và đọc file
async function readDocx(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/docx/read", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  console.log("Document structure:", data.data.structure);
  console.log("Total paragraphs:", data.data.paragraphs.length);
  console.log("Total tables:", data.data.tables.length);
}

// Đọc file local
async function readLocalDocx() {
  const filePath = "E:/App/matrixquesgen/data/input/demau.docx";
  const response = await fetch(
    `http://localhost:8000/docx/read-local?file_path=${encodeURIComponent(
      filePath
    )}`
  );

  const data = await response.json();
  return data.data;
}

// Tìm kiếm
async function searchDocx(file, keyword) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `http://localhost:8000/docx/search?keyword=${encodeURIComponent(keyword)}`,
    { method: "POST", body: formData }
  );

  const data = await response.json();
  console.log(`Found ${data.total_found} results for "${keyword}"`);
  return data.results;
}
```

## Cấu trúc dữ liệu trả về

### Structure Object

```json
{
  "file_name": "demau.docx",
  "total_paragraphs": 153,
  "total_tables": 1,
  "headings": [
    {
      "index": 5,
      "level": "Heading 1",
      "text": "Tiêu đề chính"
    }
  ],
  "sections": 1
}
```

### Paragraph Object

```json
{
  "index": 0,
  "text": "Nội dung đoạn văn",
  "style": "Normal",
  "alignment": "LEFT",
  "runs": [
    {
      "text": "Nội dung",
      "bold": false,
      "italic": false,
      "underline": false,
      "font_name": "Times New Roman",
      "font_size": 12
    }
  ]
}
```

### Table Object

```json
{
  "index": 0,
  "rows": 7,
  "cols": 2,
  "data": [
    [
      {
        "row": 0,
        "col": 0,
        "text": "Thời gian"
      },
      {
        "row": 0,
        "col": 1,
        "text": "Nội dung"
      }
    ]
  ]
}
```

## Dependencies

Module sử dụng thư viện `python-docx` đã có trong `server-requirements.txt`:

```
python-docx==1.1.0
```

## Lưu ý

1. **File format**: Chỉ hỗ trợ file `.docx` (Office Open XML), không hỗ trợ `.doc` (binary format cũ)

2. **Encoding**: Tự động xử lý encoding UTF-8

3. **Memory**: File lớn sẽ tốn nhiều memory khi load toàn bộ vào RAM

4. **Performance**:

   - Đọc file nhỏ (<5MB): rất nhanh
   - Đọc file vừa (5-20MB): nhanh
   - Đọc file lớn (>20MB): có thể chậm

5. **Error handling**: Tất cả hàm đều raise exception nếu có lỗi

## Tích hợp với MatrixQuesGen

Có thể sử dụng để:

- Đọc đề thi từ file DOCX
- Trích xuất câu hỏi từ document
- Parse ma trận từ bảng trong DOCX
- Import nội dung cho question generator

## API Documentation

Xem full API docs tại: http://localhost:8000/docs (khi server đang chạy)
