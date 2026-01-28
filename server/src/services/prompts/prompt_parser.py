"""
Service để parse và xử lý prompt templates với biến {{VARIABLE}}
"""

import re
from typing import Dict, List, Set, Optional


class PromptParserService:
    """Service parse prompt với cú pháp {{VARIABLE}}"""
    
    # Regex để tìm {{VARIABLE}}
    VARIABLE_PATTERN = re.compile(r'\{\{([A-Z_0-9]+)\}\}')
    
    @staticmethod
    def parse_prompt_content(content: str) -> Dict:
        """
        Parse nội dung prompt để tìm variables
        
        Args:
            content: Nội dung prompt
            
        Returns:
            Dict chứa variables, original content, và validation status
        """
        variables = PromptParserService.VARIABLE_PATTERN.findall(content)
        unique_vars = list(set(variables))  # Remove duplicates
        
        return {
            "variables": unique_vars,
            "original_content": content,
            "variable_count": len(unique_vars),
            "is_valid": PromptParserService.validate_prompt_syntax(content)
        }
    
    @staticmethod
    def validate_prompt_syntax(content: str) -> bool:
        """
        Validate cú pháp prompt
        
        Args:
            content: Nội dung prompt
            
        Returns:
            True nếu valid, False nếu không
        """
        # Kiểm tra cặp {{ }} có khớp không
        open_count = content.count('{{')
        close_count = content.count('}}')
        
        if open_count != close_count:
            return False
        
        # Kiểm tra tất cả variables có format đúng
        variables = PromptParserService.VARIABLE_PATTERN.findall(content)
        
        # Kiểm tra tất cả variable names chỉ chứa uppercase, số và underscore
        for var in variables:
            if not re.match(r'^[A-Z_0-9]+$', var):
                return False
        
        return True
    
    @staticmethod
    def fill_variables(content: str, variable_values: Dict[str, str]) -> str:
        """
        Thay thế {{VARIABLE}} bằng giá trị thực
        
        Args:
            content: Nội dung prompt gốc
            variable_values: Dict mapping variable name -> value
            
        Returns:
            Nội dung đã được fill
        """
        result = content
        for var_name, var_value in variable_values.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, var_value)
        
        return result
    
    @staticmethod
    def get_all_unique_variables(prompts: Dict[str, str]) -> List[str]:
        """
        Lấy tất cả unique variables từ nhiều prompts
        
        Args:
            prompts: Dict mapping prompt_name -> prompt_content
            
        Returns:
            List các unique variable names
        """
        all_vars = set()
        
        for content in prompts.values():
            variables = PromptParserService.VARIABLE_PATTERN.findall(content)
            all_vars.update(variables)
        
        return sorted(list(all_vars))
    
    @staticmethod
    def get_variable_context(content: str, variable_name: str, context_chars: int = 100) -> List[str]:
        """
        Lấy context xung quanh variable để hiển thị cho user
        
        Args:
            content: Nội dung prompt
            variable_name: Tên variable cần tìm context
            context_chars: Số ký tự context trước/sau
            
        Returns:
            List các context snippets
        """
        placeholder = f"{{{{{variable_name}}}}}"
        contexts = []
        
        index = 0
        while True:
            index = content.find(placeholder, index)
            if index == -1:
                break
            
            start = max(0, index - context_chars)
            end = min(len(content), index + len(placeholder) + context_chars)
            
            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            
            contexts.append(snippet)
            index += len(placeholder)
        
        return contexts
