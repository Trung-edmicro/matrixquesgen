"""
Module quản lý JSON schemas cho các loại câu hỏi
Hỗ trợ Rich Content: text, image, table, chart (ECharts), latex, mixed
"""
from typing import Dict


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

1. type="text" → content PHẢI LÀ STRING:
   {"type": "text", "content": "ASEAN được thành lập năm 1967"}

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
                "description": "Metadata tùy chọn",
                "properties": {
                    "caption": {"type": "string", "description": "Chú thích (VD: 'Bảng 1: Dân số')"},
                    "source": {"type": "string", "description": "Nguồn dữ liệu"},
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
  "content": "ASEAN được thành lập năm 1967 tại Bangkok"
}

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


def get_multiple_choice_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Trắc nghiệm
    
    Returns:
        Dict: JSON schema cho một câu hỏi trắc nghiệm với metadata sư phạm phong phú
    """
    return {
        "type": "object",
        "properties": {
            # === PHẦN CỐT LÕI CÂU HỎI ===
            "question_stem": {
                "type": "string",
                "description": """Nội dung câu hỏi - Hãy đặt câu hỏi tự nhiên như giáo viên thực sự:
                - Có thể dùng ngữ cảnh/tình huống thực tế để dẫn dắt
                - Đa dạng cách hỏi: Tại sao, Như thế nào, Ý nghĩa gì, Hậu quả ra sao...
                - Tránh công thức hóa: thay vì "Điều nào sau đây đúng?" hãy hỏi cụ thể hơn
                - Có thể đặt trong context lịch sử cụ thể"""
            },
            
            # Metadata hỗ trợ tư duy sáng tạo
            "question_style": {
                "type": "string",
                "description": """Phong cách câu hỏi (để AI tự nhận biết cách mình đã ra đề):
                - 'factual': Hỏi kiến thức trực tiếp
                - 'analytical': Phân tích mối quan hệ nhân quả
                - 'contextual': Đặt trong tình huống lịch sử cụ thể
                - 'comparative': So sánh các sự kiện/nhân vật
                - 'evaluative': Đánh giá ý nghĩa/tác động
                - 'application': Áp dụng kiến thức vào tình huống mới"""
            },
            
            "historical_context": {
                "type": "string",
                "description": """(Tùy chọn) Bối cảnh lịch sử cụ thể nếu câu hỏi đặt trong tình huống:
                - Trích dẫn sử liệu, tư liệu
                - Mô tả tình huống lịch sử
                - Giúp câu hỏi sinh động, gần với thực tế hơn"""
            },
            
            "pedagogical_purpose": {
                "type": "string",
                "description": """Mục đích sư phạm của câu hỏi:
                - Kiểm tra hiểu biết khái niệm cơ bản
                - Đánh giá khả năng phân tích nhân quả
                - Kiểm tra kỹ năng so sánh đối chiếu
                - Đo lường khả năng đánh giá ý nghĩa lịch sử
                - Giúp AI hiểu "tại sao ra câu hỏi này" """
            },
            
            # === PHẦN ĐÁP ÁN ===
            "options": {
                "type": "object",
                "properties": {
                    "A": {
                        "type": "string",
                        "description": "Đáp án A - Viết tự nhiên, có thể dài ngắn khác nhau"
                    },
                    "B": {
                        "type": "string",
                        "description": "Đáp án B - Không cần cân đối độ dài giả tạo với A"
                    },
                    "C": {
                        "type": "string",
                        "description": "Đáp án C - Tự nhiên nhất có thể"
                    },
                    "D": {
                        "type": "string",
                        "description": "Đáp án D - Có thể dùng phủ định, khẳng định linh hoạt"
                    }
                },
                "required": ["A", "B", "C", "D"]
            },
            
            "distractor_rationale": {
                "type": "object",
                "description": "Lý do tại sao các đáp án sai vẫn hợp lý (giúp AI tạo distractor chất lượng)",
                "properties": {
                    "A": {"type": "string", "description": "Tại sao học sinh có thể chọn A nếu A sai"},
                    "B": {"type": "string", "description": "Tại sao học sinh có thể chọn B nếu B sai"},
                    "C": {"type": "string", "description": "Tại sao học sinh có thể chọn C nếu C sai"},
                    "D": {"type": "string", "description": "Tại sao học sinh có thể chọn D nếu D sai"}
                }
            },
            
            "correct_answer": {
                "type": "string",
                "description": "Đáp án đúng (A/B/C/D)"
            },
            
            # === PHẦN PHÂN LOẠI ===
            "level": {
                "type": "string",
                "description": "Cấp độ tư duy (NB/TH/VD/VDC)"
            },
            
            "bloom_taxonomy": {
                "type": "string",
                "description": """Phân loại Bloom chi tiết hơn:
                - Remember: Nhớ, nhận biết
                - Understand: Hiểu, giải thích
                - Apply: Vận dụng vào tình huống
                - Analyze: Phân tích mối quan hệ
                - Evaluate: Đánh giá, phê phán
                - Create: Tổng hợp, sáng tạo"""
            },
            
            # === PHẦN GIẢI THÍCH ===
            "explanation": {
                "type": "string",
                "description": """Giải thích đáp án - Viết như giáo viên giải đáp:
                - Tại sao đáp án này đúng (dẫn chứng cụ thể)
                - Tại sao các đáp án khác sai (phân tích ngắn gọn)
                - Có thể thêm kiến thức mở rộng nếu cần"""
            },
            
            # === METADATA BỔ SUNG ===
            "alternative_questions": {
                "type": "array",
                "description": """(Tùy chọn) Các cách hỏi khác về cùng kiến thức:
                - Giúp thấy được nhiều góc độ tiếp cận
                - Tăng ngân hàng câu hỏi""",
                "items": {"type": "string"}
            },
            
            "difficulty_note": {
                "type": "string",
                "description": """(Tùy chọn) Ghi chú về độ khó:
                - Câu hỏi này dễ bị nhầm lẫn chỗ nào
                - Học sinh thường mắc sai lầm gì
                - Kiến thức tiền đề cần có"""
            }
        },
        "required": ["question_stem", "options", "correct_answer", "level", "explanation", "question_style"]
    }


def get_multiple_choice_array_schema() -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Trắc nghiệm
    HỖ TRỢ RICH CONTENT: Ảnh, Bảng, Biểu đồ ECharts, Công thức LaTeX
    
    Returns:
        Dict: JSON schema cho array questions với metadata sư phạm phong phú và rich content
    """
    
    # Get rich content schema một lần duy nhất
    rich_content_def = get_rich_content_schema()
    
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
                            **rich_content_def
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
                            "description": "Giải thích đáp án - text thuần, có thể có công thức inline nếu cần"
                        }
                    },
                    "required": ["question_stem", "options", "correct_answer", "level", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }


def get_essay_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Tự luận (TL)
    
    Returns:
        Dict: JSON schema cho một câu hỏi tự luận với metadata sư phạm đầy đủ
    """
    return {
        "type": "object",
        "properties": {
            "question_stem": {
                "type": "string",
                "description": """Nội dung câu hỏi tự luận - Đặt câu hỏi yêu cầu trả lời dài, có lập luận:
                - Câu hỏi mở, yêu cầu trả lời theo cấu trúc logic (mở bài - thân bài - kết luận)
                - Có thể hỏi: phân tích, so sánh, đánh giá, giải thích, nhận xét...
                - Yêu cầu học sinh vận dụng kiến thức tổng hợp, có lập luận và dẫn chứng
                - Tránh câu hỏi quá mở hoặc quá hẹp"""
            },
            
            "question_type": {
                "type": "string",
                "enum": ["analysis", "comparison", "evaluation", "explanation", "synthesis", "argumentation"],
                "description": """Loại câu hỏi tự luận:
                - 'analysis': Phân tích một hiện tượng, sự kiện, quá trình
                - 'comparison': So sánh, đối chiếu các sự kiện, giai đoạn, nhân vật
                - 'evaluation': Đánh giá ý nghĩa, tác động, vai trò
                - 'explanation': Giải thích nguyên nhân, hậu quả, mối quan hệ
                - 'synthesis': Tổng hợp, khái quát kiến thức
                - 'argumentation': Lập luận, chứng minh một quan điểm"""
            },
            
            "historical_context": {
                "type": "string",
                "description": """(Tùy chọn) Bối cảnh lịch sử hoặc tư liệu dẫn dắt:
                - Mô tả tình huống lịch sử cụ thể
                - Trích dẫn tư liệu, sử liệu
                - Đặt vấn đề để học sinh phân tích"""
            },
            
            "required_elements": {
                "type": "array",
                "description": """Các yếu tố bắt buộc phải có trong câu trả lời:
                - Liệt kê các ý chính học sinh cần trình bày
                - Các luận điểm, dẫn chứng cần thiết
                - Cấu trúc bài làm mong đợi
                - Ví dụ: ["Nguyên nhân khách quan", "Nguyên nhân chủ quan", "Ý nghĩa lịch sử", "Bài học kinh nghiệm"]""",
                "items": {"type": "string"}
            },
            
            "answer_structure": {
                "type": "object",
                "description": """Cấu trúc câu trả lời mong đợi (giúp học sinh định hướng):
                - Hướng dẫn cách triển khai bài làm
                - Các phần cần có: mở bài, thân bài, kết luận""",
                "properties": {
                    "introduction": {
                        "type": "string",
                        "description": "Hướng dẫn viết phần mở bài (giới thiệu, đặt vấn đề)"
                    },
                    "body": {
                        "type": "array",
                        "description": "Các ý chính cần triển khai trong thân bài",
                        "items": {"type": "string"}
                    },
                    "conclusion": {
                        "type": "string",
                        "description": "Hướng dẫn viết phần kết luận (khẳng định, rút ra bài học)"
                    }
                }
            },
            
            "sample_answer": {
                "type": "string",
                "description": """Câu trả lời mẫu đầy đủ (để tham khảo, chấm điểm):
                - Trình bày đầy đủ các luận điểm
                - Có dẫn chứng, lập luận logic
                - Thể hiện cấu trúc rõ ràng
                - Độ dài phù hợp với yêu cầu đề bài"""
            },
            
            "key_points": {
                "type": "array",
                "description": """Các điểm kiến thức then chốt (key points) cần có trong bài làm:
                - Liệt kê các luận điểm chính
                - Các sự kiện, nhân vật, thời gian quan trọng
                - Dẫn chứng cần thiết
                - Dùng để làm thang điểm""",
                "items": {
                    "type": "object",
                    "properties": {
                        "point": {"type": "string", "description": "Nội dung điểm kiến thức"},
                        "weight": {"type": "number", "description": "Trọng số điểm (tổng = 10)"},
                        "description": {"type": "string", "description": "Mô tả chi tiết yêu cầu"}
                    }
                }
            },
            
            "scoring_rubric": {
                "type": "object",
                "description": """Thang điểm chi tiết (rubric) để chấm bài:
                - Giúp chấm điểm khách quan, nhất quán
                - Phân loại theo mức độ đạt được""",
                "properties": {
                    "excellent": {
                        "type": "string",
                        "description": "Tiêu chí đạt điểm xuất sắc (9-10 điểm)"
                    },
                    "good": {
                        "type": "string",
                        "description": "Tiêu chí đạt điểm khá (7-8 điểm)"
                    },
                    "average": {
                        "type": "string",
                        "description": "Tiêu chí đạt điểm trung bình (5-6 điểm)"
                    },
                    "weak": {
                        "type": "string",
                        "description": "Tiêu chí đạt điểm yếu (dưới 5 điểm)"
                    }
                }
            },
            
            "level": {
                "type": "string",
                "enum": ["VD", "VDC"],
                "description": """Cấp độ tư duy (Câu hỏi tự luận thường ở mức VD hoặc VDC):
                - VD: Vận dụng kiến thức để phân tích, giải thích
                - VDC: Vận dụng cao - tổng hợp, đánh giá, sáng tạo"""
            },
            
            "bloom_taxonomy": {
                "type": "string",
                "enum": ["Apply", "Analyze", "Evaluate", "Create"],
                "description": """Phân loại Bloom cho câu hỏi tự luận:
                - Apply: Áp dụng kiến thức vào tình huống mới
                - Analyze: Phân tích, so sánh, tìm mối quan hệ
                - Evaluate: Đánh giá, phê phán có căn cứ
                - Create: Tổng hợp, sáng tạo quan điểm mới"""
            },
            
            "time_limit": {
                "type": "number",
                "description": """Thời gian làm bài đề xuất (phút):
                - Giúp học sinh phân bổ thời gian hợp lý
                - Phù hợp với độ dài yêu cầu"""
            },
            
            "word_count_range": {
                "type": "object",
                "description": """Độ dài bài làm mong đợi:
                - Giúp học sinh định hướng mức độ chi tiết""",
                "properties": {
                    "min": {"type": "number", "description": "Số từ tối thiểu"},
                    "max": {"type": "number", "description": "Số từ tối đa"}
                }
            },
            
            "pedagogical_purpose": {
                "type": "string",
                "description": """Mục đích sư phạm của câu hỏi:
                - Rèn kỹ năng tư duy phản biện
                - Phát triển khả năng lập luận logic
                - Đánh giá hiểu biết tổng hợp
                - Khuyến khích sáng tạo trong trình bày"""
            },
            
            "common_mistakes": {
                "type": "array",
                "description": """Sai lầm thường gặp khi làm bài:
                - Thiếu cấu trúc logic
                - Không có dẫn chứng
                - Trình bày lan man
                - Thiếu các yếu tố bắt buộc""",
                "items": {"type": "string"}
            },
            
            "tips_for_students": {
                "type": "array",
                "description": """Gợi ý cho học sinh khi làm bài:
                - Cách phân tích đề bài
                - Cách lập dàn ý
                - Cách triển khai lập luận
                - Cách quản lý thời gian""",
                "items": {"type": "string"}
            },
            
            "difficulty_note": {
                "type": "string",
                "description": """Ghi chú về độ khó của câu hỏi:
                - Kiến thức tiền đề cần có
                - Kỹ năng cần để trả lời tốt
                - Điểm cần chú ý khi chấm"""
            },
            
            "related_topics": {
                "type": "array",
                "description": """Các chủ đề liên quan có thể khai thác:
                - Giúp mở rộng kiến thức
                - Gợi ý cho việc ôn tập""",
                "items": {"type": "string"}
            }
        },
        "required": ["question_stem", "question_type", "required_elements", "sample_answer", "key_points", "level"]
    }


def get_essay_array_schema() -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Tự luận (TL)
    HỖ TRỢ RICH CONTENT: Câu hỏi có thể chứa tư liệu ảnh, bảng, biểu đồ
    
    Returns:
        Dict: JSON schema cho array questions TL với hướng dẫn đa dạng hóa và rich content
    """
    
    # Get rich content schema cho question_stem
    rich_content_def = get_rich_content_schema()
    
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
                            **rich_content_def
                        },
                        "question_type": {
                            "type": "string",
                            "enum": ["analysis", "comparison", "evaluation", "explanation", "synthesis", "argumentation"],
                            "description": "Loại câu hỏi tự luận"
                        },
                        "historical_context": {
                            "type": "string",
                            "description": "(Tùy chọn) Bối cảnh lịch sử hoặc tư liệu dẫn dắt"
                        },
                        "required_elements": {
                            "type": "array",
                            "description": "Các yếu tố bắt buộc phải có trong câu trả lời",
                            "items": {"type": "string"}
                        },
                        "answer_structure": {
                            "type": "object",
                            "description": "Cấu trúc câu trả lời mong đợi",
                            "properties": {
                                "introduction": {"type": "string"},
                                "body": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "conclusion": {"type": "string"}
                            }
                        },
                        "sample_answer": {
                            "type": "string",
                            "description": "Bài làm mẫu - text thuần, có thể có cấu trúc markdown"
                        },
                        "key_points": {
                            "type": "array",
                            "description": "Các điểm kiến thức then chốt cần có trong bài làm",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "point": {"type": "string"},
                                    "weight": {"type": "number"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "scoring_rubric": {
                            "type": "object",
                            "description": "Thang điểm chi tiết để chấm bài",
                            "properties": {
                                "excellent": {"type": "string"},
                                "good": {"type": "string"},
                                "average": {"type": "string"},
                                "weak": {"type": "string"}
                            }
                        },
                        "level": {
                            "type": "string",
                            "enum": ["VD", "VDC"],
                            "description": "Cấp độ tư duy"
                        },
                        "bloom_taxonomy": {
                            "type": "string",
                            "enum": ["Apply", "Analyze", "Evaluate", "Create"],
                            "description": "Phân loại Bloom"
                        },
                        "time_limit": {
                            "type": "number",
                            "description": "Thời gian làm bài đề xuất (phút)"
                        },
                        "word_count_range": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number"},
                                "max": {"type": "number"}
                            }
                        },
                        "pedagogical_purpose": {
                            "type": "string",
                            "description": "Mục đích sư phạm"
                        },
                        "common_mistakes": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "tips_for_students": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "difficulty_note": {
                            "type": "string"
                        },
                        "related_topics": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["question_stem", "question_type", "required_elements", "sample_answer", "key_points", "level"]
                }
            }
        },
        "required": ["questions"]
    }


