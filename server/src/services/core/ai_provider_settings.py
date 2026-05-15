"""
Service quản lý cài đặt AI provider (Gemini / OpenAI).
Đọc/ghi từ file JSON trong data/SA/.
"""
import json
import os
import threading
from pathlib import Path
from typing import Literal

AI_PROVIDER_GEMINI = "gemini"
AI_PROVIDER_OPENAI = "openai"
AIProvider = Literal["gemini", "openai"]

_SETTINGS_FILE_NAME = "ai-provider-settings.json"
_DEFAULT_PROVIDER: AIProvider = AI_PROVIDER_GEMINI

_lock = threading.Lock()


def _get_settings_path() -> Path:
    """Trả về đường dẫn file cài đặt AI provider."""
    # Ưu tiên DATA_DIR từ launcher.py (frozen app)
    # Nếu không có, tính toán từ __file__ (development mode)
    data_dir = os.environ.get('DATA_DIR')
    if data_dir:
        base = Path(data_dir) / "SA"
    else:
        # Dò từ vị trí file này lên đến thư mục data/SA
        base = Path(__file__).parent.parent.parent.parent.parent / "data" / "SA"
    base.mkdir(parents=True, exist_ok=True)
    return base / _SETTINGS_FILE_NAME


def get_ai_provider() -> AIProvider:
    """
    Đọc AI provider hiện tại từ file cài đặt.
    Trả về "gemini" hoặc "openai". Mặc định là "gemini".
    """
    path = _get_settings_path()
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            provider = data.get("ai_provider", _DEFAULT_PROVIDER)
            if provider in (AI_PROVIDER_GEMINI, AI_PROVIDER_OPENAI):
                return provider
    except Exception:
        pass
    return _DEFAULT_PROVIDER


def set_ai_provider(provider: AIProvider) -> None:
    """
    Ghi AI provider vào file cài đặt.

    Args:
        provider: "gemini" hoặc "openai"

    Raises:
        ValueError: Nếu provider không hợp lệ
    """
    if provider not in (AI_PROVIDER_GEMINI, AI_PROVIDER_OPENAI):
        raise ValueError(f"AI provider không hợp lệ: {provider!r}. Phải là 'gemini' hoặc 'openai'.")

    path = _get_settings_path()
    with _lock:
        existing: dict = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}
        existing["ai_provider"] = provider
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)


def create_ai_client():
    """
    Factory: tạo và trả về AI client tương ứng với cài đặt hiện tại.

    Returns:
        GenAIClient hoặc OpenAIClient (cùng interface)

    Raises:
        Exception nếu khởi tạo client thất bại
    """
    provider = get_ai_provider()

    if provider == AI_PROVIDER_OPENAI:
        from services.core.openai_client import OpenAIClient
        return OpenAIClient()
    else:
        # Mặc định: Gemini
        import os
        from services.core.genai_client import GenAIClient
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        api_key = os.getenv("GENAI_API_KEY", "")

        credentials = None
        if not api_key:
            # Ưu tiên 1: env vars (PRIVATE_KEY, PROJECT_ID, ...) — cùng cách callApi.py
            # Đây là credentials đã được xác nhận hoạt động cho English generation.
            # Dùng làm nguồn chính để tránh SA file có key bị revoke.
            if os.getenv("PRIVATE_KEY"):
                try:
                    from api.callApi import get_vertex_ai_credentials
                    credentials = get_vertex_ai_credentials()
                    if credentials:
                        if not project_id:
                            project_id = os.getenv("PROJECT_ID", "")
                        print("✓ GenAI: dùng credentials từ env vars (PRIVATE_KEY)")
                except Exception as _e:
                    print(f"⚠ GenAI: không load được env var credentials: {_e}")

            # Ưu tiên 2: file SA (chỉ khi không có env vars)
            if not credentials and credentials_path and os.path.isfile(credentials_path):
                print(f"✓ GenAI: dùng credentials từ file SA")
                # GenAIClient._initialize() sẽ load file này

        return GenAIClient(
            project_id=project_id,
            credentials_path=credentials_path if not credentials else None,
            credentials=credentials,
            api_key=api_key,
        )
