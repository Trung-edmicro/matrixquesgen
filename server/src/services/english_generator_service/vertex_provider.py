from .llm_provider import BaseLLMProvider

class VertexProvider(BaseLLMProvider):

    def __init__(self, client_31, client_25=None):
        self.client_31 = client_31
        self.client_25 = client_25

    async def generate(
        self,
        prompt,
        schema=None,
        temperature=1.0,
        max_tokens=64000
    ):
        try:
            return await self.client_31.generate(
                prompt=prompt,
                schema=schema,
                temperature=temperature,
                max_tokens=max_tokens
            )

        except Exception as e:

            error_msg = str(e).upper()

            if (
                self.client_25
                and ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg)
            ):
                return await self.client_25.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            raise