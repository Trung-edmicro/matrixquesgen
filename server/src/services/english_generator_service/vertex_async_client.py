import os
import asyncio
import vertexai
from vertexai.generative_models._generative_models import _GenerativeModel, Part, GenerationConfig
from google.api_core import exceptions as google_exceptions


class AsyncVertexClient:

    def __init__(self, project_id, creds, model, region="us-central1"):
        vertexai.init(
            project=project_id,
            location=region,
            credentials=creds
        )
        self.model = _GenerativeModel(model)

    # ==============================
    # INTERNAL SYNC CALL
    # ==============================
    def _generate_sync(self, parts, generation_config):
        response = self.model.generate_content(
            parts,
            generation_config=generation_config
        )

        candidate = response.candidates[0]

        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            full_text = "".join(
                part.text for part in candidate.content.parts
                if hasattr(part, 'text') and part.text is not None
            )
        else:
            full_text = response.text if response.text else ""

        return full_text

    # ==============================
    # ASYNC WRAPPER
    # ==============================
    async def generate(
        self,
        prompt,
        file_paths=None,
        temperature=1,
        top_p=0.1,
        max_tokens=65355
    ):

        parts = []

        # Attach files if any
        if file_paths:
            for file_path in file_paths:
                ext = os.path.splitext(file_path)[1].lower()

                if ext == ".pdf":
                    mime_type = "application/pdf"
                elif ext == ".docx":
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif ext == ".md":
                    mime_type = "text/markdown"
                else:
                    continue

                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                parts.append(
                    Part.from_data(data=file_bytes, mime_type=mime_type)
                )

        parts.append(Part.from_text(prompt))

        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
            candidate_count=1
        )

        try:
            # 🔥 CHUYỂN CALL SANG THREAD
            return await asyncio.to_thread(
                self._generate_sync,
                parts,
                generation_config
            )

        except google_exceptions.InvalidArgument as e:
            raise Exception(f"Vertex InvalidArgument: {e}")

        except Exception as e:
            raise Exception(f"Vertex Error: {e}")