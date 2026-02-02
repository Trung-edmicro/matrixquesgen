"""
Module quản lý JSON schemas cho các loại câu hỏi
Hỗ trợ Rich Content: text, image, table, chart (ECharts), latex, mixed
"""
from typing import Dict, List, Optional


# ==================== TÁCH SCHEMAS RIÊNG BIỆT CHO TỪNG TYPE ====================
# Thay vì dùng anyOf phức tạp → Mỗi type có schema riêng → AI clear hơn, ít token hơn

def get_text_content_schema() -> Dict:
    """
    Schema cho content type='text' - Text thuần
    Sử dụng khi: Câu hỏi không có rich_content_types HOẶC chỉ có LT (lý thuyết text)
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "const": "text",
                "description": "Loại content: text thuần"
            },
            "content": {
                "type": "string",
                "description": "Nội dung text thuần - string"
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Nguồn trích dẫn (bắt buộc khi dùng tư liệu ngoài SGK)"
                    }
                }
            }
        },
        "required": ["type", "content"],
        "description": "Text thuần - dùng khi câu hỏi không có bảng/biểu đồ/hình ảnh"
    }


def get_table_content_schema() -> Dict:
    """
    Schema cho content type='table' - Text + Bảng biểu
    Sử dụng khi: rich_content_types chứa 'BK' hoặc ['BK','TT','LT']
    ⚠️ LƯU Ý: Type 'table' = TEXT + BẢNG (không chỉ mỗi bảng)
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "const": "table",
                "description": "Loại content: table (text + bảng)"
            },
            "content": {
                "type": "array",
                "description": "Array chứa text và table object xen kẽ. VD: ['Dựa vào bảng:', {table_object}, 'Hãy cho biết...']",
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "description": "Text mô tả hoặc câu hỏi"
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "const": "table",
                                    "description": "Loại: table"
                                },
                                "content": {
                                    "type": "object",
                                    "properties": {
                                        "headers": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Tiêu đề cột"
                                        },
                                        "rows": {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            },
                                            "description": "Dữ liệu hàng"
                                        }
                                    },
                                    "required": ["headers", "rows"]
                                },
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "caption": {"type": "string"},
                                        "source": {"type": "string"}
                                    }
                                }
                            },
                            "required": ["type", "content"],
                            "description": "Table object"
                        }
                    ]
                },
                "minItems": 1
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Nguồn dữ liệu"}
                }
            }
        },
        "required": ["type", "content"],
        "description": """Type='table' = TEXT + BẢNG (array chứa strings và table object)
        
⚠️ VÍ DỤ:
{
  "type": "table",
  "content": [
    "Dựa vào bảng dưới đây:",
    {
      "type": "table",
      "content": {
        "headers": ["Năm", "GDP (tỷ USD)"],
        "rows": [["2010", "100"], ["2020", "150"]]
      }
    },
    "Hãy cho biết tốc độ tăng trưởng?"
  ]
}"""
    }


def get_chart_content_schema() -> Dict:
    """
    Schema cho content type='chart' - Text + Biểu đồ ECharts
    Sử dụng khi: rich_content_types chứa 'BD' hoặc ['BD','TT','LT']
    ⚠️ LƯU Ý: Type 'chart' = TEXT + BIỂU ĐỒ (không chỉ mỗi biểu đồ)
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "const": "chart",
                "description": "Loại content: chart (text + biểu đồ)"
            },
            "content": {
                "type": "array",
                "description": "Array chứa text và chart object xen kẽ. VD: ['Cho biểu đồ:', {chart_object}, 'Năm nào cao nhất?']",
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "description": "Text mô tả hoặc câu hỏi"
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "const": "chart",
                                    "description": "Loại: chart"
                                },
                                "content": {
                                    "type": "object",
                                    "properties": {
                                        "chartType": {
                                            "type": "string",
                                            "enum": ["bar", "line", "pie", "scatter", "combo"],
                                            "description": "Loại biểu đồ"
                                        },
                                        "echarts": {
                                            "type": "object",
                                            "description": "ECharts config - CHỈ CẦN 5 FIELDS: title, xAxis, yAxis, series, legend",
                                            "properties": {
                                                "title": {
                                                    "type": "object",
                                                    "properties": {
                                                        "text": {"type": "string"},
                                                        "left": {"type": "string"}
                                                    }
                                                },
                                                "xAxis": {
                                                    "type": "object",
                                                    "properties": {
                                                        "type": {"type": "string"},
                                                        "data": {"type": "array"}
                                                    }
                                                },
                                                "yAxis": {
                                                    "type": "object",
                                                    "properties": {
                                                        "type": {"type": "string"},
                                                        "name": {"type": "string"}
                                                    }
                                                },
                                                "series": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "name": {"type": "string"},
                                                            "type": {"type": "string"},
                                                            "data": {"type": "array"},
                                                            "label": {"type": "object"}
                                                        }
                                                    }
                                                },
                                                "legend": {
                                                    "type": "object",
                                                    "properties": {
                                                        "data": {"type": "array"},
                                                        "bottom": {"type": "number"}
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    "required": ["chartType", "echarts"]
                                },
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "caption": {"type": "string"},
                                        "source": {"type": "string"},
                                        "width": {"type": "number"},
                                        "height": {"type": "number"}
                                    }
                                }
                            },
                            "required": ["type", "content"],
                            "description": "Chart object"
                        }
                    ]
                },
                "minItems": 1
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"}
                }
            }
        },
        "required": ["type", "content"],
        "description": """Type='chart' = TEXT + BIỂU ĐỒ (array chứa strings và chart object)

