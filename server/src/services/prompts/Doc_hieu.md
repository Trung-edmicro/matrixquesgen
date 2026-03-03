# PROMPT TỔNG HỢP: SINH BÀI ĐỌC + CÂU HỎI + LỜI GIẢI
# (Reading Comprehension - All in One)

---

# ⛔⛔⛔ CRITICAL WARNING - ĐỌC TRƯỚC KHI BẮT ĐẦU ⛔⛔⛔

## QUY TẮC CHỐNG SAO CHÉP (KHÔNG ĐƯỢC VI PHẠM)

```
┌─────────────────────────────────────────────────────────────────┐
│  ❌ TUYỆT ĐỐI KHÔNG sao chép từ SOURCE quá 8 TỪ LIÊN TIẾP      │
│  ❌ Kể cả khi chỉ đổi 1-2 từ = VẪN VI PHẠM                     │
│  ❌ Giữ nguyên cấu trúc câu, chỉ thay từ đồng nghĩa = VI PHẠM  │
└─────────────────────────────────────────────────────────────────┘
```

### ❌ VÍ DỤ VI PHẠM (PHẢI TRÁNH):

```
SOURCE: "Smaller communities often lack the financial resources and 
technical expertise to digitise their heritage"

❌ SAI (12 từ giống): 
"Smaller communities often lack the financial resources and technical 
expertise to digitise their local history"
→ Chỉ đổi "heritage" → "local history" = VẪN VI PHẠM!

❌ SAI (10 từ giống):
"Small communities often lack the financial resources and technical 
expertise to preserve their heritage"  
→ Chỉ đổi "Smaller" → "Small", "digitise" → "preserve" = VẪN VI PHẠM!
```

### ✅ CÁCH VIẾT LẠI ĐÚNG:

```
SOURCE: "Smaller communities often lack the financial resources and 
technical expertise to digitise their heritage"

✅ ĐÚNG (viết lại hoàn toàn ~90%):
"Many small groups do not have enough money or skills to create 
digital copies of their traditions."

Phân tích:
- "Smaller communities" → "Many small groups" (đổi cụm)
- "often lack" → "do not have enough" (đổi cấu trúc)
- "financial resources" → "money" (đơn giản hóa)
- "technical expertise" → "skills" (đơn giản hóa)
- "digitise their heritage" → "create digital copies of their traditions" (đổi hoàn toàn)
```

### 📋 KỸ THUẬT VIẾT LẠI (PHẢI ÁP DỤNG)

| Kỹ thuật | SOURCE | VIẾT LẠI |
|----------|--------|----------|
| **Đổi cấu trúc câu** | "X has transformed Y" | "Y has changed because of X" |
| **Đổi chủ động ↔ bị động** | "Museums preserve artifacts" | "Artifacts are kept safe by museums" |
| **Tách câu dài** | "A, B, and C contribute to D" | "A helps D. B and C also play a role." |
| **Gộp câu ngắn** | "X is important. Y depends on X." | "Y depends on X, which is important." |
| **Đổi từ vựng + cấu trúc** | "rely on physical items" | "depend on objects you can touch" |
| **Đảo thứ tự thông tin** | "Because A, B happens" | "B happens. The reason is A." |

---

## TỔNG QUAN

**Mục tiêu:** Từ tư liệu gốc (SOURCE), sinh ra bộ đề đọc hiểu hoàn chỉnh gồm:
1. Bài đọc viết lại (PASSAGE) với các mỏ neo
2. Bảng kiểm tra mỏ neo
3. Câu hỏi trắc nghiệm + Đáp án
4. Lời giải chi tiết

**Quy trình:**
1. Trích KEY FACTS từ tư liệu gốc
2. Tạo OUTLINE mới (đổi bố cục)
3. Viết lại PASSAGE với các "mỏ neo" cho từng dạng câu hỏi
4. Sinh câu hỏi theo ma trận (đúng dạng + đúng cấp độ)
5. Viết lời giải chi tiết cho từng câu
6. **⚠️ TỰ KIỂM TRA: Rà soát TỪNG CÂU trong PASSAGE, đảm bảo KHÔNG có cụm > 8 từ giống SOURCE**

---

# ═══════════════════════════════════════════════════════════════
# DỮ LIỆU ĐẦU VÀO
# ═══════════════════════════════════════════════════════════════

### 1. Thông tin chung
```
Phần: Đọc hiểu - trả lời ({NUM_QUESTIONS} câu)
Topic: {TOPIC}
Độ dài: {TARGET_WORD_COUNT}w
```

**Ví dụ:**
```
Phần: Đọc hiểu - trả lời (8 câu)
Topic: Languages
Độ dài: 281w
```

### 2. CEFR mục tiêu cho bài đọc
```
{CEFR_LEVEL}
```
*(B1 / B2 / C1)*

### 3. Mẫu từ vựng tham chiếu (CHỈ THAM CHIẾU, KHÔNG BẮT BUỘC DÙNG)
```
{VOCAB_SAMPLE}
```

### 4. Ma trận câu hỏi
```
{MATRIX_ROWS_TEXT}
```

**Lưu ý về ma trận:**
- Chỉ cần **đủ các dạng câu hỏi** theo ma trận
- **Không bắt buộc** thứ tự câu hỏi theo ma trận
- **Không cần** chỉ định đoạn mục tiêu cho từng câu

**Ví dụ ma trận:**

| Nội dung | NB | TH | VD | VDC |
|----------|----|----|----|----|
| NOT mentioned | 1 | | | |
| Câu hỏi từ vựng - đồng nghĩa | | | 1 | |
| Câu hỏi từ vựng - trái nghĩa | | 1 | | |
| Tham chiếu | | 1 | | |
| Best paraphrased (câu trong bài) | | | 1 | |
| True/False | | 1 | | |
| Tìm đoạn phù hợp | | | 1 | |
| Tìm đoạn phù hợp | | | | 1 |

→ Tổng: 8 câu hỏi
→ Bài đọc cần cài đủ mỏ neo cho 8 dạng câu hỏi trên

### 5. Tư liệu gốc (SOURCE)
```
{SOURCE_TEXT}
```

---

# ═══════════════════════════════════════════════════════════════
# RÀNG BUỘC BẮT BUỘC
# ═══════════════════════════════════════════════════════════════

## A. Ràng buộc nội dung

| # | Ràng buộc | Mô tả |
|---|-----------|-------|
| 1 | **Không thêm thông tin** | Không thêm bất kỳ thông tin nào ngoài những gì có trong SOURCE |
| 2 | **⚠️ KHÔNG SAO CHÉP NGUYÊN VĂN** | **TUYỆT ĐỐI** không được sao chép từ SOURCE quá **8 từ liên tiếp** - kể cả khi chỉ đổi 1-2 từ! |
| 3 | **⚠️ KHÁC BIỆT TỐI THIỂU 60%** | Bài viết lại phải **KHÁC SOURCE ít nhất 60%** về từ vựng và cấu trúc câu |
| 4 | **Đổi bố cục** | Bố cục bài viết lại phải **khác SOURCE** (sắp xếp lại trình tự ý/đoạn) |
| 5 | **Đúng CEFR** | Ngôn ngữ phù hợp CEFR mục tiêu. VOCAB_SAMPLE dùng để tham chiếu độ khó |
| 6 | **Cấu trúc đoạn** | Bài đọc phải có **3–4 đoạn** với nhãn [P1], [P2], [P3], [P4] |
| 7 | **Tránh thuật ngữ hiếm** | Ưu tiên câu rõ ràng, mạch logic; tránh thuật ngữ học thuật vượt CEFR |

---

### ⚠️ CÁCH ĐẠT ĐƯỢC 60% KHÁC BIỆT

**60% khác biệt = Giữ lại NỘI DUNG (facts) nhưng thay đổi CÁCH DIỄN ĐẠT**

| Yếu tố cần thay đổi | Ví dụ |
|---------------------|-------|
| **Từ vựng** | "preserve" → "protect", "safeguard", "maintain" |
| **Cấu trúc câu** | Active ↔ Passive, Simple ↔ Complex |
| **Thứ tự thông tin** | Đảo vị trí các ý trong câu/đoạn |
| **Cách diễn đạt** | "X causes Y" → "Y results from X" → "Y is a consequence of X" |
| **Độ dài câu** | Tách câu dài → 2 câu ngắn, hoặc gộp 2 câu ngắn → 1 câu dài |

**Ví dụ đạt 60% khác biệt:**

```
SOURCE (100%):
"The preservation of cultural heritage has traditionally relied on physical 
artefacts such as manuscripts, monuments and works of art."

VIẾT LẠI (đạt ~70% khác biệt):
"For centuries, protecting cultural traditions meant keeping physical objects 
safe – old documents, historic buildings, and paintings."

Phân tích:
- "preservation" → "protecting" (đổi từ)
- "cultural heritage" → "cultural traditions" (đổi từ)
- "traditionally relied on" → "For centuries... meant" (đổi cấu trúc)
- "artefacts such as" → "physical objects... –" (đổi cách liệt kê)
- "manuscripts, monuments, works of art" → "old documents, historic buildings, paintings" (đổi từ)
```

**Ví dụ KHÔNG đạt 60% (chỉ ~20% khác biệt):**

```
SOURCE:
"The preservation of cultural heritage has traditionally relied on physical 
artefacts such as manuscripts, monuments and works of art."

VIẾT LẠI SAI (chỉ đổi 1-2 từ):
"The preservation of cultural heritage has traditionally depended on physical 
artefacts such as manuscripts, monuments and artworks."

→ Chỉ đổi "relied" → "depended", "works of art" → "artworks" = KHÔNG ĐẠT!
```

---

### ⚠️ VÍ DỤ VI PHẠM SAO CHÉP (PHẢI TRÁNH):

```
SOURCE: "Smaller communities often lack the financial resources and technical expertise to digitise their heritage"

❌ SAI: "Smaller communities often lack the financial resources and technical expertise to digitise their local history"
→ 12 từ liên tiếp giống nhau! Chỉ đổi "heritage" → "local history" = VẪN VI PHẠM

✅ ĐÚNG: "Many small communities do not have enough money or skills to create digital copies of their traditions"
→ Viết lại hoàn toàn, giữ ý nghĩa, không trùng > 8 từ, đạt ~80% khác biệt
```

## B. Ràng buộc CHỐNG MƠ HỒ (Bắt buộc)

**Khi dùng đại từ tham chiếu (it/they/this/these/which/that):**

| Yêu cầu | Mô tả |
|---------|-------|
| **1 antecedent duy nhất** | Đảm bảo chỉ có 1 antecedent hợp lệ và rõ ràng |
| **Vị trí antecedent** | Antecedent phải là 1 noun phrase cụ thể xuất hiện **ngay trước** đại từ (cùng câu hoặc câu liền kề) |
| **Tránh mơ hồ số** | Không để 2 danh từ cùng số ít/số nhiều cạnh nhau khiến đại từ có thể refer cả hai |

**Ví dụ:**
```
❌ SAI: "The plan includes a monitoring system. It updates…" 
   (it = plan hay system đều có thể đúng)

✅ ĐÚNG: "The monitoring system updates…" 
   (it chỉ có thể là monitoring system)
```

