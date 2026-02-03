# Tích hợp tạo Chart riêng vào luồng chính

## 📋 Tóm tắt

Đã tích hợp cách tạo chart riêng (3 bước) vào luồng sinh câu hỏi chính với **cấu trúc helper functions riêng** để dễ bảo trì.

## 🗂️ Cấu trúc Helper Functions

### **Thư mục mới:**

```
server/src/services/generators/helpers/
├── __init__.py
└── chart_generation_helper.py
```

### **Các functions:**

1. **`get_chart_data_schema()`**
   - Trả về JSON schema cho chart data
   - Schema đơn giản, không nested

2. **`build_chart_generation_prompt()`**
   - Tạo prompt để AI sinh chart
   - **Lấy data từ `supplementary_materials`** (từ enriched_matrix)
   - Nếu rỗng → "Tìm kiếm dữ liệu từ Niên giám thống kê 2023, 2024"

3. **`build_question_with_chart_prompt()`**
   - Tạo instruction để thêm vào prompt chính
   - Yêu cầu AI tạo **câu hỏi liên quan trực tiếp đến chart**
   - AI chỉ reference chart_id, không tạo lại echarts

4. **`merge_chart_into_question()`**
   - Merge echarts từ charts_map vào câu hỏi
   - Xử lý cả type='chart' và 'mixed'

5. **`validate_chart_completeness()`**
   - Kiểm tra chart có đầy đủ xAxis.data, series.data không
   - Trả về (is_valid, error_message)

## 🎯 Cách hoạt động

### **BƯỚC 1: Tạo Chart Riêng**

```python
charts_list = self._generate_chart_separately(spec, num_charts)
```

- Lấy `supplementary_materials` từ spec
- Gọi AI với prompt từ helper
- Validate chart completeness
- Lưu vào `charts_map`

### **BƯỚC 2: AI tạo câu hỏi với chart_id**

- Prompt được thêm instruction từ helper:

  ```
  **BIỂU ĐỒ ĐÃ TẠO SẴN:**
  - chart_1: Dân số thành thị 2010-2021

  **CÂU HỎI PHẢI LIÊN QUAN TRỰC TIẾP ĐẾN CHART:**
  ✅ "Giai đoạn nào tăng nhanh nhất?"
  ❌ "ASEAN thành lập năm nào?" (không liên quan)
  ```

- AI chỉ trả về: `{type: 'chart', chart_id: 'chart_1'}`

### **BƯỚC 3: Merge Chart vào Question**

```python
q_data = merge_chart_into_question(q_data, charts_map)
```

- Tìm chart_id trong question_stem
- Merge echarts đầy đủ vào

## ✅ Cải tiến

### **1. Lấy data từ supplementary_materials**

```python
# Trong enriched_matrix JSON:
{
  "question_code": "C4",
  "rich_content_types": ["BD"],
  "supplementary_materials": "Dân số thành thị:\n2010: 26.5 triệu\n2015: 30.9 triệu..."
}
```

- Nếu có → AI dùng data này
- Nếu rỗng → AI search "Niên giám thống kê 2023, 2024"

### **2. Cấu trúc helper riêng**

- **Lợi ích:**
  - Dễ bảo trì/cập nhật
  - Tái sử dụng cho table, image
  - Test độc lập từng function
  - Code sạch hơn trong question_generator.py

### **3. Câu hỏi liên quan chart**

- **Prompt yêu cầu:**

  ```
  CÂU HỎI PHẢI LIÊN QUAN TRỰC TIẾP ĐẾN CHART:
  - Hỏi về xu hướng, tốc độ tăng/giảm
  - So sánh giữa các năm, chỉ số
  - Đáp án dựa trên SỐ LIỆU trong chart

  VÍ DỤ TỐT:
  ✅ "Giai đoạn nào tăng nhanh nhất?"
  ✅ "Tỉ lệ tăng trưởng trung bình là bao nhiêu?"

  VÍ DỤ XẤU:
  ❌ "ASEAN thành lập năm nào?" (không dùng chart)
  ```

### **4. Validation**

- Check chart completeness trước khi merge
- Raise error nếu thiếu xAxis.data, series.data
- Log chi tiết để debug

## 📝 Log Output

```
🔄 STEP 1: Tạo 2 chart riêng...
   📄 Có tài liệu bổ sung: 350 chars
✅ Đã tạo 2 chart đầy đủ
   - chart_1: Dân số thành thị 2010-2021
   - chart_2: Tỉ trọng kinh tế Nhà nước

🔄 STEP 3: Merging charts vào 2 câu hỏi...
   ✅ Merged chart vào câu hỏi C4
   ✅ Merged chart vào câu hỏi C5
```

## 🧪 Test

- [test_chart_only_schema.py](../test_chart_only_schema.py) - Simple chart
- [test_complex_chart.py](../test_complex_chart.py) - Complex chart (dual yAxis, combo)

## 🚀 TODO tiếp theo

- [ ] Test với ma trận thật có 'BD' type và supplementary_materials
- [ ] Áp dụng helper pattern cho 'BK' (table)
- [ ] Áp dụng cho 'HA' (image)
- [ ] Add unit tests cho helpers
