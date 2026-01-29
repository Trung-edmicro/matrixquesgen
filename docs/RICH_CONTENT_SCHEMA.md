# Rich Content JSON Schema

## Tổng quan

Cấu trúc JSON mới hỗ trợ:

- ✅ Text thuần (backward compatible)
- ✅ Ảnh (images)
- ✅ Bảng (tables)
- ✅ Biểu đồ ECharts (charts)
- ✅ Công thức toán (LaTeX/KaTeX)
- ✅ Mixed content (text + images + tables + charts)

## Cấu trúc Content Block

### Content Block Types

Mỗi phần tử content là một **Content Block** với cấu trúc:

```json
{
  "type": "text|image|table|chart|latex|mixed",
  "content": "...",
  "metadata": {}
}
```

### 1. Text Block (Simple - Backward Compatible)

```json
{
  "type": "text",
  "content": "Câu hỏi đơn giản chỉ có text"
}
```

Hoặc shorthand (tương thích ngược):

```json
"Câu hỏi đơn giản chỉ có text"
```

### 2. Image Block

```json
{
  "type": "image",
  "content": "https://example.com/image.png",
  "metadata": {
    "alt": "Mô tả ảnh",
    "width": 500,
    "height": 300,
    "caption": "Hình 1: Biểu đồ nhiệt độ"
  }
}
```

### 3. Table Block

```json
{
  "type": "table",
  "content": {
    "headers": ["Cột 1", "Cột 2", "Cột 3"],
    "rows": [
      ["Data 1", "Data 2", "Data 3"],
      ["Data 4", "Data 5", "Data 6"]
    ]
  },
  "metadata": {
    "caption": "Bảng 1: Kết quả thí nghiệm",
    "bordered": true,
    "striped": true
  }
}
```

### 4. Chart Block (ECharts)

```json
{
  "type": "chart",
  "content": {
    "chartType": "line|bar|pie|scatter|heatmap",
    "echarts": {
      "title": { "text": "Biểu đồ nhiệt độ" },
      "xAxis": { "type": "category", "data": ["Mon", "Tue", "Wed"] },
      "yAxis": { "type": "value" },
      "series": [
        {
          "data": [120, 200, 150],
          "type": "line"
        }
      ]
    }
  },
  "metadata": {
    "caption": "Biểu đồ 1: Nhiệt độ theo thời gian",
    "width": "100%",
    "height": 400
  }
}
```

### 5. LaTeX Block

```json
{
  "type": "latex",
  "content": "E = mc^2",
  "metadata": {
    "display": "inline|block"
  }
}
```

### 6. Mixed Block (Complex Content)

```json
{
  "type": "mixed",
  "content": [
    {
      "type": "text",
      "content": "Quan sát hình sau:"
    },
    {
      "type": "image",
      "content": "https://example.com/diagram.png",
      "metadata": { "width": 400 }
    },
    {
      "type": "text",
      "content": "Dựa vào bảng số liệu:"
    },
    {
      "type": "table",
      "content": {
        "headers": ["Thời gian (s)", "Nhiệt độ (°C)"],
        "rows": [
          ["0", "20"],
          ["60", "80"],
          ["120", "100"]
        ]
      }
    }
  ]
}
```

## Cấu trúc Question mới

### TN (Multiple Choice) - Rich Content

