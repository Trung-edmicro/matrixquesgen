import asyncio
from google import genai
from google.genai import types


class AsyncVertexGemini31:

    def __init__(
        self,
        project_id: str,
        model: str = "gemini-3.1-pro-preview",
        thinking_level: str = "HIGH"
    ):
        """
        Gemini 3.1 Async Client for Vertex AI

        thinking_level:
        - MINIMAL
        - LOW
        - MEDIUM
        - HIGH
        """

        self.project_id = project_id
        self.model = model

        thinking_map = {
            # "MINIMAL": types.ThinkingConfig(thinking_level = "mini"),
            "LOW": types.ThinkingConfig(thinking_level = "low"),
            "MEDIUM": types.ThinkingConfig(thinking_level = "medium"),
            "HIGH": types.ThinkingConfig(thinking_level = "high")
        }

        self.thinking_level = thinking_map.get(
            thinking_level.upper(),
            types.ThinkingConfig(thinking_level = "high")
        )

        self.client = genai.Client()

    # ===================================
    # INTERNAL SYNC CALL
    # ===================================

    def _generate_sync(
        self,
        prompt,
        temperature=1.0,
        max_tokens=64000
    ):

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(
                    thinking_level=self.thinking_level
                )
            )
        )

        if response.text:
            return response.text

        return ""

    # ===================================
    # ASYNC WRAPPER
    # ===================================

    async def generate(
        self,
        prompt: str,
        temperature: float = 1.0,
        max_tokens: int = 64000
    ):

        return await asyncio.to_thread(
            self._generate_sync,
            prompt,
            temperature,
            max_tokens
        )