**Sau khi viết xong PASSAGE:** Tự rà soát tất cả đại từ và chỉnh sửa mọi chỗ có khả năng tham chiếu mơ hồ.

---

## C. Ràng buộc VĂN PHONG TỰ NHIÊN (Tránh dấu hiệu AI)

### ❌ DẤU HIỆU VĂN PHONG AI - PHẢI TRÁNH

| Loại | Dấu hiệu AI | Ví dụ sai |
|------|-------------|-----------|
| **Mở đầu sáo rỗng** | Câu mở đầu chung chung, vô nghĩa | "In today's rapidly changing world...", "In recent years...", "It is widely known that..." |
| **Từ nối quá nhiều** | Mỗi câu đều có linking word | "Furthermore... Moreover... Additionally... However... Nevertheless..." |
| **Cấu trúc quá hoàn hảo** | Mỗi đoạn đều: Topic → Support → Conclusion | Đoạn nào cũng y hệt template |
| **Từ vựng quá formal** | Toàn từ học thuật, không có từ đời thường | "utilize" thay vì "use", "commence" thay vì "start" |
| **Passive voice quá nhiều** | Câu nào cũng bị động | "It is believed that...", "It has been shown that..." |
| **Kết luận sáo rỗng** | Kết bằng câu chung chung | "In conclusion...", "To sum up...", "All in all..." |
| **Liệt kê 3 items** | Luôn liệt kê đúng 3 thứ | "X, Y, and Z" lặp đi lặp lại |
| **Câu dài đều nhau** | Mọi câu đều 20-25 từ | Không có variation |
| **Quá tích cực/lạc quan** | Mọi thứ đều "significant", "crucial", "vital" | "This is extremely important...", "This plays a crucial role..." |

---

### ✅ VĂN PHONG TỰ NHIÊN - NÊN LÀM

| Kỹ thuật | Mô tả | Ví dụ đúng |
|----------|-------|------------|
| **Mở đầu cụ thể** | Đi thẳng vào vấn đề, có chi tiết | "Museums around the world are turning to digital tools to preserve their collections." |
| **Từ nối vừa đủ** | Chỉ dùng khi cần thiết, không câu nào cũng có | Bỏ bớt "Furthermore", "Moreover" - để câu tự kết nối bằng logic |
| **Độ dài câu đa dạng** | Xen kẽ câu ngắn (8-12 từ) và câu dài (18-25 từ) | "This creates a problem. However, many organizations have found creative solutions that balance tradition with innovation." |
| **Active voice ưu tiên** | Chủ ngữ rõ ràng, hành động trực tiếp | "Museums share their collections" thay vì "Collections are shared by museums" |
| **Từ vựng tự nhiên** | Pha trộn từ formal và informal phù hợp CEFR | "help" thay vì "facilitate", "show" thay vì "demonstrate" |
| **Kết thúc tự nhiên** | Không dùng "In conclusion", kết bằng ý cuối cùng | "The challenge now is finding the right balance." |
| **Chi tiết cụ thể** | Có ví dụ, con số, tên cụ thể | "a student in London can virtually visit the Louvre" |
| **Giọng văn nhất quán** | Không nhảy giữa formal và casual | Giữ một tone xuyên suốt |

---

### 📝 VÍ DỤ SO SÁNH

**❌ Văn phong AI (SAI):**
```
In today's rapidly evolving digital landscape, the preservation of cultural heritage 
has become increasingly significant. Furthermore, technological advancements have 
revolutionized the way institutions safeguard valuable artefacts. Moreover, this 
transformation has profound implications for future generations. It is widely 
acknowledged that digital tools play a crucial role in this process.
```

**✅ Văn phong tự nhiên (ĐÚNG):**
```
Museums are changing how they protect history. Instead of relying only on glass 
cases and climate control, many now create digital copies of their most precious 
items. A visitor in Tokyo can explore ancient Greek sculptures. A researcher in 
Brazil can study medieval manuscripts without traveling to Europe. This shift 
brings both opportunities and challenges.
```

**Phân tích sự khác biệt:**

| Tiêu chí | Văn AI | Văn tự nhiên |
|----------|--------|--------------|
| Mở đầu | "In today's rapidly evolving..." (sáo rỗng) | "Museums are changing..." (cụ thể) |
| Từ nối | "Furthermore... Moreover..." (quá nhiều) | Ít từ nối, logic tự nhiên |
| Độ dài câu | Đều nhau (~20 từ) | Đa dạng (5-20 từ) |
| Chi tiết | Chung chung "institutions", "artefacts" | Cụ thể "Tokyo", "Greek sculptures" |
| Giọng văn | Quá formal, xa cách | Gần gũi, dễ đọc |

---

### 🎯 CHECKLIST VĂN PHONG TRƯỚC KHI HOÀN THÀNH

Sau khi viết xong PASSAGE, tự kiểm tra:

- [ ] Có câu nào bắt đầu bằng "In today's...", "In recent years...", "It is important..."? → **XÓA/VIẾT LẠI**
- [ ] Có quá nhiều "Furthermore", "Moreover", "Additionally" không? → **BỎ BỚT**
- [ ] Có dùng "In conclusion", "To sum up" ở cuối không? → **VIẾT LẠI**
- [ ] Độ dài câu có đa dạng không? → **THÊM CÂU NGẮN 8-12 từ**
- [ ] Có chi tiết cụ thể (tên, số, ví dụ) hay toàn khái niệm chung? → **THÊM CHI TIẾT**
- [ ] Đọc to lên có nghe tự nhiên không? → **NẾU KHÔNG → VIẾT LẠI**

---

# ═══════════════════════════════════════════════════════════════
# CÁC DẠNG CÂU HỎI VÀ "MỎ NEO" CẦN CÀI
# ═══════════════════════════════════════════════════════════════

## (1) NOT MENTIONED (Negative factual)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- Which of the following is **NOT mentioned** in paragraph X as …?
- Which of the following is **NOT stated** in paragraph X?
- According to paragraph X, all of the following are true **EXCEPT** ____.
- The passage mentions all of the following **EXCEPT** ____.

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **1 câu liệt kê đúng 3 mục** cùng loại
- Dạng gợi ý: "... such as A, B, and C." / "... including A, B, and C."
- A/B/C là danh từ/cụm danh từ rõ ràng
- **Tuyệt đối không nhắc** một mục thứ tư D trong đoạn đó
- D phải cùng trường nghĩa để làm nhiễu hợp lý
- Tốt nhất A/B/C nằm trong 1 câu (hoặc 2 câu liên tiếp) để dễ scan

**Ví dụ mỏ neo:**
```
[P1] ... Renewable energy sources such as solar power, wind energy, and hydroelectricity 
have become increasingly popular...
→ Câu hỏi: NOT mentioned? → D. nuclear energy (cùng trường nghĩa nhưng không có trong bài)
```

---

## (2) VOCABULARY – SYNONYM (in context)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- The word "X" in paragraph Y **can be best replaced by** ____.
- The word "X" in paragraph Y **mostly means** ____.
- The word "X" in paragraph Y **is closest in meaning to** ____.
- What does the word "X" in paragraph Y **mean**?

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **1 từ/cụm từ "đủ ngữ cảnh"** (ưu tiên verb/adj)
- Nghĩa được **khóa chắc** bởi câu
- Từ được hỏi phải **khó hơn hoặc ngang** 4 phương án
- **Tránh** từ đa nghĩa (set/get/make/do) hoặc ngữ cảnh không khóa nghĩa

**⚠️ CÁCH ĐÁNH DẤU TRONG PASSAGE:**
- **BÔI ĐẬM** từ sẽ hỏi synonym bằng `**từ**`
- Ví dụ: `Technology has completely **transformed** how the public engages with culture.`

**Ví dụ mỏ neo:**
```
[P1] ... The new policy has significantly **boosted** economic growth in the region...
→ "boosted" = increased / enhanced / improved / raised
→ Ngữ cảnh "economic growth" khóa nghĩa = tăng lên
```

---

## (3) VOCABULARY – ANTONYM (in context)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- The word "X" in paragraph Y is **OPPOSITE in meaning to** ____.
- The word "X" in paragraph Y **means the opposite of** ____.
- Which of the following is **OPPOSITE in meaning to** "X" in paragraph Y?

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **1 từ/cụm từ thể hiện rõ hướng nghĩa**
  - Tăng/giảm; Mở rộng/thu hẹp; Cho phép/ngăn cản...
- Ngữ cảnh phải **khóa nghĩa** để antonym rõ ràng và không gây tranh cãi
- Khi ra đề, chỉ **1 option** là trái nghĩa "chuẩn"

**⚠️ CÁCH ĐÁNH DẤU TRONG PASSAGE:**
- **BÔI ĐẬM** từ sẽ hỏi antonym bằng `**từ**`
- Ví dụ: `This approach **accelerates** the learning process.`

**Ví dụ mỏ neo:**
```
[P2] ... This approach **accelerates** the learning process...
→ "accelerates" ≠ slows down / decelerates
→ Ngữ cảnh "learning process" + "accelerates" = nhanh lên → antonym = chậm lại
```

---

## (4) REFERENCE (đại từ tham chiếu)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- The word "it/they/this" in paragraph X **refers to** ____.
- What does "it/they/this" in paragraph X **refer to**?
- The word "which" in paragraph X **refers to** ____.

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **ít nhất 1 đại từ** để hỏi
- Antecedent phải là **1 noun phrase cụ thể** đứng ngay trước
- Chỉ có **1 khả năng hợp lệ** (tuân thủ ràng buộc chống mơ hồ)

**Công thức viết an toàn:**
```
"Noun phrase X ...; it ..." 
hoặc 
"Noun phrase X .... It ..."
```

**Ví dụ mỏ neo:**
```
[P3] ... The carbon tax was introduced in 2020. It has successfully reduced emissions by 15%...
→ "It" refers to = The carbon tax (noun phrase duy nhất phù hợp)
```

---

## (5) BEST PARAPHRASED (câu trong bài)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- Which of the following **best paraphrases** the underlined sentence in paragraph X?
- Which of the following has the **closest meaning to** the underlined sentence?
- The underlined sentence in paragraph X **means that** ____.
- What does the underlined sentence in paragraph X **mean**?

---

### ⚠️⚠️⚠️ LƯU Ý CỰC KỲ QUAN TRỌNG ⚠️⚠️⚠️

**BẮT BUỘC PHẢI GẠCH CHÂN câu ứng viên ngay trong PASSAGE!**

Nếu không gạch chân → Không thể ra được câu hỏi dạng này → **THIẾU MỎ NEO**

**Cách đánh dấu gạch chân trong PASSAGE:**
```
[P2] ... Advanced tools like 3D scanning allow visitors to admire historical sites. 
<u>This innovation not only provides wider access but also raises standards of 
accuracy in recording human history.</u> Many researchers have praised...
```

