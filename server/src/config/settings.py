"""
Configuration settings for the application
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Cấu hình chung cho ứng dụng"""
    
    # Base directories
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    INPUT_DIR = DATA_DIR / "input"
    OUTPUT_DIR = DATA_DIR / "output"
    
    # Excel settings
    EXCEL_ENGINE = "openpyxl"
    DEFAULT_INPUT_FILE = "07. SỬ 12. ma trận KSCL lần 1 (1).xlsx"
    
    # Google Cloud / Vertex AI settings
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
    GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
    GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH", "")
    
    # Vertex AI Model settings
    VERTEX_AI_MODEL = os.getenv("VERTEX_AI_MODEL", "gemini-3.1-pro-preview")
    VERTEX_AI_FALLBACK_MODEL = os.getenv("VERTEX_AI_FALLBACK_MODEL", "gemini-2.5-pro")
    VERTEX_AI_TEMPERATURE = float(os.getenv("VERTEX_AI_TEMPERATURE", "0.7"))
    VERTEX_AI_TOP_P = float(os.getenv("VERTEX_AI_TOP_P", "0.95"))
    VERTEX_AI_TOP_K = int(os.getenv("VERTEX_AI_TOP_K", "40"))
    VERTEX_AI_MAX_OUTPUT_TOKENS = int(os.getenv("VERTEX_AI_MAX_OUTPUT_TOKENS", "8192"))
    VERTEX_AI_THINKING_LEVEL = os.getenv("VERTEX_AI_THINKING_LEVEL", "high")
    
    # DOCX settings
    DOCX_FONT_NAME = "Times New Roman"
    DOCX_FONT_SIZE = 12
    
    # ═════ DANH SÁCH MÃ MÔN HỌC CHÍNH THỨC ═════
    # Mã môn học bắt buộc phải có trong tên file ma trận
    VALID_SUBJECTS = [
        "DIALY",
        "GDKTPL",
        "HOAHOC",
        "LICHSU",
        "SINH",
        "VATLY",
        "TIENGANH",
    ]
    
    # ═════ DANH SÁCH MÃ LỚP CHÍNH THỨC ═════
    # Mã lớp bắt buộc phải có trong tên file ma trận (C + 1-2 số)
    VALID_GRADES = [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
        "C6",
        "C7",
        "C8",
        "C9",
        "C10",
        "C11",
        "C12",
    ]
    
    # ═════ CURRICULUM MẶC ĐỊNH ═════
    DEFAULT_CURRICULUM = "KNTT"  # Bộ sách mặc định: Kết nối Tri thức
    
    # ═════ DS Source Display Configuration ═════
    # Danh sách các môn học HIỂN THỊ source trong câu hỏi DS
    SUBJECTS_WITH_SOURCE_DISPLAY = [
        "LICHSU",  # Lịch sử cần hiển thị nguồn tư liệu
        # Thêm các môn khác cần hiển thị source vào đây
    ]
    
    @classmethod
    def should_display_source(cls, subject: str) -> bool:
        """
        Kiểm tra xem môn học có cần hiển thị source trong câu hỏi DS không
        
        Args:
            subject (str): Mã môn học (VD: "LICHSU", "GDKTPL")
            
        Returns:
            bool: True nếu cần hiển thị source, False nếu không
        """
        return subject.upper() in cls.SUBJECTS_WITH_SOURCE_DISPLAY
    
    @classmethod
    def get_input_file_path(cls, filename: Optional[str] = None) -> Path:
        """
        Lấy đường dẫn file input
        
        Args:
            filename (str, optional): Tên file. Nếu None, dùng DEFAULT_INPUT_FILE
            
        Returns:
            Path: Đường dẫn đầy đủ
        """
        if filename is None:
            filename = cls.DEFAULT_INPUT_FILE
        return cls.INPUT_DIR / filename
    
    @classmethod
    def get_output_file_path(cls, filename: str) -> Path:
        """
        Lấy đường dẫn file output
        
        Args:
            filename (str): Tên file output
            
        Returns:
            Path: Đường dẫn đầy đủ
        """
        return cls.OUTPUT_DIR / filename
    
    @classmethod
    def ensure_directories(cls):
        """Tạo các thư mục cần thiết nếu chưa tồn tại"""
        cls.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Đã kiểm tra thư mục:")
        print(f"  - Input: {cls.INPUT_DIR}")
        print(f"  - Output: {cls.OUTPUT_DIR}")
    
    @classmethod
    def validate_gcp_config(cls) -> bool:
        """
        Kiểm tra cấu hình GCP
        
        Returns:
            bool: True nếu cấu hình hợp lệ
        """
        if not cls.GCP_PROJECT_ID:
            print("⚠ Chưa cấu hình GCP_PROJECT_ID")
            return False
        
        if cls.GCP_CREDENTIALS_PATH and not os.path.exists(cls.GCP_CREDENTIALS_PATH):
            print(f"⚠ File credentials không tồn tại: {cls.GCP_CREDENTIALS_PATH}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """In thông tin cấu hình"""
        print("\n" + "=" * 80)
        print("CẤU HÌNH HỆ THỐNG")
        print("=" * 80)
        print(f"Base Directory: {cls.BASE_DIR}")
        print(f"Input Directory: {cls.INPUT_DIR}")
        print(f"Output Directory: {cls.OUTPUT_DIR}")
        print(f"\nDefault Input File: {cls.DEFAULT_INPUT_FILE}")
        print(f"\nGCP Project ID: {cls.GCP_PROJECT_ID or '(chưa cấu hình)'}")
        print(f"GCP Location: {cls.GCP_LOCATION}")
        print(f"Vertex AI Model: {cls.VERTEX_AI_MODEL}")
        print(f"Temperature: {cls.VERTEX_AI_TEMPERATURE}")
        print("=" * 80 + "\n")


class PromptTemplates:
    """Template cho các prompts sử dụng với AI"""
    
    GENERATE_QUESTIONS = """
    Bạn là một giáo viên có kinh nghiệm. Hãy tạo các câu hỏi trắc nghiệm dựa trên thông tin sau:
    
    Môn học: {subject}
    Chủ đề: {topic}
    Mức độ: {level}
    Số lượng câu hỏi: {num_questions}
    
    Yêu cầu:
    - Mỗi câu hỏi có 4 đáp án A, B, C, D
    - Chỉ có 1 đáp án đúng
    - Câu hỏi phải rõ ràng, chính xác
    - Đáp án phải phù hợp với mức độ
    
    Trả về kết quả dạng JSON với cấu trúc:
    {{
        "questions": [
            {{
                "question": "Nội dung câu hỏi",
                "options": {{
                    "A": "Đáp án A",
                    "B": "Đáp án B",
                    "C": "Đáp án C",
                    "D": "Đáp án D"
                }},
                "correct_answer": "A",
                "explanation": "Giải thích"
            }}
        ]
    }}
    """
    
    PROCESS_EXCEL_DATA = """
    Hãy phân tích dữ liệu Excel sau và tạo câu hỏi trắc nghiệm:
    
    Dữ liệu:
    {excel_data}
    
    Yêu cầu:
    - Tạo {num_questions} câu hỏi
    - Mỗi câu hỏi dựa trên dữ liệu trong bảng
    - Format JSON như mẫu trên
    """


# Khởi tạo các thư mục khi import module
Config.ensure_directories()
