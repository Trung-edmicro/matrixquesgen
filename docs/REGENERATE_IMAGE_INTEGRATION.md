# Image Generation trong Regenerate Workflow

## Tổng quan

Đã tích hợp tự động sinh ảnh (HA_MH và HA_TL) vào chức năng regenerate câu hỏi. Khi regenerate câu hỏi có `rich_content_types` chứa 'HA_MH' hoặc 'HA_TL', hệ thống sẽ tự động:

1. Sinh mô tả hình ảnh phù hợp với loại
2. Generate hình ảnh từ mô tả
3. Lưu hình ảnh vào `data/images/`
4. Merge hình ảnh vào `question_stem` theo format rich content

## Thay đổi code

### File: `server/src/api/routes/regenerate.py`

#### 1. Thêm imports mới

```python
from services.generators.image_description_service import ImageDescriptionService
from services.core.image_generation import ImageGenerator
from datetime import datetime
```

#### 2. Thêm helper function `_generate_image_for_question()`

Function này xử lý toàn bộ workflow sinh ảnh:

- Kiểm tra `rich_content_types` có chứa 'HA_MH' hoặc 'HA_TL'
- Khởi tạo AI client và ImageDescriptionService
- Sinh mô tả hình ảnh theo loại:
  - **HA_MH**: Hình ảnh minh họa (illustrative) - không bắt buộc cho việc trả lời
  - **HA_TL**: Hình ảnh tư liệu (data source) - nguồn dữ liệu trực tiếp, chi tiết
- Generate hình ảnh từ mô tả bằng ImageGenerator
- Lưu hình ảnh với format: `{question_code}_{image_type}_{timestamp}.png`
- Trả về rich content dict để merge vào câu hỏi

**Signature:**

```python
def _generate_image_for_question(
    question_code: str,
    rich_content_types: List[str],
    metadata: dict,
    lesson_data: dict,
    spec_data: dict,
    content: str
) -> Optional[dict]
```

**Returns:**

```python
{
    "type": "image",
    "content": "path/to/image.png",
    "metadata": {
        "image_type": "HA_MH" or "HA_TL",
        "description": "...",
        "caption": "..."
    }
}
```

#### 3. Tích hợp vào `regenerate_single_question()`

Sau khi generate câu hỏi mới, trước khi save:

```python
# 🖼️ Generate image if needed (HA_MH or HA_TL)
rich_content_types_dict = spec_data.get('rich_content_types', {})
rich_content_types = rich_content_types_dict.get(request.question_code, [])

if rich_content_types:
    image_rich_content = _generate_image_for_question(
        question_code=request.question_code,
        rich_content_types=rich_content_types,
        metadata=metadata,
        lesson_data=lesson_data,
        spec_data=spec_data,
        content=content
    )

    if image_rich_content:
        # Merge image into question_stem
        # Convert text stem to mixed content or append to existing mixed content
```

#### 4. Bulk regenerate

Bulk regenerate (`/api/regenerate/bulk`) tự động có image generation vì nó gọi `regenerate_single_question()` cho mỗi câu hỏi.

## Workflow chi tiết

### Case 1: Câu hỏi TN với HA_MH

```
1. User gọi /api/regenerate/question
   - session_id: "abc123"
   - question_type: "TN"
   - question_code: "C1"

2. Load enriched_matrix
   - Tìm spec cho C1
   - Phát hiện rich_content_types: ["HA_MH"]

3. Generate câu hỏi mới (TN)
   - Gọi QuestionGenerator.generate_questions_for_spec()
   - Nhận câu hỏi text

4. 🆕 Generate image (HA_MH workflow)
   - ImageDescriptionService.generate_illustrative_description()
   - ImageGenerator.generate()
   - Save image: data/images/C1_HA_MH_20260211_143022.png

5. Merge image vào question_stem
   - Convert text stem to mixed content:
   {
     "type": "mixed",
     "content": [
       "Nội dung câu hỏi...",
       {
         "type": "image",
         "content": "data/images/C1_HA_MH_20260211_143022.png",
         "metadata": {...}
       }
     ]
   }

6. Save question với image
```

### Case 2: Câu hỏi DS với HA_TL

```
1. User gọi /api/regenerate/question
   - question_type: "DS"
   - question_code: "C2"

2. Load enriched_matrix
   - Phát hiện rich_content_types: ["HA_TL"]

3. Generate câu hỏi mới (DS)
   - source_text + statements

4. 🆕 Generate image (HA_TL workflow)
   - ImageDescriptionService.generate_data_source_description()
     → Mô tả CHI TIẾT với số liệu
   - ImageGenerator.generate()
   - Save: data/images/C2_HA_TL_20260211_143045.png

5. Merge image vào source_text
   - Tương tự TN, convert to mixed content

6. Save question
```

## Điểm khác biệt HA_MH vs HA_TL

| Khía cạnh                   | HA_MH                                  | HA_TL                                  |
| --------------------------- | -------------------------------------- | -------------------------------------- |
| **Mục đích**                | Minh họa, trang trí                    | Nguồn dữ liệu trực tiếp                |
| **Chi tiết**                | Tổng quan, không cần số liệu chính xác | CHI TIẾT, số liệu, nhãn, đơn vị đầy đủ |
| **Bắt buộc**                | Không                                  | Có - cần để trả lời câu hỏi            |
| **Prompt template**         | `illustrative_image.txt`               | `data_source_image.txt`                |
| **ImageDescriptionService** | `generate_illustrative_description()`  | `generate_data_source_description()`   |

