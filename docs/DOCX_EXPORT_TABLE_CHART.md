# Xuất DOCX với Bảng và Chart

## Tính năng mới

### 1. Xuất Bảng (Table)

- ✅ **Không tô màu nền**: Bỏ tô màu nền trong bảng để gọn gàng hơn
- ✅ **Bold header**: Chỉ in đậm text header để phân biệt
- ✅ **Border đơn giản**: Sử dụng `Table Grid` style thay vì `Light Grid Accent 1`

### 2. Xuất Chart (Biểu đồ)

- ✅ **ECharts → PNG**: Render ECharts config thành ảnh PNG
- ✅ **Chèn vào DOCX**: Tự động chèn ảnh PNG vào document
- ✅ **Kích thước tối ưu**: 5.5 inches width, tự động scale height
- ✅ **Fallback**: Nếu không có playwright, hiển thị placeholder text

## Cài đặt

```bash
# Cài đặt thư viện
pip install playwright pillow

# Cài đặt Chromium browser
playwright install chromium
```

## Sử dụng

```python
from services.exporters.docx_generator import DocxGenerator

# Tạo generator
generator = DocxGenerator(verbose=True)

# Xuất file DOCX từ JSON
generator.generate_questions_document(
    json_data="path/to/questions.json",
    output_path="output.docx"
)
```

## Demo

File test: [`test_export_with_table_chart.py`](../test_export_with_table_chart.py)

```bash
python test_export_with_table_chart.py
```

## Kết quả

**Trước:**

- Bảng: Tô màu nền xanh lá/xanh dương (Light Grid Accent 1)
- Chart: Chỉ hiển thị placeholder text

**Sau:**

- ✅ Bảng: Không tô màu, chỉ bold header, border đơn giản
- ✅ Chart: Render thành ảnh PNG chất lượng cao và chèn vào DOCX

## Chi tiết kỹ thuật

### Render Chart

1. Tạo file HTML tạm với ECharts config
2. Sử dụng Playwright để load HTML và render chart
3. Screenshot phần tử `#chart` thành PNG
4. Chèn PNG vào DOCX với `run.add_picture()`
5. Cleanup: Xóa file HTML và PNG tạm

### Performance

- Mỗi chart mất ~1-2 giây để render
- File size tăng ~20-30KB cho mỗi chart
- Chromium headless mode: không hiển thị cửa sổ browser

## Files thay đổi

- [`server/src/services/exporters/docx_generator.py`](../server/src/services/exporters/docx_generator.py)
  - Thêm hàm `_render_chart_to_image()` để render ECharts → PNG
  - Cập nhật `_add_inline_table()`: Bỏ tô màu nền, chỉ bold header
  - Cập nhật `_add_inline_chart()`: Chèn ảnh PNG thay vì placeholder
  - Thêm import: `playwright`, `PIL`, `base64`, `BytesIO`

- [`requirements-build.txt`](../requirements-build.txt)
  - Thêm: `playwright==1.41.0`
  - Thêm: `pillow>=10.0.0`

## Troubleshooting

### Lỗi: "Playwright not available"

→ Cài đặt: `pip install playwright && playwright install chromium`

### Chart hiển thị placeholder thay vì ảnh

→ Kiểm tra playwright đã cài đúng: `playwright --version`

### Lỗi timeout khi render chart

→ Tăng timeout trong `page.wait_for_function()` (mặc định 5000ms)

---

**Cập nhật:** 2026-02-03
**Tác giả:** GitHub Copilot