⚠️ VÍ DỤ:
{
  "type": "chart",
  "content": [
    "Cho biểu đồ dân số thành thị:",
    {
      "type": "chart",
      "content": {
        "chartType": "bar",
        "echarts": {
          "title": {"text": "DÂN SỐ THÀNH THỊ", "left": "center"},
          "xAxis": {"type": "category", "data": ["2010", "2015", "2021"]},
          "yAxis": {"type": "value", "name": "triệu người"},
          "series": [{"name": "Dân số", "type": "bar", "data": [26.5, 30.9, 36.6]}],
          "legend": {"data": ["Dân số"], "bottom": 20}
        }
      }
    },
    "Năm nào có dân số cao nhất?"
  ]
}"""
    }


def get_image_content_schema() -> Dict:
    """
    Schema cho content type='image' - Text + Hình ảnh
    Sử dụng khi: rich_content_types chứa 'HA' hoặc ['HA','TT','LT']
    ⚠️ LƯU Ý: Type 'image' = TEXT + HÌNH ẢNH (không chỉ mỗi hình ảnh)
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "const": "image",
                "description": "Loại content: image (text + hình ảnh)"
            },
            "content": {
                "type": "array",
                "description": "Array chứa text và image object xen kẽ. VD: ['Quan sát hình:', {image_object}, 'Đây là hiện tượng gì?']",
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "description": "Text mô tả hoặc câu hỏi"
                        },
                        {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "const": "image",
                                    "description": "Loại: image"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "URL hoặc path của hình ảnh"
                                },
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "caption": {"type": "string"},
                                        "alt": {"type": "string"},
                                        "width": {"type": "number"},
                                        "height": {"type": "number"}
                                    }
                                }
                            },
                            "required": ["type", "content"],
                            "description": "Image object"
                        }
                    ]
                },
                "minItems": 1
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"}
                }
            }
        },
        "required": ["type", "content"],
        "description": """Type='image' = TEXT + HÌNH ẢNH (array chứa strings và image object)

⚠️ VÍ DỤ:
{
  "type": "image",
  "content": [
    "Quan sát bản đồ dưới đây:",
    {
      "type": "image",
      "content": "https://example.com/map.png",
      "metadata": {"caption": "Hình 1: Bản đồ ASEAN"}
    },
    "Quốc gia nào có diện tích lớn nhất?"
  ]
}"""
    }


def get_mixed_content_schema(rich_types: Optional[List[str]] = None) -> Dict:
    """
    Schema cho content type='mixed' - Kết hợp NHIỀU loại rich content
    Sử dụng khi: rich_content_types chứa NHIỀU loại khác nhau (VD: ['BK','BD'], ['BK','HA'], ['BD','HA','BK'])
    ⚠️ LƯU Ý: Type 'mixed' CHỈ dùng khi có ≥2 loại rich content khác nhau (table+chart, table+image, chart+image, ...)
    
    Args:
        rich_types: List các loại rich content (VD: ['BK', 'BD', 'HA'])
    """
    # Build description dựa trên rich_types
    types_hint = ""
    if rich_types:
        type_map = {"BK": "table", "BD": "chart", "HA": "image", "TT": "calculation"}
        available_types = [type_map.get(t, t) for t in rich_types if t in type_map]
        if available_types:
            types_hint = f" - Có thể chứa: {', '.join(available_types)}"
    
    # Build explicit example based on rich_types
    example_str = ""
    if rich_types:
        if "BD" in rich_types:
            example_str = """

⚠️ VÍ DỤ cho BIỂU ĐỒ:
[
  "Cho biểu đồ dân số thành thị:",
  {
    "type": "chart",
    "content": {
      "chartType": "bar",
      "echarts": {
        "title": {"text": "DÂN SỐ THÀNH THỊ", "left": "center"},
        "xAxis": {"type": "category", "data": ["2010", "2015", "2021"]},
        "yAxis": {"type": "value", "name": "triệu người"},
        "series": [{"name": "Dân số", "type": "bar", "data": [26.5, 30.9, 36.6]}],
        "legend": {"data": ["Dân số"], "bottom": 20}
      }
    }
  },
  "Năm nào có dân số cao nhất?"
]"""
        elif "BK" in rich_types:
            example_str = "\n\n⚠️ VÍ DỤ cho BẢNG:\n['Dựa vào bảng:', {\"type\": \"table\", \"content\": {\"headers\": [\"Năm\", \"GDP\"], \"rows\": [[\"2010\", \"100\"], [\"2020\", \"150\"]]}}, 'Hãy cho biết...']"
    
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "const": "mixed",
                "description": "Loại content: mixed (kết hợp text + rich content)"
            },
            "content": {
                "type": "array",
                "description": f"Array chứa text (string) và rich objects xen kẽ{types_hint}.{example_str}\n\n⚠️ QUAN TRỌNG: PHẢI có ít nhất 1 rich object (table/chart/image) trong array, KHÔNG chỉ có text thuần!",
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "description": "Text thuần"
                        },
                        {
                            "type": "object",
                            "description": "Rich content object - PHẢI có type và content",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["table", "chart", "image"],
                                    "description": "Loại rich content"
                                },
                                "content": {
                                    "anyOf": [
                                        {
                                            "type": "object",
                                            "properties": {
                                                "headers": {"type": "array", "items": {"type": "string"}},
                                                "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
                                            },
                                            "required": ["headers", "rows"],
                                            "description": "Table content - object {headers, rows}"
                                        },
                                        {
                                            "type": "object",
                                            "properties": {
                                                "chartType": {"type": "string", "enum": ["bar", "line", "pie", "scatter", "combo"]},
                                                "echarts": {"type": "object"}
                                            },
                                            "required": ["chartType", "echarts"],
                                            "description": "Chart content - object {chartType, echarts}"
                                        },
                                        {
                                            "type": "string",
                                            "description": "Image content - URL string"
                                        }
                                    ]
                                },
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "caption": {"type": "string"},
                                        "source": {"type": "string"}
                                    }
                                }
                            },
                            "required": ["type", "content"]
                        }
                    ]
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Nguồn dữ liệu"}
                }
            }
        },
        "required": ["type", "content"],
        "description": "Mixed content - content PHẢI là array chứa strings và objects đầy đủ"
    }