```json
{
  "question_code": "C1",
  "question_type": "TN",
  "lesson_name": "Bài 1. Cấu trúc của chất",
  "chapter_number": "1",
  "lesson_number": "1",
  "level": "NB",

  "question_stem": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "Quan sát biểu đồ sau:"
      },
      {
        "type": "chart",
        "content": {
          "chartType": "line",
          "echarts": {
            "title": { "text": "Sự thay đổi nhiệt độ" },
            "xAxis": { "data": ["0s", "30s", "60s", "90s"] },
            "yAxis": { "type": "value" },
            "series": [{ "data": [20, 50, 80, 100], "type": "line" }]
          }
        }
      },
      {
        "type": "text",
        "content": "Nhiệt độ tại thời điểm 60s là bao nhiêu?"
      }
    ]
  },

  "options": {
    "A": "50°C",
    "B": {
      "type": "mixed",
      "content": [
        { "type": "text", "content": "80°C với đồ thị: " },
        {
          "type": "image",
          "content": "graph_b.png",
          "metadata": { "width": 100 }
        }
      ]
    },
    "C": "100°C",
    "D": "120°C"
  },

  "correct_answer": "B",

  "explanation": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "Từ biểu đồ ta thấy:"
      },
      {
        "type": "table",
        "content": {
          "headers": ["Thời gian", "Nhiệt độ"],
          "rows": [
            ["60s", "80°C"],
            ["90s", "100°C"]
          ]
        }
      },
      {
        "type": "text",
        "content": "Vậy đáp án đúng là B: 80°C"
      }
    ]
  }
}
```

### DS (True/False) - Rich Content

```json
{
  "question_code": "C1",
  "question_type": "DS",
  "lesson_name": "Bài 2. Nội năng",
  "chapter_number": "1",
  "lesson_number": "2",
  "level": "mixed",

  "source_text": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "Xét thí nghiệm sau:"
      },
      {
        "type": "image",
        "content": "experiment_setup.png",
        "metadata": {
          "caption": "Hình 1: Bộ thí nghiệm",
          "width": 500
        }
      },
      {
        "type": "text",
        "content": "Kết quả đo được:"
      },
      {
        "type": "table",
        "content": {
          "headers": ["Lần đo", "Nhiệt độ (°C)", "Áp suất (atm)"],
          "rows": [
            ["1", "25", "1.0"],
            ["2", "50", "1.5"],
            ["3", "75", "2.0"]
          ]
        },
        "metadata": { "caption": "Bảng 1: Kết quả thí nghiệm" }
      }
    ]
  },

  "statements": {
    "a": {
      "text": "Áp suất tỉ lệ thuận với nhiệt độ",
      "is_correct": true
    },
    "b": {
      "text": {
        "type": "mixed",
        "content": [
          { "type": "text", "content": "Đồ thị " },
          {
            "type": "image",
            "content": "graph_option.png",
            "metadata": { "width": 80 }
          },
          { "type": "text", "content": " biểu diễn đúng mối quan hệ" }
        ]
      },
      "is_correct": false
    },
    "c": {
      "text": "Ở 100°C, áp suất khoảng 2.5 atm",
      "is_correct": true
    },
    "d": {
      "text": "Thể tích khí tăng khi nhiệt độ tăng",
      "is_correct": true
    }
  },

  "explanation": {
    "a": {
      "type": "mixed",
      "content": [
        { "type": "text", "content": "Đúng. Từ bảng số liệu, ta có biểu đồ: " },
        {
          "type": "chart",
          "content": {
            "chartType": "scatter",
            "echarts": {
              "xAxis": { "name": "Nhiệt độ (°C)" },
              "yAxis": { "name": "Áp suất (atm)" },
              "series": [
                {
                  "data": [
                    [25, 1.0],
                    [50, 1.5],
                    [75, 2.0]
                  ],
                  "type": "scatter"
                }
              ]
            }
          }
        }
      ]
    },
    "b": "Sai. Đồ thị không phản ánh đúng mối quan hệ tuyến tính.",
    "c": "Đúng. Theo quy luật tỉ lệ: P = 2.5 atm khi T = 100°C",
    "d": "Đúng. Theo định luật Gay-Lussac"
  }
}
```

### TLN (Short Answer) - Rich Content

