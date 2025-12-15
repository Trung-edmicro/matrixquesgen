# MatrixQuesGen API Documentation

API backend cho hệ thống sinh câu hỏi tự động từ ma trận.

## 🚀 Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r api-requirements.txt
```

### 2. Cấu hình biến môi trường

Tạo file `.env`:

```env
# Google Cloud AI
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=global
GCP_CREDENTIALS_PATH=path/to/credentials.json

# Processing config
MAX_WORKERS=5
MIN_INTERVAL=0.2
VERBOSE=false
MAX_RETRIES=3
RETRY_DELAY=2.0
```

### 3. Chạy API server

```bash
cd server/src/api
python main.py
```

Hoặc sử dụng uvicorn:

```bash
uvicorn server.src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API sẽ chạy tại: `http://localhost:8000`

## 📚 API Endpoints

### 1. Sinh câu hỏi

**POST** `/api/generate`

Upload file Excel ma trận và sinh câu hỏi.

**Request:**

- `file`: File Excel (.xlsx)
- `max_workers` (optional): Số threads (default: 5)
- `min_interval` (optional): Delay giữa requests (default: 0.2s)
- `max_retries` (optional): Số lần retry (default: 3)
- `retry_delay` (optional): Delay giữa retries (default: 2.0s)

**Response:**

```json
{
  "session_id": "uuid",
  "status": "processing",
  "message": "Đã bắt đầu sinh câu hỏi..."
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "file=@matrix.xlsx" \
  -F "max_workers=5"
```

---

### 2. Kiểm tra tiến độ

**GET** `/api/generate/{session_id}/progress`

Lấy tiến độ sinh câu hỏi.

**Response:**

```json
{
  "session_id": "uuid",
  "status": "processing",
  "progress": 50,
  "total_questions": 30,
  "error": null
}
```

---

### 3. Lấy danh sách sessions

**GET** `/api/questions`

Lấy danh sách tất cả sessions đã sinh.

**Query Parameters:**

- `limit` (optional): Số lượng tối đa (default: 50)
- `offset` (optional): Vị trí bắt đầu (default: 0)
- `status` (optional): Lọc theo status (processing, completed, failed)

**Response:**

```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "matrix_file": "matrix.xlsx",
      "total_questions": 30,
      "tn_count": 24,
      "ds_count": 6,
      "generated_at": "2025-12-15T10:00:00",
      "status": "completed"
    }
  ],
  "total": 10
}
```

---

### 4. Lấy chi tiết câu hỏi

**GET** `/api/questions/{session_id}`

Lấy toàn bộ câu hỏi của một session để preview/edit.

**Response:**

```json
{
  "metadata": {
    "session_id": "uuid",
    "matrix_file": "matrix.xlsx",
    "total_questions": 30,
    "tn_count": 24,
    "ds_count": 6,
    "generated_at": "2025-12-15T10:00:00",
    "status": "completed"
  },
  "questions": {
    "TN": [...],
    "DS": [...]
  }
}
```

---

### 5. Cập nhật câu hỏi

**PUT** `/api/questions/{session_id}/questions/{question_type}/{question_code}`

Cập nhật nội dung câu hỏi sau khi user sửa trên UI.

**Parameters:**

- `session_id`: ID của session
- `question_type`: TN hoặc DS
- `question_code`: C1, C2, C3...

**Request Body:**

```json
{
  "question_stem": "Câu hỏi đã được sửa...",
  "options": {
    "A": "Đáp án A mới",
    "B": "Đáp án B mới",
    "C": "Đáp án C mới",
    "D": "Đáp án D mới"
  },
  "correct_answer": "B",
  "explanation": "Giải thích mới..."
}
```

**Response:**

```json
{
  "message": "Đã cập nhật câu hỏi thành công",
  "question_code": "C1",
  "question_type": "TN"
}
```

---

### 6. Export DOCX

**POST** `/api/export/{session_id}`

Export câu hỏi ra file DOCX.

**Response:**

```json
{
  "file_path": "data/exports/matrix_20251215_100000.docx",
  "file_name": "matrix_20251215_100000.docx",
  "download_url": "/api/export/{session_id}/download"
}
```

---

### 7. Download file DOCX

**GET** `/api/export/{session_id}/download`

Download file DOCX đã export.

**Response:** File download

---

### 8. Xóa session

**DELETE** `/api/questions/{session_id}`

Xóa một session.

**Response:**

```json
{
  "message": "Đã xóa session thành công",
  "session_id": "uuid"
}
```

---

## 🔧 Workflow sử dụng

### 1. Sinh câu hỏi mới

```javascript
// 1. Upload file và bắt đầu sinh
const formData = new FormData();
formData.append("file", fileInput.files[0]);

const response = await fetch("http://localhost:8000/api/generate", {
  method: "POST",
  body: formData,
});

const { session_id } = await response.json();

// 2. Poll để check tiến độ
const interval = setInterval(async () => {
  const progress = await fetch(
    `http://localhost:8000/api/generate/${session_id}/progress`
  );
  const data = await progress.json();

  if (data.status === "completed") {
    clearInterval(interval);
    // Load câu hỏi để preview
    loadQuestions(session_id);
  }
}, 2000);
```

### 2. Preview và chỉnh sửa

```javascript
// Load câu hỏi
const response = await fetch(
  `http://localhost:8000/api/questions/${session_id}`
);
const { questions } = await response.json();

// Hiển thị trên UI để user chỉnh sửa

// Lưu chỉnh sửa
await fetch(
  `http://localhost:8000/api/questions/${session_id}/questions/TN/C1`,
  {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question_stem: "Câu hỏi đã sửa...",
      correct_answer: "B",
    }),
  }
);
```

### 3. Export file

```javascript
// Export
const exportResponse = await fetch(
  `http://localhost:8000/api/export/${session_id}`,
  {
    method: "POST",
  }
);

const { download_url } = await exportResponse.json();

// Download
window.location.href = `http://localhost:8000${download_url}`;
```

---

## 📖 Interactive Documentation

API tự động generate documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🗂️ Cấu trúc thư mục data

```
data/
├── uploads/          # File xlsx được upload
├── sessions/         # Session data (JSON)
└── exports/          # File DOCX đã export
```

---

## 🔐 Production Deployment

### 1. Sử dụng Gunicorn

```bash
pip install gunicorn

gunicorn server.src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r api-requirements.txt

CMD ["uvicorn", "server.src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. CORS Configuration

Trong production, cập nhật CORS origins trong `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🐛 Troubleshooting

### Lỗi khi upload file

- Kiểm tra file có đúng định dạng .xlsx
- Kiểm tra quyền ghi vào thư mục `data/uploads`

### Session không tìm thấy

- Kiểm tra `data/sessions` có file JSON với session_id
- Session có thể đã bị xóa

### Lỗi khi export DOCX

- Kiểm tra session đã hoàn thành (`status: completed`)
- Kiểm tra quyền ghi vào thư mục `data/exports`

---

## 📝 License

MIT
