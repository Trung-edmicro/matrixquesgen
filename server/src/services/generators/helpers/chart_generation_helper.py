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
import sys
from pathlib import Path

# Import GenChart utilities - use full module path consistent with codebase
from services.utils.chart.chart_bar import generate_bar_chart
from services.utils.chart.chart_line import generate_line_chart
from services.utils.chart.chart_pie import generate_pie_chart
from services.utils.chart.chart_area import generate_area_chart


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


def extract_chart_summary(echarts_option: Dict) -> Dict:
    """
    Trích xuất thông tin chi tiết từ echarts config để gửi kèm prompt sinh câu hỏi.
    Giúp AI hiểu rõ chart chứa dữ liệu gì → sinh câu hỏi liên quan.
    
    Args:
        echarts_option: Full ECharts config dict
    
    Returns:
        Dict với các key: xAxis_labels, yAxis_unit, series_names, data_summary
    """
    try:
        summary = {
            'xAxis_labels': [],
            'yAxis_unit': '',
            'series_names': [],
            'data_summary': ''
        }
        
        # Extract xAxis labels (danh mục)
        xAxis = echarts_option.get('xAxis', {})
        if isinstance(xAxis, dict):
            xAxis_labels = xAxis.get('data', [])
            if isinstance(xAxis_labels, list) and xAxis_labels:
                summary['xAxis_labels'] = xAxis_labels[:10]  # Limit 10 items
        
        # Extract yAxis unit/name
        yAxis = echarts_option.get('yAxis', {})
        if isinstance(yAxis, dict):
            y_name = yAxis.get('name', '')
            summary['yAxis_unit'] = y_name if y_name else yAxis.get('type', '')
        elif isinstance(yAxis, list) and yAxis:
            # Dual yAxis - lấy cái đầu
            y_name = yAxis[0].get('name', '')
            summary['yAxis_unit'] = y_name if y_name else yAxis[0].get('type', '')
        
        # Extract series names
        series = echarts_option.get('series', [])
        if isinstance(series, list):
            series_names = []
            for s in series:
                if isinstance(s, dict):
                    name = s.get('name', '')
                    if name and name != 'Labels':  # Skip label series
                        series_names.append(name)
            summary['series_names'] = series_names
        
        # Build data summary (mô tả ngắn)
        try:
            title = echarts_option.get('title', {})
            title_text = ''
            if isinstance(title, dict):
                title_text = title.get('text', '')
            elif isinstance(title, list) and title:
                title_text = title[0].get('text', '') if isinstance(title[0], dict) else ''
            
            # Tóm tắt thông tin
            parts = []
            if title_text:
                parts.append(f"Tiêu đề: {title_text}")
            if summary['xAxis_labels']:
                parts.append(f"Danh mục X: {', '.join(map(str, summary['xAxis_labels'][:5]))}")
                if len(summary['xAxis_labels']) > 5:
                    parts.append(f"(+ {len(summary['xAxis_labels']) - 5} danh mục khác)")
            if summary['yAxis_unit']:
                parts.append(f"Đơn vị Y: {summary['yAxis_unit']}")
            if summary['series_names']:
                parts.append(f"Các chỉ tiêu: {', '.join(summary['series_names'])}")
            
            summary['data_summary'] = " | ".join(parts)
        except:
            pass
        
        return summary
    except Exception as e:
        print(f"⚠️ Lỗi extract_chart_summary: {str(e)[:100]}")
        return {
            'xAxis_labels': [],
            'yAxis_unit': '',
            'series_names': [],
            'data_summary': ''
        }


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
        charts_info: List thông tin các chart đã tạo (mỗi item có chart_id, title, + optional summary fields)
        num_questions: Số câu hỏi cần tạo
        cognitive_level: Cấp độ nhận thức
    
    Returns:
        str: Instruction để thêm vào prompt chính
    """
    # Build chart list với chi tiết nếu có
    chart_details = []
    for chart in charts_info:
        chart_id = chart.get('chart_id', '')
        title = chart.get('title', '')
        
        # Tạo mô tả chi tiết từ summary fields
        detail_parts = [f"- {chart_id}: {title}"]
        
        # Thêm thông tin chi tiết nếu có
        if 'data_summary' in chart and chart['data_summary']:
            detail_parts.append(f"  📊 {chart['data_summary']}")
        elif 'xAxis_labels' in chart or 'series_names' in chart:
            # Fallback: build từ components
            components = []
            if chart.get('xAxis_labels'):
                components.append(f"Danh mục: {', '.join(map(str, chart['xAxis_labels'][:5]))}{' ...' if len(chart['xAxis_labels']) > 5 else ''}")
            if chart.get('series_names'):
                components.append(f"Chỉ tiêu: {', '.join(chart['series_names'])}")
            if components:
                detail_parts.append(f"  📊 {' | '.join(components)}")
        
        chart_details.append("\n".join(detail_parts))
    
    chart_list = "\n".join(chart_details)
    
    instruction = f"""

