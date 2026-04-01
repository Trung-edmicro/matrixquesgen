"""
Module phân tích và xử lý ma trận câu hỏi từ file Excel
"""
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
from .matrix_template_detector import MatrixTemplateDetector, MatrixTemplate


@dataclass
class QuestionSpec:
    """Đặc tả một câu hỏi hoặc nhóm câu hỏi"""
    lesson_name: str  # Tên chương - bài
    competency_level: int  # Thành phần năng lực (1, 2, 3)
    cognitive_level: str  # Cấp độ tư duy (NB, TH, VD, VDC)
    question_type: str  # Loại câu hỏi (TN nhiều lựa chọn, Đúng/Sai, Trả lời ngắn)
    num_questions: int  # Số lượng câu hỏi
    question_codes: List[str]  # Danh sách mã câu (C1, C2, ...)
    learning_outcome: str  # Đặc tả ma trận (đã lọc theo cấp độ)
    row_index: int  # Vị trí hàng trong Excel
    chapter_number: Optional[int] = None  # Số chương (1, 2, 3...)
    supplementary_material: str = ""  # Tài liệu bổ sung (nội dung ngoài SGK)
    rich_content_types: Optional[Dict[str, List[str]]] = None  # Rich content types per question code: {"C1": ["BD"], "C2": ["BK", "TT"]}
    sub_items: Optional[Dict[str, List[str]]] = None  # TL sub-question labels e.g. {'C1': ['a', 'b']}


@dataclass
class StatementSpec:
    """Đặc tả một mệnh đề trong câu Đúng/Sai"""
    statement_code: str  # Mã mệnh đề (C1A, C1B, C1C, C1D)
    label: str  # Nhãn mệnh đề (a, b, c, d)
    cognitive_level: str  # Cấp độ (NB, TH, VD, VDC)
    learning_outcome: str  # Đặc tả cho mệnh đề này
    competency_level: Optional[int] = None  # Thành phần năng lực
    materials: str = ""  # Tài liệu bổ sung (DS element level)


@dataclass
class TrueFalseQuestionSpec:
    """Đặc tả một câu hỏi Đúng/Sai hoàn chỉnh (4 mệnh đề)"""
    question_code: str  # Mã câu (C1, C2, ...)
    lesson_name: str  # Tên chương - bài
    statements: List[StatementSpec]  # Danh sách 4 mệnh đề (a, b, c, d)
    question_type: str = "DS"  # Loại câu hỏi
    chapter_number: Optional[int] = None  # Số chương (1, 2, 3...)
    supplementary_material: str = ""  # Tài liệu bổ sung cấp bài học (lesson-level)
    materials: str = ""  # Tài liệu bổ sung cấp phần tử DS (DS element level)
    rich_content_types: Optional[Dict[str, List[str]]] = None  # Rich content types per question code