```json
{
  "question_code": "C1",
  "question_type": "TLN",
  "lesson_name": "Bài 3. Nhiệt độ",
  "chapter_number": "1",
  "lesson_number": "3",
  "level": "VD",

  "question_stem": {
    "type": "mixed",
    "content": [
      { "type": "text", "content": "Xem biểu đồ sau:" },
      {
        "type": "chart",
        "content": {
          "chartType": "line",
          "echarts": {
            "title": { "text": "Quá trình đun nóng nước" },
            "xAxis": { "name": "Thời gian (phút)" },
            "yAxis": { "name": "Nhiệt độ (°C)" },
            "series": [
              {
                "data": [
                  [0, 20],
                  [5, 50],
                  [10, 80],
                  [15, 100],
                  [20, 100]
                ],
                "type": "line"
              }
            ]
          }
        }
      },
      {
        "type": "text",
        "content": "Giải thích tại sao từ phút 15-20, nhiệt độ không tăng?"
      }
    ]
  },

  "correct_answer": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "Từ phút 15-20, nước đã đạt nhiệt độ sôi 100°C. "
      },
      {
        "type": "text",
        "content": "Nhiệt lượng cung cấp không làm tăng nhiệt độ mà dùng để "
      },
      {
        "type": "latex",
        "content": "Q = mL",
        "metadata": { "display": "inline" }
      },
      {
        "type": "text",
        "content": " chuyển nước từ thể lỏng sang thể khí (hoá hơi)."
      }
    ]
  },

  "explanation": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "Đây là hiện tượng sôi. Trong giai đoạn chuyển thể:"
      },
      {
        "type": "image",
        "content": "phase_change.png",
        "metadata": { "width": 400, "caption": "Quá trình chuyển thể" }
      },
      { "type": "text", "content": "Nhiệt độ giữ nguyên ở nhiệt độ sôi." }
    ]
  }
}
```

### TL (Essay) - Rich Content

```json
{
  "question_code": "C1",
  "question_type": "TL",
  "lesson_name": "Bài 4. Khí lí tưởng",
  "chapter_number": "1",
  "lesson_number": "4",
  "level": "VD",

  "question_stem": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "Phân tích ba quá trình biến đổi trạng thái sau của khí lí tưởng:"
      },
      {
        "type": "chart",
        "content": {
          "chartType": "line",
          "echarts": {
            "title": { "text": "Đồ thị p-V" },
            "xAxis": { "name": "Thể tích V (lít)" },
            "yAxis": { "name": "Áp suất p (atm)" },
            "series": [
              {
                "name": "Đẳng nhiệt",
                "data": [
                  [1, 10],
                  [2, 5],
                  [4, 2.5],
                  [10, 1]
                ],
                "type": "line"
              },
              {
                "name": "Đẳng áp",
                "data": [
                  [1, 5],
                  [2, 5],
                  [4, 5],
                  [10, 5]
                ],
                "type": "line"
              },
              {
                "name": "Đẳng tích",
                "data": [
                  [2, 2],
                  [2, 5],
                  [2, 8],
                  [2, 10]
                ],
                "type": "line"
              }
            ]
          }
        }
      },
      {
        "type": "text",
        "content": "Giải thích đặc điểm mỗi quá trình và so sánh (150-200 từ)"
      }
    ]
  },

  "correct_answer": {
    "type": "mixed",
    "content": [
      {
        "type": "text",
        "content": "**1. Quá trình đẳng nhiệt (T = const):**\n"
      },
      { "type": "text", "content": "Theo định luật Boyle-Mariotte: " },
      {
        "type": "latex",
        "content": "pV = const",
        "metadata": { "display": "block" }
      },
      {
        "type": "text",
        "content": "Đồ thị là hyperbol trong hệ toạ độ p-V.\n\n"
      },

      { "type": "text", "content": "**2. Quá trình đẳng áp (p = const):**\n" },
      { "type": "text", "content": "Theo định luật Gay-Lussac: " },
      {
        "type": "latex",
        "content": "\\frac{V}{T} = const",
        "metadata": { "display": "block" }
      },
      {
        "type": "text",
        "content": "Đồ thị là đường thẳng song song với trục V.\n\n"
      },

      {
        "type": "text",
        "content": "**3. Quá trình đẳng tích (V = const):**\n"
      },
      { "type": "text", "content": "Theo định luật Charles: " },
      {
        "type": "latex",
        "content": "\\frac{p}{T} = const",
        "metadata": { "display": "block" }
      },
      {
        "type": "text",
        "content": "Đồ thị là đường thẳng song song với trục p.\n\n"
      },

      {
        "type": "table",
        "content": {
          "headers": ["Quá trình", "Đại lượng không đổi", "Định luật"],
          "rows": [
            ["Đẳng nhiệt", "Nhiệt độ T", "pV = const"],
            ["Đẳng áp", "Áp suất p", "V/T = const"],
            ["Đẳng tích", "Thể tích V", "p/T = const"]
          ]
        }
      }
    ]
  }
}
```

