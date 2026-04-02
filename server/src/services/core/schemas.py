"""
Module quản lý JSON schemas cho các loại câu hỏi
Hỗ trợ Rich Content: text, image, table, chart (ECharts), latex, mixed
"""
from typing import Dict, List, Optional, Union


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
                                            "description": "⚠️ BẮT BUỘC: ECharts configuration object - KHÔNG ĐƯỢC RỖNG! Phải có xAxis, yAxis, series",
                                            "properties": {
                                                "xAxis": {
                                                    "type": "object",
                                                    "description": "Trục ngang - BẮT BUỘC có 'data' array. VD: {\"type\": \"category\", \"data\": [\"2010\", \"2015\", \"2021\"]}"
                                                },
                                                "yAxis": {
                                                    "anyOf": [
                                                        {"type": "object"},
                                                        {"type": "array"}
                                                    ],
                                                    "description": "Trục dọc - BẮT BUỘC. VD: {\"type\": \"value\", \"name\": \"triệu người\"}"
                                                },
                                                "series": {
                                                    "type": "array",
                                                    "description": "Dữ liệu biểu đồ - BẮT BUỘC, array of objects. VD: [{\"name\": \"Dân số\", \"type\": \"bar\", \"data\": [26.5, 30.9, 36.6]}]",
                                                    "minItems": 1
                                                }
                                            },
                                            "required": ["xAxis", "yAxis", "series"],
                                            "additionalProperties": True
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
        "description": """VÍ DỤ CỤ THỂ - PHẢI FOLLOW:

{
  "type": "chart",
  "content": [
    "Cho biểu đồ dân số thành thị:",
    {
      "type": "chart",
      "content": {
        "chartType": "bar",
        "echarts": {
          "xAxis": {"type": "category", "data": ["2010", "2015", "2021"]},
          "yAxis": {"type": "value", "name": "triệu người"},
          "series": [{
            "name": "Dân số thành thị",
            "type": "bar",
            "data": [26.5, 30.9, 36.6]
          }]
        }
      },
      "metadata": {"source": "Niên giám thống kê 2021"}
    },
    "Năm nào có dân số cao nhất?"
  ]
}

⚠️ QUAN TRỌNG:
- echarts KHÔNG ĐƯỢC RỖNG {}
- PHẢI có xAxis.data (array strings)
- PHẢI có yAxis (object hoặc array)
- PHẢI có series[0].data (array numbers)
"""
    }


def get_image_content_schema() -> Dict:
    """
    Schema cho content type='image' - Text + Hình ảnh
    Sử dụng khi: rich_content_types chứa 'HA_MH' (minh họa) hoặc 'HA_TL' (tư liệu)
    
    ⭐ LUỒNG MỚI - AI GENERATE IMAGE:
    - AI output marker '[IMAGE_PLACEHOLDER]' trong content array
    - Thêm 'image_description' trong metadata để mô tả hình cần generate
    - ImageWorkflowService sẽ tự động:
      1. Extract image_description
      2. Generate image bằng Vertex AI Imagen
      3. Replace '[IMAGE_PLACEHOLDER]' bằng image object thực
    
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
                "description": "Array chứa text và '[IMAGE_PLACEHOLDER]' marker. Workflow service sẽ replace marker bằng hình thật. VD: ['Quan sát hình:', '[IMAGE_PLACEHOLDER]', 'Đây là hiện tượng gì?']",
                "items": {
                    "anyOf": [
                        {
                            "type": "string",
                            "description": "Text mô tả hoặc câu hỏi"
                        },
                        {
                            "type": "string",
                            "const": "[IMAGE_PLACEHOLDER]",
                            "description": "⭐ IMAGE PLACEHOLDER - Dùng marker này khi cần AI generate hình ảnh. Workflow service sẽ tự động generate và replace sau."
                        }
                    ]
                },
                "minItems": 1
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Nguồn dữ liệu"},
                    "image_description": {
                        "type": "string",
                        "description": "⭐ BẮT BUỘC khi dùng [IMAGE_PLACEHOLDER]: Mô tả chi tiết hình ảnh cần AI generate. VD: 'Bản đồ ASEAN với 10 quốc gia, màu sắc phân biệt từng nước'"
                    },
                    "caption": {"type": "string", "description": "Chú thích hiển thị cho người dùng"}
                }
            }
        },
        "required": ["type", "content"],
        "description": """Type='image' = TEXT + HÌNH ẢNH (array chứa strings và [IMAGE_PLACEHOLDER] marker)

