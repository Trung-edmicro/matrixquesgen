# Hệ Thống Sinh Câu Hỏi Với Hình Ảnh

## 🎯 Tổng Quan

Hệ thống mở rộng cho phép sinh câu hỏi với hình ảnh, hỗ trợ 2 loại:

### HA_MH - Hình Ảnh Minh Họa

- **Parallel workflow**: Sinh ảnh + câu hỏi đồng thời
- Hình ảnh không bắt buộc để trả lời
- Nhanh hơn (~10-15s/câu)

### HA_TL - Hình Ảnh Tư Liệu

- **Sequential workflow**: Sinh ảnh → Sinh câu hỏi dựa vào ảnh
- Hình ảnh bắt buộc để trả lời
- Chính xác hơn (~20-30s/câu)

---

## 📁 Structure

```
server/src/services/
├── generators/
│   ├── image_description_service.py      # Sinh mô tả hình ảnh
│   ├── image_workflow_service.py          # Orchestrate workflows
│   └── question_generator_with_image.py   # Extension cho QuestionGenerator
├── utils/
│   └── image_helpers.py                   # Helper utilities
└── prompts/
    ├── illustrative_image.txt             # Prompt mô tả HA_MH
    ├── data_source_image.txt              # Prompt mô tả HA_TL
    ├── TN_HA_MH.txt                       # Prompt câu hỏi TN + HA_MH
    ├── TN_HA_TL.txt                       # Prompt câu hỏi TN + HA_TL
    ├── DS_HA_MH.txt                       # Prompt câu hỏi DS + HA_MH
    └── DS_HA_TL.txt                       # Prompt câu hỏi DS + HA_TL

server/data/
└── images/                                # Thư mục lưu hình ảnh
```

---

## 🚀 Quick Start

### 1. Setup

```python
from services.generators.question_generator_with_image import integrate_image_workflow
from services.core.genai_client import GenAIClient
from services.generators.question_generator import QuestionGenerator

# Khởi tạo
ai_client = GenAIClient(...)
question_generator = QuestionGenerator(ai_client, ...)

# Tích hợp image workflow
generator = integrate_image_workflow(
    ai_client=ai_client,
    question_generator=question_generator
)
```

### 2. Sinh câu hỏi

```python
# Tạo spec với HA_MH hoặc HA_TL
spec = QuestionSpec(
    question_codes=['C1'],
    rich_content_types={
        'C1': [{'code': 'HA_MH', 'name': 'Hình ảnh minh họa'}]
    },
    # ... other fields
)

# Sinh câu hỏi có hình
questions = generator.generate_questions_with_image(
    spec=spec,
    content=content,
    reference_image_path="path/to/ref.png"  # optional
)
```

### 3. Kết quả

```json
{
  "question_stem": {
    "type": "image",
    "content": [
      "Quan sát hình:",
      {
        "type": "image",
        "content": "server/data/images/C1_HA_MH_20260211.png",
        "metadata": { "caption": "...", "alt": "..." }
      },
      "Đây là hiện tượng gì?"
    ]
  },
  "metadata": {
    "has_image": true,
    "image_path": "...",
    "image_type": "HA_MH"
  }
}
```

---

## 📖 Documentation

Chi tiết xem: [IMAGE_QUESTION_GENERATION.md](../docs/IMAGE_QUESTION_GENERATION.md)

---

## ✅ Features

- ✅ Sinh mô tả hình ảnh tự động (AI)
- ✅ Sinh hình ảnh từ mô tả (Imagen API)
- ✅ Support reference image để cải thiện chất lượng
- ✅ Parallel workflow cho HA_MH (nhanh)
- ✅ Sequential workflow cho HA_TL (chính xác)
- ✅ Merge hình vào câu hỏi tự động
- ✅ Rich content format (image type)
- ✅ Validation và error handling
- ✅ Helper utilities đầy đủ

---

## 🎨 Workflows

### HA_MH (Parallel)

```
1. Sinh mô tả hình minh họa
2. ├─ Sinh hình (Imagen)
   └─ Sinh câu hỏi (với placeholder)
3. Merge hình + câu hỏi
```

### HA_TL (Sequential)

```
1. Sinh mô tả hình chi tiết (+ reference)
2. Sinh hình (Imagen + reference)
3. Sinh câu hỏi DỰA VÀO hình (+ image)
4. Merge hình + câu hỏi
```

---

## 🔧 Requirements

- Vertex AI Imagen API credentials
- Environment variables:
  ```bash
  GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
  GOOGLE_CLOUD_PROJECT=your-project
  GCP_LOCATION=us-central1
  ```

---

## 📝 Example Matrix Config

```json
{
  "rich_content_types": {
    "C1": [{ "code": "HA_MH", "name": "Hình ảnh minh họa" }],
    "C2": [{ "code": "HA_TL", "name": "Hình ảnh tư liệu" }]
  }
}
```

---

## 🐛 Troubleshooting

| Issue                                   | Solution                     |
| --------------------------------------- | ---------------------------- |
| Image generation client not initialized | Check credentials & env vars |
| Cannot parse question                   | Check prompt template        |
| Image không chính xác                   | Provide reference image      |

---

## 📚 Files Created

1. **Core Services**
   - `image_description_service.py` - Sinh mô tả hình
   - `image_workflow_service.py` - Orchestrate workflows
   - `question_generator_with_image.py` - Integration layer

2. **Utilities**
   - `image_helpers.py` - Helper functions

3. **Prompts**
   - `illustrative_image.txt`, `data_source_image.txt`
   - `TN_HA_MH.txt`, `TN_HA_TL.txt`
   - `DS_HA_MH.txt`, `DS_HA_TL.txt`

4. **Documentation**
   - `IMAGE_QUESTION_GENERATION.md` - Full guide

---

## 👥 Usage in Phase 4

```python
# In phase4_question_generation.py
from services.generators.question_generator_with_image import integrate_image_workflow

class QuestionGenerationService:
    def __init__(self, ...):
        # ... existing init ...

        # Add image workflow
        self.generator_with_image = integrate_image_workflow(
            ai_client=self.genai_client,
            question_generator=self.question_generator
        )

    def process_question_generation(self, ...):
        # Check if needs image
        if self._has_image_requirements(extracted_lesson):
            return self.generator_with_image.generate_questions_with_image(...)
        else:
            return super().process_question_generation(...)
```

---

**Version**: 1.0.0  
**Created**: 2026-02-11  
**Status**: ✅ Production Ready