{'='*70}
**⚠️ BIỂU ĐỒ ĐÃ TẠO SẴN - KHÔNG TẠO LẠI ECHARTS**
{'='*70}

Các biểu đồ sau đã được tạo sẵn với dữ liệu đầy đủ:
{chart_list}

**CÁCH SỬ DỤNG CHART TRONG CÂU HỎI:**

1. **🔍 Đọc kỹ thông tin chi tiết của chart:**
   - Tiêu đề chart là gì (chủ đề, dữ liệu)?
   - Danh mục X: Những gì được so sánh? (năm, địa danh, chỉ tiêu)
   - Kiểu dữ liệu Y: Đơn vị gì? (mm, %, triệu, tỷ USD, ...)
   - Các chỉ tiêu (series): Mấy đường/cột, tên gì?

2. **✍️ Sinh câu hỏi DỰA TRÊN DỮ LIỆU THỰC TỪ CHART:**
   Dùng từ danh mục X, yAxis unit, và series names đã cung cấp.

3. **Format question_stem:**
   ```json
   {{
     "type": "chart",
     "content": [
       "Cho biểu đồ [DỰA VÀO TIÊU ĐỀ/NỘI DUNG CHART]:",
       {{
         "type": "chart",
         "chart_id": "C1"
       }},
       "[CÂU HỎI LIÊN QUAN ĐẾN DỮ LIỆU CHART]?"
     ]
   }}
   ```

4. **⚠️ QUY TẮC TẠO CÂU HỎI:**
   
   ✅ **PHẢI HỎI VỀ:**
   - Giá trị cụ thể: "Năm nào [chỉ tiêu1] cao nhất?"
   - So sánh: "So sánh [chỉ tiêu1] và [chỉ tiêu2] năm 2020?"
   - Xu hướng: "[Chỉ tiêu] có xu hướng [tăng/giảm] từ [năm] đến [năm]?"
   - Phân tích: "Nguyên nhân [chỉ tiêu] từ [giá trị1] tăng lên [giá trị2]?"
   
   ❌ **KHÔNG HỎI VỀ:**
   - Chủ đề không liên quan: "ASEAN được thành lập năm nào?"
   - Dữ liệu không có trong chart: "Dân số Đức năm 2020?" (nếu chart không có Đức)
   - Từ khác xa: "Đặc điểm khí hậu nhiệt đới?" (nếu chart chỉ về dân số)

5. **📌 VÍ DỤ CỤ THỂ:**
   
   **CHART:** Tiêu đề "Dân số thành thị 3 vùng", Danh mục X: "Hà Nội, Huế, TP.HCM", Y: "triệu người"
   
   ✅ "Dân số thành thị vùng nào cao nhất?"
   ✅ "Từ 2010 đến 2021, dân số Hà Nội tăng hay giảm?"
   ✅ "So với 2010, dân số TP.HCM năm 2021 tăng bao nhiêu phần trăm?"
   
   ❌ "Vì sao dân số Hà Nội tăng cao?" (Không dùng dữ liệu chart, yêu cầu phân tích ngoài)
   ❌ "Tính số người thêm ở Đà Nẵng" (Đà Nẵng không có trong danh mục X)

