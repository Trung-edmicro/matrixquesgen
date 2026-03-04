"""
Chart Generation Helper - Tạo biểu đồ riêng biệt để giảm nested complexity

KIẾN TRÚC LAYOUT SYSTEM (4 tầng):
====================================

1. SCHEMA (get_chart_data_schema):
   - Định nghĩa layoutLevel + layoutKey
   - AI chỉ KHAI BÁO, KHÔNG tính toán
   
2. PROMPT (build_chart_generation_prompt):
   - Hướng dẫn AI sử dụng layoutLevel
   - Ví dụ: ["source", "title", "legend"]
   
3. VALIDATE (validate_chart_completeness):
   - Kiểm tra layoutLevel/layoutKey hợp lệ
   - Đảm bảo consistency giữa các block
   
4. RUNTIME (apply_layout):
   - Tính toán grid.bottom dựa trên layoutLevel
   - Gọi trong merge_chart_into_question()
   - Đảm bảo HTML/DOCX/PNG render đồng nhất

👉 AI khai báo → Backend resolve → Frontend render
"""
from typing import Dict, List, Optional
import json


def get_chart_data_schema() -> Dict:
    """
    Trả về schema cho chart data (không nested)
    Dùng cho STEP 1: AI tạo chart riêng
    """
    return {
        "type": "object",
        "properties": {
            "charts": {
                "type": "array",
                "description": "Array các biểu đồ",
                "items": {
                    "type": "object",
                    "properties": {
                        "chart_id": {
                            "type": "string",
                            "description": "ID biểu đồ (VD: 'chart_1', 'chart_2')"
                        },
                        "title": {
                            "type": "string",
                            "description": "Tiêu đề biểu đồ (ngắn gọn, mô tả nội dung)"
                        },
                        "chartType": {
                            "type": "string",
                            "enum": ["bar", "line"],
                            "description": "Loại biểu đồ, khuyến khinh chỉ dùng 'bar' hoặc 'line'"
                        },
                        "echarts": {
                            "type": "object",
                            "description": "ECharts config đầy đủ",
                            "properties": {
                                "textStyle": {
                                    "type": "object",
                                    "properties": {
                                        "fontFamily": {
                                            "type": "string",
                                            "default": "Roboto, sans-serif"
                                        }
                                    }
                                },

                                "layoutLevel": {
                                    "type": "array",
                                    "description": "Thứ tự các block dưới biểu đồ (từ thấp lên cao)",
                                    "items": {
                                        "type": "string",
                                        "enum": ["source", "title", "legend"]
                                    },
                                    "default": ["source", "title", "legend"]
                                },

                                "title": {
                                    "type": "object",
                                    "description": "Tiêu đề biểu đồ (sẽ tự động đặt ở dưới biểu đồ, KHÔNG set top/bottom)",
                                    "properties": {
                                        "layoutKey": {
                                            "type": "string",
                                            "enum": ["title"],
                                            "default": "title",
                                            "description": "LUÔN set = 'title' để backend tự động positioning"
                                        },
                                        "text": {"type": "string"},
                                        "left": {"type": "string", "default": "center"},
                                        "textStyle": {
                                            "type": "object",
                                            "properties": {
                                                "fontSize": {"type": "number", "default": 18},
                                                "fontWeight": {"type": "string", "default": "bold"},
                                                "lineHeight": {"type": "number", "default": 20}
                                            }
                                        }
                                    },
                                    "required": ["text"]
                                },

                                "legend": {
                                    "type": "object",
                                    "description": "Chú thích biểu đồ (sẽ tự động đặt ở dưới biểu đồ, KHÔNG set top/bottom)",
                                    "properties": {
                                        "layoutKey": {
                                            "type": "string",
                                            "enum": ["legend"],
                                            "default": "legend",
                                            "description": "LUÔN set = 'legend' để backend tự động positioning"
                                        },
                                        "left": {"type": "string", "default": "center"},
                                        "itemGap": {"type": "number", "default": 20}
                                    }
                                },
                                
                                "grid": {
                                    "type": "object",
                                    "properties": {
                                        "top": {
                                            "type": "number",
                                            "description": "DO NOT set manually when layoutLevel is present"
                                        },
                                        "bottom": {
                                            "type": "number",
                                            "description": "DO NOT set manually when layoutLevel is present"
                                        },
                                        "left": {"type": "number", "default": 60},
                                        "right": {"type": "number", "default": 40}
                                    }
                                },

                                "xAxis": {
                                    "anyOf": [
                                        {
                                            "type": "object",
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "enum": ["category", "value", "time", "log"],
                                                    "description": "Loại trục: 'category' cho dữ liệu phân loại (tên, năm), 'value' cho số liệu liên tục"
                                                },
                                                "data": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "BẮT BUỘC: Array dữ liệu trục X (chỉ dùng khi type='category')"
                                                },
                                                "nameLocation": {"type": "string", "default": "end"},
                                                "nameGap": {"type": "number"},
                                                "nameTextStyle": {
                                                    "type": "object",
                                                    "properties": {
                                                        "fontSize": {"type": "number", "default": 15},
                                                        "fontWeight": {"type": "string", "default": "bold"}
                                                    }
                                                },
                                                "axisLine": {
                                                    "type": "object",
                                                    "properties": {
                                                        "show": {"type": "boolean", "default": True}
                                                    }
                                                },
                                                "axisTick": {
                                                    "type": "object",
                                                    "properties": {
                                                        "show": {"type": "boolean", "default": True}
                                                    }
                                                }
                                            },
                                            "required": ["data", "type", "nameLocation", "axisLine", "axisTick"]
                                        },
                                        {"type": "array"}
                                    ]
                                },
                                "yAxis": {
                                    "anyOf": [
                                        {
                                            "type": "object",
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "enum": ["value", "category", "time", "log"],
                                                    "description": "Loại trục: 'value' cho trục số, 'category' cho dữ liệu phân loại"
                                                },
                                                "name": {"type": "string"}
                                            }
                                        },
                                        {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {
                                                        "type": "string",
                                                        "enum": ["value", "category", "time", "log"],
                                                        "description": "Loại trục: 'value' cho trục số, 'category' cho dữ liệu phân loại"
                                                    },
                                                    "name": {"type": "string"},
                                                    "min": {"type": "number"},
                                                    "max": {"type": "number"},
                                                    "interval": {"type": "number"},
                                                    "position": {"type": "string"},
                                                    "axisLine": {
                                                        "type": "object",
                                                        "properties": {
                                                            "show": {"type": "boolean", "default": True, "description": "Bắt buộc show axisLine"},
                                                            "symbol": {"type": "array", "items": {"type": "string"}, "default": ["none", "arrow"]},
                                                            "symbolSize": {"type": "array", "items": {"type": "number"}, "default": [8, 12]}
                                                        }
                                                    },
                                                    "axisTick": {
                                                        "type": "object",
                                                        "properties": { 
                                                            "show": { "type": "boolean", "default": True }
                                                        }
                                                    },
                                                    "axisLabel": {
                                                        "type": "object",
                                                        "properties": { 
                                                            "show": { "type": "boolean", "default": True }
                                                        }
                                                    },
                                                    "splitLine": {
                                                        "type": "object",
                                                        "properties": { 
                                                            "show": { "type": "boolean", "default": False, "description": "Bắt buộc không show splitLine" }
                                                        }
                                                    },
                                                    "nameLocation": {
                                                        "type": "string",
                                                        "default": "end"
                                                    },
                                                    "nameGap": {
                                                        "type": "number",
                                                        "default": 15
                                                    },
                                                    "nameTextStyle": {
                                                        "type": "object",
                                                        "properties": {
                                                            "fontSize": {"type": "number", "default": 15},
                                                            "fontWeight": {"type": "string", "default": "bold"}
                                                        }
                                                    }
                                                },
                                                "required": ["type", "name", "axisLine", "axisTick", "axisLabel", "splitLine", "nameLocation", "nameGap"]
                                            }
                                        }
                                    ]
                                },
                                "series": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "type": {"type": "string", "enum": ["bar", "line"]},
                                            "data": {
                                                "type": "array",
                                                "items": {"type": "number"},
                                                "description": "BẮT BUỘC: Array số liệu"
                                            },
                                            "yAxisIndex": {"type": "integer"},
                                            "label": {
                                                "type": "object",
                                                "properties": {
                                                    "show": {"type": "boolean", "default": True},
                                                    "position": {"type": "string", "default": "inside"},
                                                    "formatter": {"type": "string", "default": "{c}"},
                                                }
                                            },
                                        },
                                        "required": ["name", "type", "data"]
                                    }
                                },
                                "graphic": {
                                    "type": "array",
                                    "description": "Text nguồn dữ liệu (sẽ tự động đặt ở dưới cùng, KHÔNG set top/bottom)",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "layoutKey": {
                                                "type": "string",
                                                "enum": ["source"],
                                                "default": "source",
                                                "description": "LUÔN set = 'source' để backend tự động positioning"
                                            },
                                            "type": {"type": "string", "enum": ["text"]},
                                            "left": {"type": "string", "default": "center"},
                                            "style": {
                                                "type": "object",
                                                "properties": {
                                                    "text": {"type": "string"},
                                                    "fontSize": {"type": "number", "default": 14},
                                                    "lineHeight": {"type": "number", "default": 16},
                                                    "textAlign": {"type": "string", "enum": ["center", "left", "right"], "default": "center", "description": "Căn giữa text (sử dụng textAlign cho ECharts graphic)"}
                                                },
                                                "required": ["text"]
                                            }
                                        },
                                        "required": ["type", "style"]
                                    }
                                }
                            },
                            "required": ["xAxis", "yAxis", "series"]
                        }
                    },
                    "required": ["chart_id", "title", "chartType", "echarts"]
                }
            }
        },
        "required": ["charts"]
    }


