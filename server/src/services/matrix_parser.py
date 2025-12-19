"""
Module phân tích và xử lý ma trận câu hỏi từ file Excel
"""
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from .sample_question_bank import SampleQuestionBank
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
    supplementary_materials: str = ""  # Tài liệu bổ sung (nội dung ngoài SGK)


@dataclass
class StatementSpec:
    """Đặc tả một mệnh đề trong câu Đúng/Sai"""
    statement_code: str  # Mã mệnh đề (C1A, C1B, C1C, C1D)
    label: str  # Nhãn mệnh đề (a, b, c, d)
    cognitive_level: str  # Cấp độ (NB, TH, VD, VDC)
    learning_outcome: str  # Đặc tả cho mệnh đề này
    competency_level: Optional[int] = None  # Thành phần năng lực
    supplementary_materials: str = ""  # Tài liệu bổ sung


@dataclass
class TrueFalseQuestionSpec:
    """Đặc tả một câu hỏi Đúng/Sai hoàn chỉnh (4 mệnh đề)"""
    question_code: str  # Mã câu (C1, C2, ...)
    lesson_name: str  # Tên chương - bài
    statements: List[StatementSpec]  # Danh sách 4 mệnh đề (a, b, c, d)
    question_type: str = "DS"  # Loại câu hỏi
    supplementary_materials: str = ""  # Tài liệu bổ sung chung cho câu hỏi