{'='*70}
"""
    
    return instruction


def optimize_grid_for_width(echarts: Dict, container_width: int = 1100) -> Dict:
    """
    Điều chỉnh grid config dựa trên container width để không bị cắt nội dung
    
    Strategy:
    - Hạ grid padding để maximize chart area
    - Với width 1100px, set left/right = 50 (tối ưu hóa cho legend, labels)
    - Với width < 900px, scale down tương ứng
    
    Args:
        echarts: ECharts config
        container_width: Độ rộng container (default 1100px)
    
    Returns:
        Dict: ECharts config đã optimize grid
    """
    # Không xử lý pie chart (không dùng grid)
    series = echarts.get("series", [])
    if isinstance(series, list):
        for s in series:
            if isinstance(s, dict) and s.get("type") == "pie":
                return echarts  # Skip pie charts
    
    # Get current grid config
    grid = echarts.get("grid", {})
    if not isinstance(grid, dict):
        return echarts
    
    # Tính toán grid padding hiệu quả
    current_left = grid.get("left", 80)
    current_right = grid.get("right", 80)
    
    # Strategy: Scale padding dựa trên container width
    # Reference: width=1100 -> left=50, right=50 (900px chart area)
    # Reference: width=900 -> left=63, right=63 (774px chart area via scale)
    # Reference: width=800 -> left=70, right=70 (660px chart area via scale)
    
    if container_width >= 1100:
        # Optimal: 1100px container → 50px padding mỗi side
        grid["left"] = 50
        grid["right"] = 50
    elif container_width >= 900:
        # Medium: Scale linearly between 900-1100
        # At 900: scale factor = 1.0 (use ~63 to have 774px chart area)
        # At 1100: scale factor = 0 (use 50)
        scale = (container_width - 900) / 200  # 0 to 1
        grid["left"] = int(63 - (13 * scale))  # 63 → 50
        grid["right"] = int(63 - (13 * scale))
    else:
        # Small: Aggressive reduce to minimum viable padding
        adjusted_left = max(45, int(current_left * (container_width / 900)))
        adjusted_right = max(45, int(current_right * (container_width / 900)))
        grid["left"] = adjusted_left
        grid["right"] = adjusted_right
    
    echarts["grid"] = grid
    return echarts


def apply_layout(echarts: Dict) -> Dict:
    """
    Tính toán grid.bottom và vị trí các block dựa trên layoutLevel (Runtime Layout Resolution)
    Xử lý riêng cho pie chart (không dùng grid)
    
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
    
    # Phát hiện loại chart dựa trên series
    is_pie_chart = False
    series = echarts.get("series", [])
    if isinstance(series, list):
        for s in series:
            if isinstance(s, dict) and s.get("type") == "pie":
                is_pie_chart = True
                break
    
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
    
    # ===== XỬ LÝ RIÊNG CHO PIE CHART =====
    if is_pie_chart:
        # Pie chart không dùng grid, dùng center để định vị
        # center = [horizontal%, vertical%] - đặt vị trí từ top-left của canvas
        # Để đẩy pie chart LÊN (giảm white space trên), điều chỉnh vertical% xuống
        # Ví dụ: ["50%", "50%"] → ["50%", "35%"] = di chuyển lên
        
        # Tính toán độ cao cần thiết phía dưới
        total_bottom_height = current_bottom + padding_from_grid  # Tính bằng pixels
        
        # Assume canvas height = 550px (từ metadata mới - square sizing for pie)
        # Tỉ lệ phần trăm cho blocks phía dưới
        canvas_height = 550
        blocks_height_percent = (total_bottom_height / canvas_height) * 100
        
        # Pie chart nên độc chiếm khoảng 60-70% canvas (để có chỗ cho title trên + blocks dưới)
        # center[1] = 20-30% sẽ đẩy chart lên với padding phía trên
        pie_vertical_percent = 25  # Cố định ở 25% để đẩy chart lên consistently
        
        # Cập nhật center cho tất cả pie series
        for s in echarts.get("series", []):
            if isinstance(s, dict) and s.get("type") == "pie":
                if "center" in s:
                    center = s["center"]
                    if isinstance(center, list) and len(center) >= 2:
                        # Giữ horizontal, điều chỉnh vertical
                        s["center"] = [center[0], f"{pie_vertical_percent}%"]
    else:
        # ===== XỬ LÝ CHO BAR/LINE/AREA/COMBO CHART =====
        # Set grid.bottom (tổng khoảng cách + padding)
        grid = echarts.setdefault("grid", {})
        grid["bottom"] = current_bottom + padding_from_grid
    
    # Set vị trí cụ thể cho từng block (dùng cho cả pie và non-pie charts)
    # 1. Title (đặt dưới biểu đồ)
    if "title" in positions and "title" in echarts:
        title = echarts["title"]
        if isinstance(title, list):
            # Multiple titles - update từng cái
            for t in title:
                if isinstance(t, dict):
                    t["bottom"] = positions["title"]
                    t.pop("top", None)
        else:
            title["bottom"] = positions["title"]
            title.pop("top", None)  # Xóa top nếu có
    
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


