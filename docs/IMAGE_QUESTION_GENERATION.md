# Hướng Dẫn Sử Dụng Hệ Thống Sinh Câu Hỏi Với Hình Ảnh

## Tổng quan

Hệ thống hỗ trợ sinh câu hỏi với 2 loại hình ảnh:

### 1. **HA_MH** (Hình Ảnh Minh Họa)

- **Vai trò**: Minh họa cho nội dung kiến thức
- **Đặc điểm**: KHÔNG bắt buộc để trả lời câu hỏi
- **Workflow**: PARALLEL (sinh ảnh và câu hỏi song song)

### 2. **HA_TL** (Hình Ảnh Tư Liệu)

- **Vai trò**: Nguồn dữ liệu trực tiếp
- **Đặc điểm**: BẮT BUỘC phải đọc để trả lời
- **Workflow**: SEQUENTIAL (sinh ảnh trước, sau đó sinh câu hỏi dựa vào ảnh)

---

## Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────┐
│         QuestionGeneratorWithImage (Extension)          │
│                                                         │
│  ┌───────────────┐      ┌──────────────────────────┐   │
│  │ Question      │      │ ImageWorkflowService     │   │
│  │ Generator     │◄─────┤                          │   │
│  │ (Existing)    │      │ ┌──────────────────────┐ │   │
│  └───────────────┘      │ │ ImageDescription     │ │   │
│                         │ │ Service              │ │   │
│                         │ └──────────────────────┘ │   │
│                         │ ┌──────────────────────┐ │   │
│                         │ │ ImageGenerator       │ │   │
│                         │ │ (Imagen API)         │ │   │
│                         │ └──────────────────────┘ │   │
│                         └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Các Components

### 1. **ImageDescriptionService**

```python
from services.generators.image_description_service import ImageDescriptionService

service = ImageDescriptionService(
    ai_client=genai_client,
    prompts_dir=Path("server/src/services/prompts")
)

# Sinh mô tả cho HA_MH
desc = service.generate_illustrative_description(
    subject="Sinh học",
    class_level="10",
    chapter="2",
    lesson_name="Quang hợp",
    content="...",
    learning_outcome="...",
    reference_image_path="path/to/reference.png"  # optional
)

# Sinh mô tả cho HA_TL
desc = service.generate_data_source_description(
    # same params...
)
```

**Prompt templates**:

- `server/src/services/prompts/illustrative_image.txt` (HA_MH)
- `server/src/services/prompts/data_source_image.txt` (HA_TL)

---

### 2. **ImageGenerator**

```python
from services.core.image_generation import ImageGenerator

generator = ImageGenerator(
    num_images=1,
    aspect_ratio="16:9"
)

# Sinh hình từ mô tả
images = generator.generate(
    prompt="Mô tả hình ảnh...",
    reference_image_path="path/to/reference.png"  # optional
)
```

**Lưu ý**: Yêu cầu Vertex AI Imagen API credentials.

---

### 3. **ImageWorkflowService**

```python
from services.generators.image_workflow_service import ImageWorkflowService

workflow = ImageWorkflowService(
    ai_client=genai_client,
    image_save_dir=Path("server/data/images"),
    prompts_dir=Path("server/src/services/prompts")
)

# Workflow HA_MH (parallel)
result = workflow.process_ha_mh_workflow(
    question_spec={...},
    content="...",
    reference_image_path="..."  # optional
)

# Workflow HA_TL (sequential)
result = workflow.process_ha_tl_workflow(
    question_spec={...},
    content="...",
    reference_image_path="..."  # recommended
)
```

---

### 4. **QuestionGeneratorWithImage**

```python
from services.generators.question_generator_with_image import (
    QuestionGeneratorWithImage,
    integrate_image_workflow
)

# Cách 1: Sử dụng helper function
generator_with_image = integrate_image_workflow(
    ai_client=genai_client,
    question_generator=existing_question_generator
)

# Cách 2: Khởi tạo trực tiếp
workflow = ImageWorkflowService(ai_client, ...)
generator_with_image = QuestionGeneratorWithImage(
    question_generator=existing_question_generator,
    image_workflow_service=workflow
)

# Sinh câu hỏi có hình ảnh
questions = generator_with_image.generate_questions_with_image(
    spec=question_spec,
    content=content,
    reference_image_path="path/to/ref.png"
)
```

---

## Workflows Chi Tiết

### **HA_MH Workflow** (Parallel)

```
┌─────────────────────────────────────────────────────┐
│ 1. Sinh mô tả hình ảnh minh họa                      │
│    (ImageDescriptionService)                        │
└──────────────┬──────────────────────────────────────┘
               │
               ├─────────────┬────────────────┐
               │             │                │
        ┌──────▼──────┐ ┌───▼──────────┐    │
        │ 2a. Sinh    │ │ 2b. Sinh     │    │
        │ hình ảnh    │ │ câu hỏi      │    │
        │ (Imagen)    │ │ (với         │    │
        │             │ │ placeholder) │    │
        └──────┬──────┘ └───┬──────────┘    │
               │             │                │
               └─────────────┴────────────────┘
                             │
                      ┌──────▼──────┐
                      │ 3. Merge    │
                      │ hình + Q    │
                      └─────────────┘
```

**Đặc điểm**:

- Câu hỏi KHÔNG phụ thuộc vào hình
- Hình chỉ để minh họa
- Nhanh hơn (parallel)

---

### **HA_TL Workflow** (Sequential)

```
┌─────────────────────────────────────────────────────┐
│ 1. Sinh mô tả hình ảnh CHI TIẾT                      │
│    (với reference image để chính xác)               │
└──────────────┬──────────────────────────────────────┘
               │
        ┌──────▼──────┐
        │ 2. Sinh     │
        │ hình ảnh    │
        │ (Imagen +   │
        │ reference)  │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ 3. Sinh     │
        │ câu hỏi     │
        │ DỰA VÀO     │
        │ hình        │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │ 4. Merge    │
        └─────────────┘
```

**Đặc điểm**:

- Câu hỏi BẮT BUỘC phải đọc hình
- Hình là nguồn dữ liệu chính
- Chậm hơn (sequential) nhưng chính xác

---

## Cấu hình Matrix

Trong file matrix JSON, thêm `rich_content_types`:

```json
{
  "question_specs": [
    {
      "question_codes": ["C1", "C2"],
      "question_type": "TN",
      "cognitive_level": "TH",
      "rich_content_types": {
        "C1": [
          {
            "code": "HA_MH",
            "name": "Hình ảnh minh họa",
            "description": "Hình ảnh minh họa quá trình quang hợp"
          }
        ],
        "C2": [
          {
            "code": "HA_TL",
            "name": "Hình ảnh tư liệu",
            "description": "Biểu đồ dân số để học sinh đọc và phân tích"
          }
        ]
      }
    }
  ]
}
```

---

## Kết Quả Output

Câu hỏi có hình ảnh sẽ có format:

```json
{
  "question_code": "C1",
  "question_stem": {
    "type": "image",
    "content": [
      "Quan sát hình minh họa quá trình quang hợp:",
      {
        "type": "image",
        "content": "server/data/images/C1_HA_MH_20260211_143022.png",
        "metadata": {
          "caption": "Hình 1: Quá trình quang hợp ở lục lạp",
          "alt": "Sơ đồ quang hợp"
        }
      },
      "Sản phẩm chính của quá trình này là gì?"
    ]
  },
  "options": {
    "A": "Glucose và O2",
    "B": "CO2 và H2O",
    "C": "ATP",
    "D": "Protein"
  },
  "correct_answer": "A",
  "explanation": "...",
  "metadata": {
    "has_image": true,
    "image_path": "server/data/images/C1_HA_MH_20260211_143022.png",
    "image_type": "HA_MH"
  }
}
```

---

## Prompt Templates

### Prompt cho Question Generation

**Location**: `server/src/services/prompts/`

- `TN_HA_MH.txt` - Trắc nghiệm với hình minh họa
- `TN_HA_TL.txt` - Trắc nghiệm với hình tư liệu
- `DS_HA_MH.txt` - Đúng/Sai với hình minh họa
- `DS_HA_TL.txt` - Đúng/Sai với hình tư liệu

**Markers**:

- `[IMAGE_PLACEHOLDER]` - Vị trí chèn hình trong câu hỏi
- `{{IMAGE_DESCRIPTION}}` - Mô tả hình ảnh

---

