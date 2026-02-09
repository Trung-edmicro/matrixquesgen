# API Endpoints Documentation - New Features

Tài liệu này mô tả các API endpoints mới được thêm vào hệ thống MatrixQuesGen.

## 📋 Tổng quan

Các API mới được thêm vào:

1. **Image Generation API** - Sinh ảnh minh họa bằng AI
2. **Batch Operations API** - Thao tác hàng loạt trên nhiều câu hỏi
3. **Question Validation API** - Kiểm tra và validate câu hỏi
4. **Statistics & Analytics API** - Thống kê và phân tích dữ liệu

---

## 🎨 Image Generation API

**Base Path:** `/api/images`

### 1. Generate Images

**POST** `/api/images/generate`

Sinh ảnh từ text prompt bằng Google Imagen AI.

**Request Body:**

```json
{
  "prompt": "Vẽ hình ảnh minh họa về chu trình nước trong tự nhiên",
  "num_images": 1,
  "aspect_ratio": "16:9",
  "negative_prompt": "low quality, blurry",
  "seed": 42,
  "reference_image_url": null
}
```

**Parameters:**

- `prompt` (required): Mô tả ảnh cần tạo
- `num_images`: Số lượng ảnh (1-4, mặc định 1)
- `aspect_ratio`: Tỷ lệ khung hình (1:1, 16:9, 9:16, 4:3, 3:4)
- `negative_prompt`: Những gì KHÔNG muốn có trong ảnh
- `seed`: Random seed để tái tạo kết quả
- `reference_image_url`: URL ảnh mẫu để AI học theo phong cách

**Response:**

```json
{
  "success": true,
  "image_urls": ["/api/images/file/img_abc123_0.png"],
  "message": "Đã sinh 1 ảnh thành công"
}
```

### 2. Upscale Image

**POST** `/api/images/upscale`

Upscale ảnh lên độ phân giải cao hơn.

**Request Body:**

```json
{
  "image_url": "/api/images/file/img_abc123_0.png",
  "scale_factor": 2
}
```

**Parameters:**

- `image_url` (required): URL hoặc đường dẫn đến ảnh
- `scale_factor`: Hệ số scale (2x hoặc 4x)

### 3. Create Variations

**POST** `/api/images/variations`

Tạo variations từ ảnh gốc.

**Request Body:**

```json
{
  "image_url": "/api/images/file/img_abc123_0.png",
  "prompt": "Thêm màu sắc rực rỡ hơn",
  "num_variations": 3
}
```

### 4. Get Image File

**GET** `/api/images/file/{filename}`

Lấy file ảnh đã sinh.

### 5. Get Model Info

**GET** `/api/images/model-info`

Lấy thông tin về model image generation.

---

## 🔄 Batch Operations API

**Base Path:** `/api/batch`

### 1. Batch Update Questions

**POST** `/api/batch/update`

Update nhiều câu hỏi cùng lúc.

**Request Body:**

```json
{
  "session_id": "session_123",
  "updates": [
    {
      "question_type": "TN",
      "question_code": "C1",
      "data": {
        "question": "Câu hỏi mới",
        "explanation": "Giải thích mới"
      }
    },
    {
      "question_type": "DS",
      "question_code": "C2",
      "data": {
        "difficulty": "VD"
      }
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "errors": [],
  "message": "Đã update 2/2 câu hỏi"
}
```

### 2. Batch Delete Questions

**POST** `/api/batch/delete`

Xóa nhiều câu hỏi cùng lúc.

**Request Body:**

```json
{
  "session_id": "session_123",
  "questions": [
    { "question_type": "TN", "question_code": "C1" },
    { "question_type": "DS", "question_code": "C2" }
  ]
}
```

### 3. Batch Duplicate Questions

**POST** `/api/batch/duplicate`

Duplicate nhiều câu hỏi sang session khác.

**Query Parameters:**

- `session_id` (required): ID của session nguồn
- `target_session_id`: ID của session đích (nếu null thì duplicate trong cùng session)

