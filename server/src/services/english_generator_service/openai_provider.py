import asyncio

from .llm_provider import BaseLLMProvider
from services.core.openai_client import OpenAIClient


class OpenAIProvider(BaseLLMProvider):

    def __init__(self, model="gpt-5.4"):
        self.client = OpenAIClient()
        self.client.initialize_model(model)

    async def generate(
        self,
        prompt,
        schema=None,
        temperature=1.0,
        max_tokens=64000
    ):

        if schema:
            return await asyncio.to_thread(
                self.client.generate_content_with_schema,
                prompt,
                schema
            )

        return await asyncio.to_thread(
            self.client.generate_content,
            prompt
        )