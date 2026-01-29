"""
Module tương tác với Google GenAI SDK (mới) để sử dụng Gemini 3 Pro Preview
"""
import os
import json
from typing import Dict, List, Optional, Any
from google import genai
from google.genai import types
from google.oauth2 import service_account


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
        self.model_name = os.getenv('GENAI_MODEL', 'gemini-3-pro-preview')
        
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo kết nối với GenAI"""
        try:
            # Load credentials từ file nếu có
            credentials = None
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Tạo credentials object từ service account file
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
            
            # Tạo client
            if self.api_key:
                # Express mode với API key
                self.client = genai.Client(
                    vertexai=True,
                    api_key=self.api_key
                )
            elif credentials:
                # Standard mode với explicit credentials
                self.client = genai.Client(
                    vertexai=True,
                    project=self.project_id,
                    location=self.location,
                    credentials=credentials
                )
            else:
                # Fallback: dùng Application Default Credentials
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
                        model_name: Optional[str] = None,
                        generation_config: Optional[Dict] = None):
        """
        Khởi tạo mô hình
        
        Args:
            model_name (str, optional): Tên mô hình (mặc định lấy từ GENAI_MODEL env)
            generation_config (Dict, optional): Cấu hình generation (không dùng trong SDK mới)
        """
        self.model_name = model_name or os.getenv('GENAI_MODEL', 'gemini-3-pro-preview')
        print(f"✓ Đã khởi tạo mô hình: {self.model_name}")
    
    def generate_content(self, 
                        prompt: str,
                        system_instruction: Optional[str] = None,
                        enable_search: bool = False) -> str:
        """
        Tạo nội dung từ prompt
        
        Args:
            prompt (str): Prompt đầu vào
            system_instruction (str, optional): Hướng dẫn hệ thống
            enable_search (bool): Bật Google Search (mặc định: False)
            
        Returns:
            str: Nội dung được tạo
        """
        try:
            if self.client is None:
                self._initialize()
            
            # Tạo tools nếu enable_search
            tools = None
            if enable_search:
                tools = [types.Tool(google_search=types.GoogleSearch())]
            
            # Tạo config
            config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=65536,
                system_instruction=system_instruction,
                tools=tools if tools else None
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
                                    system_instruction: Optional[str] = None,
                                    enable_search: bool = False) -> str:
        """
        Tạo nội dung với JSON schema để đảm bảo output đúng format
        
        Args:
            prompt (str): Prompt đầu vào
            response_schema (Dict): JSON schema cho response
            system_instruction (str, optional): Hướng dẫn hệ thống
            enable_search (bool): Bật Google Search (mặc định: False)
            
        Returns:
            str: Nội dung JSON được tạo
        """
        try:
            if self.client is None:
                self._initialize()
            
            # Thêm instruction vào prompt để yêu cầu JSON output
            json_instruction = "\n\n**QUAN TRỌNG**: Trả về kết quả dưới dạng JSON thuần (raw JSON), KHÔNG bọc trong markdown code block (```json), KHÔNG thêm bất kỳ text nào khác ngoài JSON object."
            enhanced_prompt = prompt + json_instruction
            
            # Tạo tools nếu enable_search
            tools = None
            if enable_search:
                tools = [types.Tool(google_search=types.GoogleSearch())]
                # print("🔍 Google Search enabled cho request này")
            
            # Tạo config với response MIME type
            config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=65536,
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                tools=tools if tools else None
            )
            
            # Generate content
            response = self.client.models.generate_content(
                model=self.model_name or "gemini-3-pro-preview",
                contents=enhanced_prompt,
                config=config
            )
            
            # Log usage metadata for debugging
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                print(f"📊 Token usage: prompt={usage.prompt_token_count}, "
                      f"candidates={usage.candidates_token_count}, "
                      f"total={usage.total_token_count}")
            
            # Check finish reason
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason
                if finish_reason != 'STOP':
                    print(f"⚠️ Response finished with reason: {finish_reason}")
                    if finish_reason == 'MAX_TOKENS':
                        print(f"⚠️ Response was truncated due to MAX_TOKENS limit!")
            
            # Extract text from response
            text = response.text if hasattr(response, 'text') and response.text is not None else ""
            
            # Clean markdown code fences if present (Google Search returns markdown-wrapped JSON)
            if text.strip().startswith("```"):
                # Remove ```json or ``` prefix
                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:]  # Remove ```json
                elif text.startswith("```"):
                    text = text[3:]  # Remove ```
                
                # Remove ``` suffix
                if text.endswith("```"):
                    text = text[:-3]
                
                text = text.strip()
            
            return text
        
        except Exception as e:
            print(f"✗ Lỗi khi tạo nội dung với schema: {str(e)}")
            raise
    
    def generate_content_with_schema_with_model(self, 
                                               prompt: str,
                                               response_schema: Dict,
                                               model_name: str,
                                               system_instruction: Optional[str] = None,
                                               enable_search: bool = False) -> str:
        """
        Tạo nội dung với JSON schema và model cụ thể
        
        Args:
            prompt (str): Prompt đầu vào
            response_schema (Dict): JSON schema cho response
            model_name (str): Tên model cần sử dụng
            system_instruction (str, optional): Hướng dẫn hệ thống
            enable_search (bool): Bật Google Search (mặc định: False)
            
        Returns:
            str: Nội dung JSON được tạo
        """
        try:
            if self.client is None:
                self._initialize()
            
            # Thêm instruction vào prompt để yêu cầu JSON output
            json_instruction = "\n\n**QUAN TRỌNG**: Trả về kết quả dưới dạng JSON thuần (raw JSON), KHÔNG bọc trong markdown code block (```json), KHÔNG thêm bất kỳ text nào khác ngoài JSON object."
            enhanced_prompt = prompt + json_instruction
            
            # Tạo tools nếu enable_search
            tools = None
            if enable_search:
                tools = [types.Tool(google_search=types.GoogleSearch())]
                # print("🔍 Google Search enabled cho request này")
            
            # Tạo config với response MIME type
            config = types.GenerateContentConfig(
                temperature=1,
                top_p=0.95,
                max_output_tokens=65536,
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                tools=tools if tools else None
            )
            
            # Generate content với model cụ thể
            response = self.client.models.generate_content(
                model=model_name,
                contents=enhanced_prompt,
                config=config
            )
            
            # Extract text from response
            text = response.text if hasattr(response, 'text') and response.text is not None else ""
            
            # Clean markdown code fences if present (Google Search returns markdown-wrapped JSON)
            if text.strip().startswith("```"):
                # Remove ```json or ``` prefix
                text = text.strip()
                if text.startswith("```json"):
                    text = text[7:]  # Remove ```json
                elif text.startswith("```"):
                    text = text[3:]  # Remove ```
                
                # Remove ``` suffix
                if text.endswith("```"):
                    text = text[:-3]
                
                text = text.strip()
            
            return text
        
        except Exception as e:
            print(f"✗ Lỗi khi tạo nội dung với schema (model: {model_name}): {str(e)}")
            raise
