# import os
# from pathlib import Path
# from typing import Optional
# from google import genai
# from google.genai import types
# from google.oauth2 import service_account

# class AsyncVertexGemini31:
#     def __init__(
#         self,
#         project_id: str,
#         location: str = "global", # Khuyên dùng us-central1 cho các bản preview
#         model: str = "gemini-3.1-pro-preview",
#         credentials_path: Optional[str] = None,
#         thinking_level: str = "MEDIUM"
#     ):
#         """
#         Gemini 3.1 Async Client chuyên biệt cho Vertex AI.
#         thinking_level: LOW, MEDIUM, HIGH
#         """
#         self.project_id = project_id
#         self.location = location
#         self.model = model
#         self.thinking_level = thinking_level.upper()
#         self.credentials_path = credentials_path
#         self.client = None
        
#         self._initialize()

#     def _initialize(self):
#         """Khởi tạo Client với xác thực Vertex AI"""
#         try:
#             credentials = None
#             if self.credentials_path and os.path.exists(self.credentials_path):
#                 credentials = service_account.Credentials.from_service_account_file(
#                     self.credentials_path,
#                     scopes=['https://www.googleapis.com/auth/cloud-platform']
#                 )

#             # Khởi tạo GenAI client với chế độ vertexai=True
#             self.client = genai.Client(
#                 vertexai=True,
#                 project=self.project_id,
#                 location=self.location,
#                 credentials=credentials
#             )
#             print(f"✓ Connected to Async Vertex AI - Model: {self.model}")
#         except Exception as e:
#             print(f"✗ Initialization Error: {e}")
#             raise

#     def _get_config(self, temperature: float, max_tokens: int) -> types.GenerateContentConfig:
#         """Tạo cấu hình chuẩn cho Gemini 3.1 Thinking"""
#         # Lưu ý: include_thoughts=True giúp model thực hiện quy trình suy nghĩ
#         thinking_config = types.ThinkingConfig(
#             include_thoughts=True, 
#             thinking_level=self.thinking_level
#         )
        
#         return types.GenerateContentConfig(
#             temperature=temperature,
#             max_output_tokens=max_tokens,
#             thinking_config=thinking_config,
#         )

#     async def generate(
#         self,
#         prompt: str,
#         temperature: float = 1.0,
#         max_tokens: int = 64000
#     ) -> str:
#         """
#         Output: Trả về string. Nếu lỗi trả về chuỗi rỗng.
#         """
#         try:
#             config = self._get_config(temperature, max_tokens)
            
#             response = await self.client.aio.models.generate_content(
#                 model=self.model,
#                 contents=prompt,
#                 config=config
#             )
            
#             return response.text if response.text else ""
#         except Exception as e:
#             print(f"Error in generate: {e}")
#             return ""

#     async def solute(
#         self, 
#         prompt: str, 
#         pdf_path: Optional[str] = None, 
#         temperature: float = 1.0, 
#         max_tokens: int = 65536
#     ) -> Optional[str]:
#         """
#         Hàm xử lý đa phương thức (PDF + Text).
#         Output: Trả về string hoặc None nếu có lỗi nghiêm trọng.
#         """
#         config = self._get_config(temperature, max_tokens)
#         contents = []
        
#         # 1. Xử lý file PDF (nếu có)
#         if pdf_path:
#             try:
#                 path = Path(pdf_path)
#                 if not path.exists():
#                     print(f"Warning: File not found at {pdf_path}")
#                 else:
#                     pdf_data = path.read_bytes()
#                     pdf_part = types.Part.from_bytes(
#                         data=pdf_data,
#                         mime_type="application/pdf"
#                     )
#                     contents.append(pdf_part)
#             except Exception as e:
#                 print(f"Error processing PDF: {e}")
#                 return None # Trả về None theo interface cũ khi lỗi file

#         # 2. Thêm Text prompt
#         contents.append(prompt)

#         try:
#             # 3. Gọi API async
#             response = await self.client.aio.models.generate_content(
#                 model=self.model,
#                 contents=contents,
#                 config=config
#             )
            
#             # Metadata Debug (tương tự bản gốc của bạn)
#             if response.usage_metadata:
#                 u = response.usage_metadata
#                 print(f"📊 [Solute] Tokens: Prompt={u.prompt_token_count}, Candidates={u.candidates_token_count}")