Hoặc dùng markdown:
```
[P2] ... Advanced tools like 3D scanning allow visitors to admire historical sites. 
__This innovation not only provides wider access but also raises standards of 
accuracy in recording human history.__ Many researchers have praised...
```

---

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **1 câu ứng viên 18–30 từ**
- Gồm **2 mệnh đề thông tin** và **logic rõ**:
  - cause–effect
  - condition–result
  - contrast
- Câu đủ "giàu nghĩa" để tạo nhiễu sai tinh vi:
  - Đảo logic
  - Đổi chủ thể/đối tượng
  - Phóng đại/thu hẹp phạm vi

**Ví dụ mỏ neo trong PASSAGE (có gạch chân):**
```
[P3] ... <u>Although the initial investment is high, renewable energy systems 
can save households significant amounts of money in the long run.</u> Many families
have reported...
→ 2 mệnh đề: (1) initial investment high, (2) save money long run
→ Logic: contrast (Although)
→ Nhiễu: đảo logic (Because...), đổi chủ thể (companies thay vì households)
```

---

## (6) TRUE / NOT TRUE (Which is TRUE…)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- Which of the following is **TRUE** according to paragraph X?
- Which of the following is **NOT TRUE** according to paragraph X?
- According to the passage, which statement is **correct**?
- Which statement is **supported by** the information in paragraph X?

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **ít nhất 3 facts** rõ ràng, cụ thể, kiểm chứng được
- **Hạn chế** may/might/could để tránh mơ hồ
- Ít nhất **1 fact có cấu trúc dễ bẫy**:
  - X allows/enables Y
  - X results in Y
  - X prevents Y

**Ví dụ mỏ neo:**
```
[P4] ... The program requires participants to attend at least 10 sessions. 
Graduates receive a certificate. The training is free for low-income families...
→ 3 facts rõ ràng: (1) 10 sessions, (2) certificate, (3) free for low-income
→ Nhiễu: đổi số (5 sessions), đổi đối tượng (all families)
```

---

## (7) LOCATING PARAGRAPH (Which paragraph mentions…)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- **Which paragraph** mentions …?
- In **which paragraph** does the author discuss …?
- The information about X can be found in **paragraph** ____.
- **Which paragraph** provides information about …?

**Mỏ neo cần có:**
- Thiết kế ít nhất **2 "ý độc quyền" (exclusive mentions)**:
  - Ý A chỉ xuất hiện rõ ở **đúng 1 đoạn**
  - Ý B chỉ xuất hiện rõ ở **đúng 1 đoạn khác**
- **Không lặp lại** từ khóa/hạt nhân của ý đó ở đoạn khác
- Ý độc quyền nên là **cơ chế/biện pháp/sự kiện/đối tượng cụ thể**, không quá chung chung

**Ví dụ mỏ neo:**
```
[P1] ... solar panels... (chỉ P1 có "solar panels")
[P2] ... carbon tax... (chỉ P2 có "carbon tax")
[P3] ... electric vehicles... (chỉ P3 có "electric vehicles")
→ Câu hỏi: Which paragraph mentions a government policy on emissions?
→ Đáp án: P2 (carbon tax là policy)
```

---

## (8) SENTENCE COMPLETION (detail dạng "will ____")

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- According to paragraph X, … **will** ____.
- According to the passage, … **can** ____.
- Based on the passage, … **is/are** ____.
- The passage states that … **has/have** ____.

**Mỏ neo cần có:**
- Trong đoạn mục tiêu có **1 cặp đối lập** (A khó/tốn kém; B dễ/nhanh)
- Có **1 hệ quả rõ ràng** của lựa chọn B (result)
- Viết sao cho chỉ có **1 hệ quả chính** phù hợp với chỗ trống
- Các cụm danh từ nổi bật khác trong đoạn vẫn xuất hiện để làm nhiễu

**Ví dụ mỏ neo:**
```
[P2] ... While redesigning products is expensive and time-consuming, 
switching to recyclable packaging can immediately reduce waste...
→ Câu hỏi: According to P2, switching to recyclable packaging will ____.
→ Đáp án: reduce waste immediately
→ Nhiễu: redesign products, increase costs (có trong đoạn nhưng sai logic)
```

---

## (9) BEST SUMMARISE (ĐOẠN)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- Which of the following **best summarises** paragraph X?
- What is the **main idea** of paragraph X?
- Paragraph X is **mainly about** ____.
- Which of the following is the **best title** for paragraph X?

**Mỏ neo cần có:**
- Đoạn mục tiêu có **1 topic sentence rõ** + **2–4 câu hỗ trợ** (examples/details)
- Không rẽ sang ý phụ lớn
- Có ít nhất **2 ví dụ/biểu hiện** để:
  - Đáp án đúng = "khái quát"
  - Nhiễu = "quá hẹp/1 ví dụ"

**Ví dụ mỏ neo:**
```
[P3] Topic: Benefits of cycling to work
- Example 1: improves physical health
- Example 2: reduces carbon footprint
- Example 3: saves money on fuel
→ Đáp án đúng: Cycling to work offers multiple benefits (khái quát)
→ Nhiễu: Cycling improves health (chỉ 1 ví dụ - quá hẹp)
```

---

## (10) DETAIL QUESTIONS (thông tin chi tiết)

**Mục tiêu ra đề:** "According to paragraph X, what is/are…?"

**Mỏ neo cần có:**
- Cài ít nhất **2 chi tiết "hỏi được"** ở các đoạn phù hợp ma trận:
  - 1 chi tiết về **nguyên nhân (cause)** hoặc **tác nhân (trigger)**
  - 1 chi tiết về **thách thức (challenge)** hoặc **giới hạn (limitation)**
- Mỗi câu hỏi chỉ có **1 đáp án đúng duy nhất**
- Các cụm dùng làm đáp án phải là **noun phrases cụ thể** (không chung chung)

**Ví dụ mỏ neo:**
```
[P4] ... The main challenge is the high cost of installation. 
However, government subsidies can reduce this barrier...
→ Câu hỏi 1: What is the main challenge? → high cost of installation
→ Câu hỏi 2: What can reduce this barrier? → government subsidies
```

---

## (11) INFERENCE (suy luận)

**Mục tiêu ra đề (ví dụ - có thể biến thể):**
- Which of the following **can be inferred** from the passage?
- It can be **inferred** from the passage that ____.
- What can be **concluded** from the passage?
- The passage **implies/suggests** that ____.

**Mỏ neo cần có:**
- Rải **2–3 dữ kiện** ở **ít nhất 2 đoạn khác nhau** để suy ra kết luận K
- **Không viết thẳng** K trong bài
- Dữ kiện phải đủ mạnh để **3 suy luận nhiễu bị loại**:
  - Nhiễu "nghe tích cực nhưng trái dữ kiện"
  - Nhiễu "phóng đại hiệu quả/mức độ"
  - Nhiễu "đảo động cơ/đảo quan hệ"
- Đáp án đúng là **kết luận hợp lý nhất** từ các dữ kiện, không cần kiến thức ngoài bài

**Ví dụ mỏ neo:**
```
[P1] ... Solar energy adoption has tripled in the past decade...
[P3] ... Government incentives have made solar panels more affordable...
→ Inference: Government policies have contributed to the growth of solar energy
→ Nhiễu: Solar energy is now the main source of electricity (phóng đại)
```

---

## (12) SENTENCE INSERTION (Điền câu vào chỗ thích hợp)

**Mục tiêu ra đề:** "Where in the passage does the following sentence best fit? '…' A. [I] B. [II] C. [III] D. [IV]"

**Mỏ neo cần có:**
- Trong PASSAGE phải có **đúng 4 marker vị trí**: [I], [II], [III], [IV]
- Viết **1 câu chèn** có:
  - Từ nối rõ (Yet/However/Therefore/For example/As a result)
  - Và/hoặc đại từ tham chiếu
- Đảm bảo **chỉ có 1 vị trí đúng**:
  - Đúng mạch logic
  - Đúng tham chiếu
- 3 vị trí sai gây gãy mạch hoặc "Yet/However" không có ý để đối lập

**Ví dụ mỏ neo:**
```
[P2] ... Many companies are adopting green practices. [I] This shift is driven by 
consumer demand. [II] However, some businesses resist change due to costs. [III] 
Government regulations are also pushing for sustainability. [IV] ...

Câu chèn: "For example, a recent survey showed that 70% of consumers prefer eco-friendly products."
→ Vị trí đúng: [II] (sau "consumer demand" - For example minh họa cho consumer demand)
→ Vị trí sai: [I] không có gì để For example, [III] sau However không hợp, [IV] không liên quan
```

---

## (13) BEST SUMMARISE (CẢ BÀI)

**Mục tiêu ra đề:** "Which of the following best summarises the passage?"

**Mỏ neo cần có:**
- Toàn bài có **1 luận điểm trung tâm**:
  - Giới thiệu ở [P1]
  - Triển khai ở [P2]-[P3]
  - Kết/ý nghĩa ở [P4]
- **Tránh** 2 luận điểm trung tâm cạnh tranh
- Nội dung đủ "bao quát" để tạo **3 nhiễu**:
  - Chỉ 1 đoạn
  - Thiếu ý trung tâm
  - Thêm ý ngoài bài

**Ví dụ mỏ neo:**
```
[P1] Introduction: Green living is becoming essential
[P2] Benefits of green living
[P3] Challenges of adopting green practices
[P4] Future outlook and recommendations
→ Luận điểm trung tâm: The importance, benefits, challenges, and future of green living
→ Nhiễu 1: Only about benefits (chỉ P2)
→ Nhiễu 2: Green living will replace all traditional practices (thêm ý ngoài bài)
→ Nhiễu 3: Challenges make green living impossible (thiếu ý trung tâm - benefits)
```

---

# ═══════════════════════════════════════════════════════════════
# FORMAT ĐẦU RA
# ═══════════════════════════════════════════════════════════════

## 1. KEY FACTS & CONSTRAINTS

```
### KEY FACTS (10–14 ý)
1. [Fact 1 - từ SOURCE]
2. [Fact 2 - từ SOURCE]
3. [Fact 3 - từ SOURCE]
...

### HARD CONSTRAINTS (tên riêng/số liệu/mốc thời gian/thuật ngữ bắt buộc giữ)
- [Constraint 1]
- [Constraint 2]
...

### KEYWORDS (8–12 từ khóa)
[keyword1], [keyword2], [keyword3], ...
```

---

## 2. OUTLINES (đổi bố cục)

```
### OUTLINE A
[P1]: [Ý chính - sắp xếp KEY FACTS]
[P2]: [Ý chính]
[P3]: [Ý chính]
[P4]: [Ý chính] (nếu có)

### OUTLINE B
[P1]: [Ý chính - sắp xếp khác OUTLINE A]
[P2]: [Ý chính]
[P3]: [Ý chính]
[P4]: [Ý chính] (nếu có)

### OUTLINE ĐƯỢC CHỌN: [A/B]
Lý do: [Giải thích ngắn tại sao chọn outline này]
```

---

## 3. PASSAGE (Bài đọc hoàn chỉnh)

