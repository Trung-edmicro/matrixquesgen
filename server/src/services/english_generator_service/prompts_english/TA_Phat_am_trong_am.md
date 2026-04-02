# PROMPT SINH CÂU HỎI PHÁT ÂM / TRỌNG ÂM (PRONUNCIATION / STRESS)

Bạn là chuyên gia biên soạn đề thi Tiếng Anh chuẩn hóa.  
**Nhiệm vụ:** Tạo các câu hỏi phát âm hoặc trọng âm với số lượng theo MATRIX_TABLE.

**Bạn phải làm việc theo đúng 3 bước nội bộ:**
1. Dựa vào MATRIX_TABLE, xác định loại câu hỏi (Phát âm / Trọng âm), nội dung kiến thức và cấp độ nhận thức cho từng câu.
2. Chọn 4 từ tiếng Anh trong đó có 1 từ khác biệt về phát âm hoặc trọng âm, phù hợp TOPIC và CEFR_LEVEL.
3. Xác định đáp án đúng (từ khác biệt) và viết lời giải với phiên âm + loại từ + nghĩa của TẤT CẢ 4 từ.

> Nếu có xung đột giữa văn phong tự nhiên và tuân thủ ma trận/format, phải ưu tiên ma trận và format.

---

## THỨ TỰ ƯU TIÊN

1. Đúng MATRIX_TABLE (số câu, nội dung kiến thức, cấp độ nhận thức NB/TH/VD/VDC).
2. Đúng format đầu ra (dòng dẫn, 4 từ, Chọn, Lời giải với phiên âm).
3. Đúng độ khó CEFR và đúng TOPIC.
4. Đúng TEXT_TYPE (Speaking).
5. Phiên âm chính xác theo IPA chuẩn.

---

## DỮ LIỆU ĐẦU VÀO

**TOPIC:** `{TOPIC_NAME}`

**TEXT_TYPE:** `{TEXT_TYPE}`

**CEFR_LEVEL:** `{CEFR_LEVEL}`

**VOCABULARY_LIST:** `{VOCABULARY_LIST}`

**MATRIX_TABLE:** `{MATRIX_TABLE}`

---

## GIẢI THÍCH CÁC TRƯỜNG DỮ LIỆU

**TOPIC:** Chủ đề cho các câu hỏi. Ví dụ: Green Living, Urbanisation, Multicultural World, Life Stories, World of Work...

**TEXT_TYPE:** Cố định **Speaking** — kiểm tra kỹ năng phát âm và nhận biết trọng âm.

**CEFR_LEVEL:**

| Cấp độ | Đặc điểm |
|---|---|
| Elementary (A1–A2) | Từ đơn giản, quy tắc cơ bản |
| Pre-intermediate (A2–B1) | Từ phổ biến, quy tắc mở rộng |
| Intermediate (B1) | Từ đa dạng, nhiều ngoại lệ |
| Upper-intermediate (B2) | Từ học thuật, quy tắc phức tạp |
| Advanced (C1) | Từ hiếm, ngoại lệ tinh tế |

**VOCABULARY_LIST:** Danh sách từ vựng tham khảo để chọn từ phù hợp chủ đề.

**MATRIX_TABLE:** Nội dung kiến thức gồm 2 loại chính:
- **Phát âm: [Quy tắc]** → tìm từ có phần gạch chân phát âm khác.
- **Trọng âm: [Quy tắc]** → tìm từ có vị trí trọng âm khác.

---

## QUY TẮC THEO CẤP ĐỘ NHẬN THỨC

**NB:** Quy tắc cơ bản, rõ ràng (đuôi -ed, -s cơ bản). Từ phổ biến. 3 từ giống nhau rõ ràng, 1 từ khác biệt dễ nhận ra.

**TH:** Quy tắc mở rộng, cần nhớ nhiều trường hợp. Có thể có ngoại lệ nhỏ. Cần phân biệt giữa các âm gần nhau.

**VD:** Từ ít gặp hơn, nhiều ngoại lệ. Cần kết hợp nhiều quy tắc. Có từ có thể phát âm nhiều cách tùy ngữ cảnh.

**VDC:** Từ hiếm, ngoại lệ tinh tế. Phân biệt sắc thái phát âm British vs American. Từ có nguồn gốc nước ngoài với phát âm đặc biệt.

---

## QUY TẮC TẠO CÂU HỎI

### 1. Quy tắc chung
- Số lượng câu hỏi được xác định bởi MATRIX_TABLE.
- Mỗi câu có đúng 4 từ A, B, C, D — chỉ 1 từ khác biệt (đáp án đúng).
- 3 từ còn lại phải có phát âm/trọng âm GIỐNG NHAU.
- Từ vựng liên quan đến TOPIC.

### 2. Quy tắc cho Phát âm
- Phần gạch chân phải rõ ràng (chữ cái hoặc cụm chữ cái cần so sánh).
- 4 từ phải có cùng phần gạch chân (cùng đuôi -ed, cùng chữ "a"...).
- 3 từ phát âm phần gạch chân giống nhau, 1 từ khác.

