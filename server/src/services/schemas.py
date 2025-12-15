"""
Module quản lý JSON schemas cho các loại câu hỏi
"""
from typing import Dict


def get_multiple_choice_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Trắc nghiệm
    
    Returns:
        Dict: JSON schema cho một câu hỏi trắc nghiệm
    """
    return {
        "type": "object",
        "properties": {
            "question_stem": {
                "type": "string",
                "description": "Nội dung câu hỏi"
            },
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
            "correct_answer": {
                "type": "string",
                "description": "Đáp án đúng (A/B/C/D)"
            },
            "level": {
                "type": "string",
                "description": "Cấp độ tư duy (NB/TH/VD/VDC)"
            },
            "explanation": {
                "type": "string",
                "description": "Giải thích đáp án"
            }
        },
        "required": ["question_stem", "options", "correct_answer", "level", "explanation"]
    }


def get_multiple_choice_array_schema() -> Dict:
    """
    Trả về JSON schema cho nhiều câu hỏi Trắc nghiệm
    
    Returns:
        Dict: JSON schema cho array questions
    """
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_stem": {
                            "type": "string",
                            "description": "Nội dung câu hỏi"
                        },
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
                        "correct_answer": {
                            "type": "string",
                            "description": "Đáp án đúng (A/B/C/D)"
                        },
                        "level": {
                            "type": "string",
                            "description": "Cấp độ tư duy (NB/TH/VD/VDC)"
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Giải thích đáp án"
                        }
                    },
                    "required": ["question_stem", "options", "correct_answer", "level", "explanation"]
                }
            }
        },
        "required": ["questions"]
    }


def get_true_false_schema() -> Dict:
    """
    Trả về JSON schema cho câu hỏi Đúng/Sai
    
    Returns:
        Dict: JSON schema cho câu hỏi Đúng/Sai với 4 mệnh đề
    """
    return {
        "type": "object",
        "properties": {
            "source_text": {
                "type": "string",
                "description": "Đoạn tư liệu lịch sử"
            },
            "statements": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "b": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "c": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    },
                    "d": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "level": {"type": "string", "enum": ["NB", "TH", "VD", "VDC"]},
                            "correct_answer": {"type": "boolean"}
                        },
                        "required": ["text", "level", "correct_answer"]
                    }
                },
                "required": ["a", "b", "c", "d"]
            },
            "explanation": {
                "type": "object",
                "properties": {
                    "a": {"type": "string"},
                    "b": {"type": "string"},
                    "c": {"type": "string"},
                    "d": {"type": "string"}
                },
                "required": ["a", "b", "c", "d"]
            }
        },
        "required": ["source_text", "statements", "explanation"]
    }