def build_chart_generation_prompt(
    lesson_name: str,
    num_charts: int,
    supplementary_materials: Optional[str] = None
) -> str:
    """
    Tạo prompt để AI sinh chart data
    
    Args:
        lesson_name: Tên bài học
        num_charts: Số lượng chart cần tạo
        supplementary_materials: Tài liệu bổ sung (từ enriched_matrix)
    
    Returns:
        str: Prompt đầy đủ
    """
    # Xác định nguồn dữ liệu
    if supplementary_materials and supplementary_materials.strip():
        print("✓ Using supplementary materials for chart generation (strict mode).")
        data_source = f"""
**DỮ LIỆU TỪ TÀI LIỆU BỔ SUNG:**
```
{supplementary_materials}
```

{'='*70}
⚠️ QUY TẮC BẮT BUỘC KHI CÓ TÀI LIỆU BỔ SUNG:
{'='*70}

1. **CHỈ SỬ DỤNG DỮ LIỆU TỪNG CÓ TRONG TÀI LIỆU TRÊN**
   - Không được thêm địa danh/trạm/năm không có trong tài liệu
   - Không được bỏ bất kỳ địa danh/trạm nào có trong tài liệu
   - Không được tự nghĩ hoặc tìm thêm dữ liệu từ nguồn khác

2. **VÍ DỤ:**
   ✅ ĐÚNG: Tài liệu có "Hà Nội, Huế, Cà Mau" 
            → Chart chỉ dùng 3 trạm này
   
   ❌ SAI: Tài liệu có "Hà Nội, Huế, Cà Mau"
           → Chart lại có "Hà Nội, Huế, Đà Nẵng, TP.HCM, Cà Mau"
           (Thêm Đà Nẵng, TP.HCM không có trong tài liệu)
   
   ❌ SAI: Câu hỏi nói "Hà Nội và TP. HCM" 
           → Nhưng tài liệu không có TP.HCM
           → BẮT BUỘC sửa câu hỏi thành "Hà Nội và Cà Mau" hoặc các trạm CÓ trong tài liệu

3. **XỬ LÝ KHI THIẾU DỮ LIỆU:**
   - Nếu câu hỏi muốn so sánh "Hà Nội và TP.HCM" nhưng tài liệu không có TP.HCM
     → Thay thế bằng trạm khác CÓ TRONG TÀI LIỆU (VD: "Hà Nội và Cà Mau")
   - Giải thích và đáp án phải dựa trên dữ liệu THỰC TẾ từ tài liệu

4. **NGUỒN DỮ LIỆU:**
   - Ghi đúng nguồn từ tài liệu (VD: "Nguồn: Niên giám Thống kê 2023")
   - Nếu tài liệu không ghi rõ nguồn → Dùng "Nguồn: Tài liệu bổ sung"

{'='*70}
"""
    else:
        print("⚠️ No supplementary materials - AI will search external data sources.")
        data_source = """
**NGUỒN DỮ LIỆU BÊN NGOÀI:**

⚠️ KHÔNG có tài liệu bổ sung → Tìm kiếm dữ liệu từ các nguồn chính thống:

1. **Nguồn ưu tiên:**
   - Niên giám Thống kê Việt Nam 2023, 2024
   - Tổng cục Thống kê (www.gso.gov.vn)
   - Báo cáo chính thức của Bộ, Ngành

2. **Yêu cầu:**
   - Dữ liệu phải chính xác, cập nhật
   - Chọn các địa danh/trạm đại diện, phù hợp với bài học
   - Ghi RÕ nguồn trong graphic (VD: "Nguồn: Niên giám Thống kê 2023")

3. **VÍ DỤ:**
   ✅ "Dân số thành thị 2010-2023" → Lấy từ Niên giám thống kê
   ✅ "Nhiệt độ trung bình Hà Nội, Huế, TP.HCM" → Chọn 3 trạm đại diện
   ✅ Ghi nguồn: "Nguồn: Niên giám Thống kê 2023"
"""
    
    # JSON examples (tách ra để tránh f-string nested too deeply)
    layout_example = '''{
  "echarts": {
    "layoutLevel": ["source", "title", "legend"],
    "title": {
      "layoutKey": "title",
      "text": "...",
      "left": "center"
    },
    "legend": {
      "layoutKey": "legend",
      "left": "center"
    },
    "graphic": [{
      "layoutKey": "source",
      "type": "text",
      "left": "center",
      "style": {
        "text": "Nguồn: ...",
        "textAlign": "center"
      }
    }]
  }
}'''
    
    axis_example = '''{
  "xAxis": {
    "type": "category",
    "data": ["2010", "2015", "2021"],
    "nameLocation": "center"
  },
  "yAxis": {
    "type": "value",
    "name": "Dân số (triệu người)",
    "nameLocation": "end"
  }
}'''
    
    prompt = f"""
Tạo {num_charts} biểu đồ thống kê cho bài học: "{lesson_name}"

{data_source}

**YÊU CẦU BIỂU ĐỒ:**

1. **Mỗi chart phải có:**
   - chart_id: Unique ID (chart_1, chart_2, ...)
   - title: Tiêu đề ngắn gọn (VD: "Dân số thành thị 2010-2021")
   - chartType: bar, line, pie, hoặc combo

2. **ECharts config ĐẦY ĐỦ:**
   - xAxis: 
     - type: "category" (BẮT BUỘC cho dữ liệu phân loại: năm, tên, địa điểm)
     - data: Array các giá trị (VD: ["2010", "2015", "2021"])
     - nameLocation: "center" hoặc "end"
     - axisLine, axisTick với show: true
   - yAxis: Object hoặc array (dual yAxis nếu cần)
     - type: "value" (BẮT BUỘC cho trục số liệu)
     - Có name (đơn vị: "triệu người", "%", "tỷ USD")
     - Có min, max, interval nếu cần
     - Có position ('left' hoặc 'right' cho dual yAxis)
     - axisLine, axisTick, axisLabel với show: true (bắt buộc)
     - splitLine với show: false (bắt buộc)
     - nameLocation: 'end' (default), nameGap: 15, nameTextStyle với fontSize, fontWeight
   - series: Array ít nhất 1 series
     - name: Tên series (VD: "Dân số thành thị")
     - type: bar, line
     - data: Array số liệu THỰC (VD: [26.5, 30.9, 36.6])
     - label: show: true, position: 'inside'
   - graphic: Array chứa text nguồn
     - type: "text"
     - left: "center"
     - style.text: "Nguồn: [tên nguồn]"
     - style.fontSize: 14 (BẮT BUỘC để dễ đọc)
     - style.textAlign: "center" (BẮT BUỘC để căn giữa text)

3. **TÍNH NĂNG NÂNG CAO (tùy chọn):**
   - Dual yAxis nếu có 2 loại dữ liệu khác đơn vị (position: 'left', 'right')
   - Combo chart (bar + line) nếu cần so sánh
   - Legend với bottom: 70
   - Grid với top, bottom, left, right để điều chỉnh không gian
   - TextStyle với fontFamily: 'Roboto, sans-serif'
   - Title textStyle với fontSize: 19, fontWeight: 'bold'
   - Axis nameTextStyle với fontSize: 15, fontWeight: 'bold'
   - Graphic style.fontSize: 14, style.textAlign: 'center' cho nguồn dữ liệu

4. **LAYOUT RULE (BẮT BUỘC TUÂN THỦ):**

⚠️ **CỰC KỲ QUAN TRỌNG - KHÔNG SET TOP/BOTTOM:**
- Backend sẽ TỰ ĐỘNG đặt title, legend, source ở DƯỚI biểu đồ
- AI CHỈ khai báo layoutLevel và layoutKey
- **TUYỆT ĐỐI KHÔNG** set title.top, title.bottom, legend.top, legend.bottom, graphic.top, graphic.bottom
- Backend sẽ tính toán vị trí chính xác dựa trên layoutLevel

Cụ thể:
```json
{layout_example}
```

⚠️ AI chỉ KHAI BÁO layout, backend XỬ LÝ positioning

5. **VÍ DỤ CHUẨN XAXIS/YAXIS:**

```json
{axis_example}
```

**CHỈ TẠO CHART DATA - KHÔNG TẠO CÂU HỎI**

Output: JSON với array charts
"""
    
    return prompt


