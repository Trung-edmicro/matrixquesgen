"""
Module tương tác với OpenAI Responses API để sử dụng GPT models.
Interface tương thích với GenAIClient để dễ dàng hoán đổi.

Sử dụng OpenAI Responses API (client.responses.create) theo tài liệu chính thức:
https://developers.openai.com/api/docs/quickstart
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, Any

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config.settings import Config as Settings


# ── Đường dẫn file cấu hình OpenAI ──────────────────────────────────────────
def _get_sa_dir() -> Path:
    """Lấy đường dẫn thư mục SA.
    Ưu tiên: SA_DIR (temp, frozen app) > DATA_DIR/SA > dev path."""
    sa_dir = os.environ.get('SA_DIR')
    if sa_dir:
        return Path(sa_dir)
    data_dir = os.environ.get('DATA_DIR')
    if data_dir:
        return Path(data_dir) / "SA"
    return Path(__file__).parent.parent.parent.parent.parent / "data" / "SA"

_SA_DIR = _get_sa_dir()
_OPENAI_CFG_FILE = _SA_DIR / "sinh-de-ma-tran-open-syscfg.bin.json"


def _load_openai_api_key() -> Optional[str]:
    """Đọc openai_api_key từ file cấu hình."""
    try:
        if _OPENAI_CFG_FILE.exists():
            with open(_OPENAI_CFG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("open_api_key") or cfg.get("openai_api_key")
    except Exception as e:
        print(f"⚠️  Không đọc được cấu hình OpenAI: {e}")
    # Fallback sang biến môi trường
    return os.getenv("OPENAI_API_KEY")


class OpenAIClient:
    """
    Client gọi OpenAI Responses API với interface tương thích GenAIClient.

    Sử dụng Responses API (client.responses.create) – API được khuyến nghị
    bởi OpenAI theo tài liệu mới nhất.

    Các method công khai:
      - generate_content(prompt, system_instruction, enable_search)
      - generate_content_with_schema(prompt, response_schema, system_instruction, enable_search)
      - generate_content_with_schema_with_model(prompt, response_schema, model_name,
                                                 system_instruction, enable_search, enable_thinking)
    Thuộc tính:
      - model_name  (str)
    """

    # Model mặc định
    DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
    FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-5.4-mini")

    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "Thư viện 'openai' chưa được cài đặt. "
                "Chạy: pip install openai"
            )

        resolved_key = api_key or _load_openai_api_key()
        if not resolved_key:
            raise ValueError(
                "Không tìm thấy OpenAI API key. "
                "Kiểm tra file cấu hình hoặc biến môi trường OPENAI_API_KEY."
            )

        self.client = OpenAI(api_key=resolved_key)
        self.model_name: str = self.DEFAULT_MODEL
        print(f"✓ Đã kết nối OpenAI Responses API - model mặc định: {self.model_name}")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_input(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> list:
        """Xây dựng input array cho Responses API."""
        parts = []
        if system_instruction:
            parts.append({"role": "system", "content": system_instruction})
        parts.append({"role": "user", "content": prompt})
        return parts

    def _log_usage(self, response) -> None:
        """Log token usage từ Responses API."""
        usage = getattr(response, "usage", None)
        if usage:
            print(
                f"📊 OpenAI token usage: "
                f"input={getattr(usage, 'input_tokens', '?')}, "
                f"output={getattr(usage, 'output_tokens', '?')}, "
                f"total={getattr(usage, 'total_tokens', '?')}",
                flush=True,
            )

    def _check_response_status(self, response) -> None:
        """Kiểm tra trạng thái response từ Responses API."""
        status = getattr(response, "status", None)
        if status and status != "completed":
            print(f"⚠️  OpenAI response status: {status}")
            if status == "incomplete":
                details = getattr(response, "incomplete_details", None)
                reason = getattr(details, "reason", "unknown") if details else "unknown"
                if reason == "max_output_tokens":
                    raise Exception("OpenAI response truncated (max_output_tokens reached).")
                raise Exception(f"OpenAI response incomplete: {reason}")
            elif status == "failed":
                error = getattr(response, "error", None)
                raise Exception(f"OpenAI response failed: {error}")

    # ── public API ──────────────────────────────────────────────────────────

    def initialize_model(self, model_name: Optional[str] = None, generation_config: Optional[Dict] = None):
        """Khởi tạo / đổi model (tương thích GenAIClient)."""
        self.model_name = model_name or self.DEFAULT_MODEL
        print(f"✓ Đã khởi tạo OpenAI model: {self.model_name}")

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        enable_search: bool = False,
    ) -> str:
        """
        Sinh nội dung từ prompt (text tự do) dùng Responses API.

        Args:
            prompt: Prompt đầu vào
            system_instruction: Hướng dẫn hệ thống
            enable_search: Ignored (dùng web_search tool nếu cần, hiện không bật)

        Returns:
            str: Nội dung sinh ra
        """
        try:
            input_msgs = self._build_input(prompt, system_instruction)
            response = self.client.responses.create(
                model=self.model_name,
                input=input_msgs,
                temperature=Settings.VERTEX_AI_TEMPERATURE,
                top_p=Settings.VERTEX_AI_TOP_P,
                max_output_tokens=Settings.VERTEX_AI_MAX_OUTPUT_TOKENS,
            )
            self._log_usage(response)
            self._check_response_status(response)
            return response.output_text or ""
        except Exception as e:
            print(f"✗ Lỗi OpenAI generate_content: {e}")
            raise

    def generate_content_with_schema(
        self,
        prompt: str,
        response_schema: Dict,
        system_instruction: Optional[str] = None,
        enable_search: bool = False,
    ) -> str:
        """
        Sinh nội dung JSON theo schema dùng Responses API.
        Thử Structured Outputs (json_schema strict) trước;
        fall back về json_object mode nếu schema không tương thích.

        Returns:
            str: JSON string
        """
        return self._call_with_structured_output(
            prompt=prompt,
            response_schema=response_schema,
            model=self.model_name,
            system_instruction=system_instruction,
        )

    def generate_content_with_schema_with_model(
        self,
        prompt: str,
        response_schema: Dict,
        model_name: str,
        system_instruction: Optional[str] = None,
        enable_search: bool = False,
        enable_thinking: bool = True,
    ) -> str:
        """
        Sinh nội dung JSON theo schema với model cụ thể dùng Responses API.

        Returns:
            str: JSON string
        """
        return self._call_with_structured_output(
            prompt=prompt,
            response_schema=response_schema,
            model=model_name,
            system_instruction=system_instruction,
        )

    # ── internal ─────────────────────────────────────────────────────────────

    def _call_with_structured_output(
        self,
        prompt: str,
        response_schema: Dict,
        model: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Gọi Responses API với Structured Outputs.

        Ưu tiên json_schema strict mode (schema-enforced output).
        Fall back về json_object mode (valid JSON) nếu schema không đáp ứng
        yêu cầu strict mode của OpenAI (ví dụ: thiếu additionalProperties: false,
        có unsupported keywords, v.v.).

        Tham khảo: https://developers.openai.com/api/docs/guides/structured-outputs
        """
        input_msgs = self._build_input(prompt, system_instruction)

        # ── Thử Structured Outputs (json_schema strict) ──────────────────────
        try:
            response = self.client.responses.create(
                model=model,
                input=input_msgs,
                temperature=Settings.VERTEX_AI_TEMPERATURE,
                top_p=Settings.VERTEX_AI_TOP_P,
                max_output_tokens=Settings.VERTEX_AI_MAX_OUTPUT_TOKENS,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "structured_output",
                        "schema": response_schema,
                        "strict": True,
                    }
                },
            )
            self._log_usage(response)
            self._check_response_status(response)
            return response.output_text or ""
        except Exception as strict_err:
            # Schema không tương thích strict mode → fall back
            print(
                f"⚠️  OpenAI strict JSON schema không tương thích "
                f"({type(strict_err).__name__}), chuyển sang json_object mode"
            )

        # ── Fall back: json_object mode + schema nhúng trong prompt ──────────
        schema_hint = (
            "\n\n**YÊU CẦU FORMAT OUTPUT**: Trả về JSON thuần (raw JSON) theo schema sau:\n"
            f"```json\n{json.dumps(response_schema, ensure_ascii=False, indent=2)}\n```\n"
            "KHÔNG bọc trong markdown code block, KHÔNG thêm text ngoài JSON."
        )
        fallback_input = self._build_input(prompt + schema_hint, system_instruction)

        try:
            response = self.client.responses.create(
                model=model,
                input=fallback_input,
                temperature=Settings.VERTEX_AI_TEMPERATURE,
                top_p=Settings.VERTEX_AI_TOP_P,
                max_output_tokens=Settings.VERTEX_AI_MAX_OUTPUT_TOKENS,
                text={"format": {"type": "json_object"}},
            )
            self._log_usage(response)
            self._check_response_status(response)

            text = (response.output_text or "").strip()
            # Làm sạch markdown fence nếu model vẫn thêm vào
            if text.startswith("```"):
                text = text[7:] if text.startswith("```json") else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            return text

        except Exception as e:
            print(f"✗ Lỗi OpenAI _call_with_structured_output (model={model}): {e}")
            raise
