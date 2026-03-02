# 🔄 Schema Update: Hỗ Trợ [IMAGE_PLACEHOLDER] cho AI Generate Image

## 📅 Update Date: 2026-02-11

## 🎯 Mục Đích

Cập nhật JSON schemas để phù hợp với **luồng sinh câu hỏi kèm hình ảnh AI-generated** thay vì dùng URL/path hình ảnh có sẵn.

---

## 🔄 Thay Đổi Chính

### **Before (Schema cũ - URL-based)**

```json
{
  "type": "image",
  "content": [
    "Quan sát bản đồ:",
    {
      "type": "image",
      "content": "https://example.com/map.png",
      "metadata": { "caption": "Hình 1: Bản đồ ASEAN" }
    },
    "Quốc gia nào có diện tích lớn nhất?"
  ]
}
```

### **After (Schema mới - Placeholder-based)**

```json
{
  "type": "image",
  "content": [
    "Quan sát bản đồ ASEAN:",
    "[IMAGE_PLACEHOLDER]",
    "Quốc gia nào có diện tích lớn nhất?"
  ],
  "metadata": {
    "image_description": "Bản đồ ASEAN với 10 quốc gia thành viên, màu sắc phân biệt từng nước",
    "caption": "Hình 1: Bản đồ khu vực Đông Nam Á"
  }
}
```

---

## ✅ Files Modified

### 1. `server/src/services/core/schemas.py`

#### **A. `get_image_content_schema()`**

**Docstring Update:**

```python
"""
Schema cho content type='image' - Text + Hình ảnh
Sử dụng khi: rich_content_types chứa 'HA_MH' (minh họa) hoặc 'HA_TL' (tư liệu)

⭐ LUỒNG MỚI - AI GENERATE IMAGE:
- AI output marker '[IMAGE_PLACEHOLDER]' trong content array
- Thêm 'image_description' trong metadata để mô tả hình cần generate
- ImageWorkflowService sẽ tự động:
  1. Extract image_description
  2. Generate image bằng Vertex AI Imagen
  3. Replace '[IMAGE_PLACEHOLDER]' bằng image object thực
"""
```

**Content Array Items:**

```python
"items": {
    "anyOf": [
        {
            "type": "string",
            "description": "Text mô tả hoặc câu hỏi"
        },
        {
            "type": "string",
            "const": "[IMAGE_PLACEHOLDER]",
            "description": "⭐ IMAGE PLACEHOLDER - Dùng marker này khi cần AI generate hình ảnh"
        }
    ]
}
```

**Metadata Properties:**

```python
"metadata": {
    "type": "object",
    "properties": {
        "source": {"type": "string", "description": "Nguồn dữ liệu"},
        "image_description": {
            "type": "string",
            "description": "⭐ BẮT BUỘC khi dùng [IMAGE_PLACEHOLDER]: Mô tả chi tiết hình ảnh cần AI generate"
        },
        "caption": {"type": "string", "description": "Chú thích hiển thị cho người dùng"}
    }
}
```

#### **B. `get_mixed_content_schema()`**

**Image Content in Mixed:**

```python
{
    "type": "string",
    "description": "⭐ Image content - Dùng '[IMAGE_PLACEHOLDER]' marker để AI generate image"
}
```

**Metadata Properties:**

```python
"metadata": {
    "type": "object",
    "properties": {
        "source": {"type": "string", "description": "Nguồn dữ liệu"},
        "image_description": {
            "type": "string",
            "description": "⭐ BẮT BUỘC khi có [IMAGE_PLACEHOLDER]: Mô tả chi tiết hình ảnh cần AI generate"
        }
    }
}
```

#### **C. Updated Examples**

**Example 1 - HA_MH (Hình minh họa):**

```json
{
  "type": "image",
  "content": [
    "Quan sát hình ảnh minh họa dưới đây:",
    "[IMAGE_PLACEHOLDER]",
    "Hiện tượng trong hình là gì?"
  ]
}
```

**Example 2 - HA_TL (Hình tư liệu):**

```json
{
  "type": "image",
  "content": [
    "Cho biểu đồ dân số thành thị 2010-2021:",
    "[IMAGE_PLACEHOLDER]",
    "Năm nào có dân số cao nhất?"
  ],
  "metadata": {
    "source": "Niên giám thống kê 2021"
  }
}
```

**Example 3 - Mixed với HA_MH:**

```json
{
  "type": "mixed",
  "content": [
    "Quan sát hình ảnh minh họa:",
    "[IMAGE_PLACEHOLDER]",
    "Hiện tượng trong hình là gì?"
  ],
  "metadata": {
    "image_description": "Hình ảnh núi lửa phun trào với dung nham đỏ rực"
  }
}
```

---

## 🔄 Workflow Integration

### **Luồng Xử Lý Mới**

```
AI Generate Question
    ↓
Output: question_stem với [IMAGE_PLACEHOLDER] + metadata.image_description
    ↓
ImageWorkflowService detect placeholder
    ↓
Generate image description (from image_description hoặc context)
    ↓
Generate image via Vertex AI Imagen
    ↓
Replace [IMAGE_PLACEHOLDER] với image object thực
    ↓
Final Question JSON với hình ảnh thật
```