**Request Body:**

```json
{
  "session_id": "session_123",
  "questions": [
    { "question_type": "TN", "question_code": "C1" },
    { "question_type": "DS", "question_code": "C2" }
  ],
  "target_session_id": "session_456"
}
```

---

## ✅ Question Validation API

**Base Path:** `/api/validate`

### 1. Validate Single Question

**POST** `/api/validate/question`

Validate một câu hỏi.

**Request Body:**

```json
{
  "question_type": "TN",
  "question_data": {
    "question": "Thủ đô của Việt Nam là gì?",
    "options": {
      "A": "Hà Nội",
      "B": "TP.HCM",
      "C": "Đà Nẵng",
      "D": "Huế"
    },
    "correct_answer": "A",
    "explanation": "Hà Nội là thủ đô của Việt Nam từ năm 1010"
  }
}
```

**Response:**

```json
{
  "valid": true,
  "question_code": null,
  "question_type": "TN",
  "issues": [
    {
      "severity": "info",
      "field": "explanation",
      "message": "Lời giải thích đầy đủ và chi tiết"
    }
  ],
  "score": 95.0
}
```

**Validation Rules:**

- **Structure Rules**: Required fields, minimum options, valid correct answer
- **Content Rules**: Question length, explanation required, content quality
- **Quality Rules**: Rich content bonus, metadata bonus

### 2. Validate Session

**POST** `/api/validate/session`

Validate toàn bộ câu hỏi trong session.

**Request Body:**

```json
{
  "session_id": "session_123",
  "strict": false
}
```

**Response:**

```json
{
  "session_id": "session_123",
  "valid": true,
  "total_questions": 50,
  "valid_questions": 48,
  "invalid_questions": 2,
  "average_score": 87.5,
  "questions_results": [...],
  "summary": {
    "errors": 2,
    "warnings": 5,
    "by_type": {
      "TN": {
        "total": 25,
        "valid": 24,
        "invalid": 1,
        "average_score": 88.2
      },
      "DS": {
        "total": 25,
        "valid": 24,
        "invalid": 1,
        "average_score": 86.8
      }
    }
  }
}
```

### 3. Get Validation Rules

**GET** `/api/validate/rules`

Lấy danh sách các rules validation.

---

## 📊 Statistics & Analytics API

**Base Path:** `/api/statistics`

### 1. Overview Statistics

**GET** `/api/statistics/overview`

Lấy thống kê tổng quan.

**Response:**

```json
{
  "total_sessions": 150,
  "total_questions": 7500,
  "questions_by_type": {
    "TN": 3500,
    "DS": 2000,
    "TLN": 1500,
    "TL": 500
  },
  "sessions_by_status": {
    "completed": 140,
    "processing": 5,
    "failed": 5
  },
  "average_questions_per_session": 50.0
}
```

### 2. Session Statistics

**GET** `/api/statistics/session/{session_id}`

Lấy thống kê chi tiết cho một session.

**Response:**

```json
{
  "session_id": "session_123",
  "total_questions": 50,
  "questions_by_type": {
    "TN": 25,
    "DS": 25
  },
  "questions_by_difficulty": {
    "NB": 15,
    "TH": 20,
    "VD": 10,
    "VDC": 5
  },
  "questions_with_rich_content": 12,
  "average_question_length": 250.5,
  "metadata": {...}
}
```

### 3. Trend Statistics

**GET** `/api/statistics/trends`

Lấy thống kê xu hướng theo thời gian.

**Query Parameters:**

- `period`: Chu kỳ (daily, weekly, monthly)
- `days`: Số ngày (1-365)

**Response:**

```json
{
  "period": "daily",
  "data": [
    {
      "date": "2026-02-09",
      "sessions": 5,
      "questions": 250
    },
    {
      "date": "2026-02-08",
      "sessions": 3,
      "questions": 150
    }
  ],
  "total_sessions": 8,
  "total_questions": 400
}
```

