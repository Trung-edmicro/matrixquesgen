# import asyncio
# from google import genai
# from google.genai import types


# class AsyncVertexGemini31:

#     def __init__(
#         self,
#         project_id: str,
#         model: str = "gemini-3.1-pro-preview",
#         thinking_level: str = "HIGH"
#     ):
#         """
#         Gemini 3.1 Async Client for Vertex AI

#         thinking_level:
#         - MINIMAL
#         - LOW
#         - MEDIUM
#         - HIGH
#         """

#         self.project_id = project_id
#         self.model = model

#         thinking_map = {
#             # "MINIMAL": types.ThinkingConfig(thinking_level = "mini"),
#             "LOW": types.ThinkingConfig(thinking_level = "low"),
#             "MEDIUM": types.ThinkingConfig(thinking_level = "medium"),
#             "HIGH": types.ThinkingConfig(thinking_level = "high")
#         }

#         self.thinking_level = thinking_map.get(
#             thinking_level.upper(),
#             types.ThinkingConfig(thinking_level = "high")
#         )

#         self.client = genai.Client()

#     # ===================================
#     # INTERNAL SYNC CALL
#     # ===================================

#     def _generate_sync(
#         self,
#         prompt,
#         temperature=1.0,
#         max_tokens=64000
#     ):

#         response = self.client.models.generate_content(
#             model=self.model,
#             contents=prompt,
#             config=types.GenerateContentConfig(
#                 temperature=temperature,
#                 max_output_tokens=max_tokens,
#                 thinking_config=types.ThinkingConfig(
#                     thinking_level=self.thinking_level
#                 )
#             )
#         )

#         if response.text:
#             return response.text

#         return ""

#     # ===================================
#     # ASYNC WRAPPER
#     # ===================================

#     async def generate(
#         self,
#         prompt: str,
#         temperature: float = 1.0,
#         max_tokens: int = 64000
#     ):

#         return await asyncio.to_thread(
#             self._generate_sync,
#             prompt,
#             temperature,
#             max_tokens
#         )

from google import genai
from google.genai import types
from pathlib import Path

class AsyncVertexGemini31:
    def __init__(
        self,
        project_id: str,
        location: str = "global",
        model: str = "gemini-3.1-pro-preview",
        thinking_level: str = "MEDIUM"
    ):
        """
        Gemini 3.1 Async Client cho Vertex AI
        
        thinking_level: MINIMAL (chỉ Flash), LOW, MEDIUM, HIGH
        """
        self.project_id = project_id
        self.location = location
        self.model = model

        # Lưu giá trị string để truyền vào config sau
        self.thinking_level_str = thinking_level.lower()
        
        # Khởi tạo Client hỗ trợ Async (AIO)
        # Nếu dùng Vertex AI trên Google Cloud, set vertexai=True
        self.client = genai.Client(
            project=self.project_id,
            location=self.location,
            vertexai=True 
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.5, # Docs khuyên giữ 1.0 cho Gemini 3
        max_tokens: int = 64000
    ):
        """
        Sử dụng client.aio để gọi async trực tiếp, không cần to_thread
        """
        
        # Cấu hình thinking
        thinking_config = types.ThinkingConfig(
            thinking_level=self.thinking_level_str
        )

        # Cấu hình generation
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            thinking_config=thinking_config,
        )

        try:
            # Gọi API async native
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            
            return response.text if response.text else ""
        except Exception as e:
            print(f"Error generating content: {e}")
            return ""
        
    async def solute(self, prompt: str,pdf_path: None, temperature: float = 1.0, max_tokens: int = 65536):
        thinking_config = types.ThinkingConfig(
            include_thoughts=True, # Cho phép trả về quá trình suy nghĩ
            thinking_level=self.thinking_level_str
        )

        # 2. Cấu hình Generation
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            thinking_config=thinking_config
        )

        # 3. Chuẩn bị nội dung (Contents)
        contents = []
        
        # Nếu có truyền file PDF
        if pdf_path:
            try:
                path = Path(pdf_path)
                if not path.exists():
                    raise FileNotFoundError(f"Không tìm thấy file tại: {pdf_path}")
                
                # Đọc file dưới dạng bytes
                pdf_data = path.read_bytes()
                
                # Tạo component PDF
                pdf_part = types.Part.from_bytes(
                    data=pdf_data,
                    mime_type="application/pdf"
                )
                contents.append(pdf_part)
            except Exception as e:
                print(f"Lỗi xử lý file PDF: {e}")
                return None

        # Thêm text prompt
        contents.append(prompt)

        try:
            # 4. Gọi API async trực tiếp
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            # Trả về kết quả văn bản
            return response.text if response.text else ""
            
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

# Cách sử dụng:
# async def main():
#     client = AsyncVertexGemini31(project_id="your-project-id")
#     res = await client.generate("Tại sao bầu trời màu xanh?")
#     print(res)