def build_question_with_chart_prompt(
    lesson_name: str,
    charts_info: List[Dict],
    num_questions: int,
    cognitive_level: str
) -> str:
    """
    Tạo prompt để AI sinh câu hỏi SỬ DỤNG chart có sẵn
    
    Args:
        lesson_name: Tên bài học
        charts_info: List thông tin các chart đã tạo
        num_questions: Số câu hỏi cần tạo
        cognitive_level: Cấp độ nhận thức
    
    Returns:
        str: Instruction để thêm vào prompt chính
    """
    chart_list = "\n".join([
        f"- {chart['chart_id']}: {chart['title']}" 
        for chart in charts_info
    ])
    
    instruction = f"""

{'='*70}
**⚠️ BIỂU ĐỒ ĐÃ TẠO SẴN - KHÔNG TẠO LẠI ECHARTS**
{'='*70}

Các biểu đồ sau đã được tạo sẵn với dữ liệu đầy đủ:
{chart_list}

**CÁCH SỬ DỤNG CHART TRONG CÂU HỎI:**

1. **question_stem format:**
   ```json
   {{
     "type": "chart",
     "content": [
       "Cho biểu đồ dân số thành thị:",
       {{
         "type": "chart",
         "chart_id": "chart_1"
       }},
       "Nhận xét nào sau đây ĐÚNG về xu hướng biến đổi?"
     ]
   }}
   ```

2. **QUAN TRỌNG:**
   - CHỈ cần ghi chart_id, KHÔNG tạo lại echarts
   - content là array: [text_before, chart_object, text_after]
   - Chart object CHỈ có: {{"type": "chart", "chart_id": "..."}}

3. **CÂU HỎI PHẢI LIÊN QUAN TRỰC TIẾP ĐẾN CHART:**
   - Hỏi về xu hướng, tốc độ tăng/giảm
   - So sánh giữa các năm, các chỉ số
   - Phân tích nguyên nhân, hệ quả từ dữ liệu
   - Đáp án dựa trên SỐ LIỆU trong chart

4. **VÍ DỤ CÂU HỎI TỐT:**
   ✅ "Giai đoạn nào dân số thành thị tăng nhanh nhất?"
   ✅ "Tỉ lệ tăng trưởng trung bình giai đoạn 2010-2021 là bao nhiêu?"
   ✅ "Nhận xét nào đúng về mối quan hệ giữa GDP và dân số?"
   
   ❌ "ASEAN được thành lập năm nào?" (không liên quan chart)
   ❌ "Đặc điểm khí hậu nhiệt đới là gì?" (không dùng data chart)

{'='*70}
"""
    
    return instruction