### 4. Subject Statistics

**GET** `/api/statistics/subjects`

Lấy thống kê theo môn học.

**Response:**

```json
[
  {
    "subject": "VATLY",
    "sessions": 50,
    "questions": 2500,
    "questions_by_type": {
      "TN": 1200,
      "DS": 800,
      "TLN": 400,
      "TL": 100
    },
    "average_score": null
  },
  ...
]
```

### 5. Recent Activity

**GET** `/api/statistics/recent-activity`

Lấy hoạt động gần đây.

**Query Parameters:**

- `limit`: Số lượng hoạt động tối đa (1-100)

### 6. Performance Metrics

**GET** `/api/statistics/performance`

Lấy metrics về hiệu suất hệ thống.

**Response:**

```json
{
  "total_sessions": 150,
  "completed_sessions": 140,
  "failed_sessions": 5,
  "success_rate": 93.33,
  "average_processing_time": 45.2
}
```

---

## 🔗 Integration với Frontend

### Sử dụng Image Generation trong câu hỏi

```javascript
// Generate image cho câu hỏi
const response = await fetch("/api/images/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    prompt: "Vẽ sơ đồ cấu tạo tế bào thực vật",
    aspect_ratio: "16:9",
    num_images: 1,
  }),
});

const result = await response.json();
const imageUrl = result.image_urls[0];

// Thêm image vào câu hỏi
await fetch(`/api/questions/${sessionId}/questions/TN/C1`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    rich_content: {
      type: "image",
      content: imageUrl,
      metadata: { caption: "Sơ đồ cấu tạo tế bào thực vật" },
    },
  }),
});
```

### Batch Update nhiều câu hỏi

```javascript
const updates = questions.map((q) => ({
  question_type: q.type,
  question_code: q.code,
  data: { difficulty: "VD" },
}));

await fetch("/api/batch/update", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    session_id: sessionId,
    updates,
  }),
});
```

### Validate trước khi export

```javascript
// Validate session trước khi export
const validateResult = await fetch(`/api/validate/session`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    session_id: sessionId,
    strict: true,
  }),
}).then((r) => r.json());

if (validateResult.valid) {
  // Proceed with export
  await fetch(`/api/export/${sessionId}`, { method: "POST" });
} else {
  // Show validation errors
  console.log(`Found ${validateResult.invalid_questions} invalid questions`);
}
```

### Hiển thị statistics dashboard

```javascript
// Get overview statistics
const overview = await fetch("/api/statistics/overview").then((r) => r.json());

// Get trends for last 30 days
const trends = await fetch("/api/statistics/trends?period=daily&days=30").then(
  (r) => r.json(),
);

// Get subject statistics
const subjects = await fetch("/api/statistics/subjects").then((r) => r.json());
```

---

## 🔒 Note về Security và Performance

### Rate Limiting

- Image generation: Giới hạn 10 requests/phút
- Batch operations: Giới hạn 100 câu hỏi/request
- Statistics: Cache 5 phút cho overview stats

### Error Handling

Tất cả API đều trả về error theo format:

```json
{
  "detail": "Error message here"
}
```

Status codes:

- 200: Success
- 400: Bad request (validation error)
- 404: Not found
- 500: Internal server error

### Best Practices

1. **Image Generation**: Sử dụng seed để tái tạo kết quả
2. **Batch Operations**: Chia nhỏ request nếu > 50 items
3. **Validation**: Chạy validation trước khi save/export
4. **Statistics**: Cache kết quả để tránh load data nhiều lần

---

## 📝 Changelog

### Version 1.1.0 (Feb 2026)

- ✅ Added Image Generation API
- ✅ Added Batch Operations API
- ✅ Added Question Validation API
- ✅ Added Statistics & Analytics API
- ✅ Updated main-api.py to include new routers
- ✅ Added API documentation

### Version 1.0.0

- Initial release với core APIs (generate, questions, export, regenerate)
