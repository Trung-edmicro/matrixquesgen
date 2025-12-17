"""
Module quản lý JSON schemas cho các loại câu hỏi
"""
from typing import Dict


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
    
    Returns:
        Dict: JSON schema cho array questions với metadata sư phạm phong phú
    """
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
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
                            "description": """Phong cách câu hỏi:
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
                            "description": """Mục đích sư phạm của câu hỏi - Giúp AI hiểu "tại sao ra câu hỏi này" """
                        },
                        
                        # === PHẦN ĐÁP ÁN ===
                        "options": {
                            "type": "object",
                            "properties": {
                                "A": {"type": "string"},
                                "B": {"type": "string"},
                                "C": {"type": "string"},
                                "D": {"type": "string"}
                            },
                            "required": ["A", "B", "C", "D"]
                        },
                        
                        "distractor_rationale": {
                            "type": "object",
                            "description": "Lý do tại sao các đáp án sai vẫn hợp lý",
                            "properties": {
                                "A": {"type": "string"},
                                "B": {"type": "string"},
                                "C": {"type": "string"},
                                "D": {"type": "string"}
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
                            "description": """Phân loại Bloom: Remember/Understand/Apply/Analyze/Evaluate/Create"""
                        },
                        
                        # === PHẦN GIẢI THÍCH ===
                        "explanation": {
                            "type": "string",
                            "description": """Giải thích đáp án - Viết như giáo viên giải đáp"""
                        },
                        
                        # === METADATA BỔ SUNG ===
                        "alternative_questions": {
                            "type": "array",
                            "description": "(Tùy chọn) Các cách hỏi khác về cùng kiến thức",
                            "items": {"type": "string"}
                        },
                        
                        "difficulty_note": {
                            "type": "string",
                            "description": "(Tùy chọn) Ghi chú về độ khó, điểm dễ nhầm lẫn"
                        }
                    },
                    "required": ["question_stem", "options", "correct_answer", "level", "explanation", "question_style"]
                }
            }
        },
        "required": ["questions"]
    }


def get_true_false_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Đúng/Sai
    
    Returns:
        Dict: JSON schema cho câu hỏi Đúng/Sai với 4 mệnh đề - Phong phú và tự nhiên hơn
    """
    return {
        "type": "object",
        "properties": {
            # === PHẦN TƯ LIỆU ===
            "source_text": {
                "type": "string",
                "description": """Đoạn tư liệu lịch sử - Hãy chọn/tạo tư liệu có giá trị:
                - Có thể là trích dẫn từ sử liệu gốc
                - Có thể là mô tả tình huống lịch sử cụ thể
                - Có thể là tổng hợp từ nhiều nguồn
                - Đủ thông tin để đặt 4 mệnh đề đa chiều
                - Tự nhiên, không gò bó công thức"""
            },
            
            "source_type": {
                "type": "string",
                "description": """Loại tư liệu (giúp AI hiểu cách xử lý):
                - 'primary_source': Tư liệu gốc (văn kiện, thư, hồi ký...)
                - 'historical_description': Mô tả sự kiện lịch sử
                - 'analytical_summary': Phân tích tổng hợp
                - 'contextual_scenario': Tình huống có bối cảnh"""
            },
            
            "pedagogical_approach": {
                "type": "string", 
                "description": """Cách tiếp cận sư phạm cho bộ câu hỏi Đ/S:
                - Kiểm tra đọc hiểu tư liệu
                - Phân tích đa góc độ một sự kiện
                - Đánh giá khả năng phán đoán
                - Phân biệt sự thật và suy luận"""
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
            
            "overall_difficulty": {
                "type": "string",
                "description": """(Tùy chọn) Đánh giá độ khó tổng thể:
                - Dễ/Trung bình/Khó
                - Yếu tố gây khó (tư liệu phức tạp, cần kiến thức sâu, phân tích đa chiều...)"""
            }
        },
        "required": ["source_text", "statements", "explanation", "source_type"]
    }
