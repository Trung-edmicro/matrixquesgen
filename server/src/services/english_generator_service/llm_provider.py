from abc import ABC, abstractmethod
from typing import Optional

class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        temperature: float = 1.0,
        max_tokens: int = 64000
    ):
        pass