## File Structure

### Complete Question Set

```json
{
  "metadata": {
    "session_id": "uuid",
    "subject": "VATLY",
    "grade": "C12",
    "curriculum": "KNTT",
    "matrix_file": "Ma trận_VATLY_KNTT_C12.xlsx",
    "total_questions": 12,
    "tn_count": 5,
    "ds_count": 2,
    "tln_count": 3,
    "tl_count": 2,
    "generated_at": "2026-01-28T12:00:00",
    "status": "completed",
    "content_version": "2.0",
    "supports_rich_content": true
  },
  "questions": {
    "TN": [
      /* TN questions */
    ],
    "DS": [
      /* DS questions */
    ],
    "TLN": [
      /* TLN questions */
    ],
    "TL": [
      /* TL questions */
    ]
  }
}
```

## Backward Compatibility

### Simple Text (Old Format)

```json
{
  "question_stem": "Câu hỏi đơn giản",
  "options": {
    "A": "Đáp án A",
    "B": "Đáp án B"
  },
  "explanation": "Giải thích đơn giản"
}
```

### Auto-converted to Rich Format

```json
{
  "question_stem": {
    "type": "text",
    "content": "Câu hỏi đơn giản"
  },
  "options": {
    "A": { "type": "text", "content": "Đáp án A" },
    "B": { "type": "text", "content": "Đáp án B" }
  },
  "explanation": {
    "type": "text",
    "content": "Giải thích đơn giản"
  }
}
```

## Implementation Notes

### 1. Parser/Validator

- Validate content block types
- Support both old (text) and new (rich) formats
- Auto-detect and convert simple text to rich format

### 2. Renderer (Frontend)

- Text: Simple `<p>` or `<span>`
- Image: `<img>` with lazy loading
- Table: `<table>` with Tailwind classes
- Chart: ECharts component
- LaTeX: KaTeX renderer
- Mixed: Recursive rendering

### 3. Generator (AI)

- Prompt AI to return structured content
- Parse AI response to extract images, tables, charts
- Store images in CDN/local storage
- Generate ECharts config from data

### 4. Storage

- Images: Store in `data/images/` or CDN
- Charts: Store config in JSON (data-driven)
- Keep JSON file size reasonable (<10MB per file)

## Example Use Cases

### Case 1: Physics with Chart

```json
{
  "question_stem": {
    "type": "mixed",
    "content": [
      { "type": "text", "content": "Đồ thị vận tốc-thời gian:" },
      {
        "type": "chart",
        "content": {
          "chartType": "line",
          "echarts": {
            /* config */
          }
        }
      },
      { "type": "text", "content": "Tính quãng đường?" }
    ]
  }
}
```

### Case 2: Chemistry with Table

```json
{
  "source_text": {
    "type": "mixed",
    "content": [
      { "type": "text", "content": "Bảng tuần hoàn một phần:" },
      {
        "type": "table",
        "content": {
          "headers": ["Nguyên tố", "Ký hiệu", "Số hiệu nguyên tử"],
          "rows": [
            ["Hydro", "H", "1"],
            ["Helium", "He", "2"]
          ]
        }
      }
    ]
  }
}
```

### Case 3: Geography with Image

```json
{
  "question_stem": {
    "type": "mixed",
    "content": [
      { "type": "text", "content": "Quan sát bản đồ:" },
      {
        "type": "image",
        "content": "map_vietnam.png",
        "metadata": { "width": 600, "caption": "Bản đồ Việt Nam" }
      },
      { "type": "text", "content": "Xác định vùng địa lí nào?" }
    ]
  }
}
```
