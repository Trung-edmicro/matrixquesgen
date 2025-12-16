"""
Module tương tác với Google GenAI SDK (mới) để sử dụng Gemini 3 Pro Preview
"""
import os
import json
from typing import Dict, List, Optional, Any
from google import genai
from google.genai import types


class GenAIClient:
    """Class xử lý tương tác với Google GenAI SDK (mới)"""
    
    def __init__(self, 
                 project_id: str,
                 location: str = "global",
                 credentials_path: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        Khởi tạo GenAI Client
        
        Args:
            project_id (str): Google Cloud Project ID
            location (str): Vùng triển khai (mặc định: global cho gemini-3-pro-preview)
            credentials_path (str, optional): Đường dẫn đến file credentials JSON
            api_key (str, optional): API key (cho express mode)
        """
        self.project_id = project_id
        self.location = location
        self.credentials_path = credentials_path
        self.api_key = api_key
        self.client = None
        self.model_name = 'gemini-3-pro-preview'
        
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo kết nối với GenAI"""
        try:
            # Set credentials path nếu có
            if self.credentials_path and os.path.exists(self.credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            
            # Tạo client
            if self.api_key:
                # Express mode
                self.client = genai.Client(
                    vertexai=True,
                    api_key=self.api_key
                )
            else:
                # Standard mode
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location
                )
            
            print(f"✓ Đã kết nối GenAI - Project: {self.project_id}, Location: {self.location}")
        
        except Exception as e:
            print(f"✗ Lỗi khi khởi tạo GenAI: {str(e)}")
            raise
    
    def initialize_model(self, 
                        model_name: str = "gemini-3-pro-preview",
                        generation_config: Optional[Dict] = None):
        """
        Khởi tạo mô hình
        
        Args:
            model_name (str): Tên mô hình (mặc định: gemini-3-pro-preview)
            generation_config (Dict, optional): Cấu hình generation (không dùng trong SDK mới)
        """
        self.model_name = model_name
        print(f"✓ Đã khởi tạo mô hình: {model_name}")
    
    def generate_content(self, 
                        prompt: str,
                        system_instruction: Optional[str] = None) -> str:
        """
        Tạo nội dung từ prompt
        
        Args:
            prompt (str): Prompt đầu vào
            system_instruction (str, optional): Hướng dẫn hệ thống
            
        Returns:
            str: Nội dung được tạo
        """
        try:
            if self.client is None:
                self._initialize()
            
            # Tạo config
            config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=8192,
                system_instruction=system_instruction
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name or "gemini-3-pro-preview",
                contents=prompt,
                config=config
            )
            
            return response.text
        
        except Exception as e:
            print(f"✗ Lỗi khi tạo nội dung: {str(e)}")
            raise
    
    def generate_content_with_schema(self, 
                                    prompt: str,
                                    response_schema: Dict,
                                    system_instruction: Optional[str] = None) -> str:
        """
        Tạo nội dung với JSON schema để đảm bảo output đúng format
        
        Args:
            prompt (str): Prompt đầu vào
            response_schema (Dict): JSON schema cho response
            system_instruction (str, optional): Hướng dẫn hệ thống
            
        Returns:
            str: Nội dung JSON được tạo
        """
        try:
            if self.client is None:
                self._initialize()
            
            # Thêm instruction vào prompt để yêu cầu JSON output
            json_instruction = "\n\n**QUAN TRỌNG**: Trả về kết quả dưới dạng JSON thuần (raw JSON), KHÔNG bọc trong markdown code block (```json), KHÔNG thêm bất kỳ text nào khác ngoài JSON object."
            enhanced_prompt = prompt + json_instruction
            
            # Tạo config với response MIME type
            config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=8192,
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name or "gemini-3-pro-preview",
                contents=enhanced_prompt,
                config=config
            )
            
            return response.text
        
        except Exception as e:
            print(f"✗ Lỗi khi tạo nội dung với schema: {str(e)}")
            raise
