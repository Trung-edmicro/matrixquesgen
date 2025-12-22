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