def get_true_false_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Đúng/Sai
    HỖ TRỢ RICH CONTENT: Tư liệu có thể chứa bảng, biểu đồ, ảnh
    
    Returns:
        Dict: JSON schema cho câu hỏi Đúng/Sai với 4 mệnh đề và rich content support
    """
    
    return {
        "type": "object",
        "properties": {
            # === PHẦN TƯ LIỆU (Rich Content Support) ===
            "source_text": get_rich_content_schema(),
            
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
                - Rèn kỹ năng làm việc với nguồn học thuật"""
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
                - Dễ debug nếu có vấn đề"""
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
                - Cách cân bằng độ khó"""
            },
            
            # === PHẦN GIẢI THÍCH ===
            "explanation": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "string",
                        "description": """Giải thích mệnh đề a - Như giáo viên chấm bài:
                        - Tại sao đúng/sai
                        - Dẫn chứng từ tư liệu hoặc kiến thức"""
                    },
                    "b": {"type": "string"},
                    "c": {"type": "string"},
                    "d": {"type": "string"}
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
                    "a": {"type": "string"},
                    "b": {"type": "string"},
                    "c": {"type": "string"},
                    "d": {"type": "string"}
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
                - Xác nhận tư liệu có giá trị sư phạm cao"""
            }
        },
        "required": ["source_text", "statements", "explanation"]
    }


def get_short_answer_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Trắc nghiệm luận (TLN)
    
    Returns:
        Dict: JSON schema cho một câu hỏi trắc nghiệm luận với metadata sư phạm
    """
    return {
        "type": "object",
        "properties": {
            # === PHẦN CỐT LÕI CÂU HỎI ===
            "question_stem": {
                "type": "string",
                "description": """Nội dung câu hỏi - Đặt câu hỏi yêu cầu trả lời ngắn gọn:
                - Câu hỏi phải rõ ràng, tập trung vào một yếu tố cụ thể
                - Yêu cầu trả lời ngắn (1-2 từ, 1 cụm từ, 1 con số, hoặc 1 câu ngắn)
                - Có thể hỏi: thời gian, địa điểm, tên riêng, khái niệm, ý nghĩa, nguyên nhân...
                - Tránh câu hỏi mơ hồ có nhiều đáp án hợp lý"""
            },
            
            "question_type": {
                "type": "string",
                "enum": ["time", "location", "name", "concept", "meaning", "cause", "result", "number"],
                "description": """Loại câu hỏi TLN (giúp AI tạo câu hỏi đa dạng):
                - 'time': Hỏi về thời gian (năm, ngày tháng, thời kỳ...)
                - 'location': Hỏi về địa điểm (quốc gia, thành phố, địa danh...)
                - 'name': Hỏi về tên riêng (nhân vật, sự kiện, tổ chức...)
                - 'concept': Hỏi về khái niệm, thuật ngữ lịch sử
                - 'meaning': Hỏi về ý nghĩa, tác động của sự kiện
                - 'cause': Hỏi về nguyên nhân của sự kiện
                - 'result': Hỏi về kết quả, hậu quả
                - 'number': Hỏi về số liệu (số lượng, con số cụ thể)"""
            },
            
            "historical_context": {
                "type": "string",
                "description": """(Tùy chọn) Bối cảnh lịch sử để dẫn dắt câu hỏi:
                - Mô tả ngắn gọn tình huống lịch sử
                - Giúp câu hỏi có ngữ cảnh rõ ràng hơn"""
            },
            
            # === PHẦN ĐÁP ÁN ===
            "correct_answer": {
                "type": "string",
                "description": """Đáp án đúng - Phải ngắn gọn, cụ thể, không mơ hồ:
                - Với câu hỏi thời gian: "8-8-1967" hoặc "Ngày 8-8-1967"
                - Với câu hỏi địa điểm: "Bangkok" hoặc "Bangkok, Thái Lan"
                - Với câu hỏi tên riêng: "ASEAN" hoặc "Hiệp hội các quốc gia Đông Nam Á"
                - Với câu hỏi khái niệm: định nghĩa ngắn gọn
                - Với câu hỏi ý nghĩa/nguyên nhân: 1-2 câu ngắn"""
            },
            
            "alternative_answers": {
                "type": "array",
                "description": """(Tùy chọn) Các đáp án chấp nhận được khác:
                - Các cách diễn đạt khác nhau của cùng một đáp án
                - Ví dụ: ["ASEAN", "Hiệp hội ASEAN", "Hiệp hội các quốc gia Đông Nam Á"]
                - Giúp chấm điểm linh hoạt hơn""",
                "items": {"type": "string"}
            },
            
            "answer_format": {
                "type": "string",
                "description": """Định dạng đáp án mong đợi (hướng dẫn cho học sinh):
                - "Trả lời bằng một ngày tháng cụ thể"
                - "Trả lời bằng tên một thành phố"
                - "Trả lời bằng tên một tổ chức quốc tế"
                - "Trả lời bằng một khái niệm lịch sử"
                - "Trả lời trong 1-2 câu ngắn gọn" """
            },
            
            # === PHẦN PHÂN LOẠI ===
            "level": {
                "type": "string",
                "enum": ["NB", "TH", "VD", "VDC"],
                "description": """Cấp độ tư duy:
                - NB: Nhớ kiến thức trực tiếp (thời gian, địa điểm, tên riêng...)
                - TH: Hiểu và giải thích (khái niệm, ý nghĩa cơ bản...)
                - VD: Vận dụng phân tích (nguyên nhân, hậu quả, mối quan hệ...)
                - VDC: Vận dụng cao, tổng hợp nhiều yếu tố"""
            },
            
            "bloom_taxonomy": {
                "type": "string",
                "enum": ["Remember", "Understand", "Apply", "Analyze"],
                "description": """Phân loại Bloom cho câu hỏi TLN:
                - Remember: Nhớ lại thông tin cụ thể
                - Understand: Giải thích khái niệm, ý nghĩa
                - Apply: Áp dụng kiến thức vào tình huống
                - Analyze: Phân tích mối quan hệ, nguyên nhân"""
            },
            
            # === PHẦN GIẢI THÍCH ===
            "explanation": {
                "type": "string",
                "description": """(Tùy chọn) Giải thích đáp án:
                - Giải thích tại sao đây là đáp án đúng
                - Cung cấp thêm bối cảnh lịch sử
                - Giúp học sinh hiểu sâu hơn"""
            },
            
            # === METADATA BỔ SUNG ===
            "pedagogical_purpose": {
                "type": "string",
                "description": """Mục đích sư phạm của câu hỏi:
                - Kiểm tra khả năng nhớ chính xác thông tin
                - Đánh giá hiểu biết về khái niệm
                - Rèn kỹ năng trả lời ngắn gọn, súc tích
                - Kiểm tra khả năng tổng hợp thông tin"""
            },
            
            "common_mistakes": {
                "type": "array",
                "description": """(Tùy chọn) Sai lầm thường gặp:
                - Những đáp án sai phổ biến
                - Tại sao học sinh dễ nhầm lẫn
                - Giúp thiết kế bài giảng tốt hơn""",
                "items": {"type": "string"}
            },
            
            "difficulty_note": {
                "type": "string",
                "description": """(Tùy chọn) Ghi chú về độ khó:
                - Câu hỏi này dễ hay khó với học sinh
                - Kiến thức tiền đề cần có
                - Kỹ năng cần để trả lời"""
            }
        },
        "required": ["question_stem", "question_type", "correct_answer", "level"]
    }