def optimize_font_sizes_for_chart_area(echarts: Dict, container_width: int = 1100) -> Dict:
    """
    Tối ưu hóa kích thước font dựa trên diện tích chart có sẵn
    Giúp tránh crowding và overlap khi chart nhỏ
    
    Strategy:
    - Width >= 1100px: Giữ font size nguyên
    - Width 900-1100px: Giảm nhẹ (90-95%)
    - Width < 900px: Giảm mạnh (80-85%)
    
    Args:
        echarts: ECharts config
        container_width: Độ rộng container
    
    Returns:
        Dict: ECharts config với font size đã optimize
    """
    # Tính font scale factor
    if container_width >= 1100:
        scale_factor = 1.0  # 100%
    elif container_width >= 900:
        # Linear scale: 900px → 0.92, 1100px → 1.0
        scale_factor = 0.92 + (container_width - 900) / 200 * 0.08
    else:
        # Aggressive: 800px → 0.83, 900px → 0.92
        scale_factor = max(0.80, 0.83 + (container_width - 800) / 100 * 0.09)
    
    # Apply scaling to axis labels, legend, title fonts
    def scale_font_size(size):
        if isinstance(size, (int, float)):
            return int(max(10, size * scale_factor))
        return size
    
    # 1. Scale xAxis labels
    if "xAxis" in echarts:
        x_axis = echarts["xAxis"]
        if isinstance(x_axis, dict):
            if "axisLabel" in x_axis and isinstance(x_axis["axisLabel"], dict):
                if "fontSize" in x_axis["axisLabel"]:
                    x_axis["axisLabel"]["fontSize"] = scale_font_size(x_axis["axisLabel"]["fontSize"])
            if "nameTextStyle" in x_axis and isinstance(x_axis["nameTextStyle"], dict):
                if "fontSize" in x_axis["nameTextStyle"]:
                    x_axis["nameTextStyle"]["fontSize"] = scale_font_size(x_axis["nameTextStyle"]["fontSize"])
    
    # 2. Scale yAxis labels
    if "yAxis" in echarts:
        y_axis = echarts["yAxis"]
        if isinstance(y_axis, dict):
            if "axisLabel" in y_axis and isinstance(y_axis["axisLabel"], dict):
                if "fontSize" in y_axis["axisLabel"]:
                    y_axis["axisLabel"]["fontSize"] = scale_font_size(y_axis["axisLabel"]["fontSize"])
            if "nameTextStyle" in y_axis and isinstance(y_axis["nameTextStyle"], dict):
                if "fontSize" in y_axis["nameTextStyle"]:
                    y_axis["nameTextStyle"]["fontSize"] = scale_font_size(y_axis["nameTextStyle"]["fontSize"])
    
    # 3. Scale legend text
    if "legend" in echarts and isinstance(echarts["legend"], dict):
        legend = echarts["legend"]
        if "textStyle" in legend and isinstance(legend["textStyle"], dict):
            if "fontSize" in legend["textStyle"]:
                legend["textStyle"]["fontSize"] = scale_font_size(legend["textStyle"]["fontSize"])
    
    # 4. Scale title text
    if "title" in echarts:
        titles = echarts["title"]
        if isinstance(titles, list):
            for title in titles:
                if isinstance(title, dict) and "textStyle" in title:
                    if "fontSize" in title["textStyle"]:
                        title["textStyle"]["fontSize"] = scale_font_size(title["textStyle"]["fontSize"])
                    if "fontSize" in title:
                        title["fontSize"] = scale_font_size(title["fontSize"])
        elif isinstance(titles, dict):
            if "textStyle" in titles and "fontSize" in titles["textStyle"]:
                titles["textStyle"]["fontSize"] = scale_font_size(titles["textStyle"]["fontSize"])
            if "fontSize" in titles:
                titles["fontSize"] = scale_font_size(titles["fontSize"])
    
    # 5. Scale series labels (bar/pie/etc labels)
    if "series" in echarts and isinstance(echarts["series"], list):
        for series in echarts["series"]:
            if isinstance(series, dict):
                # Label style
                if "label" in series and isinstance(series["label"], dict):
                    if "fontSize" in series["label"]:
                        series["label"]["fontSize"] = scale_font_size(series["label"]["fontSize"])
                
                # ItemStyle textStyle
                if "itemStyle" in series and isinstance(series["itemStyle"], dict):
                    if "textStyle" in series["itemStyle"]:
                        if "fontSize" in series["itemStyle"]["textStyle"]:
                            series["itemStyle"]["textStyle"]["fontSize"] = scale_font_size(
                                series["itemStyle"]["textStyle"]["fontSize"]
                            )
    
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
                
                # Extract metadata width for grid optimization
                container_width = 1100  # Default width
                if 'metadata' in item and isinstance(item['metadata'], dict):
                    container_width = item['metadata'].get('width', 1100)
                
                # Apply grid optimization trước layout resolution
                echarts = optimize_grid_for_width(chart_data.get('echarts', {}), container_width)
                # Optimize font sizes cho chart area
                echarts = optimize_font_sizes_for_chart_area(echarts, container_width)
                # Apply layout resolution (tính grid.bottom)
                echarts = apply_layout(echarts)
                
                # Merge echarts đã resolve vào item
                item['content'] = {
                    'chartType': chart_data.get('chartType'),
                    'echarts': echarts
                }
                # Thêm metadata nếu chưa có
                if 'metadata' not in item:
                    # Detect chart type để set appropriate dimensions
                    # Pie chart: square (550x550) để không bóp méo tròn
                    # Bar/Line/Area: landscape (850x500)
                    is_pie = False
                    if 'series' in chart_data.get('echarts', {}):
                        series = chart_data['echarts']['series']
                        if isinstance(series, list):
                            for s in series:
                                if isinstance(s, dict) and s.get('type') == 'pie':
                                    is_pie = True
                                    break
                    
                    if is_pie:
                        # Pie chart: use square dimensions to prevent distortion
                        chart_height = 550
                        chart_width = 550
                    else:
                        # Bar/Line/Area: wide landscape for legend space
                        chart_height = 500
                        chart_width = 850
                    
                    item['metadata'] = {
                        'caption': chart_data.get('title'),
                        'width': chart_width,
                        'height': chart_height
                    }
                charts_merged.add(chart_id)

    # ✨ FALLBACK: AI không sinh chart placeholder → force-inject toàn bộ charts từ charts_map
    # Xảy ra khi AI bỏ qua lệnh "dùng chart_id" và chỉ viết text
    if charts_map and not charts_merged:
        # Tìm vị trí inject: sau text đầu tiên nếu có, nếu không thì đầu array
        insert_pos = 1 if content and isinstance(content[0], str) else 0
        for chart_id, chart_data in charts_map.items():
            # Apply grid optimization trước layout resolution
            echarts = optimize_grid_for_width(chart_data.get('echarts', {}), 1100)
            # Optimize font sizes cho chart area
            echarts = optimize_font_sizes_for_chart_area(echarts, 1100)
            # Apply layout resolution
            echarts = apply_layout(echarts)
            chart_item = {
                'type': 'chart',
                'chart_id': chart_id,
                'content': {
                    'chartType': chart_data.get('chartType'),
                    'echarts': echarts
                },
                'metadata': {
                    'caption': chart_data.get('title'),
                    'width': 1100,  # Tăng từ 900 để không bị cắt nội dung
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


def build_chart_data_generation_prompt(
    lesson_name: str,
    chart_type: str,
    dimensions: str,
    cognitive_level: str,
    expected_learning_outcome: str,
    supplementary_materials: str = ""
) -> str:
    """
    Build prompt cho AI sinh dữ liệu chart từ template gen_data_chart.md
    
    Args:
        lesson_name: Tên bài học (VD: "Dân số thành thị Việt Nam")
        chart_type: Loại biểu đồ (bar, line, pie, area, combo)
        dimensions: Kích thước dữ liệu (VD: "2x3" = 2 hàng 3 cột)
        cognitive_level: Mức độ nhận thức (NB, TH, VD, VDC)
        expected_learning_outcome: Kết quả học tập mong đợi
        supplementary_materials: Tài liệu bổ sung (dataset)
    
    Returns:
        str: Prompt đầy đủ đã mapping các biến
    """
    from pathlib import Path
    
    # Load template từ file
    # Path: helpers/ -> generators/ -> services/ -> prompts/chart/gen_data_chart.md
    template_path = Path(__file__).parent.parent.parent / "prompts" / "chart" / "gen_data_chart.md"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Không tìm thấy template: {template_path}")
    
    # Map chart_type thành tên tiếng Việt
    chart_type_vn = {
        'bar': 'Bar (Cột)',
        'line': 'Line (Đường)',
        'pie': 'Pie (Tròn)',
        'area': 'Area (Miền)',
        'combo': 'Combo (Kết hợp Cột+Đường)'
    }.get(chart_type.lower(), chart_type)
    
    # Mapping các biến trong template
    prompt = template.replace('[LESSON_NAME]', lesson_name)
    prompt = prompt.replace('[TYPE_CHART]', chart_type_vn)
    prompt = prompt.replace('[DIMENSIONS]', dimensions)
    prompt = prompt.replace('[COGNITIVE_LEVEL]', cognitive_level)
    prompt = prompt.replace('[EXPECTED_LEARNING_OUTCOME]', expected_learning_outcome)
    prompt = prompt.replace('[SUPPLEMENTARY_MATERIALS]', supplementary_materials if supplementary_materials else "Không có dataset cụ thể - Tìm kiếm dữ liệu từ nguồn uy tín")
    
    return prompt


def validate_chart_data_generation(chart_data: Dict, chart_type: str = None, dimensions: str = None) -> bool:
    """
    Validate dữ liệu chart do AI sinh ra
    
    Args:
        chart_data: Dict chứa chart data từ AI
        chart_type: Loại chart mong đợi (optional, để so sánh)
        dimensions: Kích thước mong đợi "XxY" (optional, để so sánh)
    
    Returns:
        bool: True nếu valid
    
    Raises:
        ValueError: Nếu data không hợp lệ
    """
    # Check required fields
    if not isinstance(chart_data, dict):
        raise ValueError(f"chart_data phải là dict, nhận được: {type(chart_data)}")
    
    if 'chart_type' not in chart_data:
        raise ValueError("Thiếu field 'chart_type'")
    
    if 'data' not in chart_data:
        raise ValueError("Thiếu field 'data'")
    
    if 'options' not in chart_data:
        raise ValueError("Thiếu field 'options'")
    
    # Validate chart_type
    valid_types = ['bar', 'line', 'pie', 'area', 'combo']
    if chart_data['chart_type'] not in valid_types:
        raise ValueError(f"chart_type không hợp lệ: {chart_data['chart_type']}, phải là một trong: {valid_types}")
    
    # Check nếu chart_type khớp với mong đợi
    if chart_type and chart_data['chart_type'] != chart_type.lower():
        raise ValueError(f"chart_type không khớp: mong đợi '{chart_type}', nhận được '{chart_data['chart_type']}'")
    
    # Validate data structure
    data = chart_data['data']
    if not isinstance(data, dict):
        raise ValueError(f"data phải là dict, nhận được: {type(data)}")
    
    if 'series' not in data:
        raise ValueError("Thiếu field 'data.series'")
    
    series = data['series']
    if not isinstance(series, list) or len(series) == 0:
        raise ValueError(f"data.series phải là list không rỗng, nhận được: {series}")
    
    # Validate series items
    for idx, s in enumerate(series):
        if not isinstance(s, dict):
            raise ValueError(f"series[{idx}] phải là dict, nhận được: {type(s)}")
        
        if 'name' not in s:
            raise ValueError(f"series[{idx}] thiếu field 'name'")
        
        if 'data' not in s:
            raise ValueError(f"series[{idx}] thiếu field 'data'")
        
        if 'unit' not in s:
            raise ValueError(f"series[{idx}] thiếu field 'unit'")
        
        # Validate data field
        if not isinstance(s['data'], list) or len(s['data']) == 0:
            raise ValueError(f"series[{idx}].data phải là list không rỗng")
    
    # Validate categories (bắt buộc cho bar/line/area/combo)
    chart_type_val = chart_data['chart_type']
    if chart_type_val in ['bar', 'line', 'area', 'combo']:
        if 'categories' not in data:
            raise ValueError(f"chart_type='{chart_type_val}' yêu cầu field 'data.categories'")
        
        if not isinstance(data['categories'], list) or len(data['categories']) == 0:
            raise ValueError(f"data.categories phải là list không rỗng")
    
    # Validate dimensions nếu được cung cấp
    if dimensions:
        try:
            expected_rows, expected_cols = map(int, dimensions.split('x'))
            
            # Check số series (rows - không tính header)
            actual_rows = len(series)
            if actual_rows != expected_rows:
                print(f"⚠️  Warning: Số series không khớp dimensions. Mong đợi {expected_rows} hàng, nhận được {actual_rows}")
                print(f"   Expected: {expected_rows} series, Got: {actual_rows} series")
                print(f"   Dimension requirement: {dimensions}")
            
            # Check số categories (cols - không tính cột tên)
            # Lưu ý: Pie chart là trường hợp đặc biệt - mỗi slice là một "category" của cấu trúc data
            if chart_type_val in ['bar', 'line', 'area', 'combo']:
                actual_cols = len(data['categories'])
                if actual_cols != expected_cols:
                    print(f"⚠️  Warning: Số categories không khớp dimensions. Mong đợi {expected_cols} cột, nhận được {actual_cols}")
                    print(f"   Expected: {expected_cols} categories, Got: {actual_cols} categories")
                    print(f"   Dimension requirement: {dimensions}")
            elif chart_type_val == 'pie':
                # Pie chart: số series = số pie charts cần tạo
                if actual_rows != expected_cols:
                    print(f"⚠️  Warning: Pie chart - Số pies không khớp dimensions. Mong đợi {expected_cols} pie charts, nhận được {actual_rows}")
                    print(f"   For Pie chart {dimensions}: cần {expected_cols} pie charts (mỗi pie=1 cột)")
        
        except ValueError as e:
            print(f"⚠️  Warning: dimensions format không hợp lệ: {dimensions}, lỗi: {e}")
    
    # Validate options
    options = chart_data['options']
    if not isinstance(options, dict):
        raise ValueError(f"options phải là dict, nhận được: {type(options)}")
    
    # Check title (recommended)
    if 'title' not in options or not options['title']:
        print("⚠️  Warning: options.title trống, nên có tiêu đề cho biểu đồ")
    
    # Check source (recommended)
    if 'source' not in options or not options['source']:
        print("⚠️  Warning: options.source trống, nên ghi rõ nguồn dữ liệu")
    
    return True


def process_chart_data_to_option(chart_data: Dict) -> Dict:
    """
    Convert chart data (từ AI) thành ECharts option (bằng GenChart utilities)
    
    Args:
        chart_data: Dict chứa chart data đã validate
            {
                "chart_type": "bar",
                "data": {"categories": [...], "series": [...]},
                "options": {..."title": ...}
            }
    
    Returns:
        Dict: ECharts option đầy đủ
    
    Raises:
        ValueError: Nếu chart_type không được hỗ trợ
    """
    chart_type = chart_data.get('chart_type', '').lower()
    
    # Routing chart_type → GenChart function
    chart_generators = {
        'bar': generate_bar_chart,
        'line': generate_line_chart,
        'pie': generate_pie_chart,
        'area': generate_area_chart,
        # 'combo': generate_combo_chart,  # TODO: Implement if needed
    }
    
    generator_func = chart_generators.get(chart_type)
    
    if generator_func is None:
        supported_types = list(chart_generators.keys())
        raise ValueError(f"chart_type '{chart_type}' không được hỗ trợ. Các loại hỗ trợ: {supported_types}")
    
    try:
        # Call GenChart function
        echarts_option = generator_func(chart_data)
        
        if not echarts_option or not isinstance(echarts_option, dict):
            raise ValueError(f"GenChart trả về option không hợp lệ: {echarts_option}")
        
        return echarts_option
        
    except Exception as e:
        raise ValueError(f"Lỗi khi convert chart data thành ECharts option: {str(e)}")