```
[P1] [Nội dung đoạn 1 - có marker [I] nếu cần cho sentence insertion]
     [Từ cho câu hỏi từ vựng được **bôi đậm**]

[P2] [Nội dung đoạn 2 - có marker [II], [III] nếu cần]

[P3] [Nội dung đoạn 3 - có marker [IV] nếu cần]
     [Nếu có Best paraphrased: <u>Câu cần gạch chân nằm ở đây.</u>]

[P4] [Nội dung đoạn 4 - nếu có]

(Word count: XXX)
```

**⚠️ QUY TẮC ĐỊNH DẠNG ĐẶC BIỆT TRONG PASSAGE:**

| Dạng câu hỏi | Định dạng | Ví dụ |
|--------------|-----------|-------|
| **Synonym/Antonym** | **Bôi đậm** từ cần hỏi | `Technology has **transformed** how...` |
| **Best paraphrased** | <u>Gạch chân</u> câu cần hỏi | `<u>This innovation not only...</u>` |
| **Sentence insertion** | Marker vị trí | `[I] ... [II] ... [III] ... [IV]` |

**❌ KHÔNG được bôi đậm linh tinh:**
- Chỉ bôi đậm đúng số từ = số câu hỏi từ vựng trong ma trận
- Không bôi đậm tiêu đề, từ khóa topic, hoặc từ quan trọng khác

---

## 4. BẢNG KIỂM TRA MỎ NEO

```
| Dạng câu hỏi | Cấp độ | Mỏ neo đã cài | Đủ chưa? |
|--------------|--------|---------------|----------|
| NOT mentioned | NB | [mô tả ngắn] | ✅/❌ |
| Từ vựng - đồng nghĩa | VD | [từ + nghĩa] | ✅/❌ |
| Từ vựng - trái nghĩa | TH | [từ + nghĩa] | ✅/❌ |
| Tham chiếu | TH | [đại từ → antecedent] | ✅/❌ |
| Best paraphrased | VD | [câu đã GẠCH CHÂN] | ✅/❌ |
| True/False | TH | [số facts] | ✅/❌ |
| Tìm đoạn phù hợp | VD | [ý độc quyền] | ✅/❌ |
| Tìm đoạn phù hợp | VDC | [ý độc quyền] | ✅/❌ |
```

---

# ═══════════════════════════════════════════════════════════════
# CHECKLIST TỰ KIỂM
# ═══════════════════════════════════════════════════════════════

## Trước khi hoàn thành:

### Kiểm tra ràng buộc:
- [ ] Không thêm thông tin ngoài SOURCE?
- [ ] **⚠️ ĐÃ TỰ KIỂM TRA TỪNG CÂU - không sao chép > 8 từ liên tiếp?**
- [ ] **⚠️ Bài viết lại KHÁC SOURCE ít nhất 60%?** (đổi từ vựng + cấu trúc câu)
- [ ] Bố cục khác SOURCE? (đổi thứ tự ý/đoạn)
- [ ] Ngôn ngữ đúng CEFR mục tiêu?
- [ ] Có 3-4 đoạn với nhãn [P1], [P2], [P3], [P4]?
- [ ] Độ dài trong khoảng mục tiêu ±10%?

### Kiểm tra văn phong tự nhiên:
- [ ] **Không có** câu mở đầu sáo rỗng ("In today's...", "In recent years...")?
- [ ] **Không có** quá nhiều từ nối ("Furthermore", "Moreover", "Additionally")?
- [ ] **Không có** kết luận sáo rỗng ("In conclusion", "To sum up")?
- [ ] Độ dài câu **đa dạng** (có câu ngắn 8-12 từ xen kẽ)?
- [ ] Có **chi tiết cụ thể** (tên, số, ví dụ)?
- [ ] **Đọc to** lên nghe tự nhiên không?

### Kiểm tra định dạng đặc biệt:
- [ ] **Bôi đậm:** CHỈ bôi đậm từ cho câu hỏi từ vựng (synonym/antonym)?
- [ ] **Gạch chân:** Đã gạch chân câu cho paraphrasing (nếu có)?
- [ ] **Markers:** Đã có [I][II][III][IV] cho sentence insertion (nếu có)?

### Kiểm tra chống mơ hồ:
- [ ] Mọi đại từ (it/they/this/these) chỉ có 1 antecedent hợp lệ?
- [ ] Antecedent đứng ngay trước đại từ?
- [ ] Không có 2 danh từ cùng số gây mơ hồ?

### Kiểm tra mỏ neo:
- [ ] Đủ mỏ neo cho TẤT CẢ các dạng câu hỏi trong ma trận?
- [ ] Mỗi mỏ neo có thể tạo 1 đáp án đúng + 3 nhiễu hợp lý?
- [ ] Nếu có "Tìm đoạn phù hợp" → có ý độc quyền cho mỗi đoạn?
- [ ] Nếu có "Best paraphrased" → đã **GẠCH CHÂN** câu ứng viên trong PASSAGE?

### Kiểm tra chất lượng:
- [ ] Bài đọc mạch lạc, logic?
- [ ] Văn phong tự nhiên, không có dấu hiệu AI?
- [ ] Phù hợp với học sinh làm bài thi?

---

# ═══════════════════════════════════════════════════════════════
# LƯU Ý QUAN TRỌNG
# ═══════════════════════════════════════════════════════════════

## ⚠️⚠️⚠️ 5 LỖI THƯỜNG GẶP - PHẢI TRÁNH ⚠️⚠️⚠️

### LỖI 1: SAO CHÉP NGUYÊN VĂN > 8 TỪ
```
❌ SAI: Copy câu từ SOURCE, chỉ đổi 1-2 từ hoặc KHÔNG ĐỔI GÌ
   SOURCE: "Smaller communities often lack the financial resources and technical expertise to digitise their heritage"
   AI viết: "Smaller communities often lack the financial resources and technical expertise to digitise their heritage"
   → 14 từ giống y hệt = VI PHẠM NGHIÊM TRỌNG!

✅ ĐÚNG: Viết lại hoàn toàn bằng từ khác
   "Many small communities do not have enough money or skills to create digital copies of their traditions"
```

### LỖI 2: KHÔNG ĐẠT 60% KHÁC BIỆT
```
❌ SAI: Chỉ đổi vài từ, giữ nguyên cấu trúc (~20% khác biệt)
   SOURCE: "The preservation of cultural heritage has traditionally relied on physical artefacts"
   AI viết: "The protection of cultural heritage has traditionally depended on physical objects"
   → Chỉ đổi 3 từ (preservation→protection, relied→depended, artefacts→objects) = KHÔNG ĐẠT 60%!

✅ ĐÚNG: Đổi cả từ vựng LẪN cấu trúc (~70% khác biệt)
   "For centuries, keeping cultural traditions safe meant preserving physical items like old documents and paintings."
   → Đổi cấu trúc câu + đổi từ vựng + đổi cách diễn đạt = ĐẠT 60%+
```

### LỖI 3: QUÊN GẠCH CHÂN CÂU PARAPHRASE
```
❌ SAI: Có câu phù hợp nhưng KHÔNG gạch chân trong PASSAGE
   "This innovation not only provides wider access but also raises standards of accuracy."

✅ ĐÚNG: PHẢI gạch chân ngay trong PASSAGE
   "<u>This innovation not only provides wider access but also raises standards of accuracy.</u>"
```

### LỖI 4: BÔI ĐẬM LINH TINH
```
❌ SAI: Bôi đậm nhiều từ không cần thiết
   "**Technology** has **completely transformed** how the **public** engages with **traditional customs**."

✅ ĐÚNG: CHỈ bôi đậm từ/cụm từ phục vụ câu hỏi từ vựng (synonym/antonym)
   "Technology has completely **transformed** how the public engages with traditional customs."
   → Chỉ bôi đậm "transformed" vì đây là từ sẽ hỏi synonym
```

### LỖI 5: VĂN PHONG AI
```
❌ SAI: Văn phong giống AI viết
   "In today's rapidly evolving digital landscape, the preservation of cultural heritage 
   has become increasingly significant. Furthermore, technological advancements have 
   revolutionized the way institutions safeguard valuable artefacts. Moreover, this 
   transformation has profound implications for future generations."

✅ ĐÚNG: Văn phong tự nhiên như người viết
   "Museums are changing how they protect history. Instead of relying only on glass 
   cases and climate control, many now create digital copies of their most precious 
   items. A visitor in Tokyo can explore ancient Greek sculptures without leaving home."
```

**DẤU HIỆU VĂN PHONG AI cần tránh:**
- Mở đầu: "In today's...", "In recent years...", "It is widely known..."
- Từ nối quá nhiều: "Furthermore", "Moreover", "Additionally"
- Kết luận: "In conclusion", "To sum up", "All in all"
- Câu dài đều nhau, không có variation
- Toàn khái niệm chung, thiếu chi tiết cụ thể

**QUY TẮC BÔI ĐẬM:**
- CHỈ bôi đậm từ/cụm từ dùng cho câu hỏi **SYNONYM** hoặc **ANTONYM**
- KHÔNG bôi đậm bất kỳ từ nào khác
- Số lượng từ bôi đậm = số câu hỏi từ vựng trong ma trận

---

## ⚠️⚠️⚠️ BẮT BUỘC: TỰ KIỂM TRA SAO CHÉP & KHÁC BIỆT 60% ⚠️⚠️⚠️

**SAU KHI VIẾT XONG PASSAGE, PHẢI THỰC HIỆN:**

### Bước 1: Kiểm tra sao chép
1. **So sánh TỪNG CÂU** trong PASSAGE với SOURCE
2. Nếu phát hiện **> 8 từ liên tiếp giống nhau** → **VIẾT LẠI NGAY**
3. Đặc biệt chú ý các câu dài, câu có cấu trúc phức tạp

**Công thức kiểm tra:**
```
Câu SOURCE: "A B C D E F G H I J K L M N"
Câu AI:     "A B C D E F G H I X Y Z"
            ↑_______________↑
            9 từ giống = VI PHẠM → Phải viết lại!
```

### Bước 2: Kiểm tra 60% khác biệt
Với mỗi câu, tự hỏi:
- [ ] Đã đổi **từ vựng chính** (danh từ, động từ, tính từ)?
- [ ] Đã đổi **cấu trúc câu** (active↔passive, simple↔complex)?
- [ ] Đã đổi **cách diễn đạt** (X causes Y → Y results from X)?

**Nếu chỉ đổi 1-2 từ mà giữ nguyên cấu trúc → CHƯA ĐẠT 60% → VIẾT LẠI!**

---

## DANH SÁCH LƯU Ý ĐẦY ĐỦ

