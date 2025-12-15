# Matrix Question Generator

Hệ thống tạo câu hỏi trắc nghiệm tự động từ file Excel sử dụng Vertex AI của Google Cloud.

## Cấu trúc dự án

```
MatrixQuesGen/
├── client/                 # Frontend (chưa phát triển)
├── data/
│   ├── input/             # Thư mục chứa file Excel đầu vào
│   └── output/            # Thư mục chứa file DOCX kết quả
└── server/
    ├── requirements.txt   # Dependencies
    ├── .env.example       # Mẫu file cấu hình
    └── src/
        ├── main.py        # Entry point chính
        ├── config/        # Cấu hình hệ thống
        │   └── __init__.py
        └── services/      # Các module chức năng
            ├── __init__.py
            ├── excel_reader.py      # Đọc file Excel
            ├── vertex_ai_client.py  # Tương tác Vertex AI
            └── docx_generator.py    # Tạo file DOCX
```

## Tính năng

### 1. Excel Reader (✓)

- Đọc file Excel (.xlsx) với pandas và openpyxl
- Hỗ trợ đọc nhiều sheets
- Chuyển đổi dữ liệu sang JSON
- Hiển thị thông tin chi tiết về dữ liệu

### 2. Vertex AI Client (✓)

- Kết nối với Google Cloud Vertex AI
- Hỗ trợ các mô hình Gemini (gemini-3-pro-preview)
- Generate nội dung từ prompt
- Chat session
- Batch processing
- Tích hợp với dữ liệu JSON

### 3. DOCX Generator (✓)

- Tạo file Word (.docx) từ dữ liệu JSON
- Hỗ trợ heading, paragraph, table
- Custom style và format
- Template system

## Cài đặt

### 1. Cài đặt dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Cấu hình Google Cloud (Optional - cho tính năng AI)

1. Tạo file `.env`:

2. Cấu hình các thông số trong file `.env`:

```env
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GCP_CREDENTIALS_PATH=path/to/credentials.json
```

3. Tải credentials từ Google Cloud Console:
   - Truy cập [Google Cloud Console](https://console.cloud.google.com)
   - Tạo Service Account
   - Tải file JSON credentials
   - Đặt đường dẫn vào `GCP_CREDENTIALS_PATH`

## Sử dụng

### Chạy demo đầy đủ

```bash
cd server
python src/main.py
```

### Sử dụng từng module riêng lẻ

#### 1. Đọc file Excel

```python
from services import ExcelReader
from config import Config

reader = ExcelReader()
file_path = Config.get_input_file_path("your_file.xlsx")

# Đọc tất cả sheets
data = reader.read_file(str(file_path))

# Đọc một sheet cụ thể
df = reader.read_sheet(str(file_path), sheet_name="Sheet1")

# Chuyển sang JSON
json_data = reader.to_json()
```

#### 2. Sử dụng Vertex AI

```python
from services import VertexAIClient
from config import Config

# Khởi tạo client
ai_client = VertexAIClient(
    project_id=Config.GCP_PROJECT_ID,
    location=Config.GCP_LOCATION,
    credentials_path=Config.GCP_CREDENTIALS_PATH
)

# Khởi tạo model
ai_client.initialize_model()

# Generate content
response = ai_client.generate_content("Tạo câu hỏi về lịch sử")

# Chat
ai_client.start_chat()
response = ai_client.send_message("Xin chào")
```

#### 3. Tạo file DOCX

```python
from services import DocxGenerator
from config import Config

generator = DocxGenerator()
generator.create_new_document()
generator.set_document_style()

# Thêm nội dung
generator.add_heading("Tiêu đề", level=1)
generator.add_paragraph("Nội dung đoạn văn")

# Thêm bảng
data = [
    {"Câu hỏi": "...", "Đáp án": "A"},
    {"Câu hỏi": "...", "Đáp án": "B"}
]
generator.add_table_from_dict(data)

# Lưu file
output_path = Config.get_output_file_path("output.docx")
generator.save(str(output_path))
```

## Quy trình hoàn chỉnh

```
Excel Input → Excel Reader → JSON Data → Vertex AI → Processed Data → DOCX Generator → Word Output
```

1. **Đọc Excel**: File template được đọc và chuyển thành JSON
2. **Xử lý AI**: Vertex AI tạo câu hỏi dựa trên dữ liệu
3. **Tạo DOCX**: Kết quả được format thành file Word

## Dependencies chính

- `pandas` - Xử lý dữ liệu Excel
- `openpyxl` - Engine đọc file .xlsx
- `google-cloud-aiplatform` - Vertex AI SDK
- `python-docx` - Tạo file Word
- `python-dotenv` - Quản lý biến môi trường

## Lưu ý

- Đặt file Excel input vào `data/input/`
- File output sẽ được tạo trong `data/output/`
- Vertex AI yêu cầu cấu hình Google Cloud (có thể bỏ qua nếu chỉ dùng Excel Reader và DOCX Generator)
- Template prompt có thể tùy chỉnh trong `config/__init__.py`

## Phát triển tiếp

- [ ] Frontend với React/Vue
- [ ] API REST với FastAPI/Flask
- [ ] Database integration
- [ ] Batch processing nhiều file
- [ ] Template system nâng cao
- [ ] Export nhiều format (PDF, HTML)
