# CÁC CẢI TIẾN PROMPT - ĐỂ SINH CÂU HỎI TỰ NHIÊN HƠN

## 📋 Tổng quan

Đã cải thiện prompt cho cả **Trắc nghiệm (TN)** và **Đúng/Sai (DS)** để khắc phục các vấn đề:

- ❌ Câu hỏi công thức hóa, giống nhau
- ❌ Thiếu bối cảnh lịch sử cụ thể
- ❌ Đáp án cứng nhắc, giả tạo
- ❌ Giải thích đơn điệu, thiếu thông tin SGK

---

## 🎯 THAY ĐỔI CHÍNH

### 1. **Thay đổi Mindset - Từ "Chuyên gia AI" → "Giáo viên thực sự"**

**Trước:**

```
Bạn là chuyên gia biên soạn ngân hàng câu hỏi...
```

**Sau:**

```
Bạn là giáo viên Lịch sử lớp 12 có 15 năm kinh nghiệm...
Triết lý: "Câu hỏi tốt không phải là câu hỏi khó,
mà là câu hỏi giúp học sinh TƯ DUY và KẾT NỐI kiến thức"
```

**→ Tác động:** AI sẽ "nghĩ" như giáo viên, không chỉ là máy tạo câu hỏi

---

### 2. **Hướng dẫn Đa dạng hóa Phong cách**

#### Thêm phần "NGUYÊN TẮC VÀNG":

**🚫 TRÁNH:**

- "Điều nào sau đây đúng về..."
- "Theo SGK, nội dung nào..."
- Tất cả đáp án dài bằng nhau (giả tạo)

**✅ ƯU TIÊN:**

- Đặt trong BỐI CẢNH: "Năm 1945, khi Liên Xô giải phóng Đông Âu..."
- Dùng TÌNH HUỐNG: "Một học sinh nghiên cứu về NATO..."
- Hỏi về MỐI QUAN HỆ: "Tại sao việc... lại dẫn đến...?"

#### Phân bổ phong cách trong 1 đề:

- Câu trực tiếp: 30%
- Câu có ngữ cảnh: 40%
- Câu phân tích: 20%
- Câu đánh giá: 10%

**→ Tác động:** Tránh pattern giống nhau, câu hỏi đa dạng hơn

---

### 3. **Nghệ thuật tạo Distractor (Đáp án nhiễu)**

#### Thêm 4 kỹ thuật cụ thể:

1. **SAI THỜI GIAN/KHÔNG GIAN (30%)**

   - Đúng: "NATO thành lập 1949"
   - Sai hợp lý: "NATO thành lập 1945" (ngay sau CTTG2)

2. **ĐÚNG NHƯNG KHÔNG PHẢI TRỌNG TÂM (30%)**

   - Hỏi mục tiêu CHÍNH → đưa mục tiêu phụ làm nhiễu

3. **NHẦM LẪN KHÁI NIỆM GẦN (25%)**

   - "Toàn cầu hóa" vs "Khu vực hóa"
   - "NATO" vs "Var-sa-va"

4. **SAI BỐI CẢNH (15%)**
   - Đúng sự kiện nhưng sai giai đoạn/động cơ

**→ Tác động:** Distractor hợp lý, học sinh phải SUY NGHĨ mới phân biệt

---

### 4. **YÊU CẦU GIẢI THÍCH CHI TIẾT (QUAN TRỌNG NHẤT)**

#### Cấu trúc giải thích bắt buộc:

```
1. TẠI SAO ĐÁP ÁN NÀY ĐÚNG (50%):
   ✅ Dẫn chứng CỤ THỂ từ SGK:
   "Theo SGK Lịch sử 12, [tên bài], mục [số mục],
   trang [số trang], nội dung ghi rõ: '...'."

2. TẠI SAO CÁC ĐÁP ÁN KHÁC SAI (40%):
   - A sai vì: [lý do + so sánh với kiến thức đúng]
   - B sai vì: [chỉ ra điểm sai lệch]
   - C sai vì: [phân tích]

3. GỢI Ý MỞ RỘNG (10%):
   - Điểm dễ nhầm lẫn
   - Kiến thức liên quan
```

#### Ví dụ mẫu cụ thể:

**Giải thích**:

> "Theo SGK Lịch sử 12, **Bài 2** 'Trật tự thế giới hai cực I-an-ta và Chiến tranh lạnh', **mục 1.b** (**trang 15**), nội dung ghi rõ: 'Tổ chức Hiệp ước Bắc Đại Tây Dương (NATO) do Mỹ và các nước phương Tây thành lập năm 1949'.
>
> Các đáp án khác sai vì:
>
> - A sai: LHQ thành lập 1945, mục tiêu hòa bình chung
> - C sai: ASEAN thành lập 1967, tổ chức khu vực
> - D sai: Var-sa-va (1955) do Liên Xô thành lập
>
> Điểm dễ nhầm: Mốc thời gian LHQ (1945) vs NATO (1949)"

**→ Tác động:**

- Giải thích chi tiết, có thông tin tham chiếu SGK
- Phân tích TẠI SAO từng đáp án sai
- Chỉ ra điểm dễ nhầm lẫn

