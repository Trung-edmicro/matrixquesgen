import asyncio
import logging

import fitz
from .llm_provider import BaseLLMProvider
from services.core.openai_client import OpenAIClient
logger = logging.getLogger(__name__)
import json


class OpenAIProvider(BaseLLMProvider):

    def __init__(self, model="gpt-5.4"):
        self.client_wrapper = OpenAIClient()
        self.client_wrapper.initialize_model(model)

        self.raw_client = self.client_wrapper.client
        self.model_name = model

    async def generate(
        self,
        prompt,
        schema=None,
        temperature=1.0,
        max_tokens=64000
    ):

        if schema:
            return await asyncio.to_thread(
                self.client_wrapper.generate_content_with_schema,
                prompt,
                schema
            )

        return await asyncio.to_thread(
            self.client_wrapper.generate_content,
            prompt
        )
    
    # async def solute(self, prompt, pdf_path, schema=None, temperature=1.0, max_tokens=128000):
    #     try:
    #         # 1. Upload file bằng SDK OpenAI
    #         with open(pdf_path, "rb") as f:
    #             uploaded_file = await asyncio.to_thread(
    #                 self.raw_client.files.create,
    #                 file=f,
    #                 purpose="user_data"
    #             )
            
    #         # 2. Đợi file được xử lý (processed)
    #         logger.info(f"⏳ OpenAI đang xử lý file ID: {uploaded_file.id}...")
    #         while True:
    #             file_info = await asyncio.to_thread(self.raw_client.files.retrieve, uploaded_file.id)
    #             if file_info.status == "processed": 
    #                 break
    #             elif file_info.status == "error":
    #                 raise Exception("OpenAI failed to process PDF.")
    #             await asyncio.sleep(1)

    #         # 3. Gọi Chat Completion với type chuẩn (Sửa lỗi 400)
    #         # Theo lỗi báo: Supported values are: 'text', 'image_url', 'input_audio', 'refusal', 'audio', and 'file'.
    #         response = await asyncio.to_thread(
    #             self.raw_client.chat.completions.create,
    #             model=self.model_name,
    #             max_completion_tokens=max_tokens,
    #             messages=[
    #                 {
    #                     "role": "user",
    #                     "content": [
    #                         {
    #                             "type": "text",
    #                             "text": prompt
    #                         },
    #                         {
    #                             "type": "file",
    #                             "file": {
    #                                 "file_id": uploaded_file.id
    #                             }
    #                         }
    #                     ]
    #                 }
    #             ],
    #             temperature=temperature,
    #             response_format={"type": "json_object"} if schema else None
    #         )
                        
    #         return response.choices[0].message.content

    #     except Exception as e:
    #         logger.error(f"❌ Lỗi OpenAI solute: {str(e)}")
    #         raise e

    def split_pdf_text(self,pdf_path, pages_per_chunk=2):
        doc = fitz.open(pdf_path)

        chunks = []

        current_chunk = []

        for i, page in enumerate(doc):
            text = page.get_text()

            current_chunk.append(
                f"\n\n===== PAGE {i + 1} =====\n\n{text}"
            )

            if (i + 1) % pages_per_chunk == 0:
                chunks.append("\n".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks


    async def process_chunk(
        self,
        chunk_text,
        prompt,
        schema=None,
        temperature=1.0,
        max_tokens=12000
    ):

        response = await asyncio.to_thread(
            self.raw_client.responses.create,

            model=self.model_name,

            input=f"""
    {prompt}

    IMPORTANT:
    - Extract ALL questions completely
    - DO NOT summarize
    - DO NOT skip content
    - Preserve exact numbering
    - Return valid JSON only

    PDF CONTENT:

    {chunk_text}
            """,


            max_output_tokens=max_tokens,
            service_tier=self.client_wrapper.service_tier
        )

        output_text = ""

        if hasattr(response, "output"):
            for item in response.output:
                if item.type == "message":
                    for content in item.content:
                        if content.type == "output_text":
                            output_text += content.text

        return output_text
    
#     async def solute(
#     self,
#     prompt,
#     pdf_path,
#     schema=None,
#     temperature=1.0,
#     max_tokens=128000
# ):
#         try:
#             # 1. Upload PDF
#             with open(pdf_path, "rb") as f:
#                 uploaded_file = await asyncio.to_thread(
#                     self.raw_client.files.create,
#                     file=f,
#                     purpose="user_data"
#                 )

#             logger.info(f"⏳ Upload thành công file: {uploaded_file.id}")

#             # 2. Wait until processed
#             while True:
#                 file_info = await asyncio.to_thread(
#                     self.raw_client.files.retrieve,
#                     uploaded_file.id
#                 )

#                 status = getattr(file_info, "status", None)

#                 logger.info(f"📄 File status: {status}")

#                 if status == "processed":
#                     break

#                 if status == "error":
#                     raise Exception("OpenAI failed to process PDF.")

#                 await asyncio.sleep(1)

#             # 3. Responses API
#             response = await asyncio.to_thread(
#                 self.raw_client.responses.create,

#                 model=self.model_name,

#                 input=[
#                     {
#                         "role": "user",
#                         "content": [
#                             {
#                                 "type": "input_text",
#                                 "text": f"""
#     {prompt}

#     IMPORTANT:
#     - Extract ALL content completely
#     - DO NOT summarize
#     - DO NOT skip any questions
#     - Preserve all question numbers
#     - Preserve all answer choices
#     - Return full JSON
#     - Continue until ALL pages are processed
#     """
#                             },
#                             {
#                                 "type": "input_file",
#                                 "file_id": uploaded_file.id
#                             }
#                         ]
#                     }
#                 ],

#                 temperature=temperature,

#                 max_output_tokens=max_tokens
#             )

#             # 4. Extract output text
#             output_text = ""

#             if hasattr(response, "output"):
#                 for item in response.output:
#                     if item.type == "message":
#                         for content in item.content:
#                             if content.type == "output_text":
#                                 output_text += content.text

#             return output_text

#         except Exception as e:
#             logger.error(f"❌ Lỗi OpenAI solute: {str(e)}")
#             raise e

    async def solute(
        self,
        prompt,
        pdf_path,
        schema=None,
        temperature=1.0,
        max_tokens=65536
    ):
        try:
            # 1. Split PDF thành chunks
            chunks = self.split_pdf_text(
                pdf_path,
                pages_per_chunk=2
            )

            logger.info(f"📄 Total chunks: {len(chunks)}")

            final_combined_list = [] # Mảng chứa kết quả gộp

            # 2. Process từng chunk
            for idx, chunk in enumerate(chunks):
                logger.info(f"🚀 Processing chunk {idx + 1}")

                chunk_raw_text = await self.process_chunk(
                    chunk_text=chunk,
                    prompt=prompt,
                    schema=schema,
                    temperature=temperature,
                    max_tokens=128000
                )

                # --- PHẦN SỬA ĐỔI QUAN TRỌNG ---
                # Parse chunk này thành object python
                try:
                    # Dùng lại hàm xử lý JSON an toàn (nên import từ utils nếu có thể)
                    # Ở đây tôi ví dụ parse trực tiếp
                    from .json_utils import _safe_parse_json # Đảm bảo file này tồn tại
                    parsed_chunk = _safe_parse_json(chunk_raw_text)
                    
                    if isinstance(parsed_chunk, list):
                        final_combined_list.extend(parsed_chunk)
                    elif isinstance(parsed_chunk, dict):
                        final_combined_list.append(parsed_chunk)
                    
                    logger.info(f"✅ Chunk {idx + 1} parsed and merged.")
                except Exception as e:
                    logger.error(f"❌ Failed to parse chunk {idx + 1}: {e}")
                    # Optional: Lưu text thô nếu parse lỗi để debug
                    continue

            # Trả về chuỗi JSON duy nhất hợp lệ
            return json.dumps(final_combined_list, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ Lỗi OpenAI solute: {str(e)}")
            raise e
