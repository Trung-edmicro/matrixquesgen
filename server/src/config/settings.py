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
        "TOAN",
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

    # ═════ DS Material Filter Configuration ═════
    # Danh sách các môn học cần dùng AI để chọn tư liệu DS từ Drive
    # (thay vì random.choice hoặc dùng nguyên materials từ ma trận)
    SUBJECTS_WITH_MATERIAL_FILTER = [
        "LICHSU",  # Lịch sử: filter tư liệu DS bằng AI
        # Thêm các môn khác cần filter tư liệu DS vào đây
    ]

    @classmethod
    def should_filter_material(cls, subject: str) -> bool:
        """
        Kiểm tra xem môn học có cần dùng AI để filter tư liệu DS không

        Args:
            subject (str): Mã môn học (VD: "LICHSU", "GDKTPL")

        Returns:
            bool: True nếu cần filter, False nếu không
        """
        return subject.upper() in cls.SUBJECTS_WITH_MATERIAL_FILTER
    
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

# Khởi tạo các thư mục khi import module
Config.ensure_directories()
