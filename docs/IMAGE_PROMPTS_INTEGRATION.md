# Hệ Thống Prompts Với Hình Ảnh - Tích Hợp Workflow

## 🎯 Tổng Quan

Hệ thống đã được tích hợp để **tự động detect và load prompts phù hợp** khi matrix có type HA_MH hoặc HA_TL.

### Cách Hoạt Động

```
Matrix có rich_content_types
    ↓
Detect type (HA_MH hoặc HA_TL)
    ↓
Load prompt type-specific: TN_HA_MH.txt, DS_HA_TL.txt, etc.
    ↓
Nếu không có → Fallback về TN.txt, DS.txt (prompts mặc định)
```

---

## 📁 Prompts Đã Tạo (10 files)

### Cho TN (Trắc Nghiệm)

- ✅ `TN_HA_MH.txt` - Hình ảnh minh họa
- ✅ `TN_HA_TL.txt` - Hình ảnh tư liệu

### Cho DS (Đúng/Sai)

- ✅ `DS_HA_MH.txt` - Hình ảnh minh họa
- ✅ `DS_HA_TL.txt` - Hình ảnh tư liệu

### Cho TLN (Trắc Nghiệm Lượng Giá)

- ✅ `TLN_HA_MH.txt` - Hình ảnh minh họa
- ✅ `TLN_HA_TL.txt` - Hình ảnh tư liệu

### Cho TL (Tự Luận)

- ✅ `TL_HA_MH.txt` - Hình ảnh minh họa
- ✅ `TL_HA_TL.txt` - Hình ảnh tư liệu

### Prompts Mô Tả Hình Ảnh

- ✅ `illustrative_image.txt` - Mô tả HA_MH
- ✅ `data_source_image.txt` - Mô tả HA_TL

**Total**: 10 prompt files

---

## 🏗️ Kiến Trúc Đã Tích Hợp

### 1. Logic Detect Prompt (phase4_question_generation.py)

```python
def _get_prompt_path(self, question_type: str, rich_content_types: Optional[Dict] = None):
    """
    Tự động chọn prompt dựa trên rich_content_types

    Priority:
    1. Full type code: TN_HA_MH.txt, TN_HA_TL.txt
    2. Stripped type: TN_HA.txt (nếu HA_MH hoặc HA_TL)
    3. Generic: TN.txt (fallback)
    """
```

**Ví dụ**:

- Matrix có `C1: HA_MH` → Tìm `TN_HA_MH.txt` → Nếu không có → `TN_HA.txt` → `TN.txt`
- Matrix có `C2: HA_TL` → Tìm `TN_HA_TL.txt` → Nếu không có → `TN_HA.txt` → `TN.txt`

### 2. Tích Hợp Vào Tất Cả Task Types

✅ **TN** (Trắc nghiệm):

```python
spec = QuestionSpec(
    ...
    rich_content_types=spec_data.get('rich_content_types', None)
)
prompt_path = self._get_prompt_path("TN", spec_data.get('rich_content_types'))
```

✅ **DS** (Đúng/Sai):

```python
spec = TrueFalseQuestionSpec(
    ...
    rich_content_types=spec_data.get('rich_content_types', None)
)
prompt_path = self._get_prompt_path("DS", spec_data.get('rich_content_types'))
```

✅ **TLN** (Trắc Nghiệm Lượng Giá):

```python
spec = QuestionSpec(
    ...
    rich_content_types=spec_data.get('rich_content_types', None)
)
prompt_path = self._get_prompt_path("TLN", spec_data.get('rich_content_types'))
```

✅ **TL** (Tự Luận):

```python
spec = QuestionSpec(
    ...
    rich_content_types=spec_data.get('rich_content_types', None)
)
prompt_path = self._get_prompt_path("TL", spec_data.get('rich_content_types'))
```

### 3. ImageWorkflowService (Optional)

```python
# Đã khởi tạo trong __init__ (optional)
self.image_workflow_service = ImageWorkflowService(
    ai_client=self.genai_client,
    image_save_dir=None,  # Default: server/data/images
    prompts_dir=None  # Will be updated by set_prompts_directory
)
```

**Lưu ý**: ImageWorkflowService là **optional** - chỉ cho việc thực sự sinh hình ảnh. Prompt routing hoạt động độc lập.

---

## 📝 Cấu Hình Matrix

### Ví Dụ Matrix JSON

```json
{
  "lessons": [
    {
      "TN": {
        "NB": [
          {
            "code": ["C1"],
            "num": 1,
            "learning_outcome": "Hiểu cấu trúc lục lạp",
            "rich_content_types": {
              "C1": [
                {
                  "code": "HA_MH",
                  "name": "Hình ảnh minh họa",
                  "description": "Hình minh họa cấu trúc lục lạp"
                }
              ]
            }
          }
        ]
      },
      "DS": [
        {
          "question_code": "DS1",
          "statements": [...],
          "rich_content_types": {
            "DS1": [
              {
                "code": "HA_TL",
                "name": "Hình ảnh tư liệu",
                "description": "Biểu đồ dân số để đọc và phân tích"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

---

## 🚀 Cách Sử Dụng

### 1. Upload Prompts Lên Drive

Đặt các prompt files trong thư mục prompts theo cấu trúc:

```
data/prompts/
├── {SUBJECT}_{CURRICULUM}_{GRADE}/
│   ├── TN.txt
│   ├── TN_HA_MH.txt
│   ├── TN_HA_TL.txt
│   ├── DS.txt
│   ├── DS_HA_MH.txt
│   ├── DS_HA_TL.txt
│   ├── TLN.txt
│   ├── TLN_HA_MH.txt
│   ├── TLN_HA_TL.txt
│   ├── TL.txt
│   ├── TL_HA_MH.txt
│   └── TL_HA_TL.txt
```

**Ví dụ**: `LICHSU_KNTT_C12/` chứa tất cả prompts cho Lịch Sử Lớp 12

### 2. Matrix Có rich_content_types

Đảm bảo matrix JSON có `rich_content_types` cho các câu cần hình:

```json
{
  "rich_content_types": {
    "C1": [{ "code": "HA_MH", "name": "Hình ảnh minh họa" }],
    "C2": [{ "code": "HA_TL", "name": "Hình ảnh tư liệu" }]
  }
}
```

### 3. Chạy Generation

```python
from services.phases.phase4_question_generation import QuestionGenerationService

service = QuestionGenerationService(ai_provider="genai")
service.set_prompts_directory(
    subject="LICHSU",
    curriculum="KNTT",
    grade="C12"
)

# Generate - hệ thống tự động detect và load prompt phù hợp
result = service.process_enriched_matrix(
    enriched_matrix_path="data/matrix/enriched_matrix_LICHSU_KNTT_C12.json",
    question_types=["TN", "DS", "TLN", "TL"]
)
```

### 4. Logs Kiểm Tra

Khi chạy, sẽ thấy logs:

```
✓ Prompts directory set to: data/prompts/LICHSU_KNTT_C12
✓ Updated ImageWorkflowService prompts_dir
🖼️ Detected HA_MH for C1
  → TN C1: Using prompt TN_HA_MH.txt
🖼️ Detected HA_TL for DS1
  → DS DS1: Using prompt DS_HA_TL.txt
```

---

## 🎨 Prompt Features

### Markers Hỗ Trợ

Tất cả prompts đều support marker `[IMAGE_PLACEHOLDER]`:

```
"question_stem": "[IMAGE_PLACEHOLDER]\n\nQuan sát hình, hiện tượng này là gì?"
```

Hệ thống sẽ tự động replace marker này với image object khi export DOCX hoặc hiển thị UI.

### Variables Trong Prompts

Các prompts đều support các variables:

- `{{SUBJECT}}` - Môn học
- `{{CLASS}}` - Lớp
- `{{CHAPTER}}` - Chương
- `{{LESSON_NAME}}` - Tên bài học
- `{{CONTENT}}` - Nội dung SGK
- `{{EXPECTED_LEARNING_OUTCOME}}` - Kết quả học
- `{{IMAGE_DESCRIPTION}}` - Mô tả hình ảnh (cho image prompts)

---

## 🔄 Workflow Hoàn Chỉnh

### Hiện Tại (Prompt Routing Only)

```
1. Matrix có HA_MH/HA_TL
   ↓
2. Load prompt tương ứng (TN_HA_MH.txt)
   ↓
3. Generate câu hỏi với marker [IMAGE_PLACEHOLDER]
   ↓
4. Output: Câu hỏi có marker (chưa có hình thật)
```

### Tương Lai (Full Image Generation)

```
1. Matrix có HA_MH/HA_TL
   ↓
2. ImageDescriptionService → Sinh mô tả hình
   ↓
3. ImageGenerator → Sinh hình từ mô tả
   ↓
4. Load prompt tương ứng (TN_HA_MH.txt)
   ↓
5. Generate câu hỏi + Merge hình vào marker
   ↓
6. Output: Câu hỏi có hình ảnh thật
```

---

## ✅ Checklist Triển Khai

### Phase 1: Prompt Routing (✅ HOÀN THÀNH)

- [x] Tạo 10 prompt files cho TN, DS, TLN, TL
- [x] Update logic `_get_prompt_path()` để detect HA_MH/HA_TL
- [x] Tích hợp vào tất cả task types (TN, DS, TLN, TL)
- [x] Copy rich_content_types từ spec → QuestionSpec
- [x] Test với matrix có rich_content_types

### Phase 2: Image Generation (Tùy Chọn)

- [ ] Enable ImageWorkflowService
- [ ] Test ImageGenerator với Vertex AI Imagen
- [ ] Implement actual image merging vào câu hỏi
- [ ] Upload images lên storage

---

## 📊 Testing

### Test Matrix

Tạo test matrix với:

```json
{
  "rich_content_types": {
    "C1": [{ "code": "HA_MH" }],
    "C2": [{ "code": "HA_TL" }]
  }
}
```

### Kiểm Tra Logs

```bash
# Tìm log detect image type
grep "Detected HA_MH" logs.txt
grep "Using prompt TN_HA_MH.txt" logs.txt

# Kiểm tra marker trong output
grep "\[IMAGE_PLACEHOLDER\]" output.json
```

### Validate Output

Câu hỏi output phải có:

- `question_stem` chứa `[IMAGE_PLACEHOLDER]`
- Nội dung câu hỏi phù hợp với type (minh họa vs tư liệu)

---

## 🐛 Troubleshooting

### Issue: Không load được prompt

**Triệu chứng**: Log shows "Using prompt TN.txt" thay vì "TN_HA_MH.txt"

**Giải pháp**:

1. Check file tồn tại: `data/prompts/{SUBJECT}_{CURRICULUM}_{GRADE}/TN_HA_MH.txt`
2. Check rich_content_types trong matrix có đúng format
3. Check logs: `✓ Prompts directory set to: ...`

### Issue: rich_content_types không được truyền

**Triệu chứng**: Không thấy log "🖼️ Detected HA_MH"

**Giải pháp**:

1. Check matrix JSON có `rich_content_types` field
2. Check enrichment process có copy field này
3. Add debug log trong code: `print(f"DEBUG: spec rich_content_types = {spec.rich_content_types}")`

### Issue: ImageWorkflowService error

**Triệu chứng**: Error initializing ImageWorkflowService

**Giải pháp**:

- **Không cần thiết cho Phase 1** - Prompt routing hoạt động độc lập
- Nếu muốn enable: Check credentials, Vertex AI setup

---

## 📚 Files Changed

### Core Changes

- ✅ `phase4_question_generation.py`
  - Added ImageWorkflowService import
  - Updated `_get_prompt_path()` logic
  - Added `_has_image_requirements()` helper
  - Update `set_prompts_directory()` to sync with ImageWorkflowService

### New Prompt Files (10)

- ✅ `TN_HA_MH.txt`, `TN_HA_TL.txt`
- ✅ `DS_HA_MH.txt`, `DS_HA_TL.txt`
- ✅ `TLN_HA_MH.txt`, `TLN_HA_TL.txt`
- ✅ `TL_HA_MH.txt`, `TL_HA_TL.txt`
- ✅ `illustrative_image.txt`, `data_source_image.txt`

---

## 🎯 Next Steps

### Immediate

1. ✅ Upload 10 prompts lên Drive vào thư mục tương ứng
2. ✅ Test với matrix có rich_content_types
3. ✅ Verify logs và output

### Future

1. Enable ImageWorkflowService cho image generation thật
2. Implement image upload to cloud storage
3. Update UI để hiển thị hình ảnh trong preview
4. Export DOCX với hình ảnh embedded

---

**Status**: ✅ Phase 1 Complete - Prompt Routing Integrated  
**Version**: 1.0.0  
**Date**: 2026-02-11