class MatrixParser:
    """Class phân tích ma trận câu hỏi"""
    
    # Mapping cột trong Excel
    COL_STT = 1
    COL_COMPETENCY = 2
    COL_LESSON = 3
    COL_SPEC = 4
    
    # Cột cho câu hỏi trắc nghiệm nhiều lựa chọn
    COL_TN_NB = 5   # Nhận biết
    COL_TN_TH = 6   # Thông hiểu
    COL_TN_VD = 7   # Vận dụng
    
    # Cột cho câu hỏi Đúng/Sai
    COL_DS_NB = 8   # Nhận biết
    COL_DS_TH = 9   # Thông hiểu
    COL_DS_VD = 10  # Vận dụng
    
    # Cột cho câu hỏi trả lời ngắn
    COL_TLN_NB = 11  # Nhận biết
    COL_TLN_TH = 12  # Thông hiểu
    COL_TLN_VD = 13  # Vận dụng
    
    # Cột tài liệu bổ sung
    COL_SUPPLEMENTARY_1 = 14  # Tài liệu bổ sung phần 1
    COL_SUPPLEMENTARY_2 = 15  # Tài liệu bổ sung phần 2
    
    # Mapping cấp độ
    COGNITIVE_LEVEL_MAP = {
        COL_TN_NB: "NB", COL_TN_TH: "TH", COL_TN_VD: "VD",
        COL_DS_NB: "NB", COL_DS_TH: "TH", COL_DS_VD: "VD",
        COL_TLN_NB: "NB", COL_TLN_TH: "TH", COL_TLN_VD: "VD"
    }
    
    # Mapping loại câu hỏi
    QUESTION_TYPE_MAP = {
        COL_TN_NB: "TN", COL_TN_TH: "TN", COL_TN_VD: "TN",
        COL_DS_NB: "DS", COL_DS_TH: "DS", COL_DS_VD: "DS",
        COL_TLN_NB: "TLN", COL_TLN_TH: "TLN", COL_TLN_VD: "TLN"
    }
    
    def __init__(self):
        self.df = None
        self.current_competency = None
        self.current_lesson = None
        self.current_spec = None
        self.sample_question_bank: Optional[SampleQuestionBank] = None
        self.template: Optional[MatrixTemplate] = None
        self.template_metadata: dict = {}
        self.file_path: Optional[str] = None
    
    def load_excel(self, file_path: str, sheet_name: str = None):
        """
        Đọc file Excel
        
        Args:
            file_path: Đường dẫn file Excel
            sheet_name: Tên sheet cần đọc (None = tự động phát hiện)
        """
        self.file_path = file_path
        
        # Phát hiện template
        detector = MatrixTemplateDetector()
        self.template, self.template_metadata = detector.detect(file_path)
        detector.print_detection_result(self.template, self.template_metadata)
        
        # Xác định sheet name
        if sheet_name is None:
            sheet_name = self.template_metadata.get('matrix_sheet', 'Sử 12')
        
        # Đọc sheet ma trận
        self.df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        print(f"\n✓ Đã tải ma trận từ sheet '{sheet_name}': {self.df.shape[0]} hàng x {self.df.shape[1]} cột")
        
        # Load câu hỏi mẫu nếu có
        if self.template == MatrixTemplate.TEMPLATE_2:
            self.sample_question_bank = SampleQuestionBank()
            sample_sheet = self.template_metadata.get('sample_sheet')
            if sample_sheet:
                success = self.sample_question_bank.load_from_excel(file_path, sample_sheet)
                if success:
                    self.sample_question_bank.print_statistics()
    
    def parse_question_cell(self, cell_value) -> Tuple[int, List[str]]:
        """
        Parse giá trị trong ô để lấy số câu hỏi và mã câu
        
        Args:
            cell_value: Giá trị ô (VD: "2 (C1,2)" hoặc "1 (C10)")
            
        Returns:
            Tuple[int, List[str]]: (số câu hỏi, danh sách mã câu)
        """
        if pd.isna(cell_value):
            return 0, []
        
        cell_str = str(cell_value).strip()
        
        # Pattern: số (mã1, mã2, ...) hoặc số (mã)
        # VD: "2 (C1,2)" hoặc "1 (C10)" hoặc "2 (C1a, 1b)"
        pattern = r'(\d+)\s*\((.*?)\)'
        match = re.search(pattern, cell_str)
        
        if match:
            num = int(match.group(1))
            codes_str = match.group(2)
            
            # Tách các mã câu
            # Xử lý các định dạng: "C1,2", "C1a, 1b", "C6,7"
            codes = []
            parts = [p.strip() for p in codes_str.split(',')]
            
            for part in parts:
                # Nếu có chữ C ở đầu
                if part.upper().startswith('C'):
                    codes.append(part.upper())
                # Nếu chỉ có số hoặc số+chữ (1b, 2a)
                else:
                    codes.append('C' + part.upper())
            
            return num, codes
        
        return 0, []
    
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
        
        # Xác định các cột cần xử lý theo loại câu hỏi
        if question_type == "TN":
            cols_to_process = [self.COL_TN_NB, self.COL_TN_TH, self.COL_TN_VD]
        elif question_type == "DS":
            cols_to_process = [self.COL_DS_NB, self.COL_DS_TH, self.COL_DS_VD]
        elif question_type == "TLN":
            cols_to_process = [self.COL_TLN_NB, self.COL_TLN_TH, self.COL_TLN_VD]
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
            
            if pd.notna(row[self.COL_LESSON]):
                self.current_lesson = str(row[self.COL_LESSON]).strip()
            
            if pd.notna(row[self.COL_SPEC]):
                self.current_spec = str(row[self.COL_SPEC]).strip()
            
            supplementary_parts = []
            
            try:
                if self.COL_SUPPLEMENTARY_1 < len(row) and pd.notna(row[self.COL_SUPPLEMENTARY_1]):
                    content = str(row[self.COL_SUPPLEMENTARY_1]).strip()
                    if content and content != 'nan':
                        supplementary_parts.append(content)
            except (IndexError, KeyError):
                pass
            
            try:
                if self.COL_SUPPLEMENTARY_2 < len(row) and pd.notna(row[self.COL_SUPPLEMENTARY_2]):
                    content = str(row[self.COL_SUPPLEMENTARY_2]).strip()
                    if content and content != 'nan':
                        supplementary_parts.append(content)
            except (IndexError, KeyError):
                pass
            
            supplementary = "\n\n---\n\n".join(supplementary_parts) if supplementary_parts else ""
            
            # Xử lý các cột câu hỏi
            for col_idx in cols_to_process:
                num_questions, question_codes = self.parse_question_cell(row[col_idx])
                
                if num_questions > 0:
                    cognitive_level = self.COGNITIVE_LEVEL_MAP[col_idx]
                    
                    # Trích xuất đặc tả theo cấp độ
                    learning_outcome = self.extract_learning_outcome_by_level(
                        self.current_spec, 
                        cognitive_level
                    )
                    
                    # Tạo QuestionSpec
                    spec = QuestionSpec(
                        lesson_name=self.current_lesson,
                        competency_level=self.current_competency,
                        cognitive_level=cognitive_level,
                        question_type=question_type,
                        num_questions=num_questions,
                        question_codes=question_codes,
                        learning_outcome=learning_outcome,
                        row_index=row_idx,
                        supplementary_materials=supplementary
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
                        supplementary_materials=spec.supplementary_materials
                    )
                    
                    grouped[base_code].append({
                        'statement': statement,
                        'lesson_name': spec.lesson_name,
                        'supplementary_materials': spec.supplementary_materials
                    })
        
        # Tạo TrueFalseQuestionSpec cho mỗi câu
        tf_questions = []
        
        for question_code in sorted(grouped.keys(), key=lambda x: int(re.search(r'\d+', x).group())):
            items = grouped[question_code]
            
            # Sort statements by label (a, b, c, d)
            items.sort(key=lambda x: x['statement'].label)
            
            statements = [item['statement'] for item in items]
            lesson_name = items[0]['lesson_name']  # Lấy lesson_name từ statement đầu tiên
            supplementary_materials = items[0]['supplementary_materials']  # Lấy tài liệu bổ sung
            
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
                supplementary_materials=supplementary_materials
            )
            
            tf_questions.append(tf_question)
        
        return tf_questions
    
    def get_all_question_specs(self) -> Dict[str, List[QuestionSpec]]:
        """
        Lấy tất cả đặc tả câu hỏi theo loại
        
        Returns:
            Dict[str, List[QuestionSpec]]: Dict với key là loại câu hỏi (TN, DS, TLN)
        """
        return {
            "TN": self.parse_matrix("TN"),
            "DS": self.parse_matrix("DS"),
            "TLN": self.parse_matrix("TLN")
        }
    
    def has_sample_questions(self) -> bool:
        """Kiểm tra xem có ngân hàng câu hỏi mẫu không"""
        return self.sample_question_bank is not None and self.sample_question_bank.has_samples()
    
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
        
        return self.sample_question_bank.get_random_sample(
            lesson_name,
            question_type,
            cognitive_level
        )
    
    def print_specs_summary(self, specs: List[QuestionSpec]):
        """In tóm tắt các đặc tả"""
        print("\n" + "=" * 100)
        print(f"TÓM TẮT CÁC NHÓM CÂU HỎI (Tổng: {len(specs)} nhóm)")
        print("=" * 100)
        
        for idx, spec in enumerate(specs, 1):
            print(f"\n[{idx}] {spec.lesson_name}")
            print(f"    Loại: {spec.question_type} | Cấp độ: {spec.cognitive_level} | Số câu: {spec.num_questions}")
            print(f"    Mã câu: {', '.join(spec.question_codes)}")
            print(f"    Đặc tả: {spec.learning_outcome[:100]}...")