1. ⚠️ **KHÔNG THÊM THÔNG TIN:** Chỉ dùng thông tin từ SOURCE, không sáng tạo thêm
2. ⚠️ **KHÔNG SAO CHÉP > 8 TỪ:** Viết lại hoàn toàn, kể cả khi chỉ đổi 1-2 từ vẫn vi phạm!
3. ⚠️ **KHÁC BIỆT 60%:** Bài viết lại phải khác SOURCE ít nhất 60% về từ vựng và cấu trúc
4. ⚠️ **TỰ KIỂM TRA SAO CHÉP:** So sánh từng câu với SOURCE trước khi xuất bài
5. ⚠️ **ĐỔI BỐ CỤC:** Sắp xếp lại trình tự ý/đoạn khác SOURCE
6. ⚠️ **CHỐNG MƠ HỒ:** Mỗi đại từ chỉ có 1 antecedent rõ ràng
7. ⚠️ **VĂN PHONG TỰ NHIÊN:** Tránh dấu hiệu AI (xem phần C), đọc to phải nghe tự nhiên
8. ⚠️ **CÀI MỎ NEO:** Đảm bảo đủ mỏ neo cho TẤT CẢ dạng câu hỏi trong ma trận
9. ⚠️ **GẠCH CHÂN CÂU PARAPHRASE:** Nếu có dạng này trong ma trận, BẮT BUỘC gạch chân câu trong PASSAGE
10. ⚠️ **CHỈ BÔI ĐẬM TỪ CHO CÂU HỎI TỪ VỰNG:** Không bôi đậm linh tinh
11. ⚠️ **LINH HOẠT THỨ TỰ:** Không bắt buộc thứ tự câu hỏi theo ma trận, chỉ cần ĐỦ các dạng
12. ⚠️ **Ý ĐỘC QUYỀN:** Nếu có "Tìm đoạn phù hợp", mỗi ý chỉ xuất hiện ở 1 đoạn
13. ⚠️ **MARKER VỊ TRÍ:** Nếu có "Sentence insertion", phải có [I][II][III][IV]
14. ⚠️ **KIỂM TRA CUỐI:** Rà soát sao chép, khác biệt 60%, đại từ, mỏ neo, bôi đậm, văn phong trước khi xuất bài


# ═══════════════════════════════════════════════════════════════
# PHẦN B: SINH CÂU HỎI VÀ LỜI GIẢI
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# CẤP ĐỘ NHẬN THỨC VÀ QUY TẮC BẪY
# ═══════════════════════════════════════════════════════════════

## 1. ĐỊNH NGHĨA CẤP ĐỘ NHẬN THỨC

| Cấp độ | Tên | Định nghĩa | Yêu cầu với học sinh |
|--------|-----|------------|---------------------|
| **NB** | Nhận biết | Tìm thông tin **HIỂN THỊ TRỰC TIẾP** trong bài | Chỉ cần đọc và tìm đúng vị trí |
| **TH** | Thông hiểu | Cần **HIỂU** và **DIỄN GIẢI** thông tin | Phải hiểu nghĩa, không chỉ tìm từ khóa |
| **VD** | Vận dụng | Cần **TỔNG HỢP** nhiều thông tin hoặc **ÁP DỤNG** kiến thức | Kết hợp thông tin từ nhiều câu/đoạn |
| **VDC** | Vận dụng cao | Cần **SUY LUẬN SÂU** hoặc **ĐÁNH GIÁ** | Suy luận logic phức tạp, không có sẵn trong bài |

---

## 2. QUY TẮC BẪY THEO CẤP ĐỘ NHẬN THỨC

### NB (Nhận biết) - BẪY DỄ LOẠI TRỪ

| Loại bẫy | Mô tả | Ví dụ |
|----------|-------|-------|
| **Từ khóa sai đoạn** | Từ có trong bài nhưng ở đoạn khác | Hỏi P1, đáp án lấy từ P3 |
| **Đảo thông tin đơn giản** | Đổi số liệu, tên, thời gian | "2020" → "2015" |
| **Không được nhắc đến** | Thông tin không tồn tại trong đoạn | D hoàn toàn không có trong P1 |

**Đặc điểm:**
- Học sinh chỉ cần **scan** đúng vị trí là loại được
- Đáp án sai **rõ ràng** khi đối chiếu với bài

---

### TH (Thông hiểu) - BẪY CẦN PHÂN TÍCH

| Loại bẫy | Mô tả | Ví dụ |
|----------|-------|-------|
| **Paraphrase sai** | Diễn đạt lại nhưng đổi nghĩa | "reduce" → "eliminate" (giảm ≠ loại bỏ) |
| **Sai chủ thể/đối tượng** | Đúng hành động, sai người thực hiện | "students" → "teachers" |
| **Sai quan hệ logic** | Đảo nguyên nhân-kết quả | A causes B → B causes A |
| **Từ vựng gần nghĩa nhưng sai ngữ cảnh** | Synonym không phù hợp context | "house" vs "home" trong ngữ cảnh cụ thể |

**Đặc điểm:**
- Đáp án sai **có vẻ hợp lý** khi đọc lướt
- Cần **đọc kỹ** và **so sánh** với bài mới loại được

---

### VD (Vận dụng) - BẪY ĐÁNH ĐỐ

| Loại bẫy | Mô tả | Ví dụ |
|----------|-------|-------|
| **Thông tin đúng nhưng không đầy đủ** | Chỉ nêu 1 phần, thiếu ý chính | Summary chỉ nêu 1/3 nội dung đoạn |
| **Kết hợp sai** | Ghép thông tin từ 2 đoạn không liên quan | P1 + P3 nhưng không có mối liên hệ |
| **Phóng đại/Thu hẹp** | Đúng hướng nhưng sai mức độ | "some" → "all", "may" → "will" |
| **Sai trình tự logic** | Đảo thứ tự các bước/sự kiện | Step 1 → Step 3 → Step 2 |

**Đặc điểm:**
- Đáp án sai **rất gần đúng**, cần **phân tích kỹ**
- Phải **tổng hợp** nhiều thông tin mới nhận ra sai

---

### VDC (Vận dụng cao) - BẪY RẤT TINH VI

| Loại bẫy | Mô tả | Ví dụ |
|----------|-------|-------|
| **Suy luận quá xa** | Logic đúng nhưng đi quá xa dữ kiện | "X is good" → "X is the best" |
| **Đảo động cơ/mục đích** | Sai lý do tại sao làm việc đó | "to help" → "to control" |
| **Thêm thông tin ngoài bài** | Nghe hợp lý nhưng không có cơ sở | Kiến thức phổ thông nhưng bài không đề cập |
| **Tương quan ≠ Nhân quả** | X và Y cùng xảy ra ≠ X gây ra Y | "A and B increased" ≠ "A caused B to increase" |
| **Nghe tích cực nhưng trái dữ kiện** | Đáp án "đẹp" nhưng mâu thuẫn với bài | "completely solved" khi bài nói "still challenges" |

**Đặc điểm:**
- Đáp án sai **rất hấp dẫn**, phải **suy luận cẩn thận**
- Cần **đọc lại nhiều lần** và **kiểm tra logic**

---

## 3. BẢNG ÁP DỤNG CẤP ĐỘ THEO DẠNG CÂU HỎI

| Dạng câu hỏi | NB | TH | VD | VDC |
|--------------|----|----|----|----|
| **NOT mentioned** | Từ khóa rõ ràng, dễ scan | Cần hiểu paraphrase | Thông tin rải rác | - |
| **Từ vựng (Syn/Ant)** | Từ phổ thông, ngữ cảnh rõ | Từ có nhiều nghĩa, cần context | Từ học thuật, ngữ cảnh phức tạp | - |
| **Reference** | Antecedent ngay trước | Antecedent cách 1 câu | Antecedent phức tạp/dài | - |
| **Paraphrasing** | - | Câu đơn, logic đơn giản | Câu phức, 2 mệnh đề | Câu có logic tinh tế |
| **True/False** | Fact hiển thị trực tiếp | Cần hiểu nghĩa | Tổng hợp nhiều facts | - |
| **Locating paragraph** | Từ khóa độc quyền rõ | Cần hiểu ý chính đoạn | Ý ẩn, không có từ khóa trực tiếp | - |
| **Detail question** | Thông tin 1 câu | Thông tin 2-3 câu | Tổng hợp cả đoạn | Suy luận từ chi tiết |
| **Sentence insertion** | Từ nối rõ ràng | Cần hiểu mạch logic | Logic phức tạp | - |
| **Best summarise (đoạn)** | - | Đoạn có topic sentence rõ | Đoạn không có topic sentence | Đoạn có nhiều ý phụ |
| **Best summarise (bài)** | - | - | Bài có 1 luận điểm rõ | Bài có nhiều luận điểm |
| **Inference** | - | - | Suy luận từ 2 đoạn | Suy luận phức tạp, logic ẩn |

---

# ═══════════════════════════════════════════════════════════════
# QUY TẮC SINH CÂU HỎI (CHỐT CHẶT)
# ═══════════════════════════════════════════════════════════════

## QUY TẮC BẮT BUỘC

| # | Quy tắc | Mô tả |
|---|---------|-------|
| 1 | **100% từ PASSAGE** | Mọi câu hỏi và đáp án phải dựa hoàn toàn trên PASSAGE. KHÔNG dùng kiến thức ngoài bài |
| 2 | **4 lựa chọn A/B/C/D** | Mỗi câu có đúng 4 phương án |
| 3 | **⚠️ 1 ĐÁP ÁN ĐÚNG DUY NHẤT** | Chỉ có đúng 1 đáp án đúng. Nếu có 2 đáp án có thể đúng → SỬA LẠI câu hỏi hoặc phương án |
| 4 | **Đáp án đúng không theo pattern** | Đáp án đúng phân bố ngẫu nhiên (không phải toàn A hoặc toàn C) |
| 5 | **⚠️ DÙNG ĐÚNG MỎ NEO** | PHẢI sử dụng chính xác mỏ neo đã cài trong PASSAGE |
| 6 | **⚠️ ĐÚNG CẤP ĐỘ NHẬN THỨC** | Câu hỏi PHẢI đúng cấp độ trong ma trận (NB/TH/VD/VDC) |
| 7 | **⚠️ ĐỦ SỐ LƯỢNG** | Số câu hỏi PHẢI đúng với tổng số trong ma trận |

---

## ⚠️⚠️⚠️ KIỂM TRA 1 ĐÁP ÁN ĐÚNG DUY NHẤT ⚠️⚠️⚠️

**SAU KHI VIẾT XONG MỖI CÂU HỎI, PHẢI TỰ KIỂM TRA:**

### Bước 1: Thử trả lời như học sinh
- Đọc câu hỏi và 4 phương án
- Chọn đáp án mà KHÔNG nhìn đáp án đúng
- Nếu có thể chọn 2 đáp án → CÂU HỎI CÓ VẤN ĐỀ

### Bước 2: Kiểm tra từng phương án
```
Với mỗi phương án A/B/C/D, tự hỏi:
- [ ] Có evidence trong bài để chứng minh ĐÚNG không?
- [ ] Có evidence trong bài để chứng minh SAI không?

Kết quả hợp lệ:
✅ 1 phương án: CÓ evidence đúng
✅ 3 phương án: CÓ evidence sai

Kết quả KHÔNG hợp lệ:
❌ 2+ phương án có evidence đúng → SỬA LẠI
❌ 1 phương án không có evidence sai rõ ràng → SỬA LẠI
```

