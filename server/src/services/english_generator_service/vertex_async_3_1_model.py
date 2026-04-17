# from google import genai
# from google.genai import types
# from pathlib import Path

# class AsyncVertexGemini31:
#     def __init__(
#         self,
#         project_id: str,
#         location: str = "global",
#         model: str = "gemini-3.1-pro-preview",
#         thinking_level: str = "MEDIUM"
#     ):
#         """
#         Gemini 3.1 Async Client cho Vertex AI
        
#         thinking_level: MINIMAL (chỉ Flash), LOW, MEDIUM, HIGH
#         """
#         self.project_id = project_id
#         self.location = location
#         self.model = model

#         # Lưu giá trị string để truyền vào config sau
#         self.thinking_level_str = thinking_level.lower()
        
#         # Khởi tạo Client hỗ trợ Async (AIO)
#         # Nếu dùng Vertex AI trên Google Cloud, set vertexai=True
#         self.client = genai.Client(
#             project=self.project_id,
#             location=self.location,
#             vertexai=True 
#         )

#     async def generate(
#         self,
#         prompt: str,
#         temperature: float = 0.5, # Docs khuyên giữ 1.0 cho Gemini 3
#         max_tokens: int = 64000
#     ):
#         """
#         Sử dụng client.aio để gọi async trực tiếp, không cần to_thread
#         """
        
#         # Cấu hình thinking
#         thinking_config = types.ThinkingConfig(
#             thinking_level=self.thinking_level_str
#         )

#         # Cấu hình generation
#         config = types.GenerateContentConfig(
#             temperature=temperature,
#             max_output_tokens=max_tokens,
#             thinking_config=thinking_config,
#         )

#         try:
#             # Gọi API async native
#             response = await self.client.aio.models.generate_content(
#                 model=self.model,
#                 contents=prompt,
#                 config=config
#             )
            
#             return response.text if response.text else ""
#         except Exception as e:
#             print(f"Error generating content: {e}")
#             return ""
        
#     async def solute(self, prompt: str,pdf_path: None, temperature: float = 1.0, max_tokens: int = 65536):
#         thinking_config = types.ThinkingConfig(
#             include_thoughts=True, # Cho phép trả về quá trình suy nghĩ
#             thinking_level=self.thinking_level_str
#         )

#         # 2. Cấu hình Generation
#         config = types.GenerateContentConfig(
#             temperature=temperature,
#             max_output_tokens=max_tokens,
#             thinking_config=thinking_config
#         )

#         # 3. Chuẩn bị nội dung (Contents)
#         contents = []
        
#         # Nếu có truyền file PDF
#         if pdf_path:
#             try:
#                 path = Path(pdf_path)
#                 if not path.exists():
#                     raise FileNotFoundError(f"Không tìm thấy file tại: {pdf_path}")
                
#                 # Đọc file dưới dạng bytes
#                 pdf_data = path.read_bytes()
                
#                 # Tạo component PDF
#                 pdf_part = types.Part.from_bytes(
#                     data=pdf_data,
#                     mime_type="application/pdf"
#                 )
#                 contents.append(pdf_part)
#             except Exception as e:
#                 print(f"Lỗi xử lý file PDF: {e}")
#                 return None

#         # Thêm text prompt
#         contents.append(prompt)

#         try:
#             # 4. Gọi API async trực tiếp
#             response = await self.client.aio.models.generate_content(
#                 model=self.model,
#                 contents=contents,
#                 config=config
#             )
            
#             # Trả về kết quả văn bản
#             return response.text if response.text else ""
            
#         except Exception as e:
#             print(f"Error generating content: {e}")
#             return None

# # Cách sử dụng:
# # async def main():
# #     client = AsyncVertexGemini31(project_id="your-project-id")
# #     res = await client.generate("Tại sao bầu trời màu xanh?")
# #     print(res)


import os
from pathlib import Path
from typing import Optional, List, Union
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
        """
        Gemini 3.1 Async Client chuyên biệt cho Vertex AI.
        thinking_level: LOW, MEDIUM, HIGH
        """
        self.project_id = project_id
        self.location = location
        self.model = model
        self.thinking_level = thinking_level.upper()
        self.credentials_path = credentials_path
        self.client = None
        
        self._initialize()

    def _initialize(self):
        """Khởi tạo Client với xác thực Vertex AI"""
        try:
            credentials = None
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )

            # Khởi tạo GenAI client với chế độ vertexai=True
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

    def _get_config(self, temperature: float, max_tokens: int) -> types.GenerateContentConfig:
        """Tạo cấu hình chuẩn cho Gemini 3.1 Thinking"""
        # Lưu ý: include_thoughts=True giúp model thực hiện quy trình suy nghĩ
        thinking_config = types.ThinkingConfig(
            include_thoughts=True, 
            thinking_level=self.thinking_level
        )
        
        return types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            thinking_config=thinking_config,
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 1.0,
        max_tokens: int = 64000
    ) -> str:
        """
        Output: Trả về string. Nếu lỗi trả về chuỗi rỗng.
        """
        try:
            config = self._get_config(temperature, max_tokens)
            
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            return response.text if response.text else ""
        except Exception as e:
            print(f"Error in generate: {e}")
            return ""

    async def solute(
        self, 
        prompt: str, 
        pdf_path: Optional[str] = None, 
        temperature: float = 1.0, 
        max_tokens: int = 65536
    ) -> Optional[str]:
        """
        Hàm xử lý đa phương thức (PDF + Text).
        Output: Trả về string hoặc None nếu có lỗi nghiêm trọng.
        """
        config = self._get_config(temperature, max_tokens)
        contents = []
        
        # 1. Xử lý file PDF (nếu có)
        if pdf_path:
            try:
                path = Path(pdf_path)
                if not path.exists():
                    print(f"Warning: File not found at {pdf_path}")
                else:
                    pdf_data = path.read_bytes()
                    pdf_part = types.Part.from_bytes(
                        data=pdf_data,
                        mime_type="application/pdf"
                    )
                    contents.append(pdf_part)
            except Exception as e:
                print(f"Error processing PDF: {e}")
                return None # Trả về None theo interface cũ khi lỗi file

        # 2. Thêm Text prompt
        contents.append(prompt)

        try:
            # 3. Gọi API async
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            # Metadata Debug (tương tự bản gốc của bạn)
            if response.usage_metadata:
                u = response.usage_metadata
                print(f"📊 [Solute] Tokens: Prompt={u.prompt_token_count}, Candidates={u.candidates_token_count}")

            return response.text if response.text else ""
            
        except Exception as e:
            print(f"Error in solute: {e}")
            return None