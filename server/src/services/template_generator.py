"""
Service tích hợp để sinh câu hỏi với template từ file DOCX
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from services.question_parser import QuestionParser, QuestionMatrixMapper
from services.matrix_parser import MatrixParser, QuestionSpec
from services.question_generator import QuestionGenerator


class QuestionGeneratorWithTemplate:
    """
    Class sinh câu hỏi tự động với template từ file DOCX đề mẫu
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.question_parser = None
        self.parsed_questions = []  # Câu TN
        self.parsed_ds_questions = []  # Câu DS
        self.mapped_rows = []
    
    def load_template_docx(self, docx_path: str) -> bool:
        """
        Tải và parse file DOCX đề mẫu (cả TN và DS)
        
        Args:
            docx_path: Đường dẫn file DOCX
            
        Returns:
            bool: True nếu thành công
        """
        try:
            self.question_parser = QuestionParser(verbose=self.verbose)
            self.question_parser.load_docx(docx_path)
            
            # Parse câu TN
            self.parsed_questions = self.question_parser.parse_multiple_choice_questions()
            
            # Parse câu DS
            self.parsed_ds_questions = self.question_parser.parse_true_false_questions()
            
            if self.verbose:
                print(f"✓ Đã parse {len(self.parsed_questions)} câu TN từ {docx_path}")
                print(f"✓ Đã parse {len(self.parsed_ds_questions)} câu DS từ {docx_path}")
                
                # Log chi tiết DS questions
                if self.parsed_ds_questions:
                    print(f"\n📋 Chi tiết DS questions:")
                    for ds_q in self.parsed_ds_questions:
                        has_table = ds_q.get('has_table', False)
                        source_len = len(ds_q.get('source_text', ''))
                        print(f"   Câu {ds_q['number']}: has_table={has_table}, source_text={source_len} chars")
                        if has_table:
                            print(f"      Source preview: {ds_q.get('source_text', '')[:100]}...")
                
                if self.parsed_questions:
                    stats = self.question_parser.get_statistics()
                    print(f"  - Câu TN đầy đủ: {stats['complete_questions']}")
                    print(f"  - Phân bổ: {stats['by_level']}")
            
            return True
        except Exception as e:
            if self.verbose:
                print(f"✗ Lỗi khi load template DOCX: {str(e)}")
            raise
    
    @property
    def template_questions(self) -> List[Dict[str, Any]]:
        """Trả về danh sách câu hỏi TN template"""
        return self.parsed_questions
    
    @property
    def template_ds_questions(self) -> List[Dict[str, Any]]:
        """Trả về danh sách câu hỏi DS template"""
        return self.parsed_ds_questions
    
    def map_template_to_matrix(
        self,
        matrix_rows: List[Dict[str, Any]],
        mapping_mode: str = 'code'
    ) -> List[Dict[str, Any]]:
        """
        Mapping template câu hỏi với ma trận
        
        Args:
            matrix_rows: Danh sách hàng ma trận
            mapping_mode: 'code' (theo question_code), 'order' (theo thứ tự) hoặc 'smart' (theo level)
            
        Returns:
            List hàng ma trận đã mapping với template
        """
        if not self.parsed_questions:
            if self.verbose:
                print("⚠️  Chưa có câu hỏi template. Bỏ qua mapping.")
            return matrix_rows
        
        try:
            mapper = QuestionMatrixMapper(verbose=self.verbose)
            
            if mapping_mode == 'code':
                self.mapped_rows = mapper.map_by_question_code(
                    self.parsed_questions,
                    matrix_rows
                )
            elif mapping_mode == 'order':
                self.mapped_rows = mapper.map_by_order(
                    self.parsed_questions,
                    matrix_rows
                )
            else:  # smart
                self.mapped_rows = mapper.map_questions_to_matrix(
                    self.parsed_questions,
                    matrix_rows
                )
            
            if self.verbose:
                mapped_count = sum(1 for row in self.mapped_rows if row.get('question_template'))
                print(f"✓ Đã mapping template cho {mapped_count}/{len(matrix_rows)} hàng")
            
            return self.mapped_rows
            
        except Exception as e:
            if self.verbose:
                print(f"✗ Lỗi khi mapping: {str(e)}")
            raise
    
    def generate_with_template(
        self,
        generator: QuestionGenerator,
        matrix_rows: List[Dict[str, Any]],
        docx_template_path: Optional[str] = None,
        mapping_mode: str = 'smart'
    ) -> List[Any]:
        """
        Sinh câu hỏi với template từ DOCX
        
        Args:
            generator: QuestionGenerator instance
            matrix_rows: Danh sách hàng ma trận (có thể đã mapping hoặc chưa)
            docx_template_path: Đường dẫn file DOCX template (nếu chưa load)
            mapping_mode: Chế độ mapping
            
        Returns:
            List câu hỏi đã sinh
        """
        # Load template nếu cần
        if docx_template_path and not self.parsed_questions:
            self.load_template_docx(docx_template_path)
        
        # Mapping nếu cần
        if self.parsed_questions and not self.mapped_rows:
            matrix_rows = self.map_template_to_matrix(matrix_rows, mapping_mode)
        elif self.mapped_rows:
            matrix_rows = self.mapped_rows
        
        # Sinh câu hỏi
        all_questions = []
        
        for row in matrix_rows:
            # Lấy template cho hàng này
            question_template = row.get('question_template', '')
            
            # Tạo QuestionSpec từ row
            # Giả sử row có các field cần thiết
            spec = self._row_to_question_spec(row)
            
            if self.verbose:
                print(f"\n🔄 Sinh câu {spec.question_codes}")
                if question_template:
                    print(f"   📋 Có template ({len(question_template)} ký tự)")
                else:
                    print(f"   📋 Không có template")
            
            # Sinh câu hỏi với template
            questions = generator.generate_questions_for_spec(
                spec=spec,
                question_template=question_template
            )
            
            all_questions.extend(questions)
            
            if self.verbose:
                print(f"   ✓ Đã sinh {len(questions)} câu")
        
        return all_questions
    
    def _row_to_question_spec(self, row: Dict[str, Any]) -> QuestionSpec:
        """
        Chuyển đổi row ma trận sang QuestionSpec
        
        Args:
            row: Dict chứa thông tin hàng ma trận
            
        Returns:
            QuestionSpec
        """
        # Tùy thuộc vào cấu trúc row, tạo QuestionSpec phù hợp
        # Đây là ví dụ cơ bản
        from services.matrix_parser import QuestionSpec
        
        return QuestionSpec(
            question_codes=row.get('question_codes', [row.get('row_number', 'Q1')]),
            lesson_name=row.get('knowledge_content', row.get('lesson_name', '')),
            cognitive_level=row.get('cognitive_level', 'NB'),
            learning_outcome=row.get('expected_outcome', row.get('learning_outcome', '')),
            num_questions=row.get('num_questions', 1),
            question_type='TN'
        )


def generate_with_docx_template(
    generator: QuestionGenerator,
    matrix_rows: List[Dict[str, Any]],
    docx_template_path: Optional[str] = None,
    mapping_mode: str = 'smart',
    verbose: bool = False
) -> List[Any]:
    """
    Hàm tiện ích để sinh câu hỏi với template từ DOCX
    
    Args:
        generator: QuestionGenerator instance
        matrix_rows: Danh sách hàng ma trận
        docx_template_path: Đường dẫn file DOCX template
        mapping_mode: 'order' hoặc 'smart'
        verbose: Hiển thị log
        
    Returns:
        List câu hỏi đã sinh
    """
    gen_with_template = QuestionGeneratorWithTemplate(verbose=verbose)
    return gen_with_template.generate_with_template(
        generator=generator,
        matrix_rows=matrix_rows,
        docx_template_path=docx_template_path,
        mapping_mode=mapping_mode
    )