---

### 5. **Yêu cầu Metadata Sư phạm (Kết hợp Schema mới)**

AI phải điền các trường:

#### Cho Trắc nghiệm (TN):

1. **question_style**: factual / analytical / contextual / comparative / evaluative / application
2. **historical_context**: Mô tả ngữ cảnh nếu có
3. **pedagogical_purpose**: Tại sao ra câu hỏi này?
4. **bloom_taxonomy**: Remember / Understand / Apply / Analyze / Evaluate
5. **distractor_rationale**: Tại sao học sinh có thể chọn nhầm mỗi đáp án sai?

#### Cho Đúng/Sai (DS):

1. **source_type**: primary_source / historical_description / analytical_summary / contextual_scenario
2. **pedagogical_approach**: Cách tiếp cận sư phạm
3. **reasoning_type** (cho mỗi mệnh đề): direct / inference / knowledge / analysis
4. **statement_diversity_note**: Ghi chú về cách cân bằng 4 mệnh đề
5. **common_mistakes**: Điểm dễ nhầm cho từng mệnh đề

**→ Tác động:** AI phải SUY NGHĨ sâu hơn về từng câu hỏi

---

### 6. **Ví dụ "Tốt vs Tệ" cụ thể**

#### Thêm phần so sánh trực quan:

**❌ Câu hỏi TỆ:**

```
"Theo Hiến chương LHQ 1945, mục tiêu nào sau đây được chú trọng?"
→ Công thức, nhàm chán
```

**✅ Câu hỏi TỐT:**

```
"Ngày 24-10-1945, sau khi Hiến chương được 51 nước phê chuẩn,
tổ chức quốc tế nào chính thức ra đời?"
→ Có bối cảnh, tự nhiên
```

**→ Tác động:** AI có mẫu cụ thể để học theo

---

### 7. **Checklist trước khi Submit**

Thêm phần kiểm tra cuối:

```
✓ Đã đa dạng hóa phong cách? (không quá 3 câu liên tiếp cùng pattern)
✓ Đáp án có độ dài TỰ NHIÊN? (không cố tình cân bằng)
✓ Distractor hợp lý? (học sinh phải SUY NGHĨ)
✓ Explanation đã ghi: Bài, mục, trang SGK?
✓ Đã điền đầy đủ metadata?
✓ Mỗi đáp án sai có distractor_rationale?
```

**→ Tác động:** AI tự kiểm tra trước khi output

---

## 🔄 SO SÁNH TRƯỚC/SAU

### Giải thích đáp án:

**❌ TRƯỚC:**

```
"Theo nội dung sách giáo khoa, mục tiêu duy trì hòa bình
là cơ sở để thực hiện các mục tiêu khác."
```

**✅ SAU:**

```
"Theo SGK Lịch sử 12, Bài 1 'Liên Hợp Quốc',
mục 1.b (trang 8): 'Trong số các mục tiêu của Liên hợp quốc,
mục tiêu duy trì hoà bình và an ninh quốc tế được chú trọng
và là cơ sở để thực hiện các mục tiêu khác'.

Các đáp án khác sai vì:
- A, C, D đều là mục tiêu quan trọng nhưng KHÔNG phải
  là cơ sở cho các mục tiêu khác
- Theo Điều 1 Hiến chương, hòa bình là tiền đề để
  thực hiện hợp tác kinh tế, văn hóa, nhân đạo

Điểm dễ nhầm: Học sinh hay nhầm 'quan trọng nhất'
với 'là cơ sở'."
```

---

## 📊 KẾT QUẢ MONG ĐỢI

Sau khi áp dụng prompt mới, câu hỏi sinh ra sẽ:

✅ **Đa dạng phong cách** - không còn pattern lặp lại
✅ **Có bối cảnh** - gắn với tình huống lịch sử cụ thể
✅ **Tự nhiên** - như giáo viên thực sự ra đề
✅ **Distractor hợp lý** - học sinh phải tư duy mới phân biệt
✅ **Giải thích chi tiết** - có tham chiếu SGK rõ ràng (bài, mục, trang)
✅ **Metadata đầy đủ** - phục vụ phân tích và cải tiến sau này

---

## 🚀 HƯỚNG DẪN SỬ DỤNG

1. **Restart server** để load prompt mới
2. **Test với 5-10 câu** trước khi generate hàng loạt
3. **Kiểm tra chất lượng**:
   - Có đa dạng phong cách không?
   - Giải thích có ghi rõ bài/mục/trang không?
   - Metadata có đầy đủ không?
4. **Fine-tune** nếu cần (điều chỉnh tỷ lệ phong cách, ví dụ mẫu...)

---

## 📝 GHI CHÚ BỔ SUNG

- File được cập nhật:
  - `server/src/config/prompt/TN.txt`
  - `server/src/config/prompt/DS.txt`
- Schema đã được cải thiện trước đó: `server/src/services/schemas.py`
- **Quan trọng**: Prompt và Schema phải đồng bộ để AI hiểu và sử dụng đúng metadata mới

---

**Ngày cập nhật:** 16/12/2024
**Version:** 2.0 - Major improvements
