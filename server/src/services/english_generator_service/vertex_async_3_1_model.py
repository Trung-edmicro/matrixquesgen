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


import asyncio
from google import genai
from google.genai import types

class AsyncVertexGemini31:
    def __init__(
        self,
        project_id: str,
        location: str = "global",
        model: str = "gemini-3.1-pro-preview",
        thinking_level: str = "HIGH"
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
        temperature: float = 1.0, # Docs khuyên giữ 1.0 cho Gemini 3
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
            thinking_config=thinking_config
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

# Cách sử dụng:
# async def main():
#     client = AsyncVertexGemini31(project_id="your-project-id")
#     res = await client.generate("Tại sao bầu trời màu xanh?")
#     print(res)