def get_content_schema_by_rich_types(rich_content_types: Optional[List[str]] = None) -> Dict:
    """
    ⭐ HÀM CHÍNH: Chọn schema phù hợp dựa trên rich_content_types từ ma trận
    
    🎯 LOGIC PHÂN LOẠI MỚI (Rõ ràng hơn):
    
    1. None / [] / chỉ ['LT'] / chỉ ['TT'] / ['LT','TT']:
       → type='text' (text thuần)
    
    2. ['BK'] hoặc ['BK','LT'] hoặc ['BK','TT'] hoặc ['BK','LT','TT']:
       → type='table' (TEXT + BẢNG - array format)
       ⚠️ Lưu ý: Không chỉ có bảng, phải có cả text mô tả
    
    3. ['BD'] hoặc ['BD','LT'] hoặc ['BD','TT'] hoặc ['BD','LT','TT']:
       → type='chart' (TEXT + BIỂU ĐỒ - array format)
       ⚠️ Lưu ý: Không chỉ có biểu đồ, phải có cả text mô tả
    
    4. ['HA'] hoặc ['HA','LT'] hoặc ['HA','TT'] hoặc ['HA','LT','TT']:
       → type='image' (TEXT + HÌNH ẢNH - array format)
       ⚠️ Lưu ý: Không chỉ có hình ảnh, phải có cả text mô tả
    
    5. Nhiều loại khác nhau: ['BK','BD'], ['BK','HA'], ['BD','HA'], ['BK','BD','HA']:
       → type='mixed' (KẾT HỢP NHIỀU LOẠI RICH CONTENT)
       ⚠️ Lưu ý: Chỉ dùng mixed khi có ≥2 loại rich content khác nhau
    
    Args:
        rich_content_types: List các loại rich content từ matrix (VD: ['BK'], ['BD'], ['BK','BD'])
    
    Returns:
        Dict: Schema phù hợp với loại content
    """
    if not rich_content_types:
        return get_text_content_schema()
    
    # Lọc bỏ 'LT' (lý thuyết) và 'TT' (tính toán) - chỉ giữ lại BK, BD, HA
    actual_rich_types = [t for t in rich_content_types if t not in ['LT', 'TT']]
    
    # Nếu không còn rich type nào → text thuần
    if not actual_rich_types:
        return get_text_content_schema()
    
    # Nếu chỉ có 1 loại rich content (BK/BD/HA) → dùng schema riêng (text + rich)
    if len(actual_rich_types) == 1:
        rich_type = actual_rich_types[0]
        if rich_type == 'BK':
            # BK → text + table
            return get_table_content_schema()
        elif rich_type == 'BD':
            # BD → text + chart
            return get_chart_content_schema()
        elif rich_type == 'HA':
            # HA → text + image
            return get_image_content_schema()
    
    # Nhiều loại rich content khác nhau → dùng mixed
    # VD: ['BK','BD'], ['BK','HA'], ['BD','HA'], ['BK','BD','HA']
    return get_mixed_content_schema(actual_rich_types)