⭐ QUAN TRỌNG - LUỒNG AI GENERATE IMAGE:
- Khi cần AI generate hình: Dùng marker '[IMAGE_PLACEHOLDER]' trong array
- Workflow service sẽ tự động:
  1. Extract mô tả hình ảnh từ context
  2. Generate hình bằng AI
  3. Replace '[IMAGE_PLACEHOLDER]' bằng image object thực

⚠️ VÍ DỤ CHO HA_MH (Hình minh họa - AI generate):
{
  "type": "image",
  "content": [
    "Quan sát hình ảnh minh họa dưới đây:",
    "[IMAGE_PLACEHOLDER]",
    "Hiện tượng trong hình là gì?"
  ]
}

⚠️ VÍ DỤ CHO HA_TL (Hình tư liệu - AI generate từ data):
{
  "type": "image",
  "content": [
    "Cho biểu đồ dân số thành thị 2010-2021:",
    "[IMAGE_PLACEHOLDER]",
    "Năm nào có dân số cao nhất?"
  ],
  "metadata": {
    "source": "Niên giám thống kê 2021"
  }
}

⚠️ LƯU Ý:
- CHỈ dùng '[IMAGE_PLACEHOLDER]' - KHÔNG dùng URL
- Marker PHẢI là string riêng trong array, KHÔNG embed trong text
- Mô tả hình ảnh nên rõ ràng trong text xung quanh để AI generate đúng"""
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
                                                "chartType": {
                                                    "type": "string", 
                                                    "enum": ["bar", "line", "pie", "scatter", "combo"],
                                                    "description": "Loại biểu đồ"
                                                },
                                                "echarts": {
                                                    "type": "object",
                                                    "description": "⚠️ BẮT BUỘC: ECharts config - KHÔNG ĐƯỢC RỖNG! PHẢI có xAxis, yAxis, series với data",
                                                    "properties": {
                                                        "xAxis": {
                                                            "type": "object",
                                                            "description": "Trục X - PHẢI có data array"
                                                        },
                                                        "yAxis": {
                                                            "anyOf": [
                                                                {"type": "object"},
                                                                {"type": "array"}
                                                            ],
                                                            "description": "Trục Y"
                                                        },
                                                        "series": {
                                                            "type": "array",
                                                            "minItems": 1,
                                                            "description": "Data series - BẮT BUỘC có ít nhất 1 series",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "name": {"type": "string", "description": "BẮT BUỘC: Tên series. VD: 'Dân số', 'GDP'"},
                                                                    "type": {"type": "string", "enum": ["bar", "line", "pie"], "description": "BẮT BUỘC: Loại chart"},
                                                                    "data": {
                                                                        "type": "array",
                                                                        "description": "BẮT BUỘC: Array số liệu. VD: [26.5, 30.9, 36.6]",
                                                                        "minItems": 1
                                                                    }
                                                                },
                                                                "required": ["name", "type", "data"]
                                                            }
                                                        }
                                                    },
                                                    "required": ["xAxis", "yAxis", "series"]
                                                }
                                            },
                                            "required": ["chartType", "echarts"],
                                            "description": "Chart content - object {chartType, echarts}. VD: {\"chartType\": \"bar\", \"echarts\": {\"xAxis\": {\"data\": [\"2010\"]}, \"yAxis\": {}, \"series\": [{\"data\": [100]}]}}"
                                        },
                                        {
                                            "type": "string",
                                            "description": "⭐ Image content - Dùng '[IMAGE_PLACEHOLDER]' marker để AI generate image. Workflow service sẽ tự động replace sau."
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
                    "source": {"type": "string", "description": "Nguồn dữ liệu"},
                    "image_description": {
                        "type": "string",
                        "description": "⭐ BẮT BUỘC khi có [IMAGE_PLACEHOLDER]: Mô tả chi tiết hình ảnh cần AI generate. VD: 'Hình ảnh núi lửa phun trào với dung nham đỏ rực'"
                    }
                }
            }
        },
        "required": ["type", "content"],
        "description": "Mixed content - content PHẢI là array chứa strings và objects đầy đủ"
    }


def get_content_schema_by_rich_types(rich_content_types: Optional[Union[Dict, List[str]]] = None) -> Dict:
    """
    ⭐ HÀM CHÍNH: Chọn schema phù hợp dựa trên rich_content_types từ ma trận
    
    🎯 LOGIC PHÂN LOẠI MỚI (Phân biệt type chính và type phụ):
    
    1. None / [] / chỉ LT / chỉ TT / [LT, TT]:
       → type='text' (text thuần) - KHÔNG có BD/BK/HA
    
    2. Có type chính BD/BK/HA (hoặc HA_MH, HA_TL):
       → Chọn schema cụ thể:
         • Chỉ BD → get_chart_content_schema()
         • Chỉ BK → get_table_content_schema()
         • Chỉ HA/HA_MH/HA_TL → get_image_content_schema()
         • Nhiều hơn 1 type chính → get_mixed_content_schema()
       
    3. Type phụ (LT/TT) chỉ là metadata về tính chất câu hỏi:
       - LT (Lý thuyết): Câu hỏi kiểu lý thuyết
       - TT (Tính toán): Câu hỏi yêu cầu tính toán
       
    4. Type chính (BD/BK/HA) quyết định cấu trúc content:
       - BD (Biểu đồ): Câu hỏi có chart
       - BK (Bảng khảo): Câu hỏi có table
       - HA_* (Hình ảnh): Câu hỏi có image
    
    Args:
        rich_content_types: Dict hoặc List từ matrix
            - Dict format OLD: {"C1": [{"code": "LT"}, ...], "C2": [{"code": "BD"}, {"code": "TT"}]}
            - Dict format NEW (chart): {"C1": [{"type": "BD", "chart_type": "bar", "dimensions": "2x3"}]}
            - List format: ['BK'] hoặc ['BD', 'TT']
    
    Returns:
        Dict: Schema phù hợp với loại content
    """
    if not rich_content_types:
        return get_text_content_schema()
    
    # Extract all type codes from dict/list structure
    type_codes = []
    
    if isinstance(rich_content_types, dict):
        # Dict format - hỗ trợ cả old {'code': 'BD'} và new {'type': 'BD', 'chart_type': ...}
        for question_code, types_list in rich_content_types.items():
            if isinstance(types_list, list):
                for type_obj in types_list:
                    if isinstance(type_obj, dict):
                        # Try 'type' field first (new format), then 'code' field (old format)
                        type_value = type_obj.get('type') or type_obj.get('code')
                        if type_value:
                            type_codes.append(type_value)
                    elif isinstance(type_obj, str):
                        type_codes.append(type_obj)
    elif isinstance(rich_content_types, list):
        # List format: ['BK'] or ['LT', 'TT']
        type_codes = rich_content_types
    else:
        # Invalid format, default to text
        return get_text_content_schema()
    
    # Phân loại: Lọc type chính (BD/BK/HA) vs type phụ (LT/TT)
    PRIMARY_TYPES = ['BD', 'BK']  # Biểu đồ, Bảng khảo
    # HA có thể có suffix: HA_MH (minh họa), HA_TL (tư liệu)
    primary_types = [t for t in type_codes if t in PRIMARY_TYPES or t.startswith('HA')]
    
    # Nếu KHÔNG có type chính → chỉ có type phụ (LT/TT) hoặc rỗng → text thuần
    if not primary_types:
        return get_text_content_schema()
    
    # ⭐ QUAN TRỌNG: Chỉ cho phép 1 type chính
    # Normalize HA_MH, HA_TL về HA
    normalized_types = []
    for t in primary_types:
        if t.startswith('HA'):
            normalized_types.append('HA')
        else:
            normalized_types.append(t)
    
    # Remove duplicates
    unique_types = list(set(normalized_types))
    
    # Nếu chỉ có 1 type chính → dùng schema cụ thể
    if len(unique_types) == 1:
        primary_type = unique_types[0]
        
        if primary_type == 'BD':
            return get_chart_content_schema()
        elif primary_type == 'BK':
            return get_table_content_schema()
        elif primary_type == 'HA':
            return get_image_content_schema()
    
    # Nếu có nhiều hơn 1 type chính → dùng mixed (nhưng nên tránh)
    print(f"⚠️ WARNING: Multiple primary types detected: {unique_types}")
    print(f"   Quy tắc: Câu hỏi chỉ nên có 1 type chính (BD/BK/HA)")
    print(f"   Falling back to mixed schema")
    return get_mixed_content_schema(primary_types)


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

**4. HÌNH ẢNH (type: "image")** - KHI câu hỏi có rich_content_types="HA_MH" hoặc "HA_TL":

⭐ LUỒNG MỚI - AI GENERATE IMAGE:
{
  "type": "image",
  "content": "[IMAGE_PLACEHOLDER]",
  "metadata": {
    "caption": "Hình 1: Bản đồ khu vực Đông Nam Á",
    "image_description": "Bản đồ ASEAN với 10 quốc gia thành viên, có màu sắc phân biệt từng nước"
  }
}

⚠️ QUAN TRỌNG:
- Dùng '[IMAGE_PLACEHOLDER]' marker thay vì URL
- Thêm 'image_description' trong metadata để mô tả hình cần generate
- Workflow service sẽ tự động generate image và replace marker

**5. MIXED (type: "mixed")** - KHI câu hỏi có CẢ text + BK/BD/HA:

VD 1 - Câu hỏi TN có hình ảnh (HA_MH - AI generate):
{
  "type": "mixed",
  "content": [
    "Quan sát hình ảnh minh họa:",
    "[IMAGE_PLACEHOLDER]",
    "Hiện tượng trong hình là gì?"
  ],
  "metadata": {
    "image_description": "Hình ảnh minh họa hiện tượng núi lửa phun trào với dung nham đỏ rực"
  }
}

VD 2 - Câu hỏi TN có biểu đồ (BD):
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

VD 3 - Câu hỏi TLN có bảng:
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
- Câu hỏi TN CÓ hình ảnh AI-generated: PHẢI dùng type="mixed" với '[IMAGE_PLACEHOLDER]' marker
- VD đúng: 
  question_stem: {
    "type": "mixed",
    "content": [
      "Quan sát hình ảnh minh họa:",
      "[IMAGE_PLACEHOLDER]",
      "Hiện tượng trong hình là gì?"
    ],
    "metadata": {
      "image_description": "Hình ảnh núi lửa phun trào với dung nham đỏ rực"
    }
  }
- KHÔNG được chỉ có '[IMAGE_PLACEHOLDER]' mà thiếu text câu hỏi!
- PHẢI có 'image_description' trong metadata để AI generate đúng hình

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
                            "description": "💡 Nội dung câu hỏi - Công thức toán PHẢI dùng LaTeX (bọc trong $...$). VD: 'Giải phương trình $2x + 3 = 7$'",
                            **content_schema
                        },
                        
                        # === PHẦN ĐÁP ÁN ===
                        "options": {
                            "type": "object",
                            "properties": {
                                "A": {
                                    "type": "string",
                                    "description": "Đáp án A (công thức toán dùng LaTeX: $...$)"
                                },
                                "B": {
                                    "type": "string",
                                    "description": "Đáp án B (công thức toán dùng LaTeX: $...$)"
                                },
                                "C": {
                                    "type": "string",
                                    "description": "Đáp án C (công thức toán dùng LaTeX: $...$)"
                                },
                                "D": {
                                    "type": "string",
                                    "description": "Đáp án D (công thức toán dùng LaTeX: $...$)"
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
                            - ⚠️ Công thức toán PHẢI dùng LaTeX: $...$
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
                            "description": "Câu hỏi - có thể chứa bảng, biểu đồ tư liệu. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$",
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
                        "answer_structure": {
                            "type": "object",
                            "description": "Cấu trúc câu trả lời - VD: {intro: '...', body: '...', conclusion: '...'}",
                            "properties": {
                                "intro": {"type": "string", "maxLength": 100, "description": "Phần mở đầu (công thức toán dùng LaTeX: $...$)"},
                                "body": {"type": "string", "maxLength": 150, "description": "Phần thân bài (công thức toán dùng LaTeX: $...$)"},
                                "conclusion": {"type": "string", "maxLength": 100, "description": "Phần kết luận (công thức toán dùng LaTeX: $...$)"}
                            },
                            "required": ["intro", "body", "conclusion"]
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Lời giải ngắn gọn (TỐI ĐA 300 ký tự): Giải thích ngắn ngọn. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$. NGHIÊM CẤM giải dài dòng.",
                            "maxLength": 300
                        }
                    },
                    "required": ["question_stem", "question_type", "level", "answer_structure", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }


def get_essay_with_sub_items_array_schema(
    sub_items: Dict[str, List[str]],
    content_schema: Optional[Dict] = None,
) -> Dict:
    """
    Schema cho câu Tự luận CÓ ý nhỏ (a, b, c ...).

    Thay vì trả về ``answer_structure`` ở cấp câu, AI trả về ``sub_questions``
    — mảng các ý nhỏ, mỗi ý có nhãn, nội dung yêu cầu riêng và gợi ý giải.

    Args:
        sub_items: Dict phân nhóm sub-item, e.g. {'C1': ['a', 'b']}
                   (dùng để mô tả yêu cầu trong system prompt, không giới hạn
                   số lượng ở đây để tránh JSON-schema conflict).
        content_schema: Schema cho các trường rich-text (None → text schema).

    Returns:
        JSON schema có cấu trúc:
        {questions: [{question_stem, question_type, level,
                      sub_questions: [{label, question_stem,
                                       question_type, answer_structure, explanation}]}]}
    """
    if content_schema is None:
        content_schema = get_text_content_schema()

    sub_question_schema: Dict = {
        "type": "object",
        "properties": {
            "label": {
                "type": "string",
                "description": "Nhãn ý nhỏ: 'a', 'b', 'c' ...",
            },
            "question_stem": {
                "description": "Nội dung yêu cầu riêng của ý nhỏ này",
                **content_schema,
            },
            "question_type": {
                "type": "string",
                "enum": [
                    "analysis",
                    "comparison",
                    "evaluation",
                    "explanation",
                    "synthesis",
                    "argumentation",
                ],
            },
            "answer_structure": {
                "type": "object",
                "properties": {
                    "intro": {"type": "string", "maxLength": 100},
                    "body": {"type": "string", "maxLength": 150},
                    "conclusion": {"type": "string", "maxLength": 100},
                },
                "required": ["intro", "body", "conclusion"],
            },
            "explanation": {"type": "string", "maxLength": 300},
        },
        "required": [
            "label",
            "question_stem",
            "question_type",
            "answer_structure",
            "explanation",
        ],
    }

    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_stem": {
                            "description": (
                                "Đoạn dẫn / bối cảnh CHUNG cho toàn bộ câu. "
                                "Không lặp lại trong từng ý nhỏ."
                            ),
                            **content_schema,
                        },
                        "question_type": {
                            "type": "string",
                            "enum": [
                                "analysis",
                                "comparison",
                                "evaluation",
                                "explanation",
                                "synthesis",
                                "argumentation",
                            ],
                        },
                        "level": {
                            "type": "string",
                            "enum": ["NB", "TH", "VD", "VDC"],
                        },
                        "sub_questions": {
                            "type": "array",
                            "items": sub_question_schema,
                            "description": "Danh sách các ý nhỏ (a, b, c ...) của câu hỏi",
                        },
                    },
                    "required": [
                        "question_stem",
                        "question_type",
                        "level",
                        "sub_questions",
                    ],
                },
            }
        },
        "required": ["questions"],
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
                - PHẢI điền trường này với format chuẩn
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
                "description": """Loại tư liệu (giúp AI hiểu cách xử lý) - Generic types áp dụng cho mọi môn học:
                
                - 'primary_source': Tư liệu gốc, nguồn trực tiếp
                  • Lịch sử: văn kiện, tuyên bố chính thức, hồi ký
                  • Ngữ văn: văn bản gốc của tác giả, thơ, truyện
                  • Hóa học: công thức phản ứng, định luật
                  
                - 'procedural_description': Mô tả quy trình, các bước thực hiện
                  • Lịch sử: diễn biến sự kiện theo thời gian
                  • Hóa học: các bước thí nghiệm, quy trình điều chế
                  • Sinh học: quy trình sinh học, chu trình
                  
                - 'analytical_summary': Phân tích, tổng hợp từ các nhà nghiên cứu
                  • Lịch sử: đánh giá lịch sử, phân tích nguyên nhân-kết quả
                  • Ngữ văn: phê bình văn học, phân tích nghệ thuật
                  • Khoa học: kết luận nghiên cứu, phân tích hiện tượng
                  
                - 'contextual_scenario': Tình huống có bối cảnh cụ thể
                  • Tất cả môn: đặt vấn đề trong ngữ cảnh thực tế
                
                ⚠️ LƯU Ý: Nội dung chi tiết (format các bước thí nghiệm, cách trích dẫn, cấu trúc phân tích...) 
                được định hình bởi PROMPT cụ thể của từng môn học, KHÔNG cần field riêng trong schema."""
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
                                - Đa dạng cách diễn đạt
                                - ⚠️ Công thức toán PHẢI dùng LaTeX: $...$"""
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
                            "text": {"type": "string", "description": "Mệnh đề b (công thức toán dùng LaTeX: $...$)"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"},
                            "reasoning_type": {"type": "string"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "c": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Mệnh đề c (công thức toán dùng LaTeX: $...$)"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"},
                            "reasoning_type": {"type": "string"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "d": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Mệnh đề d (công thức toán dùng LaTeX: $...$)"},
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
                        - ⚠️ Công thức toán PHẢI dùng LaTeX: $...$
                        - ⚠️ NẾU SOURCE_TEXT CÓ BẢNG/BIỂU ĐỒ: CHỈ nêu kết luận, KHÔNG copy số liệu
                        - NGHIÊM CẤM: lặp lại source_text, giải dài dòng""",
                        "maxLength": 400
                    },
                    "b": {
                        "type": "string",
                        "description": "Giải thích mệnh đề b (TỐI ĐA 400 ký tự) - Tương tự mệnh đề a. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$",
                        "maxLength": 400
                    },
                    "c": {
                        "type": "string",
                        "description": "Giải thích mệnh đề c (TỐI ĐA 400 ký tự) - Tương tự mệnh đề a. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$",
                        "maxLength": 400
                    },
                    "d": {
                        "type": "string",
                        "description": "Giải thích mệnh đề d (TỐI ĐA 400 ký tự) - Tương tự mệnh đề a. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$",
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
                            "description": "Câu hỏi - có thể chứa bảng, biểu đồ. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$",
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
                            "description": "Lời giải ngắn gọn (TỐI ĐA 300 ký tự - GIẢM TỪ 500): CHỈ ghi công thức + kết quả. ⚠️ Công thức toán PHẢI dùng LaTeX: $...$. NGHIÊM CẤM giải dài dòng.",
                            "maxLength": 300
                        }
                    },
                    "required": ["question_stem", "question_type", "correct_answer", "level", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }


def get_chart_data_generation_schema() -> Dict:
    """
    Schema cho AI sinh DỮ LIỆU biểu đồ (chart data generation)
    Output sẽ được convert thành ECharts option bằng GenChart utilities
    
    Dựa trên format input của GenChart (README.md section "Chuẩn bị dữ liệu đầu vào")
    
    Returns:
        Dict: JSON schema cho chart data generation
    """
    return {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie", "area", "combo"],
                "description": "Loại biểu đồ: bar (cột), line (đường), pie (tròn), area (miền), combo (kết hợp cột+đường)"
            },
            "data": {
                "type": "object",
                "description": "Dữ liệu thô của biểu đồ - Backend sẽ convert thành ECharts option",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Trục hoành (X-axis) - Mảng các nhãn. VD: ['2010', '2015', '2021', '2024']. ⚠️ KHÔNG dùng cho Pie chart."
                    },
                    "series": {
                        "type": "array",
                        "minItems": 1,
                        "description": "Mảng các chuỗi dữ liệu - Mỗi series là một chỉ tiêu cần biểu diễn",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Tên chuỗi dữ liệu. VD: 'Nông nghiệp', 'Công nghiệp', 'Dịch vụ'"
                                },
                                "data": {
                                    "anyOf": [
                                        {
                                            "type": "array",
                                            "items": {"type": "number"},
                                            "description": "Dữ liệu dạng số (cho bar, line, area, combo). VD: [15.4, 14.5, 12.6, 11.9]"
                                        },
                                        {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "value": {"type": "number"}
                                                },
                                                "required": ["name", "value"]
                                            },
                                            "description": "Dữ liệu dạng {name, value} (chỉ cho pie). VD: [{'name': 'Nông nghiệp', 'value': 15.4}]"
                                        }
                                    ],
                                    "description": "Dữ liệu của series - Format khác nhau cho từng loại chart"
                                },
                                "unit": {
                                    "type": "string",
                                    "description": "Đơn vị của dữ liệu. VD: '%', 'Tỷ VNĐ', 'triệu người', '°C'"
                                },
                                "type": {
                                    "type": "string",
                                    "enum": ["bar", "line"],
                                    "description": "⚠️ BẮT BUỘC CHỈ cho chart_type='combo': Loại biểu đồ con (bar hoặc line) để kết hợp"
                                }
                            },
                            "required": ["name", "data", "unit"],
                            "description": "Một chuỗi dữ liệu - Chứa tên, dữ liệu và đơn vị"
                        }
                    }
                },
                "required": ["series"],
                "description": "⚠️ LƯU Ý: 'categories' BẮT BUỘC cho bar/line/area/combo, KHÔNG dùng cho pie"
            },
            "options": {
                "type": "object",
                "description": "Tùy chọn hiển thị biểu đồ",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Tiêu đề biểu đồ - Ngắn gọn. VD: 'Cơ cấu GDP giai đoạn 2010-2024'"
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "Tiêu đề phụ (mặc định để trống, chỉ cần title đủ truyền đạt nội dung chính)"
                    },
                    "show_legend": {
                        "type": "boolean",
                        "default": True,
                        "description": "Hiển thị chú giải (legend)"
                    },
                    "show_data_labels": {
                        "type": "boolean",
                        "default": True,
                        "description": "Hiển thị giá trị trên biểu đồ"
                    },
                    "x_axis_unit": {
                        "type": "string",
                        "description": "Tên đơn vị trục X. VD: 'Năm', 'Tháng', 'Quý' (mặc định: 'năm')"
                    },
                    "bar_style": {
                        "type": "string",
                        "enum": ["grouped", "stacked"],
                        "default": "grouped",
                        "description": "Kiểu cột (chỉ cho bar/combo): 'grouped' (cột ghép nhóm) hoặc 'stacked' (cột xếp chồng)"
                    },
                    "smooth": {
                        "type": "boolean",
                        "default": False,
                        "description": "Làm mịn đường (chỉ cho line)"
                    },
                    "show_percentage": {
                        "type": "boolean",
                        "default": True,
                        "description": "Hiển thị % trên lát cắt (chỉ cho pie)"
                    },
                    "source": {
                        "type": "string",
                        "description": "Nguồn dữ liệu. VD: 'Nguồn: Tổng cục Thống kê', 'Nguồn: Niên giám Thống kê 2023'"
                    },
                    "x_label_rotate": {
                        "type": "number",
                        "description": "Góc xoay nhãn trục X (độ). VD: 45"
                    },
                    "y_axis_left_unit": {
                        "type": "string",
                        "description": "Đơn vị trục Y bên trái (chỉ cho combo)"
                    },
                    "y_axis_right_unit": {
                        "type": "string",
                        "description": "Đơn vị trục Y bên phải (chỉ cho combo)"
                    },
                    "radius": {
                        "type": "string",
                        "description": "Bán kính biểu đồ tròn (chỉ cho pie). VD: '45%', '60%'"
                    },
                    "center": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Vị trí tâm biểu đồ tròn (chỉ cho pie). VD: ['50%', '50%']"
                    }
                },
                "description": "Các tùy chọn hiển thị - Một số tùy chọn chỉ áp dụng cho loại chart cụ thể"
            }
        },
        "required": ["chart_type", "data", "options"],
        "description": """Schema cho AI sinh DỮ LIỆU biểu đồ (KHÔNG phải ECharts option đầy đủ).
⚠️ LUỒNG: AI sinh data → Backend validate → Convert thành ECharts option bằng GenChart → Merge vào câu hỏi."""
    }

