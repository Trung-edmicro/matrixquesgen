"""
Module sinh câu hỏi tự động sử dụng Vertex AI
"""
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, asdict

from .matrix_parser import QuestionSpec, TrueFalseQuestionSpec
from .schemas import (
    get_multiple_choice_schema,
    get_multiple_choice_array_schema,
    get_true_false_schema
)

@dataclass
class GeneratedQuestion:
    """Câu hỏi đã được sinh"""
    question_code: str  # Mã câu (VD: C1)
    question_stem: str  # Nội dung câu hỏi
    options: Dict[str, str]  # Các lựa chọn A, B, C, D
    correct_answer: str  # Đáp án đúng
    level: str  # Cấp độ (NB/TH/VD/VDC)
    explanation: str  # Giải thích
    lesson_name: str  # Tên bài học
    question_type: str  # Loại câu hỏi (TN/DS/TLN)


@dataclass
class GeneratedTrueFalseQuestion:
    """Câu hỏi Đúng/Sai đã được sinh"""
    question_code: str  # Mã câu (VD: C1)
    source_text: str  # Đoạn tư liệu
    statements: Dict[str, Dict]  # 4 mệnh đề {a: {text, level, correct_answer}, ...}
    explanation: Dict[str, str]  # Giải thích cho mỗi mệnh đề {a: "...", b: "...", ...}
    lesson_name: str  # Tên bài học
    question_type: str = "DS"  # Loại câu hỏi


