"""
API endpoints cho cài đặt AI provider (Gemini / OpenAI).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.core.ai_provider_settings import (
    get_ai_provider,
    set_ai_provider,
    AI_PROVIDER_GEMINI,
    AI_PROVIDER_OPENAI,
)

router = APIRouter(
    prefix="/api/ai-settings",
    tags=["AI Settings"],
)


class AIProviderResponse(BaseModel):
    ai_provider: str
    available_providers: list


class SetAIProviderRequest(BaseModel):
    ai_provider: str


@router.get("", response_model=AIProviderResponse)
async def get_current_ai_provider():
    """Lấy AI provider hiện tại đang được cài đặt."""
    return AIProviderResponse(
        ai_provider=get_ai_provider(),
        available_providers=[AI_PROVIDER_GEMINI, AI_PROVIDER_OPENAI],
    )


@router.post("", response_model=AIProviderResponse)
async def set_current_ai_provider(request: SetAIProviderRequest):
    """
    Thay đổi AI provider.

    - **ai_provider**: "gemini" hoặc "openai"
    """
    if request.ai_provider not in (AI_PROVIDER_GEMINI, AI_PROVIDER_OPENAI):
        raise HTTPException(
            status_code=400,
            detail=f"AI provider không hợp lệ: '{request.ai_provider}'. Phải là 'gemini' hoặc 'openai'.",
        )
    try:
        set_ai_provider(request.ai_provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return AIProviderResponse(
        ai_provider=get_ai_provider(),
        available_providers=[AI_PROVIDER_GEMINI, AI_PROVIDER_OPENAI],
    )