# ==================== LEGACY FUNCTION (Deprecated) ====================
def get_rich_content_schema() -> Dict:
    """
    Trả về JSON schema cho Rich Content hỗ trợ 4 loại: TEXT, BK, BD, HA
    
    - TEXT: string thuần (mặc định)
    - BK (Bảng biểu): table structure với headers/rows
    - BD (Biểu đồ): ECharts config object
    - HA (Hình ảnh): URL hoặc path
    - MIXED: kết hợp text + table/chart/image
    
    Returns:
        Dict: JSON schema với properties strict và explicit types
    """
    return {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["text", "table", "chart", "image", "mixed"],
                "description": "Loại content: 'text' (text thuần), 'table' (bảng), 'chart' (biểu đồ), 'image' (hình ảnh), 'mixed' (text + rich content)"
            },
            "content": {
                "anyOf": [
                    {
                        "type": "string",
                        "description": "String cho type='text' hoặc type='image'"
                    },
                    {
                        "type": "object",
                        "properties": {
                            "headers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Headers của bảng - array of strings"
                            },
                            "rows": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "description": "Rows của bảng - array of arrays of strings"
                            }
                        },
                        "required": ["headers", "rows"],
                        "description": "Object structure cho type='table' - PHẢI CÓ headers và rows"
                    },
                    {
                        "type": "object",
                        "properties": {
                            "chartType": {
                                "type": "string",
                                "enum": ["bar", "line", "pie", "scatter", "combo"],
                                "description": "Loại biểu đồ"
                            },
                            "echarts": {
                                "type": "object",
                                "description": "ECharts config object - PHẢI là object, KHÔNG PHẢI JSON string"
                            }
                        },
                        "required": ["chartType", "echarts"],
                        "description": "Object structure cho type='chart' - PHẢI CÓ chartType và echarts"
                    },
                    {
                        "type": "array",
                        "description": "Array cho type='mixed' - chứa strings và objects xen kẽ"
                    }
                ],
                "description": """⚠️ QUY TẮC QUAN TRỌNG - PHẢI TUÂN THỦ:

1. type="text" → content PHẢI LÀ STRING + metadata.source BẮT BUỘC khi dùng tư liệu ngoài SGK:
   {"type": "text", "content": "ASEAN được thành lập năm 1967 tại Bangkok", "metadata": {"source": "Nguồn: UN Statistics 2021"}},

2. type="table" → content PHẢI LÀ OBJECT (KHÔNG PHẢI STRING):
   {
     "type": "table",
     "content": {
       "headers": ["Năm", "GDP"],
       "rows": [["2020", "100"], ["2021", "120"]]
     }
   }
   ❌ SAI: "content": "{\\"headers\\":...}" (JSON string)
   ✅ ĐÚNG: "content": {"headers": [...], "rows": [...]} (object thực)

3. type="chart" → content PHẢI LÀ OBJECT (KHÔNG PHẢI STRING):
   {
     "type": "chart",
     "content": {
       "chartType": "bar",
       "echarts": {"xAxis": {...}, "yAxis": {...}, "series": [...]}
     }
   }
   ❌ SAI: "echarts": "{\\"xAxis\\":...}" (JSON string)
   ✅ ĐÚNG: "echarts": {"xAxis": {...}} (object thực)

4. type="image" → content PHẢI LÀ STRING (URL):
   {"type": "image", "content": "https://example.com/map.png"}

5. type="mixed" → content PHẢI LÀ ARRAY chứa string và object xen kẽ:
   {
     "type": "mixed",
     "content": [
       "Dựa vào bảng:",
       {"type": "table", "content": {"headers": [...], "rows": [...]}},
       "Hãy cho biết kết quả?"
     ]
   }
   ❌ SAI: Nested object có content là JSON string
   ✅ ĐÚNG: Nested object có content là object thực"""
            },
            "metadata": {
                "type": "object",
                "description": "Metadata tùy chọn - đặc biệt khuyến khích dùng 'source' cho type='text' để trích dẫn nguồn tư liệu",
                "properties": {
                    "caption": {"type": "string", "description": "Chú thích (VD: 'Bảng 1: Dân số')"},
                    "source": {"type": "string", "description": "Nguồn dữ liệu - BẮT BUỘC cho type='text' khi dùng tư liệu ngoài SGK"},
                    "width": {"type": "number", "description": "Chiều rộng (px)"},
                    "height": {"type": "number", "description": "Chiều cao (px)"}
                }
            }
        },
        "required": ["type", "content"],
        "description": """Rich Content Structure - BẮT BUỘC tuân thủ format:

**1. TEXT THUẦN** (mặc định - khi KHÔNG có rich_content_types):
{
  "type": "text",
  "content": "ASEAN được thành lập năm 1967 tại Bangkok",
  "metadata": {
    "source": "Nguồn: UN Statistics 2021"
  }
}

**LƯU Ý QUAN TRỌNG CHO TEXT**: 
- Luôn sử dụng metadata.source khi trích dẫn tư liệu ngoài SGK
- Format nguồn: (Tác giả, "Tên tài liệu", NXB/Nguồn, năm)

**2. BẢNG (type: "table")** - KHI câu hỏi có rich_content_types="BK":
{
  "type": "table",
  "content": {
    "headers": ["Quốc gia", "Năm gia nhập", "Dân số (triệu)"],
    "rows": [
      ["Thái Lan", "1967", "70"],
      ["Việt Nam", "1995", "98"],
      ["Singapore", "1967", "5.8"]
    ]
  },
  "metadata": {
    "caption": "Bảng 1: Thông tin các nước ASEAN",
    "source": "Nguồn: UN Statistics 2021"
  }
}

**3. BIỂU ĐỒ (type: "chart")** - KHI câu hỏi có rich_content_types="BD":
{
  "type": "chart",
  "content": {
    "chartType": "bar",
    "echarts": {
      "title": {"text": "DÂN SỐ THÀNH THỊ 2010-2021", "left": "center"},
      "xAxis": {"type": "category", "data": ["2010", "2015", "2021"]},
      "yAxis": {"type": "value", "name": "triệu người"},
      "series": [{
        "name": "Dân số thành thị",
        "type": "bar",
        "data": [26.5, 30.9, 36.6],
        "label": {"show": true, "position": "top"}
      }],
      "legend": {"data": ["Dân số thành thị"], "bottom": 20}
    }
  },
  "metadata": {
    "caption": "Hình 1: Dân số thành thị",
    "width": 800,
    "height": 500,
    "source": "Nguồn: Niên giám thống kê 2021"
  }
}

**4. HÌNH ẢNH (type: "image")** - KHI câu hỏi có rich_content_types="HA":
{
  "type": "image",
  "content": "https://example.com/map.png",
  "metadata": {
    "caption": "Hình 1: Bản đồ khu vực Đông Nam Á",
    "alt": "Bản đồ ASEAN",
    "width": 600,
    "height": 400
  }
}

**5. MIXED (type: "mixed")** - KHI câu hỏi có CẢ text + BK/BD/HA:
VD 1 - Câu hỏi TN có biểu đồ:
{
  "type": "mixed",
  "content": [
    "Dựa vào biểu đồ nhiệt độ trung bình năm:",
    {
      "type": "chart",
      "content": {
        "chartType": "bar",
        "echarts": {"xAxis": {...}, "yAxis": {...}, "series": [...]}
      },
      "metadata": {"caption": "Hình 1: Nhiệt độ trung bình"}
    },
    "Nhận xét nào sau đây ĐÚNG về xu hướng nhiệt độ?"
  ]
}

VD 2 - Câu hỏi TLN có bảng:
{
  "type": "mixed",
  "content": [
    "Dựa vào bảng số liệu dưới đây:",
    {
      "type": "table",
      "content": {
        "headers": ["Năm", "Tỉ trọng (%)"],
        "rows": [["2010", "42.1"], ["2020", "50.5"]]
      },
      "metadata": {"caption": "Bảng 1: Cơ cấu GDP"}
    },
    "Hãy tính tỉ lệ tăng trưởng giữa hai năm?"
  ]
}

**LƯU Ý QUAN TRỌNG - ĐẶC BIỆT CHO DẠNG TN (Trắc nghiệm)**:
- Câu hỏi TN CÓ bảng/biểu đồ: PHẢI dùng type="mixed" với content là array [text_câu_hỏi, rich_object]
- VD đúng: 
  question_stem: {
    "type": "mixed",
    "content": [
      "Dựa vào biểu đồ:",
      {"type": "chart", "content": {...}},
      "Nhận xét nào sau đây đúng?"
    ]
  }
- KHÔNG được chỉ có biểu đồ/bảng mà thiếu text câu hỏi!

**LƯU Ý KHÁC**:
- CHỈ dùng rich content KHI câu hỏi được đánh dấu rich_content_types (BK/BD/HA)
- KHÔNG dùng field "raw_content", "rich_content" hoặc tên field tự nghĩ
- Content PHẢI đúng type: text→string, table→object, chart→object, image→string, mixed→array
- KHÔNG trả về null, KHÔNG trả về JSON string, PHẢI là object/array thực
- Với câu hỏi TN: options (A/B/C/D) thường là text thuần, CHỈ question_stem mới có rich content"""
    }

