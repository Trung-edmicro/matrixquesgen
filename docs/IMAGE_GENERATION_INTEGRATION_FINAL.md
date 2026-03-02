# ✅ IMAGE GENERATION INTEGRATION - FINAL IMPLEMENTATION

## 📅 Date: 2026-02-11

## 🎯 Vấn Đề

Sau khi AI generate câu hỏi với `[IMAGE_PLACEHOLDER]`, placeholder **không được replace** bằng hình ảnh thực. Output JSON vẫn còn marker chứ chưa có image path.

---

## 🔧 Giải Pháp

### **1. Thêm Method `_replace_image_placeholders()`**

Tích hợp vào [phase4_question_generation.py](server/src/services/phases/phase4_question_generation.py):

```python
def _replace_image_placeholders(self, questions: List, content: str) -> List:
    """Replace [IMAGE_PLACEHOLDER] with actual generated images"""

    # Initialize ImageGenerator with config from image_generation.py
    image_gen = ImageGenerator(num_images=1, aspect_ratio="16:9")

    for question in questions:
        # Check question_stem for placeholder (TN, TLN, TL)
        if has placeholder in question_stem:
            → Generate image
            → Save to data/images/generated_{uuid}.png
            → Replace placeholder with image object

        # Check source_text for placeholder (DS)
        if has placeholder in source_text:
            → Same process
```

### **2. Thêm Helper Method `_replace_placeholder_in_content()`**

Xử lý chi tiết việc replace trong content object:

```python
def _replace_placeholder_in_content(self, content_obj, image_gen, default_prompt):
    """Replace [IMAGE_PLACEHOLDER] in content array"""

    # Loop through content array
    for item in content_data:
        if item == '[IMAGE_PLACEHOLDER]':
            # Extract image_description from metadata
            image_description = metadata.get('image_description', default_prompt)

            # Generate image via ImageGenerator
            image_bytes = image_gen.generate(
                prompt=image_description,
                aspect_ratio="16:9"
            )

            # Save to file: data/images/generated_{uuid}.png
            # Replace placeholder with:
            {
                "type": "image",
                "content": "path/to/generated_image.png",
                "metadata": {"caption": "...", "generated": True}
            }
```

### **3. Gọi từ `_generate_question_task()`**

Sau khi generate questions, **trước khi return**:

```python
# After all question types (TN/DS/TLN/TL) generated
generated_questions.extend(generated)

# 🆕 Process image placeholders if ImageWorkflowService is available
if self.image_workflow_service and generated_questions:
    try:
        generated_questions = self._replace_image_placeholders(
            generated_questions, content
        )
    except Exception as img_error:
        print(f"⚠️ Error generating images: {img_error}")
        print(f"   Continuing with placeholders...")

return generated_questions
```

---

## 🔄 Workflow Hoàn Chỉnh

```
AI Generate Question
    ↓
Output: {type: "image", content: ["Text", "[IMAGE_PLACEHOLDER]", "Question"]}
    ↓
_replace_image_placeholders() detect marker
    ↓
Extract metadata.image_description
    ↓
ImageGenerator.generate(prompt=image_description)
    ↓
Save image → data/images/generated_{uuid}.png
    ↓
Replace [IMAGE_PLACEHOLDER] with image object
    ↓
Final Output: {type: "image", content: ["Text", {image_object}, "Question"]}
```

---

## 📝 Key Points

### **Config Được Sử Dụng**

- ✅ Sử dụng `ImageGenerator` từ [image_generation.py](server/src/services/core/image_generation.py)
- ✅ Model: `imagen-3.0-generate-001` (from `GEMINI_IMAGE_MODEL` env)
- ✅ Project/Location: From `GOOGLE_CLOUD_PROJECT` và `GCP_LOCATION` env
- ✅ Credentials: From `GOOGLE_APPLICATION_CREDENTIALS` env

### **Error Handling**

- 🛡️ Try-catch wrapper trong `_generate_question_task()`
- 🛡️ Nếu generate image failed → Keep placeholder, không break workflow
- 🛡️ Log errors nhưng continue với các questions còn lại

### **Image Storage**

- 📁 Path: `{APP_DIR}/data/images/generated_{uuid}.png`
- 📁 Auto-create directory nếu chưa tồn tại
- 📁 Unique filename với UUID 8 characters

---

## 🧪 Testing Checklist

### **Test Case 1: TN với HA_MH**

```json
Input matrix với rich_content_types: {"C1": [{"code": "HA_MH"}]}
→ AI output [IMAGE_PLACEHOLDER]
→ System generate image
→ Final JSON có image path
```

### **Test Case 2: DS với HA_TL**

```json
Input matrix với rich_content_types: {"C1": [{"code": "HA_TL"}]}
→ AI output [IMAGE_PLACEHOLDER] trong source_text
→ System generate visualization image
→ Final JSON có image path
```

### **Test Case 3: Error Handling**

```
ImageGenerator throws error
→ System logs error
→ Keeps [IMAGE_PLACEHOLDER]
→ Continues processing other questions
```

---

## 📊 Files Modified

1. ✅ [phase4_question_generation.py](server/src/services/phases/phase4_question_generation.py)
   - Added `import uuid`
   - Added `_replace_image_placeholders()` method (47 lines)
   - Added `_replace_placeholder_in_content()` method (92 lines)
   - Modified `_generate_question_task()` to call replacement logic

2. ✅ No changes needed in [image_generation.py](server/src/services/core/image_generation.py)
   - Already has proper `generate()` method
   - Already handles credentials and API calls
   - Already supports placeholder fallback

---

## 🚀 Next Steps

1. **Test with real matrix data** containing HA_MH/HA_TL
2. **Verify image generation** với Vertex AI credentials
3. **Check output JSON** có image paths thay vì placeholders
4. **Monitor logs** cho image generation progress:
   ```
   🖼️ Generating image: Description...
   ✓ Image saved: data/images/generated_abc123.png
   ```

---

## ⚡ Performance Notes

- Image generation **runs sequentially** cho mỗi placeholder (không parallel)
- Có thể optimize sau với ThreadPoolExecutor nếu cần
- Current implementation: **Stability > Speed**

---

**Status**: ✅ Complete & Ready for Testing  
**Version**: 2.0.0 (Full Image Generation Integration)  
**Updated By**: GitHub Copilot
