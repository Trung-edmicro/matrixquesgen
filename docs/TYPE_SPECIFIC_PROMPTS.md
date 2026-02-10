# Type-Specific Prompt Templates

## Overview

The question generation system now supports **type-specific prompt templates** based on rich content types. This allows creating specialized prompts for different content types (e.g., calculation, theory, tables, charts) while maintaining fallback to generic prompts.

## Feature Specification

### Prompt Naming Convention

Type-specific prompts follow the pattern: `{QUESTION_TYPE}_{CONTENT_TYPE}.txt`

**Question Types:**

- `TN` - Multiple choice (Trắc nghiệm)
- `DS` - True/False (Đúng/Sai)
- `TLN` - Short answer (Trả lời ngắn)
- `TL` - Essay (Tự luận)

**Rich Content Types:**

- `TT` - Calculation (Tính toán)
- `LT` - Theory (Lý thuyết)
- `BD` - Chart (Biểu đồ)
- `BK` - Table (Bảng khảo sát)
- `HA` - Image (Hình ảnh) - includes HA_MH (illustration) and HA_TL (reference)

### Examples

```
data/prompts/DIALY_KNTT_C12/
├── TN.txt           # Generic multiple choice prompt
├── TN2.txt          # Alternative generic prompt (higher priority)
├── TN_TT.txt        # Calculation-focused multiple choice
├── TN_LT.txt        # Theory-focused multiple choice
├── TN_BD.txt        # Chart-based multiple choice
├── DS.txt           # Generic true/false prompt
├── DS_TT.txt        # Calculation true/false
├── TLN.txt          # Generic short answer prompt
├── TLN_LT.txt       # Theory short answer
├── TL.txt           # Generic essay prompt
└── TL_BD.txt        # Chart analysis essay
```

## Implementation Logic

### Resolution Algorithm

The system uses the `_get_prompt_path()` helper method with this logic:

1. **Extract primary type:** Get the first rich content type from question spec
   - Example: `{"TT": {...}, "BD": {...}}` → extracts `TT`
   - Strips suffix: `HA_MH` → `HA`, `HA_TL` → `HA`

2. **Try type-specific prompt:** Check if `{TYPE}_{SUBTYPE}.txt` exists
   - Example: For TN with TT → tries `TN_TT.txt`

3. **Fallback to generic:** If type-specific not found, use `{TYPE}.txt`
   - Special case: TN prefers `TN2.txt` over `TN.txt` if available

4. **Logging:** Console output shows which prompt is used:
   ```
   ✓ Using type-specific prompt: TN_TT.txt
   ⓘ Type-specific prompt not found: TN_BD.txt, using generic: TN2.txt
   ```

### Code Integration

All 4 question types now use the helper method:

```python
# TN - Multiple Choice
prompt_path = self._get_prompt_path("TN", spec_data.get('rich_content_types'))
generated = self.question_generator.generate_questions_for_spec(
    spec=spec,
    prompt_template_path=str(prompt_path),
    content=content,
    question_template=question_template
)

# DS - True/False
prompt_path = self._get_prompt_path("DS", spec_data.get('rich_content_types'))
generated_ds = self.question_generator.generate_true_false_question(
    tf_spec=spec,
    prompt_template_path=str(prompt_path),
    content=content,
    question_template=question_template
)

# TLN - Short Answer
prompt_path = self._get_prompt_path("TLN", spec_data.get('rich_content_types'))
generated = self.question_generator.generate_tln_questions(
    spec=spec,
    prompt_template_path=str(prompt_path),
    content=content,
    question_template=question_template
)

# TL - Essay
prompt_path = self._get_prompt_path("TL", rich_types)
generated = self.question_generator.generate_tl_questions(
    spec=spec,
    prompt_template_path=str(prompt_path),
    content=content,
    question_template=question_template
)
```

## Usage Examples

### Example 1: Calculation Questions

**Matrix enriched data:**

```json
{
  "TN": {
    "VD": [
      {
        "num": 2,
        "code": ["C10", "C14"],
        "learning_outcome": "Tính toán và phân tích dữ liệu thống kê",
        "rich_content_types": {
          "TT": {
            "name": "Tính toán",
            "description": ""
          }
        }
      }
    ]
  }
}
```

**System behavior:**

1. Detects `rich_content_types` with `TT` as primary type
2. Looks for `data/prompts/DIALY_KNTT_C12/TN_TT.txt`
3. If found → uses calculation-specific prompt with detailed math instructions
4. If not found → falls back to generic `TN2.txt` or `TN.txt`

**Console output:**

```
✓ Using type-specific prompt: TN_TT.txt
```

### Example 2: Theory Questions (No Type-Specific Prompt)

**Matrix enriched data:**

```json
{
  "TLN": {
    "NB": [
      {
        "num": 3,
        "code": ["C1", "C2", "C3"],
        "learning_outcome": "Hiểu khái niệm cơ bản",
        "rich_content_types": {
          "LT": {
            "name": "Lý thuyết",
            "description": ""
          }
        }
      }
    ]
  }
}
```

**System behavior:**

1. Detects `rich_content_types` with `LT` as primary type
2. Looks for `data/prompts/DIALY_KNTT_C12/TLN_LT.txt`
3. Not found → falls back to generic `TLN.txt`

**Console output:**

```
ⓘ Type-specific prompt not found: TLN_LT.txt, using generic: TLN.txt
```

### Example 3: Chart Analysis

**Matrix enriched data:**