## Helper Utilities

### Image Helpers

```python
from services.utils.image_helpers import (
    ImageHelper,
    ImageContentBuilder,
    ImageValidator
)

# Save/load images
ImageHelper.save_image(image_data, "path/to/save.png")
data = ImageHelper.load_image("path/to/image.png")

# Build rich content
content = ImageContentBuilder.build_image_content(
    text_before="Quan sát hình:",
    image_path="path/to/image.png",
    text_after="Đây là hiện tượng gì?",
    image_caption="Hình 1: ..."
)

# Validate
is_valid, error = ImageValidator.validate_image_file("path.png")
is_valid, error = ImageValidator.validate_image_content(rich_content)
```

---

## Example: Tích hợp vào Phase 4

```python
from services.phases.phase4_question_generation import QuestionGenerationService
from services.generators.question_generator_with_image import integrate_image_workflow

class EnhancedQuestionGenerationService(QuestionGenerationService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Integrate image workflow
        self.generator_with_image = integrate_image_workflow(
            ai_client=self.genai_client,
            question_generator=self.question_generator
        )

    def process_question_generation(self, extracted_lesson, question_type, num_questions=5):
        # Check nếu có HA_MH hoặc HA_TL
        if self._has_image_requirements(extracted_lesson):
            # Use image-enhanced generator
            return self.generator_with_image.generate_questions_with_image(
                spec=extracted_lesson.question_spec,
                content=extracted_lesson.content,
                reference_image_path=extracted_lesson.reference_image
            )
        else:
            # Use normal generator
            return super().process_question_generation(
                extracted_lesson, question_type, num_questions
            )
```

---

## Lưu Ý Quan Trọng

### 1. **Credentials**

Cần thiết lập:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GCP_LOCATION="us-central1"
```

### 2. **Storage**

Hình ảnh được lưu tại: `E:\App\matrixquesgen\server\data\images\`

Format tên file: `{question_code}_{image_type}_{timestamp}.png`

### 3. **Reference Images**

- **HA_MH**: Optional (giúp sinh mô tả chính xác hơn)
- **HA_TL**: Recommended (giúp sinh mô tả và hình ảnh chính xác)

### 4. **Performance**

- **HA_MH**: ~10-15s/câu (parallel)
- **HA_TL**: ~20-30s/câu (sequential)

### 5. **Error Handling**

Tất cả services đều có try-catch và fallback:

- Image generation fail → placeholder image
- Description fail → raise exception
- Question generation fail → retry với fallback model

---

## Troubleshooting

### Lỗi: "Image generation client not initialized"

**Giải pháp**: Kiểm tra credentials và environment variables

### Lỗi: "Cannot parse question from response"

**Giải pháp**: Kiểm tra prompt template và response schema

### Hình ảnh không chính xác

**Giải pháp**:

- Cung cấp reference image
- Cải thiện mô tả trong prompt template
- Tăng temperature nếu cần đa dạng hơn

---

## Testing

```python
# Test ImageDescriptionService
from services.generators.image_description_service import ImageDescriptionService

service = ImageDescriptionService(ai_client, prompts_dir)
result = service.generate_illustrative_description(
    subject="Sinh học",
    class_level="10",
    chapter="2",
    lesson_name="Quang hợp",
    content="...",
    learning_outcome="..."
)
print(result.description)

# Test ImageWorkflowService
from services.generators.image_workflow_service import ImageWorkflowService

workflow = ImageWorkflowService(ai_client)
result = workflow.process_ha_mh_workflow(
    question_spec={...},
    content="..."
)
print(result.image.image_path)
print(result.question)
```

---

## Roadmap

- [ ] Hỗ trợ batch generation cho nhiều câu hỏi
- [ ] Upload hình lên cloud storage (Google Drive/Cloud Storage)
- [ ] Optimize prompt templates
- [ ] A/B testing cho HA_MH vs HA_TL quality
- [ ] UI preview cho hình ảnh trong câu hỏi
- [ ] Export DOCX với hình ảnh

---

## Support

Nếu gặp vấn đề, kiểm tra:

1. Logs trong console
2. File `server/data/images/` có được tạo không
3. Credentials có đúng không
4. Prompt templates có tồn tại không

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-11  
**Author**: MatrixQuesGen Team