class QuestionGenerator:
    """Class sinh câu hỏi tự động"""
    
    def __init__(self, ai_client, prompt_template_path: str, verbose: bool = False, matrix_parser=None):
        """
        Khởi tạo Question Generator
        
        Args:
            ai_client: VertexAIClient đã được khởi tạo
            prompt_template_path: Đường dẫn đến file prompt template
            verbose: Hiển thị logs chi tiết
            matrix_parser: MatrixParser (optional) - để access SampleQuestionBank
        """
        self.ai_client = ai_client
        self.prompt_template = self._load_prompt_template(prompt_template_path)
        self.verbose = verbose
        self.max_retries = 3
        self.retry_delay = 2.0
        self.matrix_parser = matrix_parser
    
    def _load_prompt_template(self, template_path: str) -> str:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise Exception(f"Không thể đọc prompt template: {e}")
    
    def _fill_prompt_template(self, 
                             spec: QuestionSpec,
                             num_questions: int = None,
                             question_template: str = "",
                             content: str = "") -> str:
        """
        Điền thông tin vào prompt template
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            num_questions: Số câu hỏi cần sinh (nếu None, lấy từ spec)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            str: Prompt đã được điền
        """
        num = num_questions if num_questions is not None else spec.num_questions
        
        # Replace các biến trong template
        prompt = self.prompt_template.replace("{{NUM}}", str(num))
        prompt = prompt.replace("{{LESSON_NAME}}", spec.lesson_name)
        prompt = prompt.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
        prompt = prompt.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
        prompt = prompt.replace("{{QUESTION_TEMPLATE}}", question_template)
        prompt = prompt.replace("{{CONTENT}}", content if content else "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_")
        
        return prompt
    
    def generate_questions_for_spec(self, spec: QuestionSpec, 
                                   prompt_template_path: str = None,
                                   question_template: str = "",
                                   content: str = "") -> List[GeneratedQuestion]:
        """
        Sinh câu hỏi cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template (nếu khác với default)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            List[GeneratedQuestion]: Danh sách câu hỏi đã sinh
        """
        # Tự động lấy câu hỏi mẫu từ SampleQuestionBank nếu có
        print(f"\n🔍 DEBUG AUTO-FETCH TN:")
        print(f"   question_template empty? {not question_template}")
        print(f"   matrix_parser exists? {self.matrix_parser is not None}")
        if self.matrix_parser:
            print(f"   has_sample_questions()? {self.matrix_parser.has_sample_questions()}")
        
        if not question_template and self.matrix_parser and self.matrix_parser.has_sample_questions():
            print(f"   → Đang auto-fetch câu mẫu TN (lesson={spec.lesson_name}, type={spec.question_type}, level={spec.cognitive_level})")
            sample = self.matrix_parser.get_sample_question(
                spec.lesson_name,
                spec.question_type,
                spec.cognitive_level
            )
            print(f"   → Kết quả: {sample.stt if sample else 'None'}")
            if sample:
                question_template = sample.content
                print(f"✓ Sử dụng câu hỏi mẫu TN từ ngân hàng (STT {sample.stt}, {len(question_template)} chars)")
        else:
            print(f"   → Không auto-fetch (điều kiện không thỏa)")
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Tạo prompt cho tất cả câu
                prompt_text = template.replace("{{NUM}}", str(spec.num_questions))
                prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
                prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
                prompt_text = prompt_text.replace("{{CONTENT}}", content if content else "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_")
                
                # Thêm tài liệu bổ sung
                if spec.supplementary_materials:
                    supplementary_text = f"```\n{spec.supplementary_materials}\n```\n\n**✓ Có tài liệu bổ sung** - Hãy tham khảo các thông tin này khi tạo câu hỏi."
                else:
                    supplementary_text = "_Không có tài liệu bổ sung. Tự tổng hợp từ kiến thức INPUT DATA._"
                prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIALS}}", supplementary_text)

                # Debug: Kiểm tra content từ PDF
                # content_info = f"Content từ PDF: {len(content)} chars" if content else "❌ KHÔNG CÓ CONTENT TỪ PDF"
                # print(f"\n📤 Gửi prompt: {', '.join(spec.question_codes)} (NUM={spec.num_questions}, Template={len(question_template)} chars, {content_info})")
                # if content:
                #     print(f"📄 Preview content: {content[:200]}...")
                print(f"--- PROMPT START TN ---\nquestion_template: {question_template}\n--- PROMPT END ---")

                # Gọi AI với array schema
                response = self.ai_client.generate_content_with_schema(
                    prompt=prompt_text,
                    response_schema=get_multiple_choice_array_schema(),
                    enable_search=True
                )
                
                # Parse response
                data = json.loads(response) if isinstance(response, str) else response
                questions_data = data.get("questions", [])
                
                # Kiểm tra nếu không có câu hỏi nào được sinh
                if not questions_data or len(questions_data) == 0:
                    raise ValueError("AI không trả về câu hỏi nào")
                
                # Tạo GeneratedQuestion cho mỗi câu
                for i, question_data in enumerate(questions_data):
                    question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"Q{i+1}"
                    
                    question = GeneratedQuestion(
                        question_code=question_code,
                        question_stem=question_data.get("question_stem", ""),
                        options=question_data.get("options", {}),
                        correct_answer=question_data.get("correct_answer", ""),
                        level=question_data.get("level", spec.cognitive_level),
                        explanation=question_data.get("explanation", ""),
                        lesson_name=spec.lesson_name,
                        question_type=spec.question_type
                    )
                    
                    generated_questions.append(question)
                
                # Thành công, thoát retry loop
                break
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {str(e)[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    # Hết retry, throw error
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu hỏi sau {self.max_retries} lần thử: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Tạo dummy questions
            for question_code in spec.question_codes:
                question = GeneratedQuestion(
                    question_code=question_code,
                    question_stem=f"[LỖI] Không thể sinh câu hỏi: {str(e)}",
                    options={"A": "", "B": "", "C": "", "D": ""},
                    correct_answer="A",
                    level=spec.cognitive_level,
                    explanation=f"Lỗi: {str(e)}",
                    lesson_name=spec.lesson_name,
                    question_type=spec.question_type
                )
                generated_questions.append(question)
        
        return generated_questions
    
    def _fill_true_false_prompt(self, tf_spec: TrueFalseQuestionSpec, prompt_template: str, question_template: str = "", content: str = "") -> str:
        """
        Điền thông tin vào prompt template cho câu Đúng/Sai
        
        Args:
            tf_spec: TrueFalseQuestionSpec chứa 4 mệnh đề
            prompt_template: Template prompt DS
            question_template: Template câu hỏi mẫu từ DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            str: Prompt đã được điền
        """
        # Replace biến chung
        prompt = prompt_template.replace("{{NUM}}", "1")
        prompt = prompt.replace("{{LESSON_NAME}}", tf_spec.lesson_name)
        prompt = prompt.replace("{{QUESTION_TEMPLATE}}", question_template)
        prompt = prompt.replace("{{CONTENT}}", content if content else "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_")
        
        # Replace tài liệu bổ sung
        if tf_spec.supplementary_materials:
            supplementary_text = f"```\n{tf_spec.supplementary_materials}\n```\n\n**✓ Có tài liệu bổ sung** - Hãy ưu tiên sử dụng các thông tin từ tài liệu này để tạo đoạn tư liệu sinh động."
        else:
            supplementary_text = "_Không có tài liệu bổ sung. Tự tổng hợp từ kiến thức INPUT DATA._"
        prompt = prompt.replace("{{SUPPLEMENTARY_MATERIALS}}", supplementary_text)
        
        # Replace cho từng mệnh đề
        for stmt in tf_spec.statements:
            label_upper = stmt.label.upper()
            prompt = prompt.replace(f"{{{{COGNITIVE_LEVEL_{label_upper}}}}}", stmt.cognitive_level)
            prompt = prompt.replace(f"{{{{EXPECTED_LEARNING_OUTCOME_{label_upper}}}}}", stmt.learning_outcome)
        
        return prompt
    
    def generate_true_false_question(self, tf_spec: TrueFalseQuestionSpec, 
                                     prompt_template_path: str,
                                     question_template: str = "",
                                     content: str = "") -> GeneratedTrueFalseQuestion:
        """
        Sinh 1 câu hỏi Đúng/Sai hoàn chỉnh (4 mệnh đề cùng lúc)
        
        Args:
            tf_spec: TrueFalseQuestionSpec chứa 4 mệnh đề
            prompt_template_path: Đường dẫn đến prompt template DS
            question_template: Template câu hỏi mẫu từ DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            GeneratedTrueFalseQuestion: Câu hỏi DS đã sinh
        """
        # Tự động lấy câu hỏi mẫu DS từ SampleQuestionBank nếu có
        print(f"\n🔍 DEBUG AUTO-FETCH DS:")
        print(f"   question_template empty? {not question_template}")
        print(f"   matrix_parser exists? {self.matrix_parser is not None}")
        if self.matrix_parser:
            print(f"   has_sample_questions()? {self.matrix_parser.has_sample_questions()}")
        
        if not question_template and self.matrix_parser and self.matrix_parser.has_sample_questions():
            print(f"   → Đang auto-fetch câu mẫu DS (lesson={tf_spec.lesson_name}, type=DS, level=ALL)")
            # Đối với DS, lấy mẫu với cấp độ bất kỳ (vì 4 mệnh đề có cấp độ khác nhau)
            sample = self.matrix_parser.get_sample_question(
                tf_spec.lesson_name,
                "DS",
                "ALL"  # Lấy mẫu DS không phân biệt cấp độ
            )
            print(f"   → Kết quả: {sample.stt if sample else 'None'}")
            if sample:
                question_template = sample.content
                print(f"✓ Sử dụng câu hỏi mẫu DS từ ngân hàng (STT {sample.stt}, {len(question_template)} chars)")
        else:
            print(f"   → Không auto-fetch (điều kiện không thỏa)")
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Load prompt template DS
                with open(prompt_template_path, 'r', encoding='utf-8') as f:
                    ds_template = f.read()
                
                # Fill prompt với question_template và content
                prompt = self._fill_true_false_prompt(tf_spec, ds_template, question_template, content)
                
                # Debug: Kiểm tra content từ PDF
                # content_info = f"Content từ PDF: {len(content)} chars" if content else "❌ KHÔNG CÓ CONTENT TỪ PDF"
                # print(f"\n📤 Gửi prompt DS: {tf_spec.question_code} (Template={len(question_template)} chars, {content_info})")
                # if content:
                #     print(f"📄 Preview content: {content[:200]}...")
                print(f"--- PROMPT START DS ---\nquestion_template: {question_template}\n--- PROMPT END ---")
                
                # Gọi AI với JSON schema + Google Search
                response = self.ai_client.generate_content_with_schema(
                    prompt=prompt,
                    response_schema=get_true_false_schema(),
                    enable_search=True
                )
                
                # Kiểm tra response
                if not response or response.strip() == "":
                    raise ValueError("Response từ AI trống")
                
                # Response đã là JSON từ schema
                data = json.loads(response) if isinstance(response, str) else response
                
                # Kiểm tra dữ liệu cần thiết
                if not data.get("source_text") or not data.get("statements"):
                    raise ValueError("Response thiếu dữ liệu bắt buộc (source_text hoặc statements)")
                
                # Tạo GeneratedTrueFalseQuestion
                question = GeneratedTrueFalseQuestion(
                    question_code=tf_spec.question_code,
                    source_text=data.get("source_text", ""),
                    statements=data.get("statements", {}),
                    explanation=data.get("explanation", {}),
                    lesson_name=tf_spec.lesson_name
                )
                
                # Thành công, return
                return question
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {str(e)[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    # Hết retry, throw error
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu {tf_spec.question_code} sau {self.max_retries} lần thử: {e}")
                    raise
    
    def generate_questions_batch(self, 
                                specs: List[QuestionSpec],
                                output_dir: Optional[str] = None) -> Dict[str, List[GeneratedQuestion]]:
        """
        Sinh câu hỏi cho nhiều QuestionSpec
        
        Args:
            specs: Danh sách QuestionSpec
            output_dir: Thư mục lưu kết quả (nếu có)
            
        Returns:
            Dict[str, List[GeneratedQuestion]]: Dict với key là loại câu hỏi
        """
        print(f"\n{'#'*80}")
        print(f"BẮT ĐẦU SINH {len(specs)} NHÓM CÂU HỎI")
        print(f"{'#'*80}")
        
        all_questions = {}
        
        for idx, spec in enumerate(specs, 1):
            print(f"\n>>> Nhóm {idx}/{len(specs)}")
            
            questions = self.generate_questions_for_spec(spec)
            
            # Lưu theo loại câu hỏi
            question_type = spec.question_type
            if question_type not in all_questions:
                all_questions[question_type] = []
            
            all_questions[question_type].extend(questions)
        
        # Lưu kết quả nếu có output_dir
        if output_dir:
            self.save_questions_to_json(all_questions, output_dir)
        
        print(f"\n{'#'*80}")
        print(f"HOÀN THÀNH SINH CÂU HỎI")
        print(f"Tổng số câu: {sum(len(qs) for qs in all_questions.values())}")
        print(f"{'#'*80}")
        
        return all_questions
    
    def save_questions_to_json(self, 
                              questions: Dict[str, List[GeneratedQuestion]], 
                              output_dir: str):
        """
        Lưu câu hỏi ra file JSON
        
        Args:
            questions: Dict chứa câu hỏi theo loại
            output_dir: Thư mục output
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for question_type, question_list in questions.items():
            # Convert to dict
            questions_dict = [asdict(q) for q in question_list]
            
            # Tạo file name
            file_name = f"questions_{question_type}.json"
            file_path = output_path / file_name
            
            # Lưu file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(questions_dict, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Đã lưu {len(question_list)} câu hỏi {question_type} vào: {file_path}")
    
    def print_question_summary(self, question: GeneratedQuestion):
        """
        In tóm tắt một câu hỏi
        
        Args:
            question: GeneratedQuestion cần in
        """
        print(f"\n{'='*80}")
        print(f"[{question.question_code}] {question.question_stem}")
        print(f"{'-'*80}")
        for key, value in question.options.items():
            marker = " ← ĐÚNG" if key == question.correct_answer else ""
            print(f"  {key}. {value}{marker}")
        print(f"{'-'*80}")
        print(f"Cấp độ: {question.level} | Bài: {question.lesson_name}")
        print(f"Giải thích: {question.explanation[:100]}...")
        print(f"{'='*80}")