## API Endpoints

### 1. Regenerate single question

**POST** `/api/regenerate/question`

```json
{
  "session_id": "abc123",
  "question_type": "TN",
  "question_code": "C1"
}
```

**Behavior mới:**

- Nếu spec có `rich_content_types: ["HA_MH"]` hoặc `["HA_TL"]`
- Tự động sinh ảnh và merge vào câu hỏi
- Không cần thêm parameter

**Response:**

```json
{
  "success": true,
  "message": "Đã sinh lại câu C1",
  "question": {
    "question_code": "C1",
    "question_stem": {
      "type": "mixed",
      "content": [
        "Text content...",
        {
          "type": "image",
          "content": "data/images/C1_HA_MH_20260211_143022.png",
          "metadata": {
            "image_type": "HA_MH",
            "description": "...",
            "caption": "..."
          }
        }
      ]
    },
    ...
  }
}
```

### 2. Regenerate bulk

**POST** `/api/regenerate/bulk`

```json
{
  "session_id": "abc123",
  "questions": [
    { "type": "TN", "code": "C1" },
    { "type": "DS", "code": "C2" },
    { "type": "TN", "code": "C5" }
  ]
}
```

**Behavior:**

- Tự động sinh ảnh cho các câu có HA_MH/HA_TL
- Parallel execution (max 5 workers)
- Mỗi worker độc lập generate image

## Testing

### Manual test

1. **Chuẩn bị:**
   - Session có câu hỏi với `rich_content_types: ["HA_MH"]` hoặc `["HA_TL"]`
   - Enriched matrix file tương ứng
   - API credentials hợp lệ

2. **Test single regenerate:**

   ```bash
   curl -X POST http://localhost:8000/api/regenerate/question \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "YOUR_SESSION_ID",
       "question_type": "TN",
       "question_code": "C1"
     }'
   ```

3. **Kiểm tra:**
   - Console logs: `🖼️ Generating HA_MH image...`
   - File image: `data/images/C1_HA_MH_*.png`
   - Response: `question_stem` có format mixed content với image

4. **Test bulk regenerate:**
   ```bash
   curl -X POST http://localhost:8000/api/regenerate/bulk \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": "YOUR_SESSION_ID",
       "questions": [
         {"type": "TN", "code": "C1"},
         {"type": "TN", "code": "C2"}
       ]
     }'
   ```

### Automated test (future)

```python
# test_regenerate_with_image.py
def test_regenerate_with_ha_mh():
    # Setup session with HA_MH question
    response = regenerate_question(
        session_id="test_session",
        question_type="TN",
        question_code="C1"
    )

    assert response['success'] == True
    question = response['question']

    # Verify image generated
    assert 'question_stem' in question
    stem = question['question_stem']
    assert stem['type'] == 'mixed'
    assert any(item.get('type') == 'image' for item in stem['content'])

    # Verify image file exists
    image_item = [item for item in stem['content'] if item.get('type') == 'image'][0]
    image_path = Path(image_item['content'])
    assert image_path.exists()
```

## Troubleshooting

### Lỗi: "No module named 'pandas'"

- Không phải lỗi của code mới
- Do import chain dependencies
- Chạy: `pip install pandas` nếu cần test local

### Lỗi: "Failed to generate image"

- Kiểm tra API credentials
- Kiểm tra ImageGenerator configuration
- Xem logs chi tiết: `print(f"❌ Error: {e}")`

### Image không được merge vào question_stem

- Kiểm tra `rich_content_types` trong enriched_matrix
- Verify `_generate_image_for_question()` return không None
- Check console logs cho warning/error

### Image description không đúng context

- Kiểm tra prompt templates (`illustrative_image.txt`, `data_source_image.txt`)
- Verify metadata (subject, grade, chapter) được truyền đúng
- Điều chỉnh prompt cho phù hợp môn học

## Checklist implementation

- [x] Add imports (ImageDescriptionService, ImageGenerator, datetime)
- [x] Create `_generate_image_for_question()` helper
- [x] Integrate into `regenerate_single_question()`
- [x] Auto-support in `regenerate_bulk()`
- [x] Handle text stem → mixed content conversion
- [x] Handle existing mixed content → append image
- [x] Error handling và logging
- [x] Docs và testing guide

## Next steps

### Phase 1: Current (✅ Done)

- Tích hợp image generation vào regenerate workflow
- Support cả single và bulk regenerate
- Tự động detect HA_MH/HA_TL từ rich_content_types

### Phase 2: Future enhancements

- [ ] Support reference images (user upload)
- [ ] Image preview trong UI trước khi regenerate
- [ ] Batch image generation optimization (parallel all images)
- [ ] Image caching (reuse similar descriptions)
- [ ] Custom image prompts per question
- [ ] A/B testing different image styles

### Phase 3: Advanced features

- [ ] Image quality feedback loop
- [ ] Auto-retry with different prompts nếu image không phù hợp
- [ ] Integration với image editing tools
- [ ] Image versioning (keep history)

## Notes

- Image generation có thể mất 5-10 giây/image
- Bulk regenerate với nhiều images sẽ chậm hơn
- Consider adding progress tracking cho bulk operations
- Image files nên được cleanup định kỳ (old unused images)
