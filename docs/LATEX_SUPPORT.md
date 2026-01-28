# LaTeX Support in Questions

## Cách sử dụng công thức LaTeX trong câu hỏi

Client hiện đã hỗ trợ hiển thị công thức toán học sử dụng cú pháp LaTeX.

### Cú pháp

#### 1. Inline Math (công thức trong dòng)

```
Giá trị của $x^2 + y^2 = 25$ là bao nhiêu?
```

Hiển thị: Giá trị của x² + y² = 25 là bao nhiêu?

#### 2. Display Math (công thức riêng dòng)

```
Công thức tính diện tích hình tròn:
$$A = \pi r^2$$
```

Hiển thị công thức ở giữa và lớn hơn.

### Ví dụ câu hỏi

#### Câu TN với công thức

```json
{
  "question_stem": "Giải phương trình $x^2 - 5x + 6 = 0$. Tổng hai nghiệm là:",
  "options": {
    "A": "$x_1 + x_2 = 5$",
    "B": "$x_1 + x_2 = -5$",
    "C": "$x_1 + x_2 = 6$",
    "D": "$x_1 + x_2 = -6$"
  },
  "correct_answer": "A",
  "explanation": "Theo định lý Viète: $x_1 + x_2 = -\\frac{b}{a} = -\\frac{-5}{1} = 5$"
}
```

#### Câu DS với công thức

```json
{
  "source_text": "Cho hàm số $f(x) = x^3 - 3x^2 + 2$. Xét tính đúng sai của các mệnh đề sau:",
  "statements": {
    "a": {
      "text": "Đạo hàm $f'(x) = 3x^2 - 6x$",
      "correct_answer": true
    },
    "b": {
      "text": "Hàm số đạt cực tiểu tại $x = 2$",
      "correct_answer": true
    }
  }
}
```

### Một số ký hiệu LaTeX thường dùng

| Ký hiệu          | LaTeX Code                               | Hiển thị      |
| ---------------- | ---------------------------------------- | ------------- |
| Phân số          | `$\frac{a}{b}$`                          | a/b           |
| Căn bậc hai      | `$\sqrt{x}$`                             | √x            |
| Căn bậc n        | `$\sqrt[n]{x}$`                          | ⁿ√x           |
| Mũ               | `$x^2$` hoặc `$x^{10}$`                  | x² hoặc x¹⁰   |
| Chỉ số           | `$x_1$` hoặc `$x_{10}$`                  | x₁ hoặc x₁₀   |
| Tổng             | `$\sum_{i=1}^{n}$`                       | Σ(i=1 đến n)  |
| Tích phân        | `$\int_{a}^{b} f(x) dx$`                 | ∫[a,b] f(x)dx |
| Pi               | `$\pi$`                                  | π             |
| Alpha, Beta      | `$\alpha, \beta$`                        | α, β          |
| Lớn hơn, nhỏ hơn | `$\geq, \leq$`                           | ≥, ≤          |
| Vô cùng          | `$\infty$`                               | ∞             |
| Vector           | `$\vec{v}$` hoặc `$\overrightarrow{AB}$` | v⃗ hoặc AB⃗   |

### Tips

1. **Escape ký tự đô la**: Nếu muốn hiển thị ký tự `$` thật, dùng `\$`
2. **Dấu ngoặc nhọn**: Dùng khi có nhiều ký tự trong mũ/chỉ số: `$x^{10}$` thay vì `$x^10$`
3. **Display mode**: Dùng `$$...$$` cho công thức quan trọng cần hiển thị riêng dòng
4. **Kiểm tra syntax**: Sử dụng [KaTeX playground](https://katex.org/) để test công thức

### Chỉnh sửa câu hỏi có LaTeX

- Khi nhấp vào câu hỏi để edit, text sẽ hiển thị ở dạng raw (với `$...$`)
- Nhập công thức LaTeX như bình thường
- Khi blur (click ra ngoài), công thức sẽ tự động render

### Troubleshooting

Nếu công thức không hiển thị đúng:

1. Kiểm tra cú pháp LaTeX có đúng không
2. Đảm bảo có đóng `$` hoặc `$$` đầy đủ
3. Một số ký tự đặc biệt cần escape: `\{`, `\}`, `\_`, `\$`
4. Check console browser để xem error message