def apply_layout(echarts: Dict) -> Dict:
    """
    Tính toán grid.bottom và vị trí các block dựa trên layoutLevel (Runtime Layout Resolution)
    
    Đây là nơi layout THỰC SỰ được áp dụng:
    - AI chỉ khai báo (layoutLevel + layoutKey)
    - Backend resolve spacing và positioning (tính grid.bottom, title.bottom, etc.)
    - HTML/DOCX/PNG render đồng nhất
    
    Args:
        echarts: ECharts config với layoutLevel
    
    Returns:
        Dict: ECharts config đã resolve grid.bottom và vị trí các block
    """
    layout = echarts.get("layoutLevel", [])
    if not layout:
        return echarts
    
    # Height ước tính cho từng block (bao gồm content + margin)
    block_heights = {
        "source": 35,   # Text nguồn: fontSize 24 + lineHeight 30 + margin
        "title": 30,    # Tiêu đề: fontSize 19 + lineHeight 24 + margin top/bottom
        "legend": 30    # Chú thích: itemHeight ~20 + itemGap + margin
    }
    
    # Gap giữa các blocks (giảm xuống để gần nhau hơn)
    gap_between_blocks = 12
    
    # Padding từ grid đến block đầu tiên (block xa nhất từ dưới)
    padding_from_grid = 25
    
    # Padding base từ đáy canvas đến block đầu tiên
    base_padding = 10
    
    # Tính vị trí từng block (từ dưới lên)
    current_bottom = base_padding
    positions = {}
    
    for idx, key in enumerate(layout):
        # Vị trí bottom của block này
        positions[key] = current_bottom
        # Di chuyển lên trên: height của block + gap
        current_bottom += block_heights.get(key, 30)
        if idx < len(layout) - 1:  # Không thêm gap sau block cuối cùng
            current_bottom += gap_between_blocks
    
    # Set grid.bottom (tổng khoảng cách + padding)
    grid = echarts.setdefault("grid", {})
    grid["bottom"] = current_bottom + padding_from_grid
    
    # Set vị trí cụ thể cho từng block
    # 1. Title (đặt dưới biểu đồ)
    if "title" in positions and "title" in echarts:
        echarts["title"]["bottom"] = positions["title"]
        echarts["title"].pop("top", None)  # Xóa top nếu có
    
    # 2. Legend (đặt dưới biểu đồ)
    if "legend" in positions and "legend" in echarts:
        echarts["legend"]["bottom"] = positions["legend"]
        echarts["legend"].pop("top", None)  # Xóa top nếu có
    
    # 3. Graphic (source - đặt dưới biểu đồ)
    if "source" in positions and "graphic" in echarts:
        for g in echarts.get("graphic", []):
            if g.get("layoutKey") == "source":
                g["bottom"] = positions["source"]
                g.pop("top", None)  # Xóa top nếu có
                # Đảm bảo text căn giữa (dùng textAlign cho ECharts graphic)
                if "style" in g:
                    g["style"]["textAlign"] = "center"
                    # Xóa align nếu có (deprecated)
                    g["style"].pop("align", None)
    
    return echarts


