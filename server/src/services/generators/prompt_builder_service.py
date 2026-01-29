"""
Prompt Builder Service
Maps PDF content to prompt templates for question generation
"""
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ..core.matrix_parser import MatrixParser, QuestionSpec, TrueFalseQuestionSpec


@dataclass
class PreparedPrompt:
    """Prepared prompt ready for AI generation"""
    prompt_text: str
    question_type: str  # TN, DS, TLN, TL
    lesson_name: str
    question_spec: any  # QuestionSpec or TrueFalseQuestionSpec
    has_content: bool
    content_length: int


class PromptBuilderService:
    """Service for building prompts with PDF content"""
    
    def __init__(self, prompt_dir: str = None):
        """
        Initialize Prompt Builder Service
        
        Args:
            prompt_dir: Directory containing prompt templates
        """
        if prompt_dir is None:
            base_dir = Path(__file__).parent.parent
            prompt_dir = base_dir.parent / "data" / "prompts"
        
        self.prompt_dir = Path(prompt_dir)
        
        # Load prompt templates
        self.templates = {}
        self.load_templates()
        
        # Load rich content guide
        self.rich_content_guide = self.load_rich_content_guide()
    
    def load_rich_content_guide(self) -> str:
        """Load rich content guide template"""
        guide_path = self.prompt_dir / "rich_content_guide.txt"
        if guide_path.exists():
            with open(guide_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def load_templates(self):
        """Load all prompt templates"""
        template_files = {
            'TN': 'TN.txt',
            'DS': 'DS.txt',
            'TLN': 'TLN.txt',
            'TL': 'TL.txt'
        }
        
        for q_type, filename in template_files.items():
            template_path = self.prompt_dir / filename
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.templates[q_type] = f.read()
                print(f"✓ Loaded template: {filename}")
            else:
                print(f"⚠️ Template not found: {filename}")
    
    def replace_variables(self, template: str, variables: Dict[str, str]) -> str:
        """
        Replace variables in template
        
        Args:
            template: Template string
            variables: Dictionary of variable_name -> value
            
        Returns:
            Template with variables replaced
        """
        result = template
        
        for var_name, var_value in variables.items():
            # Replace {{VAR_NAME}} with value
            pattern = f"{{{{{var_name}}}}}"
            result = result.replace(pattern, str(var_value))
        
        return result
    
    def _format_rich_content_types(self, spec: QuestionSpec) -> str:
        """
        Format rich content types for prompt
        
        Args:
            spec: Question specification with rich_content_types
            
        Returns:
            Formatted string for prompt
        """
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return "Không có yêu cầu đặc biệt về loại nội dung."
        
        # Build formatted string
        lines = ["Các câu hỏi yêu cầu loại nội dung sau:"]
        for code, types in spec.rich_content_types.items():
            type_list = []
            for t in types:
                if isinstance(t, dict):
                    # New format: {"code": "BK", "name": "...", "description": "..."}
                    type_name = f"{t['code']} ({t['name']})"
                else:
                    # Old format: just string "BK"
                    type_name = t
                type_list.append(type_name)
            
            lines.append(f"- Câu {code}: {', '.join(type_list)}")
        
        lines.append("")
        lines.append("Lưu ý: Hãy tạo nội dung phù hợp với loại yêu cầu (bảng số liệu, biểu đồ, hình ảnh...) theo đúng schema đã cung cấp.")
        
        return "\n".join(lines)
    
    def _format_rich_content_types_tf(self, spec: TrueFalseQuestionSpec) -> str:
        """
        Format rich content types for True/False questions
        
        Args:
            spec: TrueFalseQuestionSpec with rich_content_types
            
        Returns:
            Formatted string for prompt
        """
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return "Không có yêu cầu đặc biệt về loại nội dung."
        
        # Build formatted string
        lines = ["Các câu hỏi yêu cầu loại nội dung sau:"]
        for code, types in spec.rich_content_types.items():
            type_list = []
            for t in types:
                if isinstance(t, dict):
                    type_name = f"{t['code']} ({t['name']})"
                else:
                    type_name = t
                type_list.append(type_name)
            
            lines.append(f"- Câu {code}: {', '.join(type_list)}")
        
        lines.append("")
        lines.append("Lưu ý: Hãy tạo nội dung phù hợp với loại yêu cầu (bảng số liệu, biểu đồ, hình ảnh...) theo đúng schema đã cung cấp.")
        
        return "\n".join(lines)
    
    def build_prompt_for_tn(self, spec: QuestionSpec, content: str = "") -> PreparedPrompt:
        """
        Build prompt for TN (Trắc nghiệm) questions
        
        Args:
            spec: Question specification from matrix
            content: Content from PDF (optional)
            
        Returns:
            PreparedPrompt object
        """
        template = self.templates.get('TN', '')
        
        # Format rich content types if available
        rich_content_str = self._format_rich_content_types(spec)
        
        # Prepare variables
        variables = {
            'NUM': str(spec.num_questions),
            'LESSON_NAME': spec.lesson_name,
            'CONTENT': content if content else '[Nội dung chưa có - cần bổ sung]',
            'SUPPLEMENTARY_MATERIALS': spec.supplementary_materials if spec.supplementary_materials else '[Không có tài liệu bổ sung]',
            'COGNITIVE_LEVEL': spec.cognitive_level,
            'EXPECTED_LEARNING_OUTCOME': spec.learning_outcome if spec.learning_outcome else '[Không có yêu cầu cụ thể]',
            'QUESTION_TEMPLATE': '',  # Để trống, AI sẽ tự sinh
            'RICH_CONTENT_TYPES': rich_content_str
        }
        
        # Replace variables in template
        prompt_text = self.replace_variables(template, variables)
        
        # Inject rich content guide
        if self.rich_content_guide and (spec.rich_content_types or "BK" in str(spec) or "BD" in str(spec) or "HA" in str(spec)):
            prompt_text = f"{prompt_text}\n\n{self.rich_content_guide}"
        
        return PreparedPrompt(
            prompt_text=prompt_text,
            question_type='TN',
            lesson_name=spec.lesson_name,
            question_spec=spec,
            has_content=bool(content),
            content_length=len(content)
        )
    
    def build_prompt_for_ds(self, spec: TrueFalseQuestionSpec, content: str = "") -> PreparedPrompt:
        """
        Build prompt for DS (Đúng/Sai) questions
        
        Args:
            spec: True/False question specification
            content: Content from PDF (optional)
            
        Returns:
            PreparedPrompt object
        """
        template = self.templates.get('DS', '')
        
        # Format rich content types if available
        rich_content_str = self._format_rich_content_types_tf(spec)
        
        # Get cognitive levels and learning outcomes for each statement
        statements = spec.statements  # List of 4 StatementSpec (a, b, c, d)
        
        # Prepare variables for each statement
        variables = {
            'NUM': '1',  # DS mỗi lần sinh 1 câu (4 mệnh đề)
            'LESSON_NAME': spec.lesson_name,
            'CONTENT': content if content else '[Nội dung chưa có - cần bổ sung]',
            'SUPPLEMENTARY_MATERIALS': spec.supplementary_materials if spec.supplementary_materials else '[Không có tài liệu bổ sung]',
            'RICH_CONTENT_TYPES': rich_content_str,
            
            # Statement a
            'COGNITIVE_LEVEL_A': statements[0].cognitive_level if len(statements) > 0 else 'NB',
            'EXPECTED_LEARNING_OUTCOME_A': statements[0].learning_outcome if len(statements) > 0 else '',
            
            # Statement b
            'COGNITIVE_LEVEL_B': statements[1].cognitive_level if len(statements) > 1 else 'NB',
            'EXPECTED_LEARNING_OUTCOME_B': statements[1].learning_outcome if len(statements) > 1 else '',
            
            # Statement c
            'COGNITIVE_LEVEL_C': statements[2].cognitive_level if len(statements) > 2 else 'TH',
            'EXPECTED_LEARNING_OUTCOME_C': statements[2].learning_outcome if len(statements) > 2 else '',
            
            # Statement d
            'COGNITIVE_LEVEL_D': statements[3].cognitive_level if len(statements) > 3 else 'VD',
            'EXPECTED_LEARNING_OUTCOME_D': statements[3].learning_outcome if len(statements) > 3 else '',
            
            'QUESTION_TEMPLATE': ''  # Để trống, AI sẽ tự sinh
        }
        
        # Replace variables in template
        prompt_text = self.replace_variables(template, variables)
        
        # Inject rich content guide
        if self.rich_content_guide and (spec.rich_content_types or "BK" in str(spec) or "BD" in str(spec)):
            prompt_text = f"{prompt_text}\n\n{self.rich_content_guide}"
        
        return PreparedPrompt(
            prompt_text=prompt_text,
            question_type='DS',
            lesson_name=spec.lesson_name,
            question_spec=spec,
            has_content=bool(content),
            content_length=len(content)
        )
    
    def build_prompt_for_tln(self, spec: QuestionSpec, content: str = "") -> PreparedPrompt:
        """
        Build prompt for TLN (Trả lời ngắn) questions
        
        Args:
            spec: Question specification from matrix
            content: Content from PDF (optional)
            
        Returns:
            PreparedPrompt object
        """
        template = self.templates.get('TLN', '')
        
        # Format rich content types if available
        rich_content_str = self._format_rich_content_types(spec)
        
        # Prepare variables
        variables = {
            'NUM': str(spec.num_questions),
            'LESSON_NAME': spec.lesson_name,
            'CONTENT': content if content else '[Nội dung chưa có - cần bổ sung]',
            'DATA_TABLE_OR_INFORMATION': spec.supplementary_materials if spec.supplementary_materials else '[Không có dữ liệu bổ sung]',
            'LEVEL': spec.cognitive_level,
            'EXPECTED_LEARNING_OUTCOME': spec.learning_outcome if spec.learning_outcome else '[Không có yêu cầu cụ thể]',
            'RICH_CONTENT_TYPES': rich_content_str
        }
        
        # Replace variables in template
        prompt_text = self.replace_variables(template, variables)
        
        # Inject rich content guide
        if self.rich_content_guide and (spec.rich_content_types or "BK" in str(spec) or "BD" in str(spec)):
            prompt_text = f"{prompt_text}\n\n{self.rich_content_guide}"
        
        return PreparedPrompt(
            prompt_text=prompt_text,
            question_type='TLN',
            lesson_name=spec.lesson_name,
            question_spec=spec,
            has_content=bool(content),
            content_length=len(content)
        )
    
    def build_prompt_for_tl(self, spec: QuestionSpec, content: str = "") -> PreparedPrompt:
        """
        Build prompt for TL (Tự luận) questions
        
        Args:
            spec: Question specification from matrix
            content: Content from PDF (optional)
            
        Returns:
            PreparedPrompt object
        """
        template = self.templates.get('TL', '')
        
        # Format rich content types if available
        rich_content_str = self._format_rich_content_types(spec)
        
        # Prepare variables
        variables = {
            'NUM': str(spec.num_questions),
            'CONTENT': content if content else '[Nội dung chưa có - cần bổ sung]',
            'DATA_OR_CONTEXT': spec.supplementary_materials if spec.supplementary_materials else '[Không có dữ liệu/tình huống]',
            'COGNITIVE_LEVEL': spec.cognitive_level,
            'EXPECTED_LEARNING_OUTCOME': spec.learning_outcome if spec.learning_outcome else '[Không có yêu cầu cụ thể]',
            'QUESTION_TEMPLATE': '',
            'RICH_CONTENT_TYPES': rich_content_str
        }
        
        # Replace variables in template
        prompt_text = self.replace_variables(template, variables)
        
        # Inject rich content guide
        if self.rich_content_guide and (spec.rich_content_types or "BK" in str(spec) or "BD" in str(spec)):
            prompt_text = f"{prompt_text}\n\n{self.rich_content_guide}"
        
        return PreparedPrompt(
            prompt_text=prompt_text,
            question_type='TL',
            lesson_name=spec.lesson_name,
            question_spec=spec,
            has_content=bool(content),
            content_length=len(content)
        )
    
    def build_prompts_from_matrix(self, matrix_file: str, pdf_content_map: Dict[str, str] = None,
                                  sheet_name: str = "Sử 12") -> Dict[str, List[PreparedPrompt]]:
        """
        Build all prompts from matrix file
        
        Args:
            matrix_file: Path to Excel matrix file
            pdf_content_map: Dictionary mapping lesson_name -> content
            sheet_name: Sheet name in matrix
            
        Returns:
            Dictionary of question_type -> list of PreparedPrompt
        """
        print("\n" + "="*70)
        print("BUILDING PROMPTS FROM MATRIX")
        print("="*70)
        
        # Parse matrix
        parser = MatrixParser()
        parser.load_excel(matrix_file, sheet_name)
        
        # Get all question specs
        all_specs = parser.get_all_question_specs()
        
        # Prepare result
        result = {
            'TN': [],
            'DS': [],
            'TLN': [],
            'TL': []
        }
        
        # Use PDF content map if available
        if pdf_content_map is None:
            pdf_content_map = self.pdf_service.pdf_content_map if self.pdf_service else {}
        
        # Build prompts for TN questions
        print("\n📝 Building TN prompts...")
        for spec in all_specs['TN']:
            content = pdf_content_map.get(spec.lesson_name, '')
            prompt = self.build_prompt_for_tn(spec, content)
            result['TN'].append(prompt)
            
            status = "✓" if prompt.has_content else "⚠️"
            print(f"  {status} {spec.lesson_name} - {spec.num_questions} câu - {spec.cognitive_level}")
        
        # Build prompts for DS questions
        print("\n📝 Building DS prompts...")
        tf_questions = parser.group_true_false_questions()
        for spec in tf_questions:
            content = pdf_content_map.get(spec.lesson_name, '')
            prompt = self.build_prompt_for_ds(spec, content)
            result['DS'].append(prompt)
            
            status = "✓" if prompt.has_content else "⚠️"
            print(f"  {status} {spec.lesson_name} - {spec.question_code}")
        
        # Build prompts for TLN questions
        print("\n📝 Building TLN prompts...")
        for spec in all_specs.get('TLN', []):
            content = pdf_content_map.get(spec.lesson_name, '')
            prompt = self.build_prompt_for_tln(spec, content)
            result['TLN'].append(prompt)
            
            status = "✓" if prompt.has_content else "⚠️"
            print(f"  {status} {spec.lesson_name} - {spec.num_questions} câu - {spec.cognitive_level}")
        
        # Build prompts for TL questions
        print("\n📝 Building TL prompts...")
        for spec in all_specs.get('TL', []):
            content = pdf_content_map.get(spec.lesson_name, '')
            prompt = self.build_prompt_for_tl(spec, content)
            result['TL'].append(prompt)
            
            status = "✓" if prompt.has_content else "⚠️"
            print(f"  {status} {spec.lesson_name} - {spec.num_questions} câu - {spec.cognitive_level}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"TN prompts: {len(result['TN'])}")
        print(f"  - With content: {sum(1 for p in result['TN'] if p.has_content)}")
        print(f"  - Without content: {sum(1 for p in result['TN'] if not p.has_content)}")
        
        print(f"\nDS prompts: {len(result['DS'])}")
        print(f"  - With content: {sum(1 for p in result['DS'] if p.has_content)}")
        print(f"  - Without content: {sum(1 for p in result['DS'] if not p.has_content)}")
        
        print(f"\nTLN prompts: {len(result['TLN'])}")
        print(f"  - With content: {sum(1 for p in result['TLN'] if p.has_content)}")
        print(f"  - Without content: {sum(1 for p in result['TLN'] if not p.has_content)}")
        
        print(f"\nTL prompts: {len(result['TL'])}")
        print(f"  - With content: {sum(1 for p in result['TL'] if p.has_content)}")
        print(f"  - Without content: {sum(1 for p in result['TL'] if not p.has_content)}")
        
        return result
    
    def save_prompts_to_files(self, prompts: Dict[str, List[PreparedPrompt]], 
                             output_dir: str = None) -> Dict[str, str]:
        """
        Save prepared prompts to text files
        
        Args:
            prompts: Dictionary of question_type -> list of PreparedPrompt
            output_dir: Output directory (optional)
            
        Returns:
            Dictionary of saved file paths
        """
        if output_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent
            output_dir = base_dir / "data" / "output" / "prompts"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        for q_type, prompt_list in prompts.items():
            if not prompt_list:
                continue
            
            # Create subdirectory for each question type
            type_dir = output_dir / q_type
            type_dir.mkdir(exist_ok=True)
            
            for idx, prompt in enumerate(prompt_list, 1):
                # Create filename
                safe_lesson = re.sub(r'[^\w\s-]', '', prompt.lesson_name)
                safe_lesson = safe_lesson.replace(' ', '_')
                filename = f"{idx:03d}_{safe_lesson}_{q_type}.txt"
                
                file_path = type_dir / filename
                
                # Write prompt to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("="*70 + "\n")
                    f.write(f"PROMPT FOR: {prompt.lesson_name}\n")
                    f.write(f"Type: {q_type}\n")
                    f.write(f"Has Content: {prompt.has_content}\n")
                    f.write(f"Content Length: {prompt.content_length} chars\n")
                    f.write("="*70 + "\n\n")
                    f.write(prompt.prompt_text)
                
                saved_files[f"{q_type}_{idx}"] = str(file_path)
        
        print(f"\n💾 Saved {len(saved_files)} prompt files to: {output_dir}")
        
        return saved_files

