"""
Math Variable Mapping Service
Populates prompt template variables specific to Math subject (TOAN)
Handles multi-code question support with per-code template selection
"""

from typing import Dict, Optional, Any, List


class MathVariableMappingService:
    """
    Maps enriched_matrix question data to template variables for Math (TOAN) subject.
    Supports both single and multiple code questions with per-code template selection.
    
    Variables populated:
    - NUM: Number of questions (1 for SINGLE, N for MULTIPLE)
    - QUESTION_CODES: Comma-separated question codes (e.g., "C1, C2")
    - TEMPLATE_MODE: "SINGLE" or "MULTIPLE"
    - SELECTED_QUESTION_TEMPLATE: Template text (varies by mode)
    - COGNITIVE_LEVEL: From question level
    - EXPECTED_LEARNING_OUTCOME: From question learning_outcome
    - LESSON_NAME: From lesson data
    - CONTENT: From lesson content
    """
    
    @staticmethod
    def populate_variables_for_tn(
        spec_data: Dict[str, Any],
        lesson_data: Dict[str, Any],
        content: str = "",
        question_template: str = "",
        cognitive_level: str = ""
    ) -> Dict[str, str]:
        """
        Populate all template variables for TN (multiple choice) questions.
        
        Args:
            spec_data: Question spec from enriched_matrix (includes code, selected_templates_by_code)
            lesson_data: Lesson data from enriched_matrix
            content: Extracted lesson content (optional override)
            question_template: Question template text (optional)
            cognitive_level: Cognitive level from enriched_matrix key (NB, TH, VD, VDC)
            
        Returns:
            Dict with 8 variables: NUM, QUESTION_CODES, TEMPLATE_MODE, 
            SELECTED_QUESTION_TEMPLATE, COGNITIVE_LEVEL, EXPECTED_LEARNING_OUTCOME,
            LESSON_NAME, CONTENT
        """
        # Step 1: Extract codes and determine mode
        codes = spec_data.get('code', [])
        if isinstance(codes, str):
            codes = [codes]
        
        num_questions = len(codes) if codes else 1
        template_mode = "MULTIPLE" if num_questions > 1 else "SINGLE"
        question_codes_str = ', '.join(codes) if codes else 'C1'
        
        # Step 2: Build selected template based on mode
        selected_template = MathVariableMappingService._build_selected_template(
            codes=codes,
            spec_data=spec_data,
            template_mode=template_mode
        )
        
        # Step 3: Extract cognitive level and learning outcome
        level = cognitive_level if cognitive_level else spec_data.get('level', 'NB')
        learning_outcome = spec_data.get('learning_outcome', '')
        
        # Step 4: Extract lesson info
        lesson_name = lesson_data.get('lesson_name', '')
        lesson_content = content if content else lesson_data.get('content', '')
        
        # Build variables dict
        variables = {
            'NUM': str(num_questions),
            'QUESTION_CODES': question_codes_str,
            'TEMPLATE_MODE': template_mode,
            'SELECTED_QUESTION_TEMPLATE': selected_template,
            'COGNITIVE_LEVEL': level,
            'EXPECTED_LEARNING_OUTCOME': learning_outcome,
            'LESSON_NAME': lesson_name,
            'CONTENT': lesson_content
        }
        
        return variables
    
    @staticmethod
    def populate_variables_for_ds(
        spec_data: Dict[str, Any],
        lesson_data: Dict[str, Any],
        content: str = "",
        question_template: str = "",
        cognitive_level: str = ""
    ) -> Dict[str, str]:
        """
        Populate template variables for DS (true/false) questions.
        
        Args:
            spec_data: Question spec from enriched_matrix
            lesson_data: Lesson data from enriched_matrix
            content: Extracted lesson content (optional override)
            question_template: Question template text (optional)
            cognitive_level: Cognitive level from enriched_matrix key (NB, TH, VD, VDC)
            
        Returns:
            Dict with template variables (adapted for DS questions)
        """
        # DS typically has single question_code, but use same logic for consistency
        codes = spec_data.get('code', ['DS1'])
        if isinstance(codes, str):
            codes = [codes]
        
        selected_template = spec_data.get('selected_question_template', '')
        level = cognitive_level if cognitive_level else spec_data.get('level', 'NB')
        learning_outcome = spec_data.get('learning_outcome', '')
        lesson_name = lesson_data.get('lesson_name', '')
        lesson_content = content if content else lesson_data.get('content', '')
        
        variables = {
            'NUM': '1',  # DS is always single question per spec
            'QUESTION_CODES': codes[0] if codes else 'DS1',
            'TEMPLATE_MODE': 'SINGLE',  # DS doesn't support MULTIPLE mode yet
            'SELECTED_QUESTION_TEMPLATE': selected_template,
            'COGNITIVE_LEVEL': level,
            'EXPECTED_LEARNING_OUTCOME': learning_outcome,
            'LESSON_NAME': lesson_name,
            'CONTENT': lesson_content
        }
        
        return variables
    
    @staticmethod
    def populate_variables_for_tln(
        spec_data: Dict[str, Any],
        lesson_data: Dict[str, Any],
        content: str = "",
        question_template: str = "",
        cognitive_level: str = ""
    ) -> Dict[str, str]:
        """
        Populate template variables for TLN (short answer) questions.
        Similar to TN but typically single code per spec.
        """
        codes = spec_data.get('code', [])
        if isinstance(codes, str):
            codes = [codes]
        
        num_questions = len(codes) if codes else 1
        template_mode = "MULTIPLE" if num_questions > 1 else "SINGLE"
        question_codes_str = ', '.join(codes) if codes else 'C1'
        
        selected_template = MathVariableMappingService._build_selected_template(
            codes=codes,
            spec_data=spec_data,
            template_mode=template_mode
        )
        
        level = cognitive_level if cognitive_level else spec_data.get('level', 'NB')
        learning_outcome = spec_data.get('learning_outcome', '')
        lesson_name = lesson_data.get('lesson_name', '')
        lesson_content = content if content else lesson_data.get('content', '')
        
        variables = {
            'NUM': str(num_questions),
            'QUESTION_CODES': question_codes_str,
            'TEMPLATE_MODE': template_mode,
            'SELECTED_QUESTION_TEMPLATE': selected_template,
            'COGNITIVE_LEVEL': level,
            'EXPECTED_LEARNING_OUTCOME': learning_outcome,
            'LESSON_NAME': lesson_name,
            'CONTENT': lesson_content
        }
        
        return variables
    
    @staticmethod
    def populate_variables_for_tl(
        spec_data: Dict[str, Any],
        lesson_data: Dict[str, Any],
        content: str = "",
        question_template: str = ""
    ) -> Dict[str, str]:
        """
        Populate template variables for TL (essay) questions.
        Similar to other types but adapted for essay format.
        """
        codes = spec_data.get('code', [])
        if isinstance(codes, str):
            codes = [codes]
        
        selected_template = spec_data.get('selected_question_template', '')
        level = spec_data.get('level', 'medium')
        learning_outcome = spec_data.get('learning_outcome', '')
        lesson_name = lesson_data.get('lesson_name', '')
        lesson_content = content if content else lesson_data.get('content', '')
        
        variables = {
            'NUM': str(len(codes)) if codes else '1',
            'QUESTION_CODES': ', '.join(codes) if codes else 'C1',
            'TEMPLATE_MODE': 'SINGLE',  # TL doesn't support MULTIPLE mode
            'SELECTED_QUESTION_TEMPLATE': selected_template,
            'COGNITIVE_LEVEL': level,
            'EXPECTED_LEARNING_OUTCOME': learning_outcome,
            'LESSON_NAME': lesson_name,
            'CONTENT': lesson_content
        }
        
        return variables
    
    @staticmethod
    def _build_selected_template(
        codes: List[str],
        spec_data: Dict[str, Any],
        template_mode: str
    ) -> str:
        """
        Build selected_question_template based on template mode.
        
        For SINGLE mode: Return template text directly
        For MULTIPLE mode: Format as "Câu mã C1\n{template C1}\n\nCâu mã C2\n{template C2}..."
        
        Args:
            codes: List of question codes
            spec_data: Question spec containing selected_templates_by_code
            template_mode: "SINGLE" or "MULTIPLE"
            
        Returns:
            Formatted template text
        """
        if template_mode == "SINGLE":
            # Single mode: return template directly
            template = spec_data.get('selected_question_template', '')
            # If template is a dict, extract 'template' field
            if isinstance(template, dict):
                template = template.get('template', str(template))
            return template
        
        elif template_mode == "MULTIPLE":
            # Multiple mode: format with code labels
            selected_templates_by_code = spec_data.get('selected_templates_by_code', {})
            
            if not selected_templates_by_code:
                # Fallback: try to use single template
                template = spec_data.get('selected_question_template', '')
                if isinstance(template, dict):
                    template = template.get('template', str(template))
                return template
            
            template_parts = []
            for code in codes:
                # Get template for this code
                code_template = selected_templates_by_code.get(code, '')
                
                # If template is a dict, extract 'template' field
                if isinstance(code_template, dict):
                    code_template = code_template.get('template', '')
                
                if code_template:
                    # Format: "Câu mã C1\n{template}"
                    formatted = f"Câu mã {code}\n{code_template}"
                    template_parts.append(formatted)
            
            # Join with double newline separator
            return "\n\n".join(template_parts) if template_parts else ""
        
        return ""
    
    @staticmethod
    def populate_variables(
        question_type: str,
        spec_data: Dict[str, Any],
        lesson_data: Dict[str, Any],
        content: str = "",
        question_template: str = "",
        cognitive_level: str = ""
    ) -> Dict[str, str]:
        """
        Main method to populate variables for any question type.
        Routes to specific handler based on question_type.
        
        Args:
            question_type: "TN", "DS", "TLN", or "TL"
            spec_data: Question spec from enriched_matrix
            lesson_data: Lesson data from enriched_matrix
            content: Extracted lesson content (optional)
            question_template: Question template text (optional)
            cognitive_level: Cognitive level from enriched_matrix key (NB, TH, VD, VDC)
            
        Returns:
            Dict with all template variables ready for fill_variables()
        """
        if question_type == "TN":
            return MathVariableMappingService.populate_variables_for_tn(
                spec_data, lesson_data, content, question_template, cognitive_level
            )
        elif question_type == "DS":
            return MathVariableMappingService.populate_variables_for_ds(
                spec_data, lesson_data, content, question_template, cognitive_level
            )
        elif question_type == "TLN":
            return MathVariableMappingService.populate_variables_for_tln(
                spec_data, lesson_data, content, question_template, cognitive_level
            )
        elif question_type == "TL":
            return MathVariableMappingService.populate_variables_for_tl(
                spec_data, lesson_data, content, question_template, cognitive_level
            )
        else:
            # Fallback for unknown types
            return MathVariableMappingService._default_variables(
                spec_data, lesson_data, content
            )
    
    @staticmethod
    def _default_variables(
        spec_data: Dict[str, Any],
        lesson_data: Dict[str, Any],
        content: str = ""
    ) -> Dict[str, str]:
        """Fallback variables for unknown question types"""
        codes = spec_data.get('code', [])
        if isinstance(codes, str):
            codes = [codes]
        
        return {
            'NUM': str(len(codes)) if codes else '1',
            'QUESTION_CODES': ', '.join(codes) if codes else 'C1',
            'TEMPLATE_MODE': 'SINGLE',
            'SELECTED_QUESTION_TEMPLATE': spec_data.get('selected_question_template', ''),
            'COGNITIVE_LEVEL': spec_data.get('level', ''),
            'EXPECTED_LEARNING_OUTCOME': spec_data.get('learning_outcome', ''),
            'LESSON_NAME': lesson_data.get('lesson_name', ''),
            'CONTENT': content if content else lesson_data.get('content', '')
        }