class MatrixParser:
    """Class phân tích ma trận câu hỏi"""
    
    # Mapping cột trong Excel (0-indexed, structure mới)
    COL_STT = 0
    COL_COMPETENCY = 1  # Thường empty/merged
    COL_CHAPTER = 2  # Tên Chủ đề - Chương
    COL_LESSON = 3  # Tên Bài
    COL_SPEC = 4  # Đặc tả ma trận
    
    # Cột cho câu hỏi trắc nghiệm nhiều lựa chọn
    COL_TN_NB = 5   # Nhận biết
    COL_TN_TH = 6   # Thông hiểu
    COL_TN_VD = 7   # Vận dụng
    
    # Cột cho câu hỏi Đúng/Sai
    COL_DS_NB = 8   # Nhận biết
    COL_DS_TH = 9   # Thông hiểu
    COL_DS_VD = 10  # Vận dụng
    
    # Cột cho câu hỏi trả lời ngắn (TN dạng điền khuyết)
    COL_TLN_NB = 11  # Nhận biết
    COL_TLN_TH = 12  # Thông hiểu
    COL_TLN_VD = 13  # Vận dụng

    # Cột cho câu hỏi tự luận
    COL_TL_NB = 14  # Nhận biết
    COL_TL_TH = 15  # Thông hiểu
    COL_TL_VD = 16  # Vận dụng
    
    # Cột tài liệu bổ sung
    COL_SUPPLEMENTARY = 17  # Tài liệu bổ sung
    
    # Mapping cấp độ
    COGNITIVE_LEVEL_MAP = {
        COL_TN_NB: "NB", COL_TN_TH: "TH", COL_TN_VD: "VD",
        COL_DS_NB: "NB", COL_DS_TH: "TH", COL_DS_VD: "VD",
        COL_TLN_NB: "NB", COL_TLN_TH: "TH", COL_TLN_VD: "VD",
        COL_TL_NB: "NB", COL_TL_TH: "TH", COL_TL_VD: "VD"
    }
    
    # Mapping loại câu hỏi
    QUESTION_TYPE_MAP = {
        COL_TN_NB: "TN", COL_TN_TH: "TN", COL_TN_VD: "TN",
        COL_DS_NB: "DS", COL_DS_TH: "DS", COL_DS_VD: "DS",
        COL_TLN_NB: "TLN", COL_TLN_TH: "TLN", COL_TLN_VD: "TLN",
        COL_TL_NB: "TL", COL_TL_TH: "TL", COL_TL_VD: "TL"
    }
    
    def __init__(self, split_learning_outcome_by_level: Optional[bool] = None):
        """
        Initialize MatrixParser
        
        Args:
            split_learning_outcome_by_level: 
                - None (mặc định): Tự động phát hiện dựa trên nội dung cột "Đặc tả ma trận"
                  Nếu có các header "Nhận biết:", "Thông hiểu:", "Vận dụng:" → tách theo level
                  Nếu không có → lấy toàn bộ
                - True: Force tách theo level
                - False: Force lấy toàn bộ
        """
        self.df = None
        self.current_competency = None
        self.current_chapter = None
        self.current_lesson = None
        self.current_spec = None
        self.template: Optional[MatrixTemplate] = None
        self.template_metadata: dict = {}
        self.file_path: Optional[str] = None
        self.split_learning_outcome_by_level = split_learning_outcome_by_level
        
        # Thông tin từ tên file
        self.subject = None  # Môn học (LICHSU, TOAN, etc.)
        self.curriculum = None  # Bộ sách (KNTT, etc.)
        self.grade = None  # Lớp (C12, C11, etc.)
    
    def load_excel(self, file_path: str, sheet_name: str = None):
        """
        Đọc file Excel
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet cần đọc (None = tự động phát hiện)
        """
        self.file_path = file_path
        
        # Parse thông tin từ tên file
        filename = Path(file_path).name
        self.subject, self.curriculum, self.grade = self.parse_matrix_filename(filename)
                
        # Phát hiện template
        detector = MatrixTemplateDetector()
        self.template, self.template_metadata = detector.detect(file_path)
        # detector.print_detection_result(self.template, self.template_metadata)
        
        # Xác định sheet name
        if sheet_name is None:
            sheet_name = self.template_metadata.get('matrix_sheet', 'Sử 12')
        
        # Đọc sheet ma trận
        self.df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        print(f"\n✓ Đã tải ma trận từ sheet '{sheet_name}': {self.df.shape[0]} hàng x {self.df.shape[1]} cột")
    
    # ─────────────────────────── Code normalization helpers ─────────────────────

    @staticmethod
    def _normalize_question_code(raw: str) -> str:
        """
        Normalize a question code:
        - Ensure 'C' prefix (uppercase)
        - Keep numeric part as-is
        - Preserve the case of any trailing letter suffix
          (e.g. 'c1a' → 'C1a', 'C1A' → 'C1A', '1' → 'C1')
        This allows distinguishing TL sub-items (lowercase) from
        DS statement labels (uppercase, added later by group_true_false_questions).
        """
        raw = raw.strip()
        m = re.match(r'^[Cc]?(\d+)([a-zA-Z]*)$', raw)
        if m:
            return 'C' + m.group(1) + m.group(2)
        # Fallback: keep as-is but upper the C
        return re.sub(r'^[Cc]', 'C', raw) if re.match(r'^[Cc]', raw) else 'C' + raw

    @staticmethod
    def _extract_tl_sub_items(
        codes: List[str],
    ) -> Tuple[List[str], Optional[Dict[str, List[str]]]]:
        """
        For TL questions: detect codes with lowercase letter suffix as sub-items
        and group them by numeric base.

        Examples:
          ['C1a', 'C1b'] → (['C1'], {'C1': ['a', 'b']})
          ['C1']         → (['C1'], None)           # no sub-item
          ['C1a']        → (['C1'], {'C1': ['a']})  # single sub-item
          ['C1', 'C2']   → (['C1', 'C2'], None)     # multiple plain codes
        """
        base_to_subs: Dict[str, List[str]] = {}
        has_sub = False
        for code in codes:
            m = re.match(r'^C(\d+)([a-z]+)$', code)  # lowercase suffix → sub-item
            if m:
                base = 'C' + m.group(1)
                sub = m.group(2)
                base_to_subs.setdefault(base, []).append(sub)
                has_sub = True
            else:
                if code not in base_to_subs:
                    base_to_subs[code] = []
        base_codes = list(base_to_subs.keys())
        sub_items = {k: v for k, v in base_to_subs.items() if v} if has_sub else None
        return base_codes, sub_items

    # ─────────────────────────────────────────────────────────────────────────────

    def parse_question_cell(self, cell_value) -> Tuple[int, List[str], Dict[str, List[str]]]:
        """
        Parse giá trị trong ô để lấy số câu hỏi, mã câu và rich content types
        
        Args:
            cell_value: Giá trị ô 
                VD: "2 (C1,2)" hoặc "1 (C10)"
                VD với rich content (format cũ): "1 (C3-[BK])" hoặc "2 (C4-[BD],C5-[BK])" hoặc "1 (C1-[BK,TT])"
                VD với chart dimensions (format mới): "1 (C1-Bar2x3)" hoặc "2 (C1-Line3x4,C2-Pie1x5)"
            
        Returns:
            Tuple[int, List[str], Dict[str, List[str]]]: (số câu hỏi, danh sách mã câu, rich_content_types)
                rich_content_types (format cũ): {"C1": ["BD"], "C2": ["BK", "TT"]}
                rich_content_types (format mới): {"C1": [{"type": "BD", "chart_type": "bar", "dimensions": "2x3"}]}
        """
        if pd.isna(cell_value):
            return 0, [], {}
        
        cell_str = str(cell_value).strip()
        
        # Pattern mới: số (mã1-[type1,type2], mã2-[type3], ...)
        # VD: "2 (C4-[BD],C5-[BK])" hoặc "1 (C1-[BK,TT])"
        pattern_with_types = r'(\d+)\s*\((.*?)\)'
        match = re.search(pattern_with_types, cell_str)
        
        if match:
            num = int(match.group(1))
            codes_str = match.group(2)
            
            codes = []
            rich_types = {}
            
            # Split by comma nhưng phải cẩn thận với [] bên trong
            # Parse từng phần: "C4-[BD]", "C5-[BK]", "C1-[BK,TT]"
            parts = []
            current_part = ""
            bracket_level = 0
            
            for char in codes_str:
                if char == '[':
                    bracket_level += 1
                elif char == ']':
                    bracket_level -= 1
                elif char == ',' and bracket_level == 0:
                    parts.append(current_part.strip())
                    current_part = ""
                    continue
                current_part += char
            
            if current_part.strip():
                parts.append(current_part.strip())
            
            for part in parts:
                # Check NEW FORMAT FIRST: "C1-Bar2x3", "C2-Line3x4", "C3-Pie1x5"
                match_chart_dimensions = re.match(r'([Cc]?\d+[A-Za-z]*)-([A-Za-z]+)(\d+)x(\d+)', part)
                
                if match_chart_dimensions:
                    # Format mới: C1-Bar2x3 → {"type": "BD", "chart_type": "bar", "dimensions": "2x3"}
                    code_part = match_chart_dimensions.group(1)
                    chart_type_raw = match_chart_dimensions.group(2).lower()  # bar, line, pie, area, combo
                    rows = match_chart_dimensions.group(3)
                    cols = match_chart_dimensions.group(4)
                    
                    # Normalize code
                    code = self._normalize_question_code(code_part)
                    codes.append(code)
                    
                    # Validate chart_type
                    valid_chart_types = ['bar', 'line', 'pie', 'area', 'combo']
                    if chart_type_raw not in valid_chart_types:
                        print(f"⚠️  Warning: Invalid chart_type '{chart_type_raw}' for {code}, defaulting to 'bar'")
                        chart_type_raw = 'bar'
                    
                    # Store as dict format
                    rich_types[code] = [{
                        "type": "BD",  # Biểu đồ
                        "chart_type": chart_type_raw,
                        "dimensions": f"{rows}x{cols}"
                    }]
                    continue
                
                # Check OLD FORMAT: "C4-[BD]" hoặc "C1-[BK,TT]"
                match_with_type = re.match(r'([Cc]?\d+[A-Za-z]*)-\[([^\]]+)\]', part)
                
                if match_with_type:
                    # Format cũ với bracket
                    code_part = match_with_type.group(1)
                    types_str = match_with_type.group(2)

                    # Normalize code — preserves lowercase suffix for TL sub-items
                    code = self._normalize_question_code(code_part)
                    codes.append(code)

                    # Parse types: "BD" hoặc "BK,TT"
                    types = [t.strip().upper() for t in types_str.split(',')]
                    rich_types[code] = types
                else:
                    # Không có rich content type
                    code = self._normalize_question_code(part)
                    codes.append(code)
            
            return num, codes, rich_types
        
        return 0, [], {}
    
    def parse_rich_content_types_sheet(self) -> Dict[str, Dict[str, str]]:
        """
        Parse sheet "Loại" để lấy định nghĩa các loại câu hỏi với rich content
        
        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping mã loại -> {name, description}
            Example: {
                "LT": {"name": "Lý thuyết", "description": "Câu hỏi lý thuyết cơ bản"},
                "TT": {"name": "Tính toán", "description": "Câu hỏi có công thức tính toán"},
                "BD": {"name": "Biểu đồ", "description": "Câu hỏi có biểu đồ"},
                "BK": {"name": "Bảng khảo", "description": "Câu hỏi có bảng số liệu"},
                "HA": {"name": "Hình ảnh", "description": "Câu hỏi có hình ảnh"}
            }
        """
        if not self.file_path:
            return {}
        
        try:
            # Đọc sheet "Loại"
            df_types = pd.read_excel(self.file_path, sheet_name="Loại", header=None)
            
            rich_types = {}
            
            # Parse từng hàng (bỏ qua header nếu có)
            for idx in range(len(df_types)):
                row = df_types.iloc[idx]
                
                # Bỏ qua hàng trống hoặc header
                if pd.isna(row[0]) or str(row[0]).strip().upper() in ['MÃ', 'STT', '']:
                    continue
                
                # Column 0: Mã (LT, TT, BD, BK, HA)
                # Column 1: Tên loại
                # Column 2: Mô tả (nếu có)
                code = str(row[0]).strip().upper()
                name = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else ""
                description = str(row[2]).strip() if len(row) > 2 and pd.notna(row[2]) else ""
                
                if code and name:
                    rich_types[code] = {
                        "name": name,
                        "description": description
                    }
            
            print(f"✓ Đã parse {len(rich_types)} loại câu hỏi từ sheet 'Loại': {list(rich_types.keys())}")
            return rich_types
            
        except Exception as e:
            print(f"⚠️  Không thể đọc sheet 'Loại': {e}")
            return {}
    
    def parse_chapter_number(self, chapter_text: str) -> Optional[int]:
        """
        Parse số chương từ chuỗi tên chương (hỗ trợ cả số La Mã)
        
        Args:
            chapter_text: Chuỗi tên chương (VD: "Chương I. ...", "Chủ đề 1. ...")
            
        Returns:
            Optional[int]: Số chương hoặc None nếu không parse được
        """
        if pd.isna(chapter_text):
            return None
        
        chapter_str = str(chapter_text).strip()
        
        # Thử parse số Arabic trước: "Chủ đề 1" hoặc "Chương 2"
        pattern_arabic = r'(?:Chủ đề|Chương)\s*(\d+)'
        match = re.search(pattern_arabic, chapter_str, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        # Nếu không có số Arabic, thử parse số La Mã: "Chương I", "Chương II"
        pattern_roman = r'(?:Chủ đề|Chương)\s*([IVXLCDM]+)'
        match = re.search(pattern_roman, chapter_str, re.IGNORECASE)
        if match:
            roman = match.group(1).upper()
            # Convert Roman to Arabic
            roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
            result = 0
            prev_value = 0
            for char in reversed(roman):
                value = roman_map.get(char, 0)
                if value < prev_value:
                    result -= value
                else:
                    result += value
                prev_value = value
            return result if result > 0 else None
        
        return None
    
    def parse_matrix_filename(self, filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse tên file ma trận để trích xuất môn, bộ và lớp
        
        Args:
            filename: Tên file (VD: "Ma trận_LICHSU_KNTT_C12.xlsx" hoặc "Ma trận_TOAN_C12.xlsx")
            
        Returns:
            Tuple[subject, curriculum, grade]: (môn, bộ, lớp)
        """
        # Pattern: Ma trận_[môn]_[bộ]_[lớp].xlsx hoặc Ma trận_[môn]_[lớp].xlsx
        # VD: Ma trận_LICHSU_KNTT_C12.xlsx hoặc Ma trận_TOAN_C12.xlsx
        pattern = r'Ma trận_([A-Z]+)(?:_([A-Z]+))?_([A-Z]\d+)\.xlsx?'
        match = re.search(pattern, filename, re.IGNORECASE)
        
        if match:
            subject = match.group(1).upper()  # LICHSU, TOAN
            curriculum = match.group(2).upper() if match.group(2) else None  # KNTT (có thể None)
            grade = match.group(3).upper()  # C12
            return subject, curriculum, grade
        
        return None, None, None
    
    def parse_lesson_number(self, lesson_text: str) -> Optional[int]:
        """
        Parse số bài từ tên bài
        
        Args:
            lesson_text: Tên bài (VD: "Bài 10. Khái quát về công cuộc Đổi mới từ năm 1986 đến nay")
            
        Returns:
            Optional[int]: Số bài hoặc None
        """
        if pd.isna(lesson_text):
            return None
        
        lesson_str = str(lesson_text).strip()
        
        # Pattern để tìm số sau "Bài"
        # VD: "Bài 10." -> 10
        pattern = r'Bài\s*(\d+)'
        match = re.search(pattern, lesson_str, re.IGNORECASE)
        
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        return None
    
    def generate_drive_path(self, chapter_number: Optional[int] = None, lesson_number: Optional[int] = None) -> List[str]:
        """
        Tạo path cho Google Drive từ thông tin đã parse
        
        Args:
            chapter_number: Số chương (nếu không truyền sẽ tự detect)
            lesson_number: Số bài (nếu không truyền sẽ tự detect)
            
        Returns:
            List[str]: Path segments ['grade', 'subject', 'folder_name']
        """
        if not self.grade or not self.subject:
            raise ValueError("Cannot generate path: missing grade or subject info from filename")
        
        # Nếu không truyền chapter/lesson number, tự detect từ data
        if chapter_number is None or lesson_number is None:
            # Tìm chapter và lesson number từ data
            detected_chapter = None
            detected_lesson = None
            
            if self.df is not None:
                # Duyệt qua tất cả rows (không bỏ qua header như trong parse_matrix)
                for row_idx in range(len(self.df)):
                    row = self.df.iloc[row_idx]
                    
                    # Parse chapter - sử dụng tên cột hoặc index
                    try:
                        # Thử dùng tên cột trước
                        if 'Chủ đề - Chương' in self.df.columns:
                            chapter_col = 'Chủ đề - Chương'
                        else:
                            chapter_col = self.COL_CHAPTER
                        
                        if pd.notna(row[chapter_col]):
                            chapter_text = str(row[chapter_col]).strip()
                            detected_chapter = self.parse_chapter_number(chapter_text)
                    except (KeyError, IndexError):
                        pass
                    
                    # Parse lesson - sử dụng tên cột hoặc index
                    try:
                        if 'Bài' in self.df.columns:
                            lesson_col = 'Bài'
                        else:
                            lesson_col = self.COL_LESSON
                            
                        if pd.notna(row[lesson_col]):
                            lesson_text = str(row[lesson_col]).strip()
                            detected_lesson = self.parse_lesson_number(lesson_text)
                    except (KeyError, IndexError):
                        pass
                    
                    # Nếu đã tìm thấy cả hai, dừng
                    if detected_chapter is not None and detected_lesson is not None:
                        break
            
            if chapter_number is None:
                chapter_number = detected_chapter
            if lesson_number is None:
                lesson_number = detected_lesson
        
        # Tạo folder name theo format: {subject}_{curriculum}_{grade}_{chapter}_{lesson}
        # VD: LICHSU_KNTT_C12_4_10
        folder_parts = [self.subject]
        if self.curriculum:
            folder_parts.append(self.curriculum)
        folder_parts.append(self.grade)
        
        if chapter_number is not None:
            folder_parts.append(str(chapter_number))
        if lesson_number is not None:
            folder_parts.append(str(lesson_number))
        
        folder_name = "_".join(folder_parts)
        
        # Tạo path: [grade, subject, folder_name]
        path = [self.grade, self.subject, folder_name]
        
        return path
    
    def has_level_headers(self, spec_text: str) -> bool:
        """
        Kiểm tra xem spec text có chứa các level headers không
        
        Args:
            spec_text: Nội dung đặc tả ma trận
            
        Returns:
            bool: True nếu có ít nhất 1 header level (Nhận biết:, Thông hiểu:, Vận dụng:)
        """
        if pd.isna(spec_text):
            return False
        
        spec_text = str(spec_text).strip()
        
        # Các pattern header cần tìm
        level_patterns = [
            "Nhận biết:",
            "Thông hiểu:",
            "Vận dụng:",
            "Vận dụng cao:"
        ]
        
        # Kiểm tra có ít nhất 1 pattern
        for pattern in level_patterns:
            if pattern in spec_text:
                return True
        
        return False
    
    def extract_learning_outcome_by_level(self, spec_text: str, cognitive_level: str) -> str:
        """
        Trích xuất đặc tả ma trận theo cấp độ nhận thức
        
        Args:
            spec_text: Nội dung đặc tả ma trận đầy đủ
            cognitive_level: Cấp độ (NB, TH, VD, VDC)
            
        Returns:
            str: Đặc tả tương ứng với cấp độ
        """
        if pd.isna(spec_text):
            return ""
        
        spec_text = str(spec_text).strip()
        
        # Mapping tên cấp độ
        level_names = {
            "NB": ["Nhận biết:", "Nhận biết"],
            "TH": ["Thông hiểu:", "Thông hiểu"],
            "VD": ["Vận dụng:", "Vận dụng"],
            "VDC": ["Vận dụng cao:", "Vận dụng cao"]
        }
        
        # Tìm nội dung tương ứng với cấp độ
        result_lines = []
        current_level = None
        
        lines = spec_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Kiểm tra xem dòng này có phải là header cấp độ không
            is_level_header = False
            for level, names in level_names.items():
                if any(line.startswith(name) for name in names):
                    current_level = level
                    is_level_header = True
                    break
            
            # Nếu đang ở đúng cấp độ cần tìm
            if current_level == cognitive_level:
                if is_level_header:
                    # Thêm header (có thể loại bỏ nếu không cần)
                    result_lines.append(line)
                else:
                    # Thêm nội dung
                    result_lines.append(line)
            elif is_level_header and current_level != cognitive_level:
                # Đã sang cấp độ khác, dừng lại nếu đã có kết quả
                if result_lines:
                    break
        
        return '\n'.join(result_lines).strip()
    
    def parse_matrix(self, question_type: str = "TN") -> List[QuestionSpec]:
        """
        Phân tích ma trận và tạo danh sách đặc tả câu hỏi
        
        Args:
            question_type: Loại câu hỏi cần parse (TN, DS, TLN)
            
        Returns:
            List[QuestionSpec]: Danh sách đặc tả câu hỏi
        """
        if self.df is None:
            raise ValueError("Chưa load file Excel. Hãy gọi load_excel() trước.")
        
        question_specs = []
        
        # Track processed question codes per lesson to avoid duplicates
        processed_codes_per_lesson = {}
        
        # Xác định các cột cần xử lý theo loại câu hỏi
        if question_type == "TN":
            cols_to_process = [self.COL_TN_NB, self.COL_TN_TH, self.COL_TN_VD]
        elif question_type == "DS":
            cols_to_process = [self.COL_DS_NB, self.COL_DS_TH, self.COL_DS_VD]
        elif question_type == "TLN":
            cols_to_process = [self.COL_TLN_NB, self.COL_TLN_TH, self.COL_TLN_VD]
        elif question_type == "TL":
            cols_to_process = [self.COL_TL_NB, self.COL_TL_TH, self.COL_TL_VD]
        else:
            raise ValueError(f"Loại câu hỏi không hợp lệ: {question_type}")
        
        # Duyệt qua các hàng (bỏ qua header - 2 hàng đầu)
        for row_idx in range(2, len(self.df)):
            row = self.df.iloc[row_idx]
            
            # Cập nhật thông tin hiện tại từ các cột cơ bản
            if pd.notna(row[self.COL_COMPETENCY]) and row[self.COL_COMPETENCY] != '\\':
                try:
                    self.current_competency = int(row[self.COL_COMPETENCY])
                except:
                    pass
            
            if pd.notna(row[self.COL_CHAPTER]):
                chapter_text = str(row[self.COL_CHAPTER]).strip()
                self.current_chapter = self.parse_chapter_number(chapter_text)
            
            # Default chapter to 0 for subjects without chapters (like DIALY)
            if self.current_chapter is None:
                self.current_chapter = 0
            
            if pd.notna(row[self.COL_LESSON]):
                self.current_lesson = str(row[self.COL_LESSON]).strip()
            
            if pd.notna(row[self.COL_SPEC]):
                self.current_spec = str(row[self.COL_SPEC]).strip()
            
            supplementary_parts = []
            
            # Chỉ có 1 cột tài liệu bổ sung
            try:
                if self.COL_SUPPLEMENTARY < len(row) and pd.notna(row[self.COL_SUPPLEMENTARY]):
                    content = str(row[self.COL_SUPPLEMENTARY]).strip()
                    if content and content != 'nan':
                        supplementary_parts.append(content)
            except (IndexError, KeyError):
                pass
            
            supplementary = "\n\n---\n\n".join(supplementary_parts) if supplementary_parts else ""
            
            # Initialize tracking for this lesson if not exists
            lesson_key = f"{self.current_chapter}_{self.current_lesson}"
            if lesson_key not in processed_codes_per_lesson:
                processed_codes_per_lesson[lesson_key] = set()
            
            # Xử lý các cột câu hỏi
            for col_idx in cols_to_process:
                num_questions, question_codes, rich_types = self.parse_question_cell(row[col_idx])
                
                if num_questions > 0:
                    cognitive_level = self.COGNITIVE_LEVEL_MAP[col_idx]
                    
                    # Filter out duplicate question codes for this lesson
                    new_codes = []
                    filtered_rich_types = {}
                    for code in question_codes:
                        if code not in processed_codes_per_lesson[lesson_key]:
                            new_codes.append(code)
                            processed_codes_per_lesson[lesson_key].add(code)
                            # Preserve rich content types for non-duplicate codes
                            if code in rich_types:
                                filtered_rich_types[code] = rich_types[code]
                    
                    # Skip if all codes were duplicates
                    if not new_codes:
                        continue
                    
                    # Lấy learning_outcome theo chế độ
                    should_split = self.split_learning_outcome_by_level
                    
                    # Auto-detect nếu chế độ là None
                    if should_split is None:
                        should_split = self.has_level_headers(self.current_spec)

                    if should_split:
                        # Chế độ split: tách theo level
                        learning_outcome = self.extract_learning_outcome_by_level(
                            self.current_spec, cognitive_level
                        )

                    else:
                        # Chế độ full: lấy toàn bộ
                        learning_outcome = self.current_spec if self.current_spec else ""

                    # ⚠️ AUTO-CORRECTION: TN có rich_content_types → chuyển thành TLN
                    # Vì TN với bảng/biểu đồ thực chất là câu tính toán (TLN)
                    actual_question_type = question_type
                    if question_type == "TN" and filtered_rich_types:
                        actual_question_type = "TLN"
                        # print(f"🔄 [AUTO-FIX] {', '.join(new_codes)}: TN → TLN (có rich_content_types)")

                    # For TL: extract sub-item letters (e.g. C1a, C1b → base C1 with sub_items)
                    tl_sub_items: Optional[Dict[str, List[str]]] = None
                    if actual_question_type == "TL":
                        si_base_codes, tl_sub_items = self._extract_tl_sub_items(new_codes)
                        if si_base_codes != new_codes:
                            # Remap any rich_type keys from sub-item codes to base codes
                            remapped_rich: Dict[str, List[str]] = {}
                            for orig_c, rich_list in filtered_rich_types.items():
                                mb = re.match(r'^C(\d+)[a-z]+$', orig_c)
                                base_c = 'C' + mb.group(1) if mb else orig_c
                                remapped_rich.setdefault(base_c, rich_list)
                            filtered_rich_types = remapped_rich
                            new_codes = si_base_codes

                    # Tạo QuestionSpec với số câu và mã câu đã được deduplicate
                    spec = QuestionSpec(
                        lesson_name=self.current_lesson,
                        competency_level=self.current_competency,
                        cognitive_level=cognitive_level,
                        question_type=actual_question_type,  # Sử dụng type đã được auto-correct
                        num_questions=len(new_codes),  # Cập nhật số câu thực tế
                        question_codes=new_codes,  # Chỉ giữ các mã chưa xử lý
                        learning_outcome=learning_outcome,
                        row_index=row_idx,
                        chapter_number=self.current_chapter,
                        supplementary_material=supplementary,
                        rich_content_types=filtered_rich_types if filtered_rich_types else None,
                        sub_items=tl_sub_items,
                    )
                    
                    question_specs.append(spec)
        
        return question_specs
    
    def group_true_false_questions(self) -> List[TrueFalseQuestionSpec]:
        """
        Group các mệnh đề Đúng/Sai thành câu hỏi hoàn chỉnh
        
        Returns:
            List[TrueFalseQuestionSpec]: Danh sách câu hỏi DS hoàn chỉnh (4 mệnh đề)
        """
        # Parse tất cả statements từ ma trận
        all_specs = self.parse_matrix(question_type="DS")
        
        # Group theo số câu (C1, C2, C3...)
        from collections import defaultdict
        grouped = defaultdict(list)
        
        for spec in all_specs:
            for code in spec.question_codes:
                # Extract base number: C1A -> C1, C2B -> C2
                base_code = re.match(r'(C\d+)', code, re.IGNORECASE).group(1).upper()
                
                # Extract statement label: C1A -> A, C1B -> B
                label_match = re.search(r'([A-D])$', code, re.IGNORECASE)
                if label_match:
                    label = label_match.group(1).lower()
                    
                    statement = StatementSpec(
                        statement_code=code.upper(),
                        label=label,
                        cognitive_level=spec.cognitive_level,
                        learning_outcome=spec.learning_outcome,
                        competency_level=spec.competency_level,
                        materials=spec.supplementary_material
                    )
                    
                    grouped[base_code].append({
                        'statement': statement,
                        'lesson_name': spec.lesson_name,
                        'chapter_number': spec.chapter_number,
                        'supplementary_material': spec.supplementary_material,
                        'rich_content_types': spec.rich_content_types
                    })
        
        # Tạo TrueFalseQuestionSpec cho mỗi câu
        tf_questions = []
        
        for question_code in sorted(grouped.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
            items = grouped[question_code]
            
            # Sort statements by label (a, b, c, d)
            items.sort(key=lambda x: x['statement'].label)
            
            statements = [item['statement'] for item in items]
            lesson_name = items[0]['lesson_name']  # Lấy lesson_name từ statement đầu tiên
            supplementary_material = items[0]['supplementary_material']  # Lấy tài liệu bổ sung
            chapter_number = items[0]['chapter_number']  # Lấy chapter_number từ item đầu tiên
            
            # Aggregate rich_content_types from all statements into a single dict at question level
            aggregated_rich_types = None
            all_types = []
            seen_codes = set()
            
            for item in items:
                if item.get('rich_content_types'):
                    # Each item may have types like {"C1A": ["BK"], "C1B": ["TT"]}
                    for stmt_code, types in item['rich_content_types'].items():
                        for type_code in types:
                            if type_code not in seen_codes:
                                seen_codes.add(type_code)
                                all_types.append(type_code)
            
            # If we found any types, create aggregated dict at question level
            if all_types:
                aggregated_rich_types = {question_code: all_types}
            
            # Kiểm tra có đủ 4 mệnh đề không
            if len(statements) != 4:
                continue
            
            # Kiểm tra có đủ a, b, c, d không
            labels = [s.label for s in statements]
            if labels != ['a', 'b', 'c', 'd']:
                continue
            
            tf_question = TrueFalseQuestionSpec(
                question_code=question_code,
                lesson_name=lesson_name,
                statements=statements,
                chapter_number=chapter_number,
                supplementary_material=supplementary_material,
                rich_content_types=aggregated_rich_types
            )
            
            tf_questions.append(tf_question)
        
        return tf_questions
    
    def get_all_question_specs(self) -> Dict[str, List[QuestionSpec]]:
        """
        Lấy tất cả đặc tả câu hỏi theo loại
        
        Returns:
            Dict[str, List[QuestionSpec]]: Dict với key là loại câu hỏi (TN, DS, TLN, TL)
        """
        return {
            "TN": self.parse_matrix("TN"),
            "DS": self.parse_matrix("DS"),
            "TLN": self.parse_matrix("TLN"),
            "TL": self.parse_matrix("TL")
        }
    
    def has_sample_questions(self) -> bool:
        """Kiểm tra xem có ngân hàng câu hỏi mẫu không"""
        return False
    
    def get_sample_question(self, lesson_name: str, question_type: str, cognitive_level: str):
        """
        Lấy câu hỏi mẫu ngẫu nhiên
        
        Args:
            lesson_name: Tên bài
            question_type: Loại câu hỏi (TN, DS, TLN)
            cognitive_level: Cấp độ (NB, TH, VD, VDC)
            
        Returns:
            SampleQuestion hoặc None
        """
        if not self.has_sample_questions():
            return None
        
        return None  # Sample question bank removed
    
    def print_specs_summary(self, specs: List[QuestionSpec]):
        """In tóm tắt các đặc tả"""
        print("\n" + "=" * 100)
        print(f"TÓM TẮT CÁC NHÓM CÂU HỎI (Tổng: {len(specs)} nhóm)")
        print("=" * 100)
        
        for idx, spec in enumerate(specs, 1):
            chapter_info = f" | Chương: {spec.chapter_number}" if spec.chapter_number else ""
            print(f"\n[{idx}] {spec.lesson_name}{chapter_info}")
            print(f"    Loại: {spec.question_type} | Cấp độ: {spec.cognitive_level} | Số câu: {spec.num_questions}")
            print(f"    Mã câu: {', '.join(spec.question_codes)}")
            print(f"    Đặc tả: {spec.learning_outcome[:100]}...")