### Bước 3: Kiểm tra logic
- Đáp án đúng có **BẮT BUỘC** phải đúng không? (không phải "có thể đúng")
- Đáp án sai có **CHẮC CHẮN** sai không? (không phải "có thể sai")

**Ví dụ câu hỏi có vấn đề:**
```
❌ SAI: Which of the following is TRUE?
A. Technology helps preserve culture. → Đúng (có trong bài)
B. Digital tools make culture accessible. → CŨNG ĐÚNG (có trong bài)
→ 2 đáp án đúng = PHẢI SỬA LẠI

✅ ĐÚNG: Which of the following is TRUE about the challenges?
A. Technology helps preserve culture. → Sai (không phải challenge)
B. Small communities lack resources. → ĐÚNG (challenge được nhắc)
C. Digital tools are expensive. → Sai (không được nhắc)
D. All museums have adopted digital methods. → Sai (trái với bài)
→ Chỉ 1 đáp án đúng = OK
```

---

## QUY TẮC CHO PHƯƠNG ÁN NHIỄU

| # | Quy tắc | Chi tiết |
|---|---------|----------|
| 1 | **Cùng loại** | Cùng từ loại (noun/verb/adj), cùng chủ đề với đáp án đúng |
| 2 | **Lý do sai rõ ràng** | Mỗi phương án sai phải có lý do cụ thể: không được nhắc đến / sai chi tiết / sai logic / sai tham chiếu / phóng đại |
| 3 | **Không sai ngữ pháp** | Phương án sai vì NỘI DUNG, không phải vì ngữ pháp |
| 4 | **Độ dài tương đương** | Các phương án có độ dài gần bằng nhau |
| 5 | **Độ khó phù hợp cấp độ** | NB: sai rõ ràng; TH: có vẻ đúng khi đọc lướt; VD: gần đúng; VDC: rất hấp dẫn |

---

## QUY TẮC THEO DẠNG CÂU HỎI

### Reference (Quy chiếu)
- Đại từ phải có **antecedent duy nhất**
- Đáp án phải là **cụm danh từ cụ thể** (không trả lời kiểu "the whole idea" hoặc "the previous sentence")
- Phương án nhiễu: danh từ khác trong cùng đoạn nhưng sai số/sai nghĩa

### Vocabulary (Từ vựng)
- Từ được hỏi phải **khó hơn hoặc ngang** với 4 phương án
- Các options phải **cùng từ loại** (verb/adj/noun) và **phù hợp ngữ pháp** chỗ trống
- Phương án nhiễu: từ gần nghĩa nhưng sai ngữ cảnh, hoặc từ cùng trường nghĩa nhưng khác nghĩa

### NOT Mentioned
- **3 options** phải được nhắc tới (hoặc mô tả rõ) trong đoạn mục tiêu
- **1 option** (đáp án đúng) không xuất hiện trong đoạn đó
- Option không xuất hiện phải **cùng trường nghĩa** để tạo nhiễu hợp lý

### Sentence Insertion
- Chỉ **1 vị trí** là đúng
- Các vị trí sai vì: gãy mạch logic / tham chiếu sai / từ nối không phù hợp
- Giải thích phải chỉ rõ tại sao mỗi vị trí sai

### Paraphrasing
- Đáp án đúng phải **giữ nguyên nghĩa** nhưng **đổi cấu trúc/từ vựng**
- Phương án nhiễu: đảo logic / đổi chủ thể / phóng đại / thu hẹp phạm vi

### Best Summarise
- Đáp án đúng phải **bao quát** toàn bộ nội dung (đoạn/bài)
- Phương án nhiễu: quá hẹp (chỉ 1 ý) / quá rộng (thêm ý ngoài bài) / thiếu ý chính

### Inference
- Đáp án đúng phải **suy luận được** từ dữ kiện trong bài
- KHÔNG được viết thẳng trong bài
- Phương án nhiễu: suy luận quá xa / trái dữ kiện / thêm thông tin ngoài bài

### Detail Question
- Đáp án đúng phải **chính xác** với thông tin trong bài
- Phương án nhiễu: sai số liệu / sai đối tượng / sai thời gian / không được nhắc đến

---

# ═══════════════════════════════════════════════════════════════
# FORMAT ĐẦU RA HOÀN CHỈNH
# ═══════════════════════════════════════════════════════════════

## PHẦN 1: BÀI ĐỌC (PASSAGE)

```
[TIÊU ĐỀ BÀI ĐỌC]

[P1] [Nội dung đoạn 1]
     [Có **từ bôi đậm** cho Vocabulary nếu cần]

[P2] [Nội dung đoạn 2]
     [Có markers [I][II] cho Sentence Insertion nếu cần]

[P3] [Nội dung đoạn 3]
     [Có <u>câu gạch chân</u> cho Paraphrasing nếu cần]
     [Có markers [III][IV] nếu cần]

[P4] [Nội dung đoạn 4]

(Word count: XXX words)
```

---

## PHẦN 2: BẢNG KIỂM TRA MỎ NEO

```
| STT | Dạng câu hỏi | Cấp độ | Mỏ neo trong bài | Vị trí |
|-----|--------------|--------|------------------|--------|
| 1 | Locating | TH | [từ khóa độc quyền] | P2 |
| 2 | Vocabulary | TH | **từ bôi đậm** = nghĩa | P2 |
| 3 | Detail | VD | [chi tiết cụ thể] | P3 |
| 4 | Paraphrasing | VD | <u>câu gạch chân</u> | P3 |
| 5 | Reference | VD | "đại từ" → antecedent | P3 |
| 6 | Sentence Insertion | VD | Vị trí đúng: [I] | P2 |
| 7 | Best Summarise | VD | [ý chính toàn bài] | - |
| 8 | Inference | VDC | [dữ kiện 1] + [dữ kiện 2] → [suy luận] | P1+P3 |
| ... | ... | ... | ... | ... |
```

---

## PHẦN 3: CÂU HỎI VÀ ĐÁP ÁN

```
Read the following passage and mark the letter A, B, C, or D on your answer sheet to indicate the correct answer to each of the questions.

[PASSAGE]

Question [số] [Dạng câu hỏi - Cấp độ]: [Nội dung câu hỏi]
A. [Phương án A]
B. [Phương án B]
C. [Phương án C]
D. [Phương án D]

Question [số + 1] [Dạng câu hỏi - Cấp độ]: [Nội dung câu hỏi]
A. [Phương án A]
B. [Phương án B]
C. [Phương án C]
D. [Phương án D]

... (tiếp tục cho đến hết)

---

ANSWER KEY:
[số]. [A/B/C/D]
[số + 1]. [A/B/C/D]
...
```

---

## PHẦN 4: LỜI GIẢI CHI TIẾT ⚠️ BẮT BUỘC

### Format lời giải (THỐNG NHẤT cho TẤT CẢ các dạng):

```
Question [số]. [Nội dung câu hỏi]
A. [đáp án A]		B. [đáp án B]		C. [đáp án C]		D. [đáp án D]

Lời giải
Chọn [A/B/C/D]
A. [đáp án A]: [dịch nghĩa tiếng Việt]
B. [đáp án B]: [dịch nghĩa tiếng Việt]
C. [đáp án C]: [dịch nghĩa tiếng Việt]
D. [đáp án D]: [dịch nghĩa tiếng Việt]
Thông tin: [Trích nguyên văn câu/đoạn liên quan từ bài]
Tạm dịch: [Dịch đoạn thông tin sang tiếng Việt]
```

---

## VÍ DỤ LỜI GIẢI CHI TIẾT

### Ví dụ 1: NOT mentioned

```
Question 18. Which of the following is NOT mentioned in paragraph 1 as a type of collected real-time data?
A. weather patterns		B. data analytics		C. plant growth		D. soil conditions

Lời giải
Chọn B
A. weather patterns: kiểu thời tiết
B. data analytics: phân tích dữ liệu
C. plant growth: sự phát triển của cây trồng
D. soil conditions: tình trạng đất đai
Thông tin: Additionally, the collected real-time data on soil conditions, weather patterns, and plant growth enables farmers to accelerate the decision-making process that maximises productivity while minimising resource wastage.
Tạm dịch: Ngoài ra, dữ liệu thời gian thực được thu thập về tình trạng đất đai, kiểu thời tiết và sự phát triển của cây trồng cho phép nông dân đẩy nhanh quá trình ra quyết định nhằm tối đa hóa năng suất đồng thời giảm thiểu lãng phí tài nguyên.
```

### Ví dụ 2: Vocabulary (Synonym)

```
Question 19. The word "__accelerate__" in paragraph 1 can be best replaced by ______.
A. install		B. speed		C. guide		D. require

Lời giải
Chọn B
A. install (v): cài đặt
B. speed (v): tăng tốc = accelerate (v): đẩy nhanh
C. guide (v): hướng dẫn
D. require (v): yêu cầu
Thông tin: Additionally, the collected real-time data on soil conditions, weather patterns, and plant growth enables farmers to __accelerate__ the decision-making process that maximises productivity while minimising resource wastage.
Tạm dịch: Ngoài ra, dữ liệu thời gian thực được thu thập về tình trạng đất đai, kiểu thời tiết và sự phát triển của cây trồng cho phép nông dân đẩy nhanh quá trình ra quyết định nhằm tối đa hóa năng suất đồng thời giảm thiểu lãng phí tài nguyên.
```

### Ví dụ 3: Reference

```
Question 20. The word "This decision" in paragraph 3 refers to ______.
A. his experiment with abstract forms		B. his choice to resign from teaching
C. his bold approach to art			D. the criticism from the public

Lời giải
Chọn B
A. his experiment with abstract forms: thử nghiệm của ông với các hình thức trừu tượng
B. his choice to resign from teaching: sự lựa chọn từ chức giảng dạy của ông
C. his bold approach to art: cách tiếp cận táo bạo với nghệ thuật của ông
D. the criticism from the public: sự chỉ trích từ công chúng
Thông tin: Eventually, he chose to resign from his teaching post to devote all his energy to sculpture. This decision was risky, but it allowed him to solidify his place as a pioneer of modern art.
Tạm dịch: Cuối cùng, ông chọn từ chức giảng dạy để dành toàn bộ năng lượng cho điêu khắc. Quyết định này rủi ro, nhưng nó cho phép ông củng cố vị trí tiên phong trong nghệ thuật hiện đại.
```

### Ví dụ 4: Paraphrasing

```
Question 21. Which of the following best paraphrases the underlined sentence in paragraph 3?
A. Both artists and the public were confused by Thomas's new style.
B. The public appreciated his bold approach, but other artists were shocked.
C. Although other artists respected his daring style, ordinary people found it difficult to understand.
D. Thomas changed his style because the public was shocked.

Lời giải
Chọn C
A. Both artists and the public were confused by Thomas's new style: Cả nghệ sĩ và công chúng đều bối rối trước phong cách mới của Thomas.
B. The public appreciated his bold approach, but other artists were shocked: Công chúng đánh giá cao cách tiếp cận táo bạo của ông, nhưng các nghệ sĩ khác bị sốc.
C. Although other artists respected his daring style, ordinary people found it difficult to understand: Mặc dù các nghệ sĩ khác tôn trọng phong cách táo bạo của ông, người bình thường thấy khó hiểu.
D. Thomas changed his style because the public was shocked: Thomas thay đổi phong cách vì công chúng bị sốc.
Thông tin: While his bold approach earned admiration from fellow artists, it often shocked and confused the general public.
Tạm dịch: Trong khi cách tiếp cận táo bạo của ông nhận được sự ngưỡng mộ từ các nghệ sĩ đồng nghiệp, nó thường gây sốc và bối rối cho công chúng.
```

