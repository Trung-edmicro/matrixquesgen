"""
Module sinh câu hỏi tự động sử dụng Vertex AI
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, asdict

from .matrix_parser import QuestionSpec, TrueFalseQuestionSpec


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
    
    def __init__(self, ai_client, prompt_template_path: str):
        """
        Khởi tạo Question Generator
        
        Args:
            ai_client: VertexAIClient đã được khởi tạo
            prompt_template_path: Đường dẫn đến file prompt template
        """
        self.ai_client = ai_client
        self.prompt_template = self._load_prompt_template(prompt_template_path)
    
    def _load_prompt_template(self, template_path: str) -> str:
        """
        Đọc prompt template từ file
        
        Args:
            template_path: Đường dẫn đến file template
            
        Returns:
            str: Nội dung template
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✓ Đã tải prompt template từ: {template_path}")
            return content
        except Exception as e:
            raise Exception(f"Không thể đọc prompt template: {e}")
    
    def _fill_prompt_template(self, 
                             spec: QuestionSpec,
                             num_questions: int = None) -> str:
        """
        Điền thông tin vào prompt template
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            num_questions: Số câu hỏi cần sinh (nếu None, lấy từ spec)
            
        Returns:
            str: Prompt đã được điền
        """
        num = num_questions if num_questions is not None else spec.num_questions
        
        # Replace các biến trong template
        prompt = self.prompt_template.replace("{{NUM}}", str(num))
        prompt = prompt.replace("{{KNOWLEDGE_CONTENT}}", spec.lesson_name)
        prompt = prompt.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
        prompt = prompt.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
        
        return prompt
    
    def _get_multiple_choice_schema(self) -> Dict:
        """
        Trả về JSON schema cho câu hỏi Trắc nghiệm
        
        Returns:
            Dict: JSON schema
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
    
    def _get_multiple_choice_array_schema(self) -> Dict:
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
    
    def generate_questions_for_spec(self, spec: QuestionSpec, prompt_template_path: str = None) -> List[GeneratedQuestion]:
        """
        Sinh câu hỏi cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template (nếu khác với default)
            
        Returns:
            List[GeneratedQuestion]: Danh sách câu hỏi đã sinh
        """
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        print(f"\n{'='*80}")
        print(f"Đang sinh {spec.num_questions} câu hỏi {spec.question_type} - {spec.cognitive_level}")
        print(f"Bài: {spec.lesson_name}")
        print(f"Mã câu: {', '.join(spec.question_codes)}")
        print(f"{'='*80}")
        
        generated_questions = []
        
        try:
            # Tạo prompt cho tất cả câu
            prompt_text = template.replace("{{NUM}}", str(spec.num_questions))
            prompt_text = prompt_text.replace("{{KNOWLEDGE_CONTENT}}", spec.lesson_name)
            prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
            prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", spec.learning_outcome)
            
            print(f"\n🤖 Đang gọi AI để sinh {spec.num_questions} câu...")
            
            # Gọi AI với array schema
            response = self.ai_client.generate_content_with_schema(
                prompt=prompt_text,
                response_schema=self._get_multiple_choice_array_schema()
            )
            
            # Parse response
            data = json.loads(response) if isinstance(response, str) else response
            questions_data = data.get("questions", [])
            
            if len(questions_data) != spec.num_questions:
                print(f"⚠️ AI trả về {len(questions_data)} câu, mong đợi {spec.num_questions}")
            
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
                print(f"  ✓ Câu {i+1}/{len(questions_data)}: {question_code}")
            
            print(f"\n✅ Đã sinh {len(generated_questions)} câu")
            
        except Exception as e:
            print(f"\n❌ Lỗi khi sinh câu hỏi: {e}")
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
    
    def _fill_true_false_prompt(self, tf_spec: TrueFalseQuestionSpec, prompt_template: str) -> str:
        """
        Điền thông tin vào prompt template cho câu Đúng/Sai
        
        Args:
            tf_spec: TrueFalseQuestionSpec chứa 4 mệnh đề
            prompt_template: Template prompt DS
            
        Returns:
            str: Prompt đã được điền
        """
        print("\n" + "="*80)
        print("📝 CHUẨN BỊ PROMPT ĐÚNG/SAI")
        print("="*80)
        
        print(f"📌 Câu: {tf_spec.question_code}")
        print(f"📌 Bài học: {tf_spec.lesson_name}")
        print(f"📌 Số mệnh đề: {len(tf_spec.statements)}")
        
        # Replace biến chung
        prompt = prompt_template.replace("{{NUM}}", "1")
        prompt = prompt.replace("{{KNOWLEDGE_CONTENT}}", tf_spec.lesson_name)
        
        # Replace cho từng mệnh đề
        for stmt in tf_spec.statements:
            label_upper = stmt.label.upper()
            prompt = prompt.replace(f"{{{{COGNITIVE_LEVEL_{label_upper}}}}}", stmt.cognitive_level)
            prompt = prompt.replace(f"{{{{EXPECTED_LEARNING_OUTCOME_{label_upper}}}}}", stmt.learning_outcome)
            
            print(f"  ({stmt.label}) [{stmt.cognitive_level}] {stmt.statement_code}")
            print(f"      {stmt.learning_outcome[:80]}...")
        
        print("-" * 80)
        return prompt
    
    def _get_true_false_schema(self) -> Dict:
        """
        Trả về JSON schema cho câu hỏi Đúng/Sai
        
        Returns:
            Dict: JSON schema
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
    
    def generate_true_false_question(self, tf_spec: TrueFalseQuestionSpec, 
                                     prompt_template_path: str) -> GeneratedTrueFalseQuestion:
        """
        Sinh 1 câu hỏi Đúng/Sai hoàn chỉnh (4 mệnh đề cùng lúc)
        
        Args:
            tf_spec: TrueFalseQuestionSpec chứa 4 mệnh đề
            prompt_template_path: Đường dẫn đến prompt template DS
            
        Returns:
            GeneratedTrueFalseQuestion: Câu hỏi DS đã sinh
        """
        print(f"\n{'='*80}")
        print(f"🎯 SINH CÂU HỎI ĐÚNG/SAI: {tf_spec.question_code}")
        print(f"{'='*80}")
        print(f"📚 Bài: {tf_spec.lesson_name}")
        print(f"🔢 Số mệnh đề: {len(tf_spec.statements)}")
        print(f"{'='*80}")
        
        try:
            # Load prompt template DS
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                ds_template = f.read()
            
            # Fill prompt
            prompt = self._fill_true_false_prompt(tf_spec, ds_template)
            
            # Gọi AI với JSON schema
            print("\n🤖 Đang gọi AI để sinh câu hỏi...")
            response = self.ai_client.generate_content_with_schema(
                prompt=prompt,
                response_schema=self._get_true_false_schema()
            )
            
            print(f"✅ Đã nhận response từ AI")
            print(f"📄 Response preview: {response[:200] if response else '(empty)'}...")
            
            # Kiểm tra response
            if not response or response.strip() == "":
                raise ValueError("Response từ AI trống")
            
            # Response đã là JSON từ schema
            data = json.loads(response) if isinstance(response, str) else response
            
            # Tạo GeneratedTrueFalseQuestion
            question = GeneratedTrueFalseQuestion(
                question_code=tf_spec.question_code,
                source_text=data.get("source_text", ""),
                statements=data.get("statements", {}),
                explanation=data.get("explanation", {}),
                lesson_name=tf_spec.lesson_name
            )
            
            print(f"\n✅ Đã sinh câu {tf_spec.question_code}")
            print(f"📖 Tư liệu: {question.source_text[:100]}...")
            print(f"📋 Mệnh đề:")
            for label in ['a', 'b', 'c', 'd']:
                if label in question.statements:
                    stmt = question.statements[label]
                    status = "✓ Đúng" if stmt.get('correct_answer') else "✗ Sai"
                    print(f"  ({label}) [{stmt.get('level')}] {status}: {stmt.get('text', '')[:60]}...")
            
            return question
            
        except Exception as e:
            print(f"\n❌ Lỗi khi sinh câu {tf_spec.question_code}: {e}")
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
