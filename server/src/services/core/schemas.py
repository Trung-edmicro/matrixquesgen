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
                "description": """YÊU CẦU ĐA DẠNG - TRÁNH LẶP:
                
                **BẮT BUỘC khi sinh nhiều câu hỏi**:
                - Mỗi câu hỏi phải hỏi về GÓC ĐỘ KHÁC NHAU của cùng kiến thức
                - KHÔNG được lặp lại nội dung câu hỏi (dù diễn đạt khác)
                - KHÔNG được lặp lại đáp án giữa các câu
                - KHÔNG được dùng cùng pattern/cấu trúc cho tất cả câu
                
                **Ví dụ ĐÚNG** (sinh 2 câu về ASEAN):
                Câu 1: "Ngày 8-8-1967, tại Bangkok, sự kiện lịch sử nào đã diễn ra?" (hỏi về sự kiện)
                Câu 2: "Mục tiêu chính của ASEAN khi thành lập là gì?" (hỏi về mục đích)
                
                **Ví dụ SAI** (lặp nội dung):
                Câu 1: "ASEAN được thành lập năm nào?"
                Câu 2: "Hiệp hội ASEAN ra đời vào thời gian nào?" (cùng hỏi về thời gian)
                
                **Chiến lược đa dạng hóa**:
                - Câu 1: Thời gian/Địa điểm (When/Where)
                - Câu 2: Nguyên nhân/Bối cảnh (Why)
                - Câu 3: Kết quả/Tác động (What happened)
                - Câu 4: Ý nghĩa/Đánh giá (Significance)""",
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
    
    Returns:
        Dict: JSON schema cho array questions TL với hướng dẫn đa dạng hóa
    """
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": """YÊU CẦU ĐA DẠNG - TRÁNH LẶP CHO CÂU HỎI TỰ LUẬN:
                
                **BẮT BUỘC khi sinh nhiều câu hỏi**:
                - Mỗi câu hỏi phải có GÓC ĐỘ TIẾP CẬN KHÁC NHAU
                - KHÔNG được lặp lại cùng một dạng câu hỏi (phân tích, so sánh, đánh giá...)
                - Đa dạng về question_type (analysis/comparison/evaluation/explanation/synthesis/argumentation)
                - Cân bằng độ khó và phạm vi kiến thức
                
                **Ví dụ ĐÚNG** (sinh 3 câu về ASEAN):
                Câu 1: "Phân tích các yếu tố thúc đẩy sự ra đời của ASEAN năm 1967" (analysis)
                Câu 2: "So sánh vai trò của ASEAN trước và sau Chiến tranh lạnh" (comparison)
                Câu 3: "Đánh giá ý nghĩa của việc thành lập ASEAN đối với Đông Nam Á" (evaluation)
                
                **Ví dụ SAI** (lặp dạng câu hỏi):
                Câu 1: "Phân tích nguyên nhân thành lập ASEAN" (analysis)
                Câu 2: "Phân tích ý nghĩa của ASEAN" (analysis - trùng dạng)
                
                **Chiến lược đa dạng hóa**:
                - Ưu tiên các question_type khác nhau
                - Hỏi về nhiều khía cạnh: nguyên nhân, quá trình, kết quả, ý nghĩa, bài học
                - Kết hợp các góc nhìn: lịch sử, chính trị, kinh tế, xã hội, văn hóa""",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_stem": {
                            "type": "string",
                            "description": "Nội dung câu hỏi tự luận - Yêu cầu trả lời dài, có lập luận"
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
                            "description": "Câu trả lời mẫu đầy đủ"
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
    
    Returns:
        Dict: JSON schema cho câu hỏi Đúng/Sai với 4 mệnh đề - Phong phú và tự nhiên hơn
    """
    return {
        "type": "object",
        "properties": {
            # === PHẦN TƯ LIỆU ===
            "source_text": {
                "type": "string",
                "description": """Đoạn tư liệu lịch sử - ƯU TIÊN LẤY TỪ NGUỒN HỌC THUẬT NGOÀI SGK:
                
                **KHUYẾN KHÍCH MẠNH**:
                - Tư liệu từ tạp chí khoa học (Lịch sử, Lí luận Chính trị, Nghiên cứu Quốc tế...)
                - Trích từ sách chuyên khảo của các nhà sử học uy tín
                - Bài phân tích chuyên sâu từ báo chí uy tín
                - Văn kiện/tuyên bố chính thức (UN, ASEAN, Chính phủ...)
                
                **YÊU CẦU**:
                - Phải phù hợp với nội dung kiến thức SGK (không sai lệch)
                - Đủ thông tin để đặt 4 mệnh đề đa chiều
                - Tự nhiên, có phân tích chuyên sâu hơn SGK
                - Có góc nhìn mới, cập nhật
                
                **GHI NGUỒN Ở CUỐI (BẮT BUỘC nếu dùng nguồn ngoài)**:
                - Nếu source_origin != 'textbook' → PHẢI thêm citation trong dấu () ở CUỐI đoạn tư liệu
                - Định dạng: (Tác giả, \"Tên bài\", Tạp chí số X (tháng/năm), tr. Y)
                - Ví dụ: \"...ASEAN đã quy tụ đủ 10 quốc gia.\\n(Nguyễn Viết Thảo, \"Bối cảnh hình thành...\", Tạp chí Lí luận Chính trị số 541 (3/2023), tr. 151)\"
                
                **CHỈ DÙNG TƯ LIỆU TỪ SGK KHI**:
                - Không tìm được nguồn ngoài phù hợp
                - Hoặc khi kết hợp với nguồn ngoài để làm phong phú"""
            },
            
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
    
    Returns:
        Dict: JSON schema cho array questions TLN với hướng dẫn đa dạng hóa
    """
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": """YÊU CẦU ĐA DẠNG - TRÁNH LẶP CHO CÂU HỎI TLN:
                
                **BẮT BUỘC khi sinh nhiều câu hỏi**:
                - Mỗi câu hỏi phải hỏi về YẾU TỐ KHÁC NHAU (thời gian/địa điểm/nhân vật/ý nghĩa...)
                - KHÔNG được lặp lại cùng một kiểu câu hỏi
                - Đa dạng về question_type (time/location/name/concept/meaning/cause/result)
                - Cân bằng độ khó (NB/TH/VD)
                
                **Ví dụ ĐÚNG** (sinh 3 câu về thành lập ASEAN):
                Câu 1: "ASEAN được thành lập vào ngày nào?" (question_type: time, level: NB)
                Câu 2: "Thành phố nào là nơi diễn ra lễ ký tuyên bố Bangkok?" (question_type: location, level: NB)
                Câu 3: "Mục đích chính của ASEAN khi thành lập là gì?" (question_type: meaning, level: TH)
                
                **Ví dụ SAI** (lặp kiểu câu hỏi):
                Câu 1: "ASEAN được thành lập năm nào?" (time)
                Câu 2: "Tuyên bố Bangkok được ký vào năm nào?" (time - trùng kiểu)
                
                **Chiến lược đa dạng hóa**:
                - Ưu tiên các question_type khác nhau
                - Trộn các cấp độ NB, TH, VD
                - Hỏi về nhiều khía cạnh: thời gian, không gian, nhân vật, ý nghĩa, nguyên nhân, kết quả""",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_stem": {
                            "type": "string",
                            "description": "Nội dung câu hỏi - Yêu cầu trả lời ngắn gọn, cụ thể"
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
                            "description": "Đáp án đúng - Ngắn gọn chỉ 2-3 từ, cụ thể"
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
                            "description": "(Tùy chọn) Giải thích đáp án"
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