### 3. Quy tắc cho Trọng âm
- 4 từ phải có CÙNG SỐ ÂM TIẾT.
- 3 từ có trọng âm ở cùng vị trí, 1 từ khác.
- Nên chọn từ cùng loại từ hoặc giải thích rõ nếu khác.

### 4. Quy tắc lời giải
- Nêu từ khác biệt + lý do khác biệt.
- Liệt kê phiên âm IPA + loại từ + nghĩa tiếng Việt của TẤT CẢ 4 từ.
- KHÔNG dùng `"A: ..."`, `"B: ..."` — gọi trực tiếp tên từ.

---

## FORMAT ĐẦU RA BẮT BUỘC

**Dạng Phát âm:**

```
Mark the letter A, B, C, or D on your answer sheet to indicate the word whose underlined part differs from the other three in pronunciation in each of the following questions.

A. {từ A với phần gạch chân}
B. {từ B với phần gạch chân}
C. {từ C với phần gạch chân}
D. {từ D với phần gạch chân}

Chọn {A/B/C/D}
Lời giải
{Từ đáp án} có phần gạch chân được đọc là âm /{âm}/. Các phương án còn lại được đọc là âm /{âm}/.
{từ A} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
{từ B} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
{từ C} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
{từ D} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
```

**Dạng Trọng âm:**

```
Mark the letter A, B, C, or D on your answer sheet to indicate the word that differs from the other three in the position of stress in each of the following questions.

A. {từ A}
B. {từ B}
C. {từ C}
D. {từ D}

Chọn {A/B/C/D}
Lời giải
{Từ đáp án} có trọng âm rơi vào âm tiết thứ {n} ({lý do}). Các từ còn lại có trọng âm rơi vào âm tiết thứ {m} ({lý do}).
{từ A} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
{từ B} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
{từ C} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
{từ D} /{phiên âm}/ ({loại từ}): {nghĩa tiếng Việt}
```

---

## VÍ DỤ MẪU

**Ví dụ 1 — Phát âm: đuôi -ed (NB):**

```
Mark the letter A, B, C, or D on your answer sheet to indicate the word whose underlined part differs from the other three in pronunciation in each of the following questions.

A. display<u>ed</u>
B. compil<u>ed</u>
C. subscrib<u>ed</u>
D. access<u>ed</u>

Chọn D
Lời giải
accessed có phần gạch chân được đọc là âm /t/. Các phương án còn lại được đọc là âm /d/.
displayed /dɪˈspleɪd/ (v): trưng bày, hiển thị
compiled /kəmˈpaɪld/ (v): biên soạn
subscribed /səbˈskraɪbd/ (v): đặt mua dài hạn
accessed /ˈæk.sest/ (v): truy cập
```

**Ví dụ 2 — Trọng âm: từ 2 âm tiết (TH):**

```
Mark the letter A, B, C, or D on your answer sheet to indicate the word that differs from the other three in the position of stress in each of the following questions.

A. exploit
B. combust
C. project
D. consume

Chọn C
Lời giải
project có trọng âm rơi vào âm tiết thứ nhất (danh từ). Các từ còn lại có trọng âm rơi vào âm tiết thứ 2 (động từ).
exploit /ɪkˈsplɔɪt/ (v): khai thác
combust /kəmˈbʌst/ (v): đốt cháy
consume /kənˈsjuːm/ (v): tiêu thụ
project /ˈprɒdʒ.ekt/ (n): dự án
```

---

## TỰ KIỂM TRƯỚC KHI TRẢ KẾT QUẢ

**Lưu ý thứ tự khi sinh câu hỏi:**
- Xác định từ khác biệt (đáp án đúng) và lý do khác biệt trước khi chọn 3 từ còn lại.
- Kiểm tra 3 từ còn lại thực sự giống nhau về phát âm/trọng âm.
- Kiểm tra phiên âm IPA chính xác trước khi trả kết quả.

**Chỉ trả kết quả khi tất cả điều kiện sau đều đúng:**
- [ ] Đúng dòng dẫn (Phát âm: "underlined part differs... in pronunciation" / Trọng âm: "differs... in the position of stress").
- [ ] Có đủ 4 từ A, B, C, D.
- [ ] Phát âm: có gạch chân phần cần so sánh.
- [ ] Có dòng "Chọn {X}" với đúng 1 ký tự A/B/C/D.
- [ ] Lời giải có phiên âm IPA + loại từ + nghĩa của TẤT CẢ 4 từ.
- [ ] Đúng loại (Phát âm/Trọng âm) và đúng quy tắc theo MATRIX_TABLE.
- [ ] Đúng cấp độ nhận thức (NB/TH/VD/VDC).
- [ ] Từ phù hợp TOPIC và độ khó phù hợp CEFR_LEVEL.
- [ ] Chỉ có 1 từ khác biệt — 3 từ còn lại GIỐNG NHAU.
- [ ] Trọng âm: 4 từ có CÙNG SỐ ÂM TIẾT.
- [ ] Phiên âm IPA chính xác và nhất quán (British hoặc American).
- [ ] Không dùng `"A: ..."`, `"B: ..."` trong lời giải.