def get_multiple_choice_array_schema(content_schema: Optional[Dict] = None) -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Trắc nghiệm
    HỖ TRỢ RICH CONTENT: Ảnh, Bảng, Biểu đồ ECharts, Công thức LaTeX
    
    Args:
        content_schema: Schema cho question_stem (nếu None → dùng text_content_schema)
    
    Returns:
        Dict: JSON schema cho array questions với metadata sư phạm phong phú và rich content
    """
    
    # Sử dụng content_schema được truyền vào, hoặc mặc định text schema
    if content_schema is None:
        content_schema = get_text_content_schema()
    
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": """Mảng các câu hỏi trắc nghiệm. Mỗi câu hỏi phải khác nhau về nội dung và góc độ tiếp cận.""",
                "items": {
                    "type": "object",
                    "properties": {
                        # === PHẦN CỐT LÕI CÂU HỎI ===
                        "question_stem": {
                            "description": "Nội dung câu hỏi - có thể là text, table, chart, image, hoặc mixed",
                            **content_schema
                        },
                        
                        # === PHẦN ĐÁP ÁN ===
                        "options": {
                            "type": "object",
                            "properties": {
                                "A": {
                                    "type": "string",
                                    "description": "Đáp án A - text thuần"
                                },
                                "B": {
                                    "type": "string",
                                    "description": "Đáp án B - text thuần"
                                },
                                "C": {
                                    "type": "string",
                                    "description": "Đáp án C - text thuần"
                                },
                                "D": {
                                    "type": "string",
                                    "description": "Đáp án D - text thuần"
                                }
                            },
                            "required": ["A", "B", "C", "D"]
                        },
                        
                        "correct_answer": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D"],
                            "description": "Đáp án đúng"
                        },
                        
                        # === PHẦN PHÂN LOẠI ===
                        "level": {
                            "type": "string",
                            "enum": ["NB", "TH", "VD", "VDC"],
                            "description": "Cấp độ nhận thức"
                        },
                        
                        # === PHẦN GIẢI THÍCH ===
                        "explanation": {
                            "type": "string",
                            "description": """Lời giải ngắn gọn (TỐI ĐA 500 ký tự):
                            - Giải thích tại sao đáp án đúng
                            - Tại sao các đáp án khác sai
                            - ⚠️ NẾU CÓ BẢNG/BIỂU ĐỒ/ẢNH: CHỈ nêu kết luận, KHÔNG copy số liệu
                            - NGHIÊM CẤM: giải dài dòng, lặp lại, giải đi giải lại""",
                            "maxLength": 500
                        }
                    },
                    "required": ["question_stem", "options", "correct_answer", "level", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }

def get_essay_array_schema(content_schema: Optional[Dict] = None) -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Tự luận (TL)
    HỖ TRỢ RICH CONTENT: Câu hỏi có thể chứa tư liệu ảnh, bảng, biểu đồ
    
    Args:
        content_schema: Schema cho question_stem (nếu None → dùng text_content_schema)
    
    Returns:
        Dict: JSON schema cho array questions TL - tối ưu hóa độ dài output
    """
    
    # Sử dụng content_schema được truyền vào, hoặc mặc định text schema
    if content_schema is None:
        content_schema = get_text_content_schema()
    
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": "Mảng câu hỏi Tự luận. Mỗi câu phải khác nhau về góc độ tiếp cận (analysis/comparison/evaluation).",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_stem": {
                            "description": "Câu hỏi - có thể chứa bảng, biểu đồ tư liệu",
                            **content_schema
                        },
                        "question_type": {
                            "type": "string",
                            "enum": ["analysis", "comparison", "evaluation", "explanation", "synthesis", "argumentation"],
                            "description": "Loại câu hỏi"
                        },
                        "level": {
                            "type": "string",
                            "enum": ["VD", "VDC"],
                            "description": "Cấp độ"
                        },
                        "historical_context": {
                            "type": "string",
                            "description": "Bối cảnh lịch sử (nếu cần) - TỐI ĐA 200 ký tự",
                            "maxLength": 200
                        },
                        "required_elements": {
                            "type": "array",
                            "items": {"type": "string", "maxLength": 100},
                            "description": "Các yếu tố bắt buộc phải có trong câu trả lời (3-5 items)",
                            "minItems": 3,
                            "maxItems": 5
                        },
                        "answer_structure": {
                            "type": "object",
                            "description": "Cấu trúc câu trả lời - VD: {intro: '...', body: '...', conclusion: '...'}",
                            "properties": {
                                "intro": {"type": "string", "maxLength": 100},
                                "body": {"type": "string", "maxLength": 150},
                                "conclusion": {"type": "string", "maxLength": 100}
                            },
                            "required": ["intro", "body", "conclusion"]
                        },
                        "sample_answer": {
                            "type": "string",
                            "description": "Câu trả lời mẫu ngắn gọn - TỐI ĐA 150 ký tự",
                            "maxLength": 150
                        },
                        "key_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "point": {"type": "string", "maxLength": 30},
                                    "score": {"type": "number"}
                                },
                                "required": ["point", "score"]
                            },
                            "description": "Điểm kiến thức then chốt (3-4 items) - Mỗi point TỐI ĐA 30 ký tự",
                            "minItems": 3,
                            "maxItems": 4
                        },
                        "scoring_rubric": {
                            "type": "string",
                            "description": "Thang điểm tổng quát - TỐI ĐA 100 ký tự. VD: 'Phân tích đúng 3 điểm chính (6đ), kết luận logic (1đ)'",
                            "maxLength": 100
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Lời giải ngắn gọn (TỐI ĐA 300 ký tự): Giải thích ngắn ngọn. NGHIÊM CẤM giải dài dòng.",
                            "maxLength": 300
                        }
                    },
                    "required": ["question_stem", "question_type", "level", "required_elements", "answer_structure", "sample_answer", "key_points", "scoring_rubric", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }

def get_true_false_schema(content_schema: Optional[Dict] = None) -> Dict:
    """
    Trả về JSON schema cho câu hỏi Đúng/Sai
    HỖ TRỢ RICH CONTENT: Tư liệu có thể chứa bảng, biểu đồ, ảnh
    
    Args:
        content_schema: Schema cho source_text (nếu None → dùng text_content_schema)
    
    Returns:
        Dict: JSON schema cho câu hỏi Đúng/Sai với 4 mệnh đề và rich content support
    """
    
    # Sử dụng content_schema được truyền vào, hoặc mặc định text schema
    if content_schema is None:
        content_schema = get_text_content_schema()
    
    return {
        "type": "object",
        "properties": {
            # === PHẦN TƯ LIỆU (Rich Content Support) ===
            "source_text": content_schema,
            
            "source_citation": {
                "type": "string",
                "description": """TRÍCH DẪN NGUỒN - BẮT BUỘC LUÔN PHẢI ĐIỀN:
                
                **QUY TẮC BẮT BUỘC**:
                - 100% câu hỏi phải có tư liệu từ nguồn ngoài SGK
                  → PHẢI điền trường này với format chuẩn
                - KHÔNG BAO GIỜ được để null/trống
                
                **Định dạng chuẩn**:
                (Tác giả, "Tên bài/sách", Tên tạp chí/NXB số X (tháng/năm), tr. Y)
                
                **Ví dụ ĐÚNG**:
                - Tạp chí: (Nguyễn Viết Thảo, "Bối cảnh hình thành và đặc điểm nổi bật của cục diện thế giới hiện nay", Tạp chí Lí luận Chính trị số 541 (3/2023), tr. 151)
                - Sách: (Phan Huy Lê, "Lịch sử Việt Nam", NXB Giáo dục, 2020, tr. 234)
                - Văn kiện: (Tuyên bố ASEAN, Bangkok, 08/08/1967, ASEAN Secretariat)
                - Web chính thống: (ASEAN, "Charter", asean.org, truy cập 2024)
                
                **Ví dụ SAI (không chấp nhận)**:
                - "Wikipedia"
                - "Nguồn internet"  
                - "SGK Lịch sử 12" (nếu dùng SGK thì để null, đừng điền)
                
                **QUAN TRỌNG**: Việc ghi nguồn chuẩn xác thể hiện tính học thuật và giúp kiểm chứng chất lượng tư liệu!"""
            },
            
            "source_origin": {
                "type": "string",
                "enum": ["academic_journal", "scholarly_book", "official_document", "reputable_media"],
                "description": """NGUỒN GỐC TƯ LIỆU (Bắt buộc phải điền - 100% phải từ nguồn ngoài SGK):
                
                **BẮT BUỘC chọn 1 trong 4 loại nguồn học thuật**:
                1. 'academic_journal': Tạp chí khoa học (Ưu tiên cao nhất - 40%)
                   → Ví dụ: Tạp chí Lí luận Chính trị, Nghiên cứu Lịch sử, Nghiên cứu Quốc tế...
                   → BẮT BUỘC điền source_citation
                
                2. 'scholarly_book': Sách chuyên khảo (30%)
                   → Ví dụ: Sách của các nhà sử học, sách nghiên cứu chuyên sâu
                   → BẮT BUỘC điền source_citation
                
                3. 'official_document': Văn kiện chính thức (20%)
                   → Ví dụ: Hiến chương UN, Tuyên bố ASEAN, Nghị quyết Chính phủ...
                   → BẮT BUỘC điền source_citation
                
                4. 'reputable_media': Báo chí uy tín (10%)
                   → Ví dụ: Nhân Dân, VnExpress, BBC (chỉ bài phân tích chuyên sâu)
                   → BẮT BUỘC điền source_citation
                
                **CẤM TUYỆT ĐỐI**:
                - KHÔNG được dùng 'textbook' (đã bị loại bỏ)
                - KHÔNG được dùng 'combined' nếu có thành phần SGK
                - 100% tư liệu phải từ nguồn ngoài đã search được
                
                **LƯU Ý**: Luôn ưu tiên nguồn học thuật (1-2) hơn nguồn khác!"""
            },
            
            "source_type": {
                "type": "string",
                "description": """Loại tư liệu (giúp AI hiểu cách xử lý):
                - 'primary_source': Tư liệu gốc (văn kiện, thư, hồi ký, tuyên bố chính thức...)
                - 'historical_description': Mô tả sự kiện lịch sử (tái hiện sinh động)
                - 'analytical_summary': Phân tích tổng hợp (từ các nhà nghiên cứu)
                - 'contextual_scenario': Tình huống có bối cảnh (đặt vấn đề trong ngữ cảnh)"""
            },
            
            "pedagogical_approach": {
                "type": "string", 
                "description": """Cách tiếp cận sư phạm cho bộ câu hỏi Đ/S:
                - Kiểm tra đọc hiểu tư liệu học thuật
                - Phân tích đa góc độ một sự kiện
                - Đánh giá khả năng phán đoán dựa trên tư liệu chuyên sâu
                - Phân biệt sự thật và suy luận
                - Rèn kỹ năng làm việc với nguồn học thuật""",
                "maxLength": 200
            },
            
            "search_evidence": {
                "type": "string",
                "description": """GHI CHÚ QUÁ TRÌNH TÌM KIẾM (Khuyến khích điền để minh bạch):
                
                **Nên ghi**:
                - Query đã search: "Ví dụ: 'ASEAN thành lập 1967 Bangkok tuyên bố nguyên văn'"
                - Tại sao chọn tư liệu này: "Nguồn từ tạp chí khoa học uy tín, phân tích sâu hơn SGK"
                - So sánh với INPUT DATA: "Phù hợp với nội dung SGK về thành lập ASEAN, bổ sung góc nhìn mới"
                - Nguồn khác đã xem xét: "Đã xem Wikipedia nhưng không đủ uy tín"
                
                **Lợi ích**:
                - Giúp kiểm chứng chất lượng search
                - Minh bạch quy trình tạo câu hỏi
                - Dễ debug nếu có vấn đề""",
                "maxLength": 300
            },
            
            # === PHẦN 4 MỆNH ĐỀ ===
            "statements": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": """Mệnh đề a - Viết tự nhiên như phát biểu thông thường:
                                - Không cần bắt đầu bằng công thức giống nhau
                                - Có thể ngắn hoặc dài tùy nội dung
                                - Đa dạng cách diễn đạt"""
                            },
                            "level": {
                                "type": "string", 
                                "enum": ["NB", "TH", "VD", "VDC"]
                            },
                            "correct_answer": {"type": "boolean"},
                            "reasoning_type": {
                                "type": "string",
                                "description": """Loại suy luận cần để trả lời:
                                - 'direct': Có trực tiếp trong tư liệu
                                - 'inference': Cần suy luận từ tư liệu
                                - 'knowledge': Cần kiến thức nền
                                - 'analysis': Cần phân tích mối quan hệ"""
                            }
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "b": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"},
                            "reasoning_type": {"type": "string"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "c": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"},
                            "reasoning_type": {"type": "string"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "d": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"},
                            "reasoning_type": {"type": "string"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    }
                },
                "required": ["a", "b", "c", "d"]
            },
            
            "statement_diversity_note": {
                "type": "string",
                "description": """(Tùy chọn) Ghi chú về tính đa dạng của 4 mệnh đề:
                - Đã kiểm tra các góc độ nào (thời gian, không gian, nhân quả, ý nghĩa...)
                - Tại sao chọn 4 mệnh đề này
                - Cách cân bằng độ khó""",
                "maxLength": 200
            },
            
            # === PHẦN GIẢI THÍCH ===
            "explanation": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "string",
                        "description": """Giải thích mệnh đề a (TỐI ĐA 400 ký tự):
                        - Tại sao đúng/sai
                        - Dẫn chứng từ tư liệu hoặc kiến thức
                        - ⚠️ NẾU SOURCE_TEXT CÓ BẢNG/BIỂU ĐỒ: CHỈ nêu kết luận, KHÔNG copy số liệu
                        - NGHIÊM CẤM: lặp lại source_text, giải dài dòng""",
                        "maxLength": 400
                    },
                    "b": {
                        "type": "string",
                        "description": "Giải thích mệnh đề b (TỐI ĐA 400 ký tự) - Tương tự mệnh đề a",
                        "maxLength": 400
                    },
                    "c": {
                        "type": "string",
                        "description": "Giải thích mệnh đề c (TỐI ĐA 400 ký tự) - Tương tự mệnh đề a",
                        "maxLength": 400
                    },
                    "d": {
                        "type": "string",
                        "description": "Giải thích mệnh đề d (TỐI ĐA 400 ký tự) - Tương tự mệnh đề a",
                        "maxLength": 400
                    }
                },
                "required": ["a", "b", "c", "d"]
            },
            
            # === METADATA BỔ SUNG ===
            "common_mistakes": {
                "type": "object",
                "description": """(Tùy chọn) Sai lầm thường gặp cho từng mệnh đề:
                - Học sinh hay nhầm lẫn điểm nào
                - Tại sao dễ nhầm""",
                "properties": {
                    "a": {"type": "string", "maxLength": 150},
                    "b": {"type": "string", "maxLength": 150},
                    "c": {"type": "string", "maxLength": 150},
                    "d": {"type": "string", "maxLength": 150}
                }
            },
            
            "source_quality_note": {
                "type": "string",
                "description": """ĐÁNH GIÁ CHẤT LƯỢNG TƯ LIỆU (Nên điền khi dùng nguồn ngoài):
                
                **Nên đánh giá**:
                - Giá trị học thuật: "Bài phân tích từ tạp chí uy tín, có tham khảo nhiều nguồn"
                - So với SGK: "Bổ sung góc nhìn phân tích chuyên sâu hơn, cập nhật hơn"
                - Độ tin cậy: "Tác giả là chuyên gia về lịch sử thế giới hiện đại"
                - Phù hợp học sinh: "Ngôn ngữ học thuật nhưng dễ hiểu, phù hợp lớp 12"
                
                **Mục đích**:
                - Giúp đánh giá xem tư liệu có đủ chất lượng không
                - Đảm bảo tư liệu phù hợp với trình độ học sinh
                - Xác nhận tư liệu có giá trị sư phạm cao""",
                "maxLength": 300
            }
        },
        "required": [
            "source_text",
            "source_citation",
            "source_origin",
            "statements",
            "explanation"
        ]
    }

def get_short_answer_array_schema(content_schema: Optional[Dict] = None) -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Trắc nghiệm luận (TLN)
    HỖ TRỢ RICH CONTENT: Câu hỏi có thể chứa ảnh, bảng, biểu đồ
    
    Args:
        content_schema: Schema cho question_stem (nếu None → dùng text_content_schema)
    
    Returns:
        Dict: JSON schema cho array questions TLN với hướng dẫn đa dạng hóa và rich content
    """
    
    # Sử dụng content_schema được truyền vào, hoặc mặc định text schema
    if content_schema is None:
        content_schema = get_text_content_schema()
    
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": "Mảng câu hỏi TLN. Mỗi câu phải khác nhau về loại (time/location/name/concept).",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_stem": {
                            "description": "Câu hỏi - có thể chứa bảng, biểu đồ",
                            **content_schema
                        },
                        "question_type": {
                            "type": "string",
                            "enum": ["time", "location", "name", "concept", "meaning", "cause", "result", "number"],
                            "description": "Loại câu hỏi"
                        },
                        "correct_answer": {
                            "type": "string",
                            "description": "Đáp án đúng - CHỈ GHI SỐ (không có đơn vị, không có chữ). VD: '38', '177', '2.5'"
                        },
                        "level": {
                            "type": "string",
                            "enum": ["NB", "TH", "VD", "VDC"],
                            "description": "Cấp độ tư duy"
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Lời giải ngắn gọn (TỐI ĐA 300 ký tự - GIẢM TỪ 500): CHỈ ghi công thức + kết quả. NGHIÊM CẤM giải dài dòng.",
                            "maxLength": 300
                        }
                    },
                    "required": ["question_stem", "question_type", "correct_answer", "level", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }

