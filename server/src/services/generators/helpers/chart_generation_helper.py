"""
Chart Generation Helper - Tạo biểu đồ riêng biệt để giảm nested complexity
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
                                "title": {
                                    "type": "object",
                                    "properties": {
                                        "text": {
                                            "type": "string",
                                            "description": "Tiêu đề biểu đồ"
                                        },
                                        "left": {
                                            "type": "string",
                                            "default": "center",
                                            "description": "BẮT BUỘC: center"
                                        },
                                        "top": {
                                            "type": "string",
                                            "default": "88%",
                                        },
                                        "textStyle": {
                                            "type": "object",
                                            "properties": {
                                                "fontSize": {"type": "number", "default": 20},
                                                "fontWeight": {"type": "string", "default": "bold"}
                                            }
                                        }
                                    },
                                    "required": ["text", "left", "top"]
                                },
                                "legend": {
                                    "type": "object",
                                    "properties": {
                                        "data": {
                                            "type": "array", 
                                            "items": {"type": "string"}
                                        },
                                        "bottom": {
                                            "type": "number",
                                            "default": 70
                                        }
                                    }
                                },
                                
                                "grid": {
                                    "type": "object",
                                    "properties": {
                                        "top": {"type": "number"},
                                        "bottom": {"type": "number"},
                                        "left": {"type": "number"},
                                        "right": {"type": "number"},
                                    }
                                },

                                "xAxis": {
                                    "anyOf": [
                                        {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string"},
                                                "data": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "BẮT BUỘC: Array dữ liệu trục X"
                                                },
                                                "name": {"type": "string"},
                                                "nameLocation": {"type": "string", "default": "end"},
                                                "nameGap": {"type": "number"},
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
                                            "required": ["data", "type", "nameLocation", "name", "axisLine", "axisTick"]
                                        },
                                        {"type": "array"}
                                    ]
                                },
                                "yAxis": {
                                    "anyOf": [
                                        {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string"},
                                                "name": {"type": "string"}
                                            }
                                        },
                                        {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "type": {"type": "string"},
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
                                                            "fontSize": {"type": "number"},
                                                            "fontWeight": {"type": "string", "default": "bold"}
                                                        }
                                                    }
                                                },
                                                "required": ["type", "name", "axisLine", "axisTick", "axisLabel", "splitLine", "nameLocation", "nameGap", "nameTextStyle"]
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
                                    "description": "Text nguồn hoặc ghi chú",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": ["text"],
                                                "description": "Loại element"
                                            },
                                            "left": {
                                                "type": "string",
                                                "enum": ["center"],
                                                "description": "BẮT BUỘC: center"
                                            },
                                            "bottom": {
                                                "type": "string",
                                                "enum": ["20"],
                                                "description": "BẮT BUỘC: 20"
                                            },
                                            "style": {
                                                "type": "object",
                                                "properties": {
                                                    "text": {
                                                        "type": "string",
                                                        "description": "Text nguồn (VD: 'Nguồn: Niên giám...')"
                                                    },
                                                    "fontSize": {
                                                        "type": "number",
                                                        "default": 13
                                                    },
                                                    "fontStyle": {
                                                        "type": "string",
                                                        "enum": ["italic"],
                                                        "default": "italic"
                                                    }
                                                },
                                                "required": ["text"]
                                            }
                                        },
                                        "required": ["type", "left", "bottom", "style"]
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
    
    prompt = f"""
Tạo {num_charts} biểu đồ thống kê cho bài học: "{lesson_name}"

{data_source}

**YÊU CẦU BIỂU ĐỒ:**

1. **Mỗi chart phải có:**
   - chart_id: Unique ID (chart_1, chart_2, ...)
   - title: Tiêu đề ngắn gọn (VD: "Dân số thành thị 2010-2021")
   - chartType: bar, line, pie, hoặc combo

2. **ECharts config ĐẦY ĐỦ:**
   - xAxis.data: Array các giá trị (VD: ["2010", "2015", "2021"])
   - yAxis: Object hoặc array (dual yAxis nếu cần)
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
     - text: "Nguồn: [tên nguồn]"
     - fontSize: 13, fontStyle: "italic"

3. **TÍNH NĂNG NÂNG CAO (tùy chọn):**
   - Dual yAxis nếu có 2 loại dữ liệu khác đơn vị (position: 'left', 'right')
   - Combo chart (bar + line) nếu cần so sánh
   - Legend với bottom: 70
   - Grid với top, bottom, left, right để điều chỉnh không gian
   - TextStyle với fontFamily: 'Roboto, sans-serif'
   - Title textStyle với fontSize: 18, fontWeight: 'bold'

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
    
    # Tìm và merge chart
    for idx, item in enumerate(content):
        if isinstance(item, dict) and item.get('type') == 'chart':
            # Lấy chart_id (nếu AI trả về) hoặc dùng chart đầu tiên
            chart_id = item.get('chart_id')
            
            if not chart_id and charts_map:
                # Fallback: lấy chart đầu tiên
                chart_id = list(charts_map.keys())[0]
            
            if chart_id and chart_id in charts_map:
                chart_data = charts_map[chart_id]
                # Merge echarts vào item
                item['content'] = {
                    'chartType': chart_data.get('chartType'),
                    'echarts': chart_data.get('echarts')
                }
                # Thêm metadata nếu chưa có
                if 'metadata' not in item:
                    item['metadata'] = {
                        'caption': chart_data.get('title'),
                        'width': 900,
                        'height': 550
                    }
    
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