def merge_chart_into_question(
    question_data: Dict,
    charts_map: Dict[str, Dict]
) -> Dict:
    """
    Merge chart data vào câu hỏi (STEP 3)
    
    Args:
        question_data: Dữ liệu câu hỏi từ AI
        charts_map: Map chart_id -> chart_data
    
    Returns:
        Dict: Câu hỏi đã merge chart
    """
    if 'question_stem' not in question_data:
        return question_data
    
    stem = question_data['question_stem']
    if not isinstance(stem, dict):
        return question_data
    
    # Chỉ xử lý type='chart' hoặc 'mixed' có chứa chart
    if stem.get('type') not in ['chart', 'mixed']:
        return question_data
    
    content = stem.get('content', [])
    if not isinstance(content, list):
        return question_data
    
    # Tìm và merge chart vào placeholder đã có
    charts_merged = set()  # track which chart_ids were merged
    for idx, item in enumerate(content):
        if isinstance(item, dict) and item.get('type') == 'chart':
            # Lấy chart_id (nếu AI trả về) hoặc dùng chart đầu tiên chưa dùng
            chart_id = item.get('chart_id')
            
            if not chart_id and charts_map:
                # Fallback: lấy chart đầu tiên chưa được merge
                remaining = [k for k in charts_map if k not in charts_merged]
                chart_id = remaining[0] if remaining else list(charts_map.keys())[0]
            
            if chart_id and chart_id in charts_map:
                chart_data = charts_map[chart_id]
                
                # Apply layout resolution (tính grid.bottom)
                echarts = apply_layout(chart_data.get('echarts', {}))
                
                # Merge echarts đã resolve vào item
                item['content'] = {
                    'chartType': chart_data.get('chartType'),
                    'echarts': echarts
                }
                # Thêm metadata nếu chưa có
                if 'metadata' not in item:
                    chart_height = 850  # Tăng chiều cao để hiển thị rõ ràng hơn
                    item['metadata'] = {
                        'caption': chart_data.get('title'),
                        'width': 900,
                        'height': chart_height
                    }
                charts_merged.add(chart_id)

    # ✨ FALLBACK: AI không sinh chart placeholder → force-inject toàn bộ charts từ charts_map
    # Xảy ra khi AI bỏ qua lệnh "dùng chart_id" và chỉ viết text
    if charts_map and not charts_merged:
        # Tìm vị trí inject: sau text đầu tiên nếu có, nếu không thì đầu array
        insert_pos = 1 if content and isinstance(content[0], str) else 0
        for chart_id, chart_data in charts_map.items():
            echarts = apply_layout(chart_data.get('echarts', {}))
            chart_item = {
                'type': 'chart',
                'chart_id': chart_id,
                'content': {
                    'chartType': chart_data.get('chartType'),
                    'echarts': echarts
                },
                'metadata': {
                    'caption': chart_data.get('title'),
                    'width': 900,
                    'height': 850
                }
            }
            content.insert(insert_pos, chart_item)
            insert_pos += 1  # inject each subsequent chart after the previous
            print(f"   ⚡ Force-injected chart '{chart_id}' into question (AI skipped placeholder)")
    
    return question_data