```json
{
  "DS": {
    "VDC": [
      {
        "question_code": "DS2",
        "statements": [...],
        "rich_content_types": {
          "BD": {
            "name": "Biểu đồ",
            "description": ""
          }
        }
      }
    ]
  }
}
```

**System behavior:**

1. Detects `BD` (chart) as primary type
2. Looks for `data/prompts/DIALY_KNTT_C12/DS_BD.txt`
3. Uses chart analysis prompt with instructions for reading/interpreting charts

**Console output:**

```
✓ Using type-specific prompt: DS_BD.txt
```

## Benefits

### 1. **Flexibility**

- Create specialized prompts only when needed
- No need to modify all prompt types at once
- Gradual migration path from generic to specialized prompts

### 2. **Quality Improvement**

- Calculation questions get math-specific instructions
- Theory questions focus on conceptual understanding
- Chart questions include visualization interpretation guidelines
- Table questions handle structured data analysis

### 3. **Maintainability**

- Fallback ensures system never breaks due to missing prompts
- Clear logging shows which prompts are used
- Easy to test: just add a new `.txt` file

### 4. **Backward Compatibility**

- Existing systems work unchanged with generic prompts
- No breaking changes to existing workflows
- Optional enhancement that activates when files are present

## Creating Type-Specific Prompts

### Step 1: Identify Need

Check your enriched matrix for `rich_content_types` patterns:

```bash
grep -r "rich_content_types" data/matrix/
```

### Step 2: Create Specialized Prompt

Copy the generic prompt and customize for the specific type:

```bash
cd data/prompts/DIALY_KNTT_C12/
cp TN.txt TN_TT.txt
# Edit TN_TT.txt to add calculation-specific instructions
```

### Step 3: Test and Iterate

Run generation and observe console logs:

```bash
python launcher.py
# Watch for: "✓ Using type-specific prompt: TN_TT.txt"
```

### Step 4: Quality Check

Compare questions generated with type-specific vs generic prompts:

- Check if mathematical notation is properly formatted
- Verify chart references are correct
- Ensure table data is accurately cited

## File Locations

**Implementation:**

- `server/src/services/phases/phase4_question_generation.py`
  - Method: `_get_prompt_path()`
  - Lines: ~204-256 (helper method)
  - Lines: ~1298-1480 (usage in TN/DS/TLN/TL generation)

**Prompts:**

- `data/prompts/{SUBJECT}_{CURRICULUM}_{GRADE}/`
  - Generic: `TN.txt`, `TN2.txt`, `DS.txt`, `TLN.txt`, `TL.txt`
  - Type-specific: `{TYPE}_{SUBTYPE}.txt`

**Matrix:**

- Input: `data/matrix/enriched_matrix_*.json`
  - Contains `rich_content_types` in question specs

## Migration Guide

### Adding First Type-Specific Prompt

1. **Analyze current prompts:**

   ```bash
   ls data/prompts/DIALY_KNTT_C12/
   # Output: TN.txt, TN2.txt, DS.txt, TLN.txt, TL.txt
   ```

2. **Identify most common rich type:**

   ```bash
   grep -o '"[A-Z_]*":\s*{' data/matrix/enriched_matrix_DIALY_KNTT_C12.json | sort | uniq -c
   # Example output:
   #   15 "TT": {
   #   10 "LT": {
   #    5 "BD": {
   ```

3. **Create TN_TT.txt for calculation questions:**

   ```bash
   cp data/prompts/DIALY_KNTT_C12/TN.txt data/prompts/DIALY_KNTT_C12/TN_TT.txt
   ```

4. **Customize the prompt:**
   - Add: "QUAN TRỌNG: Câu hỏi yêu cầu tính toán, hãy đảm bảo..."
   - Add: "Bao gồm các bước giải chi tiết trong explanation"
   - Add: "Sử dụng ký hiệu toán học chuẩn"

5. **Test and observe:**
   ```bash
   python launcher.py
   # Watch console for prompt selection logs
   ```

## Future Enhancements

### Potential Additions

- Multi-type prompts: `TN_TT_BD.txt` for calculation + chart
- Level-specific: `TN_VDC_TT.txt` for advanced calculation
- Subject-specific: `TN_TT_DIALY.txt` vs `TN_TT_HOAHOC.txt`

### Dynamic Prompt Selection

- Weight-based selection for multi-type content
- AI-assisted prompt recommendation
- A/B testing different prompt variants

## Troubleshooting

### Issue: Type-specific prompt not being used

**Symptoms:**

```
ⓘ Type-specific prompt not found: TN_TT.txt, using generic: TN2.txt
```

**Solutions:**

1. Check file exists: `ls data/prompts/DIALY_KNTT_C12/TN_TT.txt`
2. Verify file permissions: `chmod 644 TN_TT.txt`
3. Check spelling: Must match exactly (case-sensitive)

### Issue: Wrong type code extracted

**Symptoms:**

```
⚠️ Could not extract type code from rich_content_types: ...
```

**Solutions:**

1. Validate matrix JSON structure
2. Ensure `rich_content_types` is a dict, not a list
3. Check for empty dicts: `{}`

### Issue: All questions use generic prompt

**Cause:** No `rich_content_types` in enriched matrix

**Solutions:**

1. Re-run enrichment: Ensure rich types are populated
2. Check matrix enrichment logs for warnings
3. Verify DOCX matrix has type columns filled

## Related Documentation

- [Rich Content Schema](RICH_CONTENT_SCHEMA.md)
- [Prompt Improvements](PROMPT_IMPROVEMENTS.md)
- [Multiple Matrix Templates](MULTIPLE_MATRIX_TEMPLATES.md)