#             return response.text if response.text else ""
            
#         except Exception as e:
#             print(f"Error in solute: {e}")
#             return None


import os
from pathlib import Path
from typing import Optional, List, Union, Any, Type
from pydantic import BaseModel # Import Pydantic để định nghĩa schema
from google import genai
from google.genai import types
from google.oauth2 import service_account

class AsyncVertexGemini31:
    def __init__(
        self,
        project_id: str,
        location: str = "global", # Khuyên dùng us-central1 cho các bản preview
        model: str = "gemini-3.1-pro-preview",
        credentials_path: Optional[str] = None,
        thinking_level: str = "MEDIUM"
    ):
        self.project_id = project_id
        self.location = location
        self.model = model
        self.thinking_level = thinking_level.upper()
        self.credentials_path = credentials_path
        self.client = None
        
        self._initialize()

    def _initialize(self):
        try:
            credentials = None
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )

            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location,
                credentials=credentials
            )
            print(f"✓ Connected to Async Vertex AI - Model: {self.model}")
        except Exception as e:
            print(f"✗ Initialization Error: {e}")
            raise

    def _get_config(
        self, 
        temperature: float, 
        max_tokens: int, 
        schema: Optional[Union[Type[BaseModel], dict]] = None
    ) -> types.GenerateContentConfig:
        """Tạo cấu hình bao gồm cả Thinking và JSON Schema nếu có"""
        
        thinking_config = types.ThinkingConfig(
            include_thoughts=True, 
            thinking_level=self.thinking_level
        )
        
        config_params = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "thinking_config": thinking_config,
        }

        # Nếu có schema, cấu hình để trả về JSON
        if schema:
            config_params["response_mime_type"] = "application/json"
            
            # Nếu là Pydantic class, chuyển sang JSON Schema dict
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                config_params["response_json_schema"] = schema.model_json_schema()
            else:
                config_params["response_json_schema"] = schema

        return types.GenerateContentConfig(**config_params)

    async def generate(
        self,
        prompt: str,
        schema: Optional[Union[Type[BaseModel], dict]] = None,
        temperature: float = 1.0,
        max_tokens: int = 64000
    ) -> Union[str, Any]:
        """
        Hàm generate cơ bản. Nếu có schema, sẽ trả về kết quả đã được parse.
        """
        try:
            config = self._get_config(temperature, max_tokens, schema)
            
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            res_text = response.text if response.text else ""
            
            # Nếu dùng schema và là Pydantic, tự động validate và trả về object
            if schema and isinstance(schema, type) and issubclass(schema, BaseModel) and res_text:
                return schema.model_validate_json(res_text)
            
            return res_text
        except Exception as e:
            print(f"Error in generate: {e}")
            return ""

    async def solute(
        self, 
        prompt: str, 
        pdf_path: Optional[str] = None, 
        schema: Optional[Union[Type[BaseModel], dict]] = None,
        temperature: float = 1.0, 
        max_tokens: int = 65536
    ) -> Optional[Union[str, Any]]:
        """
        Hàm xử lý đa phương thức (PDF + Text) với Structured Output.
        """
        config = self._get_config(temperature, max_tokens, schema)
        contents = []
        
        if pdf_path:
            try:
                path = Path(pdf_path)
                if path.exists():
                    pdf_data = path.read_bytes()
                    pdf_part = types.Part.from_bytes(
                        data=pdf_data,
                        mime_type="application/pdf"
                    )
                    contents.append(pdf_part)
            except Exception as e:
                print(f"Error processing PDF: {e}")
                return None

        contents.append(prompt)

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            if response.usage_metadata:
                u = response.usage_metadata
                print(f"📊 [Solute] Tokens: Prompt={u.prompt_token_count}, Candidates={u.candidates_token_count}")

            res_text = response.text if response.text else ""

            if schema and isinstance(schema, type) and issubclass(schema, BaseModel) and res_text:
                return schema.model_validate_json(res_text)
            print(f">>>>>> Succesfully generate with gemini 3.1 pro")
            return res_text
            
        except Exception as e:
            print(f"Error in solute: {e}")
            return None

