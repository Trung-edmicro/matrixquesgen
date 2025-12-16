"""
Service phân tích và trích xuất câu hỏi trắc nghiệm từ file DOCX
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
from services.docx_reader import DocxReader


class QuestionParser:
    """Class phân tích câu hỏi trắc nghiệm từ DOCX"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.reader = DocxReader(verbose=verbose)
        self.questions = []
    
    def load_docx(self, file_path: str) -> bool:
        """
        Tải file DOCX
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            bool: True nếu thành công
        """
        try:
            self.reader.load_document(file_path)
            if self.verbose:
                print(f"✓ Đã tải file: {file_path}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"✗ Lỗi khi tải file: {str(e)}")
            raise
    
    def _is_question_start(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Kiểm tra xem đoạn text có phải là bắt đầu câu hỏi không
        
        Args:
            text: Nội dung text
            
        Returns:
            Dict chứa thông tin câu hỏi nếu là câu hỏi, None nếu không
        """
        # Pattern: Câu 1 (NB). hoặc Câu 1. hoặc Câu 1 (TH):
        patterns = [
            r'^Câu\s+(\d+)\s*\(([A-Z]+)\)[\.:]\s*(.+)',  # Câu 1 (NB). Text
            r'^Câu\s+(\d+)\s*\(([A-Z]+)\)\s*(.+)',       # Câu 1 (NB) Text
            r'^Câu\s+(\d+)[\.:]\s*(.+)',                  # Câu 1. Text
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip(), re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    # Có cấp độ
                    return {
                        'number': int(match.group(1)),
                        'level': match.group(2).upper(),
                        'question_text': match.group(3).strip()
                    }
                else:
                    # Không có cấp độ
                    return {
                        'number': int(match.group(1)),
                        'level': None,
                        'question_text': match.group(2).strip()
                    }
        
        return None
    
    def _is_answer_option(self, text: str) -> Optional[Dict[str, str]]:
        """
        Kiểm tra xem đoạn text có phải là phương án trả lời không
        
        Args:
            text: Nội dung text
            
        Returns:
            Dict chứa key và nội dung nếu là phương án, None nếu không
        """
        # Pattern: A. Text hoặc A) Text hoặc A: Text
        pattern = r'^([A-D])[\.):\s]\s*(.+)'
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        
        if match:
            return {
                'key': match.group(1).upper(),
                'text': match.group(2).strip()
            }
        
        return None
    
    def parse_multiple_choice_questions(self) -> List[Dict[str, Any]]:
        """
        Phân tích câu hỏi trắc nghiệm dạng TN (4 phương án)
        
        Returns:
            List[Dict]: Danh sách câu hỏi đã parse
        """
        if self.reader.document is None:
            raise ValueError("Chưa tải document. Gọi load_docx() trước.")
        
        paragraphs = self.reader.get_paragraphs()
        questions = []
        current_question = None
        
        for para in paragraphs:
            text = para['text'].strip()
            
            if not text:
                continue
            
            # Kiểm tra có phải câu hỏi mới không
            question_info = self._is_question_start(text)
            if question_info:
                # Lưu câu hỏi cũ nếu có
                if current_question and self._is_complete_question(current_question):
                    questions.append(current_question)
                
                # Bắt đầu câu hỏi mới
                current_question = {
                    'number': question_info['number'],
                    'level': question_info['level'],
                    'question_text': question_info['question_text'],
                    'options': {},
                    'raw_text': text
                }
                continue
            
            # Kiểm tra có phải phương án trả lời không
            if current_question:
                option_info = self._is_answer_option(text)
                if option_info:
                    current_question['options'][option_info['key']] = option_info['text']
                else:
                    # Nếu không phải phương án, có thể là phần tiếp theo của câu hỏi
                    if len(current_question['options']) == 0:
                        # Chưa có phương án nào -> nối vào câu hỏi
                        current_question['question_text'] += ' ' + text
                        current_question['raw_text'] += '\n' + text
        
        # Lưu câu hỏi cuối cùng
        if current_question and self._is_complete_question(current_question):
            questions.append(current_question)
        
        self.questions = questions
        
        if self.verbose:
            print(f"✓ Đã phân tích {len(questions)} câu hỏi")
            for q in questions[:3]:  # Hiển thị 3 câu đầu
                print(f"\n  Câu {q['number']} ({q['level']}): {q['question_text'][:50]}...")
                print(f"    Số phương án: {len(q['options'])}")
        
        return questions
    
    def _is_complete_question(self, question: Dict[str, Any]) -> bool:
        """
        Kiểm tra câu hỏi có đầy đủ không (4 phương án A, B, C, D)
        
        Args:
            question: Dict câu hỏi
            
        Returns:
            bool: True nếu đầy đủ
        """
        required_options = {'A', 'B', 'C', 'D'}
        return required_options.issubset(set(question['options'].keys()))
    
    def _is_source_text_start(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Kiểm tra xem đoạn text có phải là bắt đầu câu hỏi DS không
        
        Pattern: Câu 1. Cho đoạn tư liệu sau: hoặc Câu 1. Cho tư liệu: hoặc Câu 1. Cho bảng thông tin sau:
        
        Args:
            text: Nội dung text
            
        Returns:
            Dict chứa thông tin câu hỏi nếu là câu DS, None nếu không
        """
        patterns = [
            r'^Câu\s+(\d+)\.\s*Cho\s+đoạn\s+tư\s+liệu\s+sau[:\.]?',  # Câu 1. Cho đoạn tư liệu sau:
            r'^Câu\s+(\d+)\.\s*Cho\s+tư\s+liệu\s+sau[:\.]?',          # Câu 1. Cho tư liệu sau:
            r'^Câu\s+(\d+)\.\s*Cho\s+đoạn\s+tư\s+liệu[:\.]?',        # Câu 1. Cho đoạn tư liệu:
            r'^Câu\s+(\d+)\.\s*Cho\s+bảng\s+thông\s+tin\s+sau[:\.]?',  # Câu 1. Cho bảng thông tin sau:
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip(), re.IGNORECASE)
            if match:
                # Phát hiện xem có phải dạng bảng không
                has_table = 'bảng' in text.lower()
                return {
                    'number': int(match.group(1)),
                    'level': None,  # Level sẽ được xác định từ mệnh đề
                    'source_text': '',  # Sẽ được fill sau
                    'has_table': has_table
                }
        
        return None
    
    def _is_statement(self, text: str) -> Optional[Dict[str, str]]:
        """
        Kiểm tra xem đoạn text có phải là mệnh đề a, b, c, d không
        
        Args:
            text: Nội dung text
            
        Returns:
            Dict chứa key, level và nội dung nếu là mệnh đề, None nếu không
        """
        # Pattern với level: (NB) a. Text hoặc (TH) b. Text
        pattern_with_level = r'^\(([A-Z]+)\)\s+([a-d])\.\s*(.+)'
        match = re.match(pattern_with_level, text.strip(), re.IGNORECASE)
        
        if match:
            return {
                'level': match.group(1).upper(),
                'key': match.group(2).lower(),
                'text': match.group(3).strip()
            }
        
        # Pattern không có level: a. Text hoặc a) Text hoặc a: Text
        pattern = r'^([a-d])[\.\):]\s*(.+)'
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        
        if match:
            return {
                'level': None,
                'key': match.group(1).lower(),
                'text': match.group(2).strip()
            }
        
        return None
    
    def get_question_by_number(self, number: int) -> Optional[Dict[str, Any]]:
        """
        Lấy câu hỏi theo số thứ tự
        
        Args:
            number: Số thứ tự câu hỏi
            
        Returns:
            Dict câu hỏi hoặc None
        """
        for q in self.questions:
            if q['number'] == number:
                return q
        return None
    
    def get_questions_by_level(self, level: str) -> List[Dict[str, Any]]:
        """
        Lấy các câu hỏi theo cấp độ
        
        Args:
            level: Cấp độ (NB, TH, VD, VDC)
            
        Returns:
            List câu hỏi
        """
        return [q for q in self.questions if q['level'] == level.upper()]
    
    def format_question_as_template(self, question: Dict[str, Any]) -> str:
        """
        Format câu hỏi thành template để dùng trong prompt
        
        Args:
            question: Dict câu hỏi
            
        Returns:
            str: Câu hỏi đã format
        """
        template = f"Câu {question['number']}"
        if question['level']:
            template += f" ({question['level']})"
        template += f". {question['question_text']}\n"
        
        for key in ['A', 'B', 'C', 'D']:
            if key in question['options']:
                template += f"{key}. {question['options'][key]}\n"
        
        return template.strip()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Thống kê câu hỏi
        
        Returns:
            Dict thống kê
        """
        total = len(self.questions)
        by_level = {}
        
        for q in self.questions:
            level = q['level'] or 'Unknown'
            by_level[level] = by_level.get(level, 0) + 1
        
        incomplete = sum(1 for q in self.questions if not self._is_complete_question(q))
        
        return {
            'total_questions': total,
            'by_level': by_level,
            'incomplete_questions': incomplete,
            'complete_questions': total - incomplete
        }
    
    def parse_true_false_questions(self) -> List[Dict[str, Any]]:
        """
        Phân tích câu hỏi dạng DS (Đúng/Sai) - có tư liệu và 4 mệnh đề a, b, c, d
        Hỗ trợ cả tư liệu dạng text và dạng bảng
        
        Returns:
            List[Dict]: Danh sách câu hỏi DS đã parse
        """
        if self.reader.document is None:
            raise ValueError("Chưa tải document. Gọi load_docx() trước.")
        
        paragraphs = self.reader.get_paragraphs()
        tables = self.reader.get_tables()
        questions = []
        current_question = None
        in_source_text = False
        next_table_index = 0  # Để track bảng tiếp theo
        
        for para in paragraphs:
            text = para['text'].strip()
            
            if not text:
                continue
            
            # Kiểm tra có phải câu DS mới không
            ds_info = self._is_source_text_start(text)
            if ds_info:
                # Lưu câu hỏi cũ nếu đầy đủ
                if current_question and self._is_complete_ds_question(current_question):
                    questions.append(current_question)
                
                # Bắt đầu câu DS mới
                current_question = {
                    'number': ds_info['number'],
                    'level': None,  # Sẽ lấy từ mệnh đề đầu tiên
                    'source_text': '',
                    'statements': {},
                    'statement_levels': {},  # Lưu level của từng mệnh đề
                    'raw_text': text,
                    'has_table': ds_info.get('has_table', False)
                }
                
                # Nếu là dạng bảng, tìm bảng tiếp theo và add vào source_text
                if ds_info.get('has_table') and next_table_index < len(tables):
                    table_text = self._format_table_as_text(tables[next_table_index])
                    current_question['source_text'] = table_text
                    next_table_index += 1
                    in_source_text = False  # Không thu thập thêm text
                else:
                    in_source_text = True
                continue
            
            # Kiểm tra có phải mệnh đề không
            if current_question:
                statement_info = self._is_statement(text)
                if statement_info:
                    in_source_text = False
                    current_question['statements'][statement_info['key']] = statement_info['text']
                    if statement_info['level']:
                        current_question['statement_levels'][statement_info['key']] = statement_info['level']
                    # Lấy level từ mệnh đề đầu tiên
                    if current_question['level'] is None and statement_info['level']:
                        current_question['level'] = statement_info['level']
                else:
                    # Nếu không phải mệnh đề và đang trong tư liệu
                    if in_source_text:
                        # Nối vào source_text
                        if current_question['source_text']:
                            current_question['source_text'] += '\n' + text
                        else:
                            current_question['source_text'] = text
                        current_question['raw_text'] += '\n' + text
        
        # Lưu câu cuối
        if current_question and self._is_complete_ds_question(current_question):
            questions.append(current_question)
        
        if self.verbose:
            print(f"✓ Đã phân tích {len(questions)} câu DS")
            for q in questions[:3]:
                print(f"\n  Câu {q['number']} ({q.get('level', 'N/A')}): {q['source_text'][:50]}...")
                print(f"    Số mệnh đề: {len(q['statements'])}")
        
        return questions
    
    def _format_table_as_text(self, table_data: Dict[str, Any]) -> str:
        """
        Format bảng từ DOCX thành text để làm tư liệu
        
        Args:
            table_data: Dict chứa dữ liệu bảng từ DocxReader.get_tables()
            
        Returns:
            str: Nội dung bảng dạng text
        """
        lines = []
        for row in table_data['data']:
            # Join các cell trong row
            row_text = ' | '.join([cell['text'] for cell in row])
            lines.append(row_text)
        
        return '\n'.join(lines)
    
    def _is_complete_ds_question(self, question: Dict[str, Any]) -> bool:
        """
        Kiểm tra câu DS có đầy đủ không (4 mệnh đề a, b, c, d)
        
        Args:
            question: Dict câu hỏi DS
            
        Returns:
            bool: True nếu đầy đủ
        """
        required_statements = {'a', 'b', 'c', 'd'}
        return required_statements.issubset(set(question['statements'].keys()))
    
    def format_ds_question_as_template(self, question: Dict[str, Any]) -> str:
        """
        Format câu DS thành template để dùng trong prompt
        
        Args:
            question: Dict câu DS
            
        Returns:
            str: Câu DS đã format
        """
        has_table = question.get('has_table', False)
        
        if has_table:
            template = f"Câu {question['number']}. Cho bảng thông tin sau:\n"
        else:
            template = f"Câu {question['number']}. Cho đoạn tư liệu sau:\n"
            
        template += f"{question['source_text']}\n\n"
        
        for key in ['a', 'b', 'c', 'd']:
            if key in question['statements']:
                level = question.get('statement_levels', {}).get(key, '')
                if level:
                    template += f"({level}) {key}. {question['statements'][key]}\n"
                else:
                    template += f"{key}. {question['statements'][key]}\n"
        
        result = template.strip()
                
        return result


class QuestionMatrixMapper:
    """Class mapping câu hỏi mẫu với ma trận"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def map_questions_to_matrix(
        self,
        questions: List[Dict[str, Any]],
        matrix_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Mapping câu hỏi mẫu với từng hàng của ma trận
        
        Args:
            questions: Danh sách câu hỏi đã parse
            matrix_rows: Danh sách các hàng trong ma trận
            
        Returns:
            List các hàng ma trận đã được gắn template
        """
        mapped_rows = []
        question_index = 0
        
        for row in matrix_rows:
            mapped_row = row.copy()
            
            # Lấy số lượng câu hỏi cần sinh cho hàng này
            num_questions = row.get('num_questions', 1)
            
            # Tìm câu hỏi mẫu phù hợp
            # Ưu tiên: cùng cấp độ > theo thứ tự
            template_questions = []
            
            target_level = row.get('cognitive_level', '').upper()
            
            # Tìm câu hỏi cùng cấp độ
            same_level_questions = [
                q for q in questions 
                if q.get('level') == target_level
            ]
            
            if same_level_questions and question_index < len(same_level_questions):
                template_questions.append(same_level_questions[question_index % len(same_level_questions)])
            elif question_index < len(questions):
                # Nếu không có cùng cấp độ, lấy theo thứ tự
                template_questions.append(questions[question_index % len(questions)])
            
            # Format template
            if template_questions:
                parser = QuestionParser()
                templates = [parser.format_question_as_template(q) for q in template_questions]
                mapped_row['question_template'] = '\n\n'.join(templates)
            else:
                mapped_row['question_template'] = ''
            
            mapped_rows.append(mapped_row)
            question_index += 1
        
        if self.verbose:
            print(f"✓ Đã mapping {len(mapped_rows)} hàng ma trận với câu hỏi mẫu")
        
        return mapped_rows
    
    def map_by_order(
        self,
        questions: List[Dict[str, Any]],
        matrix_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Mapping theo thứ tự: câu 1 -> hàng 1, câu 2 -> hàng 2, ...
        
        Args:
            questions: Danh sách câu hỏi
            matrix_rows: Danh sách hàng ma trận
            
        Returns:
            List hàng ma trận đã mapping
        """
        mapped_rows = []
        
        for idx, row in enumerate(matrix_rows):
            mapped_row = row.copy()
            
            if idx < len(questions):
                parser = QuestionParser()
                template = parser.format_question_as_template(questions[idx])
                mapped_row['question_template'] = template
            else:
                mapped_row['question_template'] = ''
            
            mapped_rows.append(mapped_row)
        
        if self.verbose:
            print(f"✓ Đã mapping {min(len(questions), len(matrix_rows))} câu hỏi theo thứ tự")
        
        return mapped_rows
    
    def map_by_question_code(
        self,
        questions: List[Dict[str, Any]],
        matrix_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Mapping theo question_code: C1 → Câu 1, C12 → Câu 12
        
        Args:
            questions: Danh sách câu hỏi đã parse
            matrix_rows: Danh sách hàng ma trận
            
        Returns:
            List hàng ma trận đã mapping
        """
        mapped_rows = []
        
        # Tạo dict để tra cứu nhanh: {1: question, 2: question, ...}
        question_dict = {q['number']: q for q in questions}
        
        for row in matrix_rows:
            mapped_row = row.copy()
            
            # Lấy question_code (VD: "C1", "C12")
            question_code = row.get('question_code', '')
            
            # Extract số từ question_code (C1 → 1, C12 → 12)
            match = re.search(r'C(\d+)', question_code)
            
            if match:
                question_number = int(match.group(1))
                
                # Tìm câu hỏi tương ứng
                if question_number in question_dict:
                    parser = QuestionParser()
                    template = parser.format_question_as_template(question_dict[question_number])
                    mapped_row['question_template'] = template
                    
                    if self.verbose:
                        print(f"  ✓ {question_code} → Câu {question_number}")
                else:
                    mapped_row['question_template'] = ''
                    if self.verbose:
                        print(f"  ⚠ {question_code} → Không tìm thấy câu {question_number}")
            else:
                mapped_row['question_template'] = ''
                if self.verbose:
                    print(f"  ⚠ {question_code} → Không parse được số")
            
            mapped_rows.append(mapped_row)
        
        if self.verbose:
            mapped_count = sum(1 for r in mapped_rows if r.get('question_template'))
            print(f"\n✓ Đã mapping {mapped_count}/{len(matrix_rows)} câu theo question_code")
        
        return mapped_rows


# Hàm tiện ích
def parse_questions_from_docx(file_path: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Hàm tiện ích để parse câu hỏi từ DOCX
    
    Args:
        file_path: Đường dẫn file
        verbose: Hiển thị log
        
    Returns:
        List câu hỏi
    """
    parser = QuestionParser(verbose=verbose)
    parser.load_docx(file_path)
    return parser.parse_multiple_choice_questions()


def map_questions_to_matrix(
    questions: List[Dict[str, Any]],
    matrix_rows: List[Dict[str, Any]],
    mapping_mode: str = 'order',
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Hàm tiện ích để mapping câu hỏi với ma trận
    
    Args:
        questions: Danh sách câu hỏi
        matrix_rows: Danh sách hàng ma trận
        mapping_mode: Chế độ mapping ('order' hoặc 'smart')
        verbose: Hiển thị log
        
    Returns:
        List hàng ma trận đã mapping
    """
    mapper = QuestionMatrixMapper(verbose=verbose)
    
    if mapping_mode == 'order':
        return mapper.map_by_order(questions, matrix_rows)
    else:
        return mapper.map_questions_to_matrix(questions, matrix_rows)
