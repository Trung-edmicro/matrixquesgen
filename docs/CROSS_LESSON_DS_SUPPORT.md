# Cross-Lesson DS Question Support

## Vấn đề

Trong một số môn học (ví dụ: Hóa Học), câu hỏi Đúng/Sai (DS) có 4 mệnh đề (a, b, c, d) nhưng các mệnh đề này nằm rải rác ở nhiều bài khác nhau.

**Ví dụ:**

- **Bài 1**: Có C1A (TH), C1B (VD), C1C (TH)
- **Bài 2**: Có C1D (VD)

→ Để sinh 1 câu DS hoàn chỉnh, cần gộp context từ cả 2 bài.

## Giải pháp

### Phase 1: Parse Matrix

- **Giữ nguyên**: Mỗi statement vẫn thuộc bài của nó trong JSON
- C1A, C1B, C1C → lưu trong Bài 1
- C1D → lưu trong Bài 2

### Phase 4: Generate Questions

Khi xử lý câu DS:

1. **Check completeness**: Kiểm tra xem bài hiện tại có đủ 4 statements không
2. **Search across lessons**: Nếu thiếu, tìm các statements còn lại trong các bài khác
3. **Merge context**: Gộp nội dung từ tất cả các bài có liên quan:
   - `content`: Nội dung bài học
   - `learning_outcome`: Mục tiêu học tập
   - `supplementary_materials`: Tài liệu bổ sung
4. **Generate**: Gửi 1 prompt duy nhất với context đầy đủ cho AI

## Implementation

### Helper Module: `cross_lesson_ds_helper.py`

```python
def merge_cross_lesson_ds_context(
    matrix_data: Dict,
    current_chapter: str,
    current_lesson: str,
    question_code: str,
    current_statements: List[Dict],
    current_lesson_data: Dict
) -> Optional[Dict]
```

**Returns:**

```python
{
    "spec_data": {...},              # DS spec với đủ 4 statements
    "merged_lesson_data": {...},     # Lesson data đã merge
    "merged_content": "...",         # Content từ tất cả bài
    "merged_supplementary": "...",   # Tài liệu bổ sung merged
    "source_lessons": ["3_6", "3_7"] # Danh sách bài đã merge
}
```

### Phase 4 Integration

```python
elif task_type == "DS":
    spec_data = task['spec_data']
    current_statements = spec_data.get('statements', [])

    # Check if need merge (< 4 statements)
    if len(current_statements) < 4:
        merged_result = merge_cross_lesson_ds_context(...)

        if merged_result:
            # Use merged data
            spec_data = merged_result['spec_data']
            content = merged_result['merged_content']
            supplementary = merged_result['merged_supplementary']
```

## Example Output

```
⏳ DS C1: Only 3 statements, searching across lessons...
✓ DS C1: Merged from lessons: 1_1, 1_2
```

## Benefits

✅ **Tự động phát hiện**: Không cần config thủ công
✅ **Flexible**: Hỗ trợ cả 2 luồng (cross-lesson và single-lesson)
✅ **Context đầy đủ**: AI nhận được tất cả thông tin cần thiết
✅ **Maintainable**: Logic tách biệt trong helper module

## Limitations

- Chỉ merge khi tìm đủ 4 statements (a, b, c, d)
- Nếu không đủ 4 statements, câu đó sẽ bị skip
- Content merged có thể dài → cần monitor token limits

## Testing

Để test với file có cross-lesson DS:

```bash
python server/src/api/main-api.py
# Upload Ma trận_HOAHOC_KNTT_C11.xlsx
# Check logs for "Merged from lessons"
```

## Migration

**Không cần migration** - Code tương thích ngược:

- File ma trận cũ (statements trong cùng 1 bài) → hoạt động bình thường
- File ma trận mới (statements cross-lesson) → tự động merge