def validate_chart_completeness(chart_data: Dict) -> tuple[bool, str]:
    """
    Kiểm tra chart có đầy đủ dữ liệu không theo schema
    
    Args:
        chart_data: Chart data cần kiểm tra
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    # Check required fields ở level chart
    required_chart_fields = ["chart_id", "title", "chartType", "echarts"]
    for field in required_chart_fields:
        if field not in chart_data:
            return False, f"Thiếu field '{field}' ở level chart"
    
    # Check chart_id không rỗng
    if not chart_data.get("chart_id", "").strip():
        return False, "chart_id rỗng"
    
    # Check title không rỗng
    if not chart_data.get("title", "").strip():
        return False, "title rỗng"
    
    # Check chartType hợp lệ
    valid_chart_types = ["bar", "line"]
    if chart_data.get("chartType") not in valid_chart_types:
        return False, f"chartType phải là một trong {valid_chart_types}"
    
    # Check echarts object
    echarts = chart_data.get('echarts', {})
    if not isinstance(echarts, dict):
        return False, "echarts phải là object"
    
    # Check required fields trong echarts
    required_echarts_fields = ["title", "xAxis", "yAxis", "series"]
    for field in required_echarts_fields:
        if field not in echarts:
            return False, f"Thiếu field '{field}' trong echarts"
    
    # Check echarts.title
    title_obj = echarts.get('title', {})
    if not isinstance(title_obj, dict):
        return False, "echarts.title phải là object"
    
    # Check title.text
    if not title_obj.get('text', '').strip():
        return False, "echarts.title.text rỗng"
    
    # Check title.left = "center" (bắt buộc)
    if title_obj.get('left') != 'center':
        return False, "echarts.title.left phải là 'center'"
    
    # Check layoutLevel (nếu có)
    layout = echarts.get("layoutLevel", [])
    if layout:
        if not isinstance(layout, list):
            return False, "layoutLevel phải là array"
        
        valid_keys = {"source", "title", "legend"}
        for key in layout:
            if key not in valid_keys:
                return False, f"layoutLevel chứa giá trị không hợp lệ: {key}"
        
        # Check layoutKey consistency
        if "title" in layout:
            if echarts.get("title", {}).get("layoutKey") != "title":
                return False, "title.layoutKey phải là 'title' khi layoutLevel có 'title'"
        
        if "legend" in layout:
            if echarts.get("legend", {}).get("layoutKey") != "legend":
                return False, "legend.layoutKey phải là 'legend' khi layoutLevel có 'legend'"
        
        if "source" in layout:
            graphics = echarts.get("graphic", [])
            if not any(g.get("layoutKey") == "source" for g in graphics):
                return False, "layoutLevel có 'source' nhưng graphic.layoutKey='source' không tồn tại"
        
        # Check KHÔNG có top/bottom trong title, legend, graphic (backend sẽ tự động set)
        if "title" in layout and "title" in echarts:
            if "top" in echarts["title"] or "bottom" in echarts["title"]:
                return False, "title KHÔNG được set top/bottom khi dùng layoutLevel (backend tự động positioning)"
        
        if "legend" in layout and "legend" in echarts:
            if "top" in echarts["legend"] or "bottom" in echarts["legend"]:
                return False, "legend KHÔNG được set top/bottom khi dùng layoutLevel (backend tự động positioning)"
        
        if "source" in layout and "graphic" in echarts:
            for i, g in enumerate(echarts.get("graphic", [])):
                if g.get("layoutKey") == "source":
                    if "top" in g or "bottom" in g:
                        return False, f"graphic[{i}] (source) KHÔNG được set top/bottom khi dùng layoutLevel (backend tự động positioning)"
    
    # Check xAxis
    x_axis = echarts.get('xAxis')
    if isinstance(x_axis, dict):
        x_data = x_axis.get('data', [])
        if not x_data:
            return False, "xAxis.data rỗng"
        if not isinstance(x_data, list):
            return False, "xAxis.data phải là array"
    elif isinstance(x_axis, list):
        if not x_axis:
            return False, "xAxis array rỗng"
    else:
        return False, "xAxis phải là object hoặc array"
    
    # Check yAxis
    y_axis = echarts.get('yAxis')
    if isinstance(y_axis, dict):
        # Single yAxis - check basic structure
        pass  # yAxis object có thể không cần data
    elif isinstance(y_axis, list):
        # Multiple yAxis
        if not y_axis:
            return False, "yAxis array rỗng"
        for i, axis in enumerate(y_axis):
            if not isinstance(axis, dict):
                return False, f"yAxis[{i}] phải là object"
            # Check required fields for yAxis
            if 'type' not in axis:
                return False, f"yAxis[{i}] thiếu field 'type'"
            if 'name' not in axis:
                return False, f"yAxis[{i}] thiếu field 'name'"
            # Check optional fields if present
            if 'axisLine' in axis:
                axis_line = axis['axisLine']
                if not isinstance(axis_line, dict):
                    return False, f"yAxis[{i}].axisLine phải là object"
                if 'symbol' in axis_line and not isinstance(axis_line['symbol'], list):
                    return False, f"yAxis[{i}].axisLine.symbol phải là array"
                if 'symbolSize' in axis_line and not isinstance(axis_line['symbolSize'], list):
                    return False, f"yAxis[{i}].axisLine.symbolSize phải là array"
    else:
        return False, "yAxis phải là object hoặc array"
    
    # Check series
    series = echarts.get('series', [])
    if not isinstance(series, list) or len(series) == 0:
        return False, "series phải là array không rỗng"
    
    # Check từng series
    for i, s in enumerate(series):
        if not isinstance(s, dict):
            return False, f"series[{i}] phải là object"
        
        # Check required fields trong series
        required_series_fields = ["name", "type", "data"]
        for field in required_series_fields:
            if field not in s:
                return False, f"series[{i}] thiếu field '{field}'"
        
        # Check name không rỗng
        if not str(s.get("name", "")).strip():
            return False, f"series[{i}].name rỗng"
        
        # Check type hợp lệ
        if s.get("type") not in ["bar", "line"]:
            return False, f"series[{i}].type phải là 'bar' hoặc 'line'"
        
        # Check data là array không rỗng
        data = s.get("data", [])
        if not isinstance(data, list) or len(data) == 0:
            return False, f"series[{i}].data phải là array không rỗng"
        
        # Check yAxisIndex nếu có (cho dual yAxis)
        if "yAxisIndex" in s:
            y_axis_index = s["yAxisIndex"]
            if not isinstance(y_axis_index, int) or y_axis_index < 0:
                return False, f"series[{i}].yAxisIndex phải là integer >= 0"
        
        # Check label nếu có
        if 'label' in s:
            label = s['label']
            if not isinstance(label, dict):
                return False, f"series[{i}].label phải là object"
            if 'show' in label and not isinstance(label['show'], bool):
                return False, f"series[{i}].label.show phải là boolean"
            if 'position' in label and label['position'] not in ['top', 'left', 'right', 'bottom', 'inside', 'insideLeft', 'insideRight', 'insideTop', 'insideBottom', 'insideTopLeft', 'insideTopRight', 'insideBottomLeft', 'insideBottomRight']:
                return False, f"series[{i}].label.position không hợp lệ"
            if 'formatter' in label and not isinstance(label['formatter'], str):
                return False, f"series[{i}].label.formatter phải là string"
    
    # Check graphic (nếu có)
    graphic = echarts.get('graphic', [])
    if graphic:
        if not isinstance(graphic, list):
            return False, "graphic phải là array"
        
        for i, g in enumerate(graphic):
            if not isinstance(g, dict):
                return False, f"graphic[{i}] phải là object"
            
            # Check type = "text"
            if g.get('type') != 'text':
                return False, f"graphic[{i}].type phải là 'text'"
            
            # Check left = "center" (bắt buộc)
            if g.get('left') != 'center':
                return False, f"graphic[{i}].left phải là 'center'"
            
            # Check style.text
            style = g.get('style', {})
            if not isinstance(style, dict):
                return False, f"graphic[{i}].style phải là object"
            
            if not style.get('text', '').strip():
                return False, f"graphic[{i}].style.text rỗng"
    
    return True, ""