def get_short_answer_array_schema() -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Trắc nghiệm luận (TLN)
    HỖ TRỢ RICH CONTENT: Câu hỏi có thể chứa ảnh, bảng, biểu đồ
    
    Returns:
        Dict: JSON schema cho array questions TLN với hướng dẫn đa dạng hóa và rich content
    """
    
    # Get rich content schema một lần
    rich_content_def = get_rich_content_schema()
    
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
                            **rich_content_def
                        },
                        "question_type": {
                            "type": "string",
                            "enum": ["time", "location", "name", "concept", "meaning", "cause", "result", "number"],
                            "description": "Loại câu hỏi (time/location/name/concept/meaning/cause/result/number)"
                        },
                        "historical_context": {
                            "type": "string",
                            "description": "(Tùy chọn) Bối cảnh lịch sử dẫn dắt"
                        },
                        "correct_answer": {
                            "type": "string",
                            "description": "Đáp án đúng - CHỈ GHI SỐ (không có đơn vị, không có chữ). VD: '38', '177', '2.5' - không viết '38%' hay '177 lần'"
                        },
                        "alternative_answers": {
                            "type": "array",
                            "description": "(Tùy chọn) Các cách diễn đạt khác được chấp nhận",
                            "items": {"type": "string"}
                        },
                        "answer_format": {
                            "type": "string",
                            "description": "Định dạng đáp án mong đợi"
                        },
                        "level": {
                            "type": "string",
                            "enum": ["NB", "TH", "VD", "VDC"],
                            "description": "Cấp độ tư duy"
                        },
                        "bloom_taxonomy": {
                            "type": "string",
                            "enum": ["Remember", "Understand", "Apply", "Analyze"],
                            "description": "Phân loại Bloom"
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Giải thích đáp án - Chỉ ghi công thức và cách tính (tối đa 500 ký tự)",
                            "maxLength": 500
                        },
                        "pedagogical_purpose": {
                            "type": "string",
                            "description": "Mục đích sư phạm"
                        },
                        "common_mistakes": {
                            "type": "array",
                            "description": "(Tùy chọn) Sai lầm thường gặp",
                            "items": {"type": "string"}
                        },
                        "difficulty_note": {
                            "type": "string",
                            "description": "(Tùy chọn) Ghi chú về độ khó"
                        }
                    },
                    "required": ["question_stem", "question_type", "correct_answer", "level"]
                }
            }
        },
        "required": ["questions"]
    }