### Ví dụ 5: Inference

```
Question 22. Which of the following can be inferred from the passage about Thomas's character?
A. He valued financial stability more than creative freedom.
B. He was easily discouraged by negative criticism from the public.
C. He preferred to follow established rules rather than explore new ideas.
D. He possessed a strong resilience to pursue his own artistic vision despite opposition.

Lời giải
Chọn D
A. He valued financial stability more than creative freedom: Ông coi trọng sự ổn định tài chính hơn tự do sáng tạo.
B. He was easily discouraged by negative criticism from the public: Ông dễ dàng nản lòng trước những lời chỉ trích tiêu cực từ công chúng.
C. He preferred to follow established rules rather than explore new ideas: Ông thích tuân theo các quy tắc đã được thiết lập hơn là khám phá ý tưởng mới.
D. He possessed a strong resilience to pursue his own artistic vision despite opposition: Ông sở hữu sự kiên cường mạnh mẽ để theo đuổi tầm nhìn nghệ thuật của riêng mình bất chấp sự phản đối.
Thông tin: 
- P1: "Although his father pushed him towards a stable career, Thomas felt a deep connection to art from an early age."
- P3: "Critics were harsh, yet he refused to compromise his vision."
Tạm dịch: 
- P1: Mặc dù cha ông thúc đẩy ông theo đuổi sự nghiệp ổn định, Thomas cảm thấy kết nối sâu sắc với nghệ thuật từ nhỏ.
- P3: Các nhà phê bình khắc nghiệt, nhưng ông từ chối thỏa hiệp tầm nhìn của mình.
```

### Ví dụ 6: Best Summarise

```
Question 23. Which of the following best summarises the passage?
A. Thomas was a sculptor who only created abstract forms to shock the public.
B. Despite financial difficulties in his youth, Thomas became a wealthy teacher.
C. Thomas's life was a journey of artistic dedication, evolving from traditional influences to a unique style that left a lasting legacy.
D. The primary achievement of Thomas was establishing a foundation to support his family.

Lời giải
Chọn C
A. Thomas was a sculptor who only created abstract forms to shock the public: Thomas là một nhà điêu khắc chỉ tạo ra các hình thức trừu tượng để gây sốc cho công chúng.
B. Despite financial difficulties in his youth, Thomas became a wealthy teacher: Bất chấp khó khăn tài chính thời trẻ, Thomas trở thành một giáo viên giàu có.
C. Thomas's life was a journey of artistic dedication, evolving from traditional influences to a unique style that left a lasting legacy: Cuộc đời Thomas là hành trình cống hiến nghệ thuật, phát triển từ những ảnh hưởng truyền thống đến phong cách độc đáo để lại di sản lâu dài.
D. The primary achievement of Thomas was establishing a foundation to support his family: Thành tựu chính của Thomas là thành lập một quỹ để hỗ trợ gia đình ông.
Thông tin: Bài viết trình bày hành trình nghệ thuật của Thomas: P1 (tuổi thơ, đam mê nghệ thuật) → P2 (ảnh hưởng từ nghệ thuật cổ) → P3 (phong cách abstract gây tranh cãi) → P4 (di sản để lại, Thomas Foundation).
Tạm dịch: Cuộc đời Thomas là hành trình cống hiến nghệ thuật, phát triển từ những ảnh hưởng truyền thống đến phong cách độc đáo để lại di sản lâu dài.
```

### Ví dụ 7: Sentence Insertion

```
Question 24. Where in paragraph 2 does the following sentence best fit?
"For instance, millions of plastic bottles end up in the ocean every year, harming marine life."
A. [I]		B. [II]		C. [III]		D. [IV]

Lời giải
Chọn A
A. [I]: Vị trí sau câu nói về đồ nhựa tồn tại hàng thế kỷ
B. [II]: Vị trí sau câu nói về chuyển sang đồ tái sử dụng
C. [III]: Vị trí sau câu nói về tái chế bị ô nhiễm
D. [IV]: Vị trí cuối đoạn, trước khi chuyển sang ý mới
Thông tin: Items such as straws, bags, and food packaging are used for minutes but last for centuries. [I] Instead of relying on these disposable conveniences, individuals should switch to reusable alternatives.
Tạm dịch: Các vật dụng như ống hút, túi và bao bì thực phẩm được sử dụng trong vài phút nhưng tồn tại hàng thế kỷ. [I] Thay vì dựa vào những tiện ích dùng một lần này, mọi người nên chuyển sang các lựa chọn thay thế có thể tái sử dụng.
```

### Ví dụ 8: Locating Paragraph

```
Question 25. In which paragraph does the author mention a specific artwork in Paris that inspired Thomas?
A. Paragraph 1		B. Paragraph 2		C. Paragraph 3		D. Paragraph 4

Lời giải
Chọn B
A. Paragraph 1: Đoạn 1 - nói về tuổi thơ và học vấn của Thomas
B. Paragraph 2: Đoạn 2 - nói về ảnh hưởng từ nghệ thuật cổ và tác phẩm ở Paris
C. Paragraph 3: Đoạn 3 - nói về phong cách abstract và sự tranh cãi
D. Paragraph 4: Đoạn 4 - nói về giai đoạn sau chiến tranh và di sản
Thông tin: Specifically, a Mayan statue he observed in Paris became a profound inspiration, heavily influencing his famous reclining figures.
Tạm dịch: Cụ thể, một bức tượng Maya mà ông quan sát ở Paris đã trở thành nguồn cảm hứng sâu sắc, ảnh hưởng mạnh mẽ đến các tác phẩm tượng nằm nổi tiếng của ông.
```

### Ví dụ 9: Detail Question

```
Question 26. According to paragraph 3, why did Thomas decide to stop teaching?
A. Because he wanted to focus entirely on creating his art.
B. Because the critics forced him to leave his job.
C. Because his students did not understand his abstract style.
D. Because he wanted to travel to Paris again.

Lời giải
Chọn A
A. Because he wanted to focus entirely on creating his art: Vì ông muốn tập trung hoàn toàn vào việc sáng tạo nghệ thuật.
B. Because the critics forced him to leave his job: Vì các nhà phê bình buộc ông phải rời bỏ công việc.
C. Because his students did not understand his abstract style: Vì học sinh của ông không hiểu phong cách trừu tượng của ông.
D. Because he wanted to travel to Paris again: Vì ông muốn đi du lịch Paris lần nữa.
Thông tin: Eventually, he chose to resign from his teaching post to devote all his energy to sculpture.
Tạm dịch: Cuối cùng, ông chọn từ chức giảng dạy để dành toàn bộ năng lượng cho điêu khắc.
```

---

# ═══════════════════════════════════════════════════════════════
# CHECKLIST TỔNG HỢP TRƯỚC KHI HOÀN THÀNH
# ═══════════════════════════════════════════════════════════════

## A. Kiểm tra BÀI ĐỌC:
- [ ] Không sao chép > 8 từ liên tiếp từ SOURCE?
- [ ] Khác biệt SOURCE ít nhất 60%?
- [ ] Có đủ [P1], [P2], [P3], [P4]?
- [ ] Đại từ tham chiếu rõ ràng, không mơ hồ?
- [ ] Văn phong tự nhiên (không có dấu hiệu AI)?
- [ ] Độ dài đúng ±10%?

## B. Kiểm tra ĐỊNH DẠNG:
- [ ] **Bôi đậm** từ cho Vocabulary? (số từ = số câu hỏi Vocabulary)
- [ ] **Gạch chân** câu cho Paraphrasing?
- [ ] **Markers [I][II][III][IV]** cho Sentence Insertion?

## C. Kiểm tra CÂU HỎI:
- [ ] Đủ số lượng theo ma trận?
- [ ] Đúng dạng theo ma trận?
- [ ] Đúng cấp độ NB/TH/VD/VDC?
- [ ] ⚠️ Mỗi câu chỉ có **1 đáp án đúng duy nhất**?
- [ ] Đáp án phân bố ngẫu nhiên?
- [ ] Phương án nhiễu có lý do sai rõ ràng?

## D. Kiểm tra LỜI GIẢI:
- [ ] Có Evidence trích từ bài cho MỌI câu?
- [ ] Có dịch tiếng Việt cho Evidence?
- [ ] Giải thích tại sao đáp án đúng?
- [ ] Giải thích tại sao 3 phương án còn lại sai (với lý do cụ thể)?

---

# ═══════════════════════════════════════════════════════════════
# LỖI THƯỜNG GẶP KHI SINH CÂU HỎI - PHẢI TRÁNH
# ═══════════════════════════════════════════════════════════════

## ❌ LỖI 1: CÓ 2 ĐÁP ÁN ĐÚNG
```
❌ SAI: Which is TRUE about technology?
A. It helps preserve culture. → ĐÚNG
B. It makes heritage accessible. → CŨNG ĐÚNG
→ 2 đáp án đúng = VI PHẠM!

✅ ĐÚNG: Thêm điều kiện để chỉ 1 đáp án đúng
"Which is TRUE about the CHALLENGES of technology?"
```

## ❌ LỖI 2: SAI CẤP ĐỘ NHẬN THỨC
```
❌ SAI: Ma trận yêu cầu NB nhưng câu hỏi cần suy luận (VDC)
   Ma trận: Locating - NB
   Câu hỏi: "Which paragraph implies that..." → SAI! (cần suy luận = VDC)

✅ ĐÚNG: Câu hỏi phù hợp cấp độ
   Ma trận: Locating - NB  
   Câu hỏi: "Which paragraph mentions composting?" → ĐÚNG (từ khóa trực tiếp = NB)
```

## ❌ LỖI 3: THIẾU/THỪA CÂU HỎI SO VỚI MA TRẬN
```
❌ SAI: Ma trận yêu cầu 2 câu Best Summarise (đoạn) nhưng chỉ có 1 câu
❌ SAI: Ma trận yêu cầu 10 câu nhưng chỉ có 9 câu

✅ ĐÚNG: Đếm lại và đảm bảo ĐỦ SỐ LƯỢNG và ĐÚNG DẠNG
```

## ❌ LỖI 4: KHÔNG DÙNG ĐÚNG MỎ NEO
```
❌ SAI: Câu Vocabulary hỏi từ KHÔNG được bôi đậm trong PASSAGE
❌ SAI: Câu Paraphrasing hỏi câu KHÔNG được gạch chân trong PASSAGE

✅ ĐÚNG: Hỏi đúng từ/câu đã được đánh dấu trong bài đọc
```

## ❌ LỖI 5: THIẾU LỜI GIẢI HOẶC LỜI GIẢI CHUNG CHUNG
```
❌ SAI: Không có lời giải
❌ SAI: "A sai vì không đúng" → quá chung chung!

✅ ĐÚNG: "A sai vì bài nói 'some students' không phải 'all students' → phóng đại"
```

---

# KẾT THÚC PROMPT

---

## DANH SÁCH LƯU Ý KHI SINH CÂU HỎI

1. ⚠️ **100% TỪ PASSAGE:** Không được dùng kiến thức ngoài bài
2. ⚠️ **1 ĐÁP ÁN ĐÚNG DUY NHẤT:** Kiểm tra kỹ không có 2 đáp án có thể đúng
3. ⚠️ **ĐÚNG CẤP ĐỘ:** Độ khó câu hỏi + bẫy phải phù hợp NB/TH/VD/VDC
4. ⚠️ **ĐỦ SỐ LƯỢNG:** Đếm lại số câu hỏi phải khớp với ma trận
5. ⚠️ **DÙNG ĐÚNG MỎ NEO:** Phải sử dụng chính xác mỏ neo trong bảng
6. ⚠️ **EVIDENCE BẮT BUỘC:** Mọi lời giải phải có trích dẫn từ bài
7. ⚠️ **GIẢI THÍCH CỤ THỂ:** Không được viết chung chung "A sai vì không đúng"
8. ⚠️ **TỪ VỰNG:** Hỏi đúng từ đã **bôi đậm** trong PASSAGE
9. ⚠️ **PARAPHRASE:** Hỏi đúng câu đã **gạch chân** trong PASSAGE
10. ⚠️ **REFERENCE:** Antecedent phải RÕ RÀNG, không mơ hồ
11. ⚠️ **SENTENCE INSERTION:** Vị trí đúng phải khớp với bảng mỏ neo
12. ⚠️ **INFERENCE:** Suy luận từ dữ kiện, không phải suy đoán

---

## QUY TRÌNH SINH ĐỀ HOÀN CHỈNH

```
═══════════════════════════════════════════════════════════════
BƯỚC 1: VIẾT BÀI ĐỌC
═══════════════════════════════════════════════════════════════
a. Đọc SOURCE → Trích KEY FACTS
b. Tạo OUTLINE mới (đổi bố cục khác SOURCE)
c. Viết lại PASSAGE:
   - Không sao chép > 8 từ
   - Khác biệt 60%+
   - Văn phong tự nhiên
   - Cài đủ mỏ neo (bôi đậm, gạch chân, markers)
d. Kiểm tra đại từ không mơ hồ

═══════════════════════════════════════════════════════════════
BƯỚC 2: TẠO BẢNG MỎ NEO
═══════════════════════════════════════════════════════════════
Liệt kê đầy đủ các mỏ neo đã cài:
| STT | Dạng câu hỏi | Cấp độ | Mỏ neo | Vị trí | Ghi chú |

═══════════════════════════════════════════════════════════════
BƯỚC 3: SINH CÂU HỎI
═══════════════════════════════════════════════════════════════
Với MỖI câu hỏi trong ma trận:
a. Viết câu hỏi (đúng dạng + đúng cấp độ)
b. Viết đáp án đúng (dựa trên mỏ neo)
c. Viết 3 phương án nhiễu:
   - NB: sai rõ ràng
   - TH: có vẻ đúng khi đọc lướt
   - VD: gần đúng, thiếu 1 phần
   - VDC: rất hấp dẫn, logic nhưng sai
d. Kiểm tra: Chỉ 1 đáp án đúng?
e. Kiểm tra: Đúng cấp độ nhận thức?

═══════════════════════════════════════════════════════════════
BƯỚC 4: VIẾT LỜI GIẢI
═══════════════════════════════════════════════════════════════
Với MỖI câu hỏi:
a. Ghi đáp án đúng
b. Ghi dạng câu hỏi + cấp độ
c. Phân tích đáp án đúng
d. Trích Evidence từ bài
e. Dịch Evidence sang tiếng Việt
f. Giải thích tại sao 3 đáp án còn lại SAI (lý do cụ thể)

═══════════════════════════════════════════════════════════════
BƯỚC 5: KIỂM TRA TỔNG THỂ
═══════════════════════════════════════════════════════════════
□ Bài đọc: Không sao chép > 8 từ? Khác 60%? Văn phong tự nhiên?
□ Định dạng: Đủ bôi đậm, gạch chân, markers?
□ Câu hỏi: Đủ số lượng? Đúng dạng? Đúng cấp độ?
□ Đáp án: Mỗi câu chỉ 1 đáp án đúng?
□ Lời giải: Có Evidence? Có dịch? Có giải thích 3 đáp án sai?
```

---

## VÍ DỤ BẢNG MỎ NEO CHI TIẾT

Dưới đây là ví dụ bảng mỏ neo đầy đủ cho 1 bài đọc về "Digital Preservation of Cultural Heritage":

| Dạng câu hỏi | Cấp độ | Mỏ neo | Vị trí | Ghi chú |
|--------------|--------|--------|--------|---------|
| Từ vựng - Synonym | TH | **safeguarded** | P1 | = protected, preserved |
| Từ vựng - Antonym | TH | **anxiety** | P3 | ≠ calmness, confidence |
| Paraphrasing | VD | <u>To address these issues, many organisations are adopting a hybrid model that combines physical displays with digital platforms.</u> | P3 | 2 mệnh đề, cause-effect |
| Reference | VD | "These applications" → Artificial Intelligence tools | P4 | Antecedent ở câu trước |
| NOT mentioned | NB | Có: 3D scanning, VR, AI tools; Không có: blockchain | P1-P2 | Blockchain là nhiễu |
| Locating | NB | P1: bamboo dancing; P2: diaspora, identity; P3: anxiety, hybrid model; P4: AI tools | - | Ý độc quyền mỗi đoạn |
| Sentence insertion | TH | [I] sau "identity and origin"; [II] sau "ancestors' customs"; [III] cuối P2; [IV] cuối P3 | P2, P3 | Vị trí đúng: [I] |
| Detail (VD) | VD | "student in London can virtually join a festivity or watch traditional bamboo dancing in Vietnam" | P1 | Chi tiết cụ thể |
| Detail (VDC) | VDC | "diaspora communities to reconnect with their identity and origin" | P2 | Cần tổng hợp nhiều câu |
| Summarise (đoạn) VD | VD | P2: Education + diaspora + tourism | P2 | Topic + 3 examples |
| Summarise (đoạn) VDC | VDC | P3: Challenges (money, skills, authenticity, hybrid model) | P3 | Nhiều ý, không có topic sentence rõ |
| Summarise (bài) | VD | Digital preservation: benefits (P1-P2), challenges (P3), future (P4) | Toàn bài | 1 luận điểm trung tâm |
| Inference | VDC | P1: "share with multicultural audience globally" + P2: "diaspora reconnect with identity" → Technology bridges cultural gaps | P1 + P2 | Không viết thẳng trong bài |

**⚠️ LƯU Ý VỀ BẢNG MỎ NEO:**
- Bảng mỏ neo giúp biết CHÍNH XÁC từ/câu/ý nào đã được cài sẵn để hỏi
- PHẢI sử dụng đúng mỏ neo trong bảng, KHÔNG được tự chọn mỏ neo khác
- Số lượng mỏ neo = số câu hỏi trong ma trận
- Cột "Ghi chú" giúp ghi nhớ đáp án đúng và logic

---

# ═══════════════════════════════════════════════════════════════
# ⚠️⚠️⚠️ MANDATORY SELF-CHECK (BẮT BUỘC THỰC HIỆN) ⚠️⚠️⚠️
# ═══════════════════════════════════════════════════════════════

## TRƯỚC KHI HOÀN THÀNH, BẮT BUỘC THỰC HIỆN CÁC BƯỚC SAU:

### BƯỚC A: RÀ SOÁT SAO CHÉP

**Với TỪNG CÂU trong PASSAGE đã viết:**

1. So sánh với SOURCE gốc
2. Đếm số từ liên tiếp giống nhau
3. Nếu > 8 từ giống → **PHẢI VIẾT LẠI NGAY**

### BƯỚC B: TẠO BẢNG KIỂM TRA SAO CHÉP

**Sau khi viết xong PASSAGE, BẮT BUỘC tạo bảng sau:**

```markdown
## BẢNG KIỂM TRA SAO CHÉP (MANDATORY)

| # | Câu trong PASSAGE | Câu tương ứng trong SOURCE | Số từ giống liên tiếp | Đạt/Không đạt |
|---|-------------------|---------------------------|----------------------|---------------|
| 1 | "Many small groups do not have enough money..." | "Smaller communities often lack the financial resources..." | 0 từ | ✅ ĐẠT |
| 2 | "..." | "..." | X từ | ✅/❌ |
| ... | ... | ... | ... | ... |

**Kết quả:** Tất cả các câu đều < 8 từ giống liên tiếp? [CÓ/KHÔNG]
```

### BƯỚC C: SỬA LỖI (NẾU CÓ)

Nếu có câu nào > 8 từ giống liên tiếp:

1. **DỪNG LẠI** - Không tiếp tục sang phần câu hỏi
2. **VIẾT LẠI** câu đó theo kỹ thuật trong phần CRITICAL WARNING
3. **CẬP NHẬT** bảng kiểm tra
4. **XÁC NHẬN** tất cả đạt trước khi tiếp tục

---

## 📋 CHECKLIST CUỐI CÙNG

Trước khi output kết quả, kiểm tra:

### Bài đọc (PASSAGE):
- [ ] ⚠️ **KHÔNG có cụm > 8 từ giống SOURCE** (đã kiểm tra từng câu)
- [ ] Khác biệt SOURCE ít nhất 60%
- [ ] Đủ 3-4 đoạn với [P1], [P2], [P3], [P4]
- [ ] Văn phong tự nhiên, không dấu hiệu AI
- [ ] Đã bôi đậm từ cho câu hỏi Vocabulary
- [ ] Đã gạch chân câu cho câu hỏi Paraphrasing
- [ ] Đã đánh dấu [I], [II], [III], [IV] cho Sentence Insertion (nếu có)
- [ ] Đại từ tham chiếu không mơ hồ

### Bảng mỏ neo:
- [ ] Đủ số lượng mỏ neo = số câu hỏi trong ma trận
- [ ] Mỗi mỏ neo có vị trí cụ thể [Px]

### Câu hỏi & Đáp án:
- [ ] Đủ số lượng câu hỏi theo ma trận
- [ ] Mỗi câu có đúng 4 phương án A, B, C, D
- [ ] Mỗi câu chỉ có 1 đáp án đúng duy nhất
- [ ] Đúng cấp độ nhận thức (NB/TH/VD/VDC)

### Lời giải:
- [ ] Mỗi câu có Evidence trích từ bài
- [ ] Mỗi câu có Tạm dịch tiếng Việt
- [ ] Mỗi câu giải thích tại sao 3 đáp án còn lại SAI

---

# ═══════════════════════════════════════════════════════════════
# KẾT THÚC PROMPT TỔNG HỢP
# ═══════════════════════════════════════════════════════════════
