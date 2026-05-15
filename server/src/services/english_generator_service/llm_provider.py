from abc import ABC, abstractmethod
from typing import Any, Optional

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
    
    @abstractmethod
    async def solute(
        self,
        prompt: str,
        pdf_path: str,
        schema: Optional[Any] = None,
        temperature: float = 1.0,
        max_tokens: int = 65536
    ):
        pass