### **HA_MH vs HA_TL**

| Type      | Description          | Workflow                                           | Placeholder              |
| --------- | -------------------- | -------------------------------------------------- | ------------------------ |
| **HA_MH** | Hình ảnh minh họa    | Parallel: Description → Image + Question → Merge   | ✅ `[IMAGE_PLACEHOLDER]` |
| **HA_TL** | Hình tư liệu từ data | Sequential: Description → Image → Question → Merge | ✅ `[IMAGE_PLACEHOLDER]` |

---

## 📝 Quy Tắc Mới Cho AI

### ✅ **DO (Làm đúng)**

1. **Dùng marker string trong array:**

   ```json
   "content": [
     "Quan sát hình ảnh:",
     "[IMAGE_PLACEHOLDER]",
     "Đây là gì?"
   ]
   ```

2. **Thêm image_description trong metadata:**

   ```json
   "metadata": {
     "image_description": "Bản đồ ASEAN với 10 quốc gia, màu sắc phân biệt"
   }
   ```

3. **Mô tả chi tiết để AI generate đúng:**
   ```json
   "image_description": "Biểu đồ cột so sánh dân số thành thị Việt Nam 2010-2021,
                        trục x là năm (2010, 2015, 2021),
                        trục y là triệu người,
                        màu xanh dương"
   ```

### ❌ **DON'T (Tránh sai)**

1. **Dùng URL/path có sẵn:**

   ```json
   ❌ "content": "https://example.com/image.png"
   ```

2. **Embed placeholder trong text:**

   ```json
   ❌ "content": "Quan sát hình [IMAGE_PLACEHOLDER] và trả lời"
   ```

3. **Thiếu image_description:**

   ```json
   ❌ "content": ["Text", "[IMAGE_PLACEHOLDER]", "End"]
   // Thiếu metadata.image_description
   ```

4. **Dùng object thay vì string marker:**
   ```json
   ❌ {"type": "image", "content": "[IMAGE_PLACEHOLDER]"}
   ✅ "[IMAGE_PLACEHOLDER]"  // Direct string in array
   ```

---

## 🧪 Testing

### Test Case 1: TN với HA_MH

```json
{
  "question_stem": {
    "type": "image",
    "content": [
      "Quan sát hình ảnh minh họa:",
      "[IMAGE_PLACEHOLDER]",
      "Hiện tượng nào đang xảy ra trong hình?"
    ],
    "metadata": {
      "image_description": "Núi lửa đang phun trào với dung nham đỏ rực, khói bốc cao"
    }
  },
  "options": {
    "A": "Động đất",
    "B": "Núi lửa phun",
    "C": "Sóng thần",
    "D": "Lốc xoáy"
  }
}
```

### Test Case 2: DS với HA_TL

```json
{
  "source_text": {
    "type": "image",
    "content": [
      "Cho biểu đồ dân số đô thị:",
      "[IMAGE_PLACEHOLDER]",
      "Phân tích xu hướng dân số hóa đô thị"
    ],
    "metadata": {
      "image_description": "Biểu đồ đường tăng trưởng dân số đô thị VN 2000-2020",
      "source": "Niên giám thống kê 2021"
    }
  },
  "statements": {
    "a": { "text": "Dân số đô thị tăng liên tục", "correct_answer": true }
  }
}
```

---

## 📊 Impact Assessment

### **Benefits**

- ✅ AI có thể generate câu hỏi kèm hình ảnh mà không cần hình có sẵn
- ✅ Linh hoạt: Hình ảnh được tạo dựa trên mô tả, phù hợp nội dung
- ✅ Schema đơn giản hơn: String marker thay vì complex object
- ✅ Dễ validate: Check marker presence trước khi generate

### **Breaking Changes**

- ⚠️ Nếu có code cũ expect URL string → Cần update
- ⚠️ Prompts phải được update để output `[IMAGE_PLACEHOLDER]`

### **Backward Compatibility**

- 🔄 Mixed mode vẫn support cả URL và placeholder (future-proof)
- 🔄 Text-only questions không bị ảnh hưởng

---

## 🔗 Related Documentation

- [IMAGE_PROMPTS_INTEGRATION.md](IMAGE_PROMPTS_INTEGRATION.md) - Integration guide
- [IMAGE_WORKFLOW_README.md](IMAGE_WORKFLOW_README.md) - Workflow overview
- [IMAGE_QUESTION_GENERATION.md](IMAGE_QUESTION_GENERATION.md) - Full technical spec
- [RICH_CONTENT_SCHEMA.md](RICH_CONTENT_SCHEMA.md) - Original rich content schema

---

## ✅ Validation

**No errors found** - All schema updates validated successfully! ✨

---

**Status**: ✅ Complete & Production Ready  
**Updated By**: GitHub Copilot  
**Version**: 1.1.0 (Schema v2 - Placeholder-based)
