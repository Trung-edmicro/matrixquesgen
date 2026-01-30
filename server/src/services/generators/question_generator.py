"""
Module sinh câu hỏi tự động sử dụng Vertex AI
"""
import json
import re
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, asdict

from ..core.matrix_parser import QuestionSpec, TrueFalseQuestionSpec
from ..core.schemas import (
    get_multiple_choice_array_schema,
    get_true_false_schema,
    get_short_answer_array_schema,
    get_essay_array_schema
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
    # Metadata fields for source citation (REQUIRED per schema)
    source_citation: str = ""  # Trích dẫn nguồn học thuật
    source_origin: str = ""  # Loại nguồn (academic_journal/scholarly_book/official_document/reputable_media)
    source_type: str = ""  # Loại tư liệu (primary_source/historical_description/analytical_summary/contextual_scenario)
    pedagogical_approach: str = ""  # Cách tiếp cận sư phạm
    search_evidence: str = ""  # Ghi chú quá trình tìm kiếm


@dataclass
class GeneratedEssayQuestion:
    """Câu hỏi Tự luận đã được sinh"""
    question_code: str  # Mã câu (VD: C1)
    question_stem: str  # Nội dung câu hỏi
    question_type: str  # Loại câu hỏi tự luận (analysis/comparison/evaluation/explanation/synthesis/argumentation)
    historical_context: str  # Bối cảnh lịch sử (optional)
    required_elements: List[str]  # Các yếu tố bắt buộc
    answer_structure: Dict  # Cấu trúc câu trả lời mong đợi
    sample_answer: str  # Câu trả lời mẫu
    key_points: List[Dict]  # Các điểm kiến thức then chốt
    scoring_rubric: Dict  # Thang điểm chi tiết
    level: str  # Cấp độ (NB/TH/VD/VDC)
    lesson_name: str  # Tên bài học
    question_type_main: str = "TL"  # Loại câu hỏi chính
    chapter_number: int = 0  # Số chương
    lesson_number: int = 0  # Số bài


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
        self.max_retries = 5
        self.retry_delay = 5.0
        self.matrix_parser = matrix_parser
        self.fallback_model = os.getenv('GEMINI_FALLBACK_MODEL')
    
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
    
    def _format_rich_content_types(self, spec: QuestionSpec) -> str:
        """
        Format rich content types for prompt injection
        
        Args:
            spec: QuestionSpec with optional rich_content_types attribute
            
        Returns:
            Formatted string describing required rich content types
        """
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return """**YÊU CẦU NỘI DUNG**: Câu hỏi này không có đánh dấu BD/BK/HA trong ma trận.
⏩ **BẮT BUỘC**: Chỉ dùng **text thuần** (type="text"), KHÔNG dùng table/chart/image/mixed.
⏩ question_stem PHẢI là: {"type": "text", "content": "..."}"""
        
        lines = ["**YÊU CẦU:** Các câu hỏi sau cần tạo với loại nội dung đặc biệt (RICH CONTENT):"]
        for code, types in spec.rich_content_types.items():
            type_list = []
            for t in types:
                if isinstance(t, dict):
                    # Format: {"code": "BK", "name": "Bảng khảo, bảng số liệu", "description": "..."}
                    type_name = f"{t['code']} - {t['name']}"
                else:
                    # Just string like "BK"
                    type_name = t
                type_list.append(type_name)
            lines.append(f"  • Câu **{code}**: {', '.join(type_list)}")
        
        lines.append("")
        lines.append("⚠️ **QUAN TRỌNG**: Đối với các câu có yêu cầu rich content:")
        lines.append("- question_stem PHẢI có cấu trúc: {type: 'table'/'chart'/'image', content: {...}}")
        lines.append("- KHÔNG dùng {type: 'text', content: '...'} cho những câu này")
        lines.append("- Tham khảo schema để tạo đúng cấu trúc table/chart/image")
        
        return "\n".join(lines)
    
    def _format_rich_content_types_tf(self, spec: TrueFalseQuestionSpec) -> str:
        """
        Format rich content types for True/False questions
        
        Args:
            spec: TrueFalseQuestionSpec with optional rich_content_types attribute
            
        Returns:
            Formatted string describing required rich content types
        """
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return """**YÊU CẦU NỘI DUNG**: Câu hỏi này không có đánh dấu BD/BK/HA trong ma trận.
⏩ **BẮT BUỘC**: Chỉ dùng **text thuần** (type="text") cho source_text, KHÔNG dùng table/chart/image/mixed.
⏩ source_text PHẢI là: {"type": "text", "content": "..."}"""
        
        lines = ["**YÊU CẦU:** Câu hỏi này cần tạo với loại nội dung đặc biệt (RICH CONTENT):"]
        for code, types in spec.rich_content_types.items():
            type_list = []
            for t in types:
                if isinstance(t, dict):
                    type_name = f"{t['code']} - {t['name']}"
                else:
                    type_name = t
                type_list.append(type_name)
            lines.append(f"  • {', '.join(type_list)}")
        
        lines.append("")
        lines.append("⚠️ **QUAN TRỌNG**: Đối với câu hỏi có yêu cầu rich content:")
        lines.append("- source_text PHẢI có cấu trúc: {type: 'table'/'chart'/'image', content: {...}}")
        lines.append("- KHÔNG dùng {type: 'text', content: '...'}")
        lines.append("- Tham khảo schema để tạo đúng cấu trúc table/chart/image")
        
        return "\n".join(lines)
    
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
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        last_error = None
        tried_fallback = False
        
        # Retry logic với fallback model
        for attempt in range(self.max_retries):
            try:
                # Tạo prompt cho tất cả câu
                prompt_text = template.replace("{{NUM}}", str(spec.num_questions))
                prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
                prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
                prompt_text = prompt_text.replace("{{CONTENT}}", content if content else "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_")
                
                # Format rich_content_types if available
                rich_content_str = self._format_rich_content_types(spec)
                prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", rich_content_str)
                
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
                    # print(f"📄 Preview content: {content[:200]}...")
                # print(f"--- PROMPT START TN ---\n{prompt_text}\n--- PROMPT END ---")

                # Gọi AI với array schema - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt_text,
                        response_schema=get_multiple_choice_array_schema(),
                        model_name=self.fallback_model,
                        enable_search=True
                    )
                else:
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
                
                # VALIDATION: Nếu không có rich_content_types, cưỡng chế chuyển sang text-only
                if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
                    for q_data in questions_data:
                        if 'question_stem' in q_data and isinstance(q_data['question_stem'], dict):
                            if q_data['question_stem'].get('type') != 'text':
                                print(f"⚠️  FORCE TEXT-ONLY: Câu {q_data.get('question_code', '?')} có type={q_data['question_stem'].get('type')}, chuyển sang text")
                                # Chuyển sang text thuần
                                if q_data['question_stem'].get('type') == 'mixed':
                                    # Trích xuất text từ mixed
                                    content = q_data['question_stem'].get('content', [])
                                    text_parts = [item if isinstance(item, str) else '' for item in content]
                                    q_data['question_stem'] = {"type": "text", "content": ' '.join(text_parts).strip()}
                                else:
                                    # Có thể là table/chart/image, không thể chuyển đổi -> reject
                                    raise ValueError(f"Câu hỏi có rich content không mong muốn (type={q_data['question_stem'].get('type')}) khi ma trận không yêu cầu")
                
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
                last_error = e
                error_str = str(e)
                
                # Kiểm tra nếu là lỗi 429 và chưa thử fallback
                is_rate_limit = "429" in error_str and "RESOURCE_EXHAUSTED" in error_str
                
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                elif is_rate_limit and not tried_fallback:
                    # Thử fallback model
                    tried_fallback = True
                    print(f"🔄 Hết {self.max_retries} lần thử với model chính, chuyển sang fallback model: {self.fallback_model}")
                    # Reset attempt counter cho fallback
                    attempt = -1  # Sẽ tăng lên 0 ở vòng lặp tiếp theo
                    continue
                else:
                    # Hết retry và hết fallback, tạo dummy questions
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu hỏi sau {self.max_retries} lần thử")
                        if tried_fallback:
                            print(f"   (đã thử cả fallback model {self.fallback_model})")
                        print(f"   Error: {error_str}")
                        import traceback
                        traceback.print_exc()
                    
                    # Tạo dummy questions với error message
                    error_msg = f"Lỗi sinh câu hỏi: {error_str}"
                    for question_code in spec.question_codes:
                        question = GeneratedQuestion(
                            question_code=question_code,
                            question_stem=error_msg,
                            options={"A": "", "B": "", "C": "", "D": ""},
                            correct_answer="A",
                            level=spec.cognitive_level,
                            explanation=f"Lỗi: {error_str}",
                            lesson_name=spec.lesson_name,
                            question_type=spec.question_type
                        )
                        generated_questions.append(question)
                    break  # Thoát loop sau khi tạo dummy questions
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
        
        # Format rich_content_types if available
        rich_content_str = self._format_rich_content_types_tf(tf_spec)
        prompt = prompt.replace("{{RICH_CONTENT_TYPES}}", rich_content_str)
        
        # Replace tài liệu bổ sung
        if tf_spec.supplementary_materials:
            supplementary_text = f"```\n{tf_spec.supplementary_materials}\n```\n\n**✓ Có tài liệu bổ sung** - Hãy ưu tiên sử dụng các thông tin từ tài liệu này để tạo đoạn tư liệu sinh động."
        else:
            supplementary_text = "_Không có tài liệu bổ sung. Tự tổng hợp từ kiến thức INPUT DATA._"
        prompt = prompt.replace("{{SUPPLEMENTARY_MATERIALS}}", supplementary_text)
        prompt = prompt.replace("{{MATERIALS}}", tf_spec.supplementary_materials or "")
        
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
        tried_fallback = False
        
        # Retry logic với fallback model với fallback model
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
                # print(f"--- PROMPT START DS ---\n{prompt}\n--- PROMPT END ---")
                # print("content", content)
                # print("question_template:", question_template)

                # Gọi AI với JSON schema + Google Search - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt,
                        response_schema=get_true_false_schema(),
                        model_name=self.fallback_model,
                        enable_search=True
                    )
                else:
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
                
                # Clean statements - remove reasoning_type if present
                statements = data.get("statements", {})
                for key in statements:
                    if 'reasoning_type' in statements[key]:
                        del statements[key]['reasoning_type']
                
                # DEBUG: Kiểm tra source_citation
                source_citation = data.get("source_citation", "")
                source_origin = data.get("source_origin", "")
                if not source_citation or not source_origin:
                    print(f"⚠️  DS {tf_spec.question_code}: Thiếu source_citation={bool(source_citation)}, source_origin={bool(source_origin)}")
                    print(f"   AI Response keys: {list(data.keys())}")
                    # FALLBACK: Tạo citation mặc định nếu thiếu
                    if not source_citation:
                        source_citation = "(Nguồn: SGK Lịch sử 12, Chương trình Kết nối tri thức, 2024)"
                        print(f"   ➡️  Sử dụng citation mặc định")
                    if not source_origin:
                        source_origin = "scholarly_book"  # Default to textbook
                        print(f"   ➡️  Sử dụng origin mặc định: {source_origin}")
                
                # VALIDATION: Nếu không có rich_content_types, force text-only cho source_text
                source_text = data.get("source_text", "")
                if not hasattr(tf_spec, 'rich_content_types') or not tf_spec.rich_content_types:
                    if isinstance(source_text, dict) and source_text.get('type') != 'text':
                        print(f"⚠️  FORCE TEXT-ONLY DS: source_text có type={source_text.get('type')}, chuyển sang text")
                        if source_text.get('type') == 'mixed':
                            content = source_text.get('content', [])
                            text_parts = [item if isinstance(item, str) else '' for item in content]
                            source_text = {"type": "text", "content": ' '.join(text_parts).strip()}
                        else:
                            raise ValueError(f"DS source_text có rich content không mong muốn (type={source_text.get('type')})")
                
                # Tạo GeneratedTrueFalseQuestion với tất cả metadata fields
                question = GeneratedTrueFalseQuestion(
                    question_code=tf_spec.question_code,
                    source_text=source_text,
                    statements=statements,
                    explanation=data.get("explanation", {}),
                    lesson_name=tf_spec.lesson_name,
                    source_citation=source_citation,
                    source_origin=source_origin,
                    source_type=data.get("source_type", ""),
                    pedagogical_approach=data.get("pedagogical_approach", ""),
                    search_evidence=data.get("search_evidence", "")
                )
                
                return question
                
            except Exception as e:
                error_str = str(e)
                
                # Kiểm tra nếu là lỗi 429 và chưa thử fallback
                is_rate_limit = "429" in error_str and "RESOURCE_EXHAUSTED" in error_str
                
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                elif is_rate_limit and not tried_fallback:
                    # Thử fallback model
                    tried_fallback = True
                    print(f"🔄 Hết {self.max_retries} lần thử với model chính, chuyển sang fallback model: {self.fallback_model}")
                    # Reset attempt counter cho fallback
                    attempt = -1  # Sẽ tăng lên 0 ở vòng lặp tiếp theo
                    continue
                else:
                    # Hết retry và hết fallback, tạo dummy question
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu {tf_spec.question_code} sau {self.max_retries} lần thử")
                        if tried_fallback:
                            print(f"   (đã thử cả fallback model {self.fallback_model})")
                        print(f"   Error: {error_str}")
                        import traceback
                        traceback.print_exc()
                    
                    # Tạo dummy DS question với error message trong source_text
                    error_msg = f"Lỗi sinh câu hỏi: {error_str}"
                    question = GeneratedTrueFalseQuestion(
                        question_code=tf_spec.question_code,
                        source_text=error_msg,
                        statements={},
                        explanation={},
                        lesson_name=tf_spec.lesson_name
                    )
                    return question
    
    def generate_tln_questions(self, 
                              spec: QuestionSpec,
                              prompt_template_path: str = None,
                              question_template: str = "",
                              content: str = "") -> List[GeneratedQuestion]:
        """
        Sinh câu hỏi TLN (Trắc nghiệm luận) cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template TLN (nếu khác với default)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            List[GeneratedQuestion]: Danh sách câu hỏi TLN đã sinh
        """        
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        last_error = None
        tried_fallback = False
        
        # Retry logic với fallback model
        for attempt in range(self.max_retries):
            try:
                # Tạo prompt cho tất cả câu TLN
                prompt_text = template.replace("{{NUM}}", str(spec.num_questions))
                prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
                prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
                prompt_text = prompt_text.replace("{{CONTENT}}", content if content else "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_")
                
                # Format rich_content_types if available
                rich_content_str = self._format_rich_content_types(spec)
                prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", rich_content_str)
                
                # Thêm tài liệu bổ sung
                if spec.supplementary_materials:
                    supplementary_text = f"```\n{spec.supplementary_materials}\n```\n\n**✓ Có tài liệu bổ sung** - Hãy tham khảo các thông tin này khi tạo câu hỏi."
                else:
                    supplementary_text = "_Không có tài liệu bổ sung. Tự tổng hợp từ kiến thức INPUT DATA._"
                prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIALS}}", supplementary_text)

                # Gọi AI với TLN array schema - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt_text,
                        response_schema=get_short_answer_array_schema(),
                        model_name=self.fallback_model,
                        enable_search=True
                    )
                else:
                    response = self.ai_client.generate_content_with_schema(
                        prompt=prompt_text,
                        response_schema=get_short_answer_array_schema(),
                        enable_search=True
                    )
                
                # Parse response
                data = json.loads(response) if isinstance(response, str) else response
                questions_data = data.get("questions", [])
                
                # Kiểm tra nếu không có câu hỏi nào được sinh
                if not questions_data or len(questions_data) == 0:
                    raise ValueError("AI không trả về câu hỏi nào")
                
                # Tạo GeneratedQuestion cho mỗi câu TLN
                for i, question_data in enumerate(questions_data):
                    question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"Q{i+1}"
                    
                    # TLN không có options (A/B/C/D), chỉ có correct_answer
                    question = GeneratedQuestion(
                        question_code=question_code,
                        question_stem=question_data.get("question_stem", ""),
                        options={},  # Empty dict for TLN
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
                last_error = e
                error_str = str(e)
                
                # Kiểm tra nếu là lỗi 429 và chưa thử fallback
                is_rate_limit = "429" in error_str and "RESOURCE_EXHAUSTED" in error_str
                
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                elif is_rate_limit and not tried_fallback:
                    # Thử fallback model
                    tried_fallback = True
                    print(f"🔄 Hết {self.max_retries} lần thử với model chính, chuyển sang fallback model: {self.fallback_model}")
                    # Reset attempt counter cho fallback
                    attempt = -1  # Sẽ tăng lên 0 ở vòng lặp tiếp theo
                    continue
                else:
                    # Hết retry và hết fallback, tạo dummy questions
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu hỏi TLN sau {self.max_retries} lần thử")
                        if tried_fallback:
                            print(f"   (đã thử cả fallback model {self.fallback_model})")
                        print(f"   Error: {error_str}")
                        import traceback
                        traceback.print_exc()
                    
                    # Tạo dummy questions với error message
                    error_msg = f"Lỗi sinh câu hỏi: {error_str}"
                    for question_code in spec.question_codes:
                        question = GeneratedQuestion(
                            question_code=question_code,
                            question_stem=error_msg,
                            options={},  # Empty for TLN
                            correct_answer="",
                            level=spec.cognitive_level,
                            explanation=f"Lỗi: {error_str}",
                            lesson_name=spec.lesson_name,
                            question_type=spec.question_type
                        )
                        generated_questions.append(question)
                    break  # Thoát loop sau khi tạo dummy questions
        
        return generated_questions

    def generate_tl_questions(self, 
                             spec: QuestionSpec,
                             prompt_template_path: str = None,
                             question_template: str = "",
                             content: str = "") -> List[GeneratedEssayQuestion]:
        """
        Sinh câu hỏi TL (Tự luận) cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template TL (nếu khác với default)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            List[GeneratedEssayQuestion]: Danh sách câu hỏi TL đã sinh
        """        
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        last_error = None
        tried_fallback = False
        
        # Retry logic với fallback model
        for attempt in range(self.max_retries):
            try:
                # Tạo prompt cho tất cả câu TL
                prompt_text = template.replace("{{NUM}}", str(spec.num_questions))
                prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
                prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
                prompt_text = prompt_text.replace("{{CONTENT}}", content if content else "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_")
                
                # Format rich_content_types if available
                rich_content_str = self._format_rich_content_types(spec)
                prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", rich_content_str)
                
                # Thêm tài liệu bổ sung
                if spec.supplementary_materials:
                    supplementary_text = f"```\n{spec.supplementary_materials}\n```\n\n**✓ Có tài liệu bổ sung** - Hãy tham khảo các thông tin này khi tạo câu hỏi."
                else:
                    supplementary_text = "_Không có tài liệu bổ sung. Tự tổng hợp từ kiến thức INPUT DATA._"
                prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIALS}}", supplementary_text)
                
                if self.verbose:
                    print(f"📝 Generating {spec.num_questions} TL questions for lesson: {spec.lesson_name}")
                    print(f"🎯 Cognitive level: {spec.cognitive_level}")
                
                # Gọi AI với TL array schema - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt_text,
                        response_schema=get_essay_array_schema(),
                        model_name=self.fallback_model,
                        enable_search=True
                    )
                else:
                    response = self.ai_client.generate_content_with_schema(
                        prompt=prompt_text,
                        response_schema=get_essay_array_schema(),
                        enable_search=True
                    )
                
                # Parse response
                data = json.loads(response) if isinstance(response, str) else response
                questions_data = data.get("questions", [])
                
                # Kiểm tra nếu không có câu hỏi nào được sinh
                if not questions_data or len(questions_data) == 0:
                    raise ValueError("AI không trả về câu hỏi nào")
                
                # Tạo GeneratedEssayQuestion cho mỗi câu TL
                for i, question_data in enumerate(questions_data):
                    question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"TL{spec.row_index + 1 + i}"
                    
                    question = GeneratedEssayQuestion(
                        question_code=question_code,
                        question_stem=question_data.get("question_stem", ""),
                        question_type=question_data.get("question_type", "analysis"),
                        historical_context=question_data.get("historical_context", ""),
                        required_elements=question_data.get("required_elements", []),
                        answer_structure=question_data.get("answer_structure", {}),
                        sample_answer=question_data.get("sample_answer", ""),
                        key_points=question_data.get("key_points", []),
                        scoring_rubric=question_data.get("scoring_rubric", {}),
                        level=spec.cognitive_level,
                        lesson_name=spec.lesson_name
                    )
                    generated_questions.append(question)
                    
                    if self.verbose:
                        print(f"✅ Generated TL question {i+1}/{len(questions_data)}: {question.question_stem[:50]}...")
                
                # Thành công, thoát loop
                break
                
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                
                if self.verbose:
                    print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str}")
                
                # Thử fallback model nếu chưa thử và còn attempt
                if not tried_fallback and attempt < self.max_retries - 1 and self.fallback_model:
                    if self.verbose:
                        print(f"🔄 Thử fallback model: {self.fallback_model}")
                    tried_fallback = True
                    # Temporarily change model
                    original_model = self.ai_client.model_name
                    self.ai_client.model_name = self.fallback_model
                    
                    try:
                        # Retry with fallback model using array schema
                        response = self.ai_client.generate_content_with_schema_with_model(
                            prompt=prompt_text,
                            response_schema=get_essay_array_schema(),
                            model_name=self.fallback_model,
                            enable_search=True
                        )
                        
                        # Parse response
                        data = json.loads(response) if isinstance(response, str) else response
                        questions_data = data.get("questions", [])
                        
                        if not questions_data or len(questions_data) == 0:
                            raise ValueError("AI không trả về câu hỏi nào với fallback model")
                        
                        # Tạo GeneratedEssayQuestion cho mỗi câu TL
                        for i, question_data in enumerate(questions_data):
                            question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"TL{spec.row_index + 1 + i}"
                            
                            question = GeneratedEssayQuestion(
                                question_code=question_code,
                                question_stem=question_data.get("question_stem", ""),
                                question_type=question_data.get("question_type", "analysis"),
                                historical_context=question_data.get("historical_context", ""),
                                required_elements=question_data.get("required_elements", []),
                                answer_structure=question_data.get("answer_structure", {}),
                                sample_answer=question_data.get("sample_answer", ""),
                                key_points=question_data.get("key_points", []),
                                scoring_rubric=question_data.get("scoring_rubric", {}),
                                level=spec.cognitive_level,
                                lesson_name=spec.lesson_name
                            )
                            generated_questions.append(question)
                            
                            if self.verbose:
                                print(f"✅ Generated TL question {i+1}/{len(questions_data)} with fallback: {question.question_stem[:50]}...")
                        
                        # Thành công với fallback, thoát loop
                        break
                        
                    except Exception as fallback_e:
                        if self.verbose:
                            print(f"❌ Fallback cũng thất bại: {str(fallback_e)}")
                        # Restore original model
                        self.ai_client.model_name = original_model
                        continue
                    
                    # Restore original model
                    self.ai_client.model_name = original_model
                
                # Chờ trước khi retry
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # Nếu tất cả attempts thất bại, tạo dummy question
        if not generated_questions:
            if self.verbose:
                print(f"❌ Tất cả {self.max_retries} lần thử đều thất bại. Tạo dummy TL question.")
            
            for i in range(spec.num_questions):
                question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"TL{spec.row_index + 1 + i}"
                question = GeneratedEssayQuestion(
                    question_code=question_code,
                    question_stem=f"Câu hỏi tự luận cho bài: {spec.lesson_name} (Cognitive level: {spec.cognitive_level})",
                    question_type="analysis",
                    historical_context="",
                    required_elements=["Nguyên nhân", "Diễn biến", "Ý nghĩa"],
                    answer_structure={
                        "introduction": "Giới thiệu vấn đề",
                        "body": ["Nguyên nhân", "Diễn biến", "Ý nghĩa"],
                        "conclusion": "Kết luận và bài học"
                    },
                    sample_answer="Đây là câu trả lời mẫu cho câu hỏi tự luận.",
                    key_points=[
                        {"point": "Nguyên nhân", "weight": 3, "description": "Phân tích nguyên nhân"},
                        {"point": "Diễn biến", "weight": 4, "description": "Mô tả diễn biến"},
                        {"point": "Ý nghĩa", "weight": 3, "description": "Đánh giá ý nghĩa"}
                    ],
                    scoring_rubric={
                        "excellent": "Trả lời đầy đủ, logic, có dẫn chứng (9-10 điểm)",
                        "good": "Trả lời khá đầy đủ, có lập luận (7-8 điểm)",
                        "average": "Trả lời cơ bản, thiếu lập luận (5-6 điểm)",
                        "weak": "Trả lời sai hoặc thiếu nhiều (dưới 5 điểm)"
                    },
                    level=spec.cognitive_level,
                    lesson_name=spec.lesson_name
                )
                generated_questions.append(question)
        
        return generated_questions

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
        
    def generate_questions_with_custom_prompt(self, prompt_template: str, content: str, num_questions: int) -> List[GeneratedQuestion]:
        """
        Generate questions using a custom prompt template
        
        Args:
            prompt_template: The full prompt template with placeholders already filled
            content: Lesson content
            num_questions: Number of questions to generate
            
        Returns:
            List[GeneratedQuestion]: Generated questions
        """
        try:
            # Call AI with the custom prompt
            response = self.ai_client.generate_content_with_schema(
                prompt=prompt_template,
                response_schema=get_multiple_choice_array_schema(),
                enable_search=True
            )
            
            # Validate response
            if not response:
                print("❌ AI returned empty response")
                return []
            
            # Check if response is truncated (common sign: doesn't end with } or ])
            response_str = response if isinstance(response, str) else str(response)
            if not response_str.rstrip().endswith('}') and not response_str.rstrip().endswith(']'):
                print(f"⚠️ Response appears truncated (length: {len(response_str)})")
                print(f"⚠️ Response ends with: ...{response_str[-100:]}")
            
            # Parse response
            data = json.loads(response) if isinstance(response, str) else response
            questions_data = data.get("questions", [])
            
            generated_questions = []
            for i, question_data in enumerate(questions_data):
                question_code = f"C{i+1}"
                
                question = GeneratedQuestion(
                    question_code=question_code,
                    question_stem=question_data.get("question_stem", ""),
                    options=question_data.get("options", {}),
                    correct_answer=question_data.get("correct_answer", ""),
                    level=question_data.get("level", "medium"),
                    explanation=question_data.get("explanation", ""),
                    lesson_name="",  # Will be set by caller
                    question_type="TN"
                )
                
                generated_questions.append(question)
            
            return generated_questions
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"❌ Raw response: {response[:500] if response else 'None'}")
            return []
        except Exception as e:
            print(f"❌ Error generating questions with custom prompt: {e}")
            return []
    
    def generate_ds_with_custom_prompt(self, prompt_template: str, content: str, question_code: str) -> Optional[GeneratedTrueFalseQuestion]:
        """
        Generate DS question using a custom prompt template
        
        Args:
            prompt_template: The full prompt template with placeholders already filled
            content: Lesson content
            question_code: Question code for the DS question
            
        Returns:
            GeneratedTrueFalseQuestion or None
        """
        try:
            # Call AI with the custom prompt
            response = self.ai_client.generate_content_with_schema(
                prompt=prompt_template,
                response_schema=get_true_false_schema(),
                enable_search=True
            )
            
            # Debug: Log response
            print(f"🔍 DEBUG DS: AI Response length: {len(response) if response else 0}")
            if response:
                print(f"🔍 DEBUG DS: AI Response preview: {response[:200]}...")
            else:
                print("🔍 DEBUG DS: AI Response is empty!")
            
            # Parse response
            data = json.loads(response) if isinstance(response, str) else response
            
            # Create GeneratedTrueFalseQuestion with all metadata fields
            question = GeneratedTrueFalseQuestion(
                question_code=question_code,
                source_text=data.get("source_text", ""),
                statements=data.get("statements", {}),
                explanation=data.get("explanation", {}),
                lesson_name="",  # Will be set by caller
                question_type="DS",
                source_citation=data.get("source_citation", ""),
                source_origin=data.get("source_origin", ""),
                source_type=data.get("source_type", ""),
                pedagogical_approach=data.get("pedagogical_approach", ""),
                search_evidence=data.get("search_evidence", "")
            )
            
            return question
            
        except json.JSONDecodeError as e:
            print(f"❌ DS JSON Parse Error: {e}")
            print(f"❌ DS Raw response: {response[:500] if response else 'None'}")
            return None
        except Exception as e:
            print(f"❌ Error generating DS question with custom prompt: {e}")
            return None
        
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
