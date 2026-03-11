"""
Session Generation History
Thread-safe in-memory tracker of questions already generated in a single exam session.
Used to inject context into subsequent AI prompts to prevent duplicate questions within
the same exam (session).
"""
import threading
from typing import Optional


class SessionGenerationHistory:
    """
    Per-session tracker of generated question stems.

    Keys: (chapter, lesson, q_type) → list of {"code", "stem", "level"}
    All operations are thread-safe via an internal lock.

    Usage in generation flow:
    1. Create ONE instance per exam generation call.
    2. After each question is generated, call .add() to record its stem.
    3. Before the next question in the same (chapter, lesson, type) group,
       call .format_context() to get the "already generated" block to inject
       into the AI prompt.
    """

    MAX_STEM_LENGTH = 350  # Truncate stems to keep prompts compact

    def __init__(self):
        self._lock = threading.Lock()
        # key: (chapter, lesson, q_type) → list[{"code", "stem", "level"}]
        self._data: dict = {}

    def add(self, chapter: str, lesson: str, q_type: str,
            code: str, stem: str, level: str = "") -> None:
        """Record a generated question."""
        key = (str(chapter), str(lesson), q_type)
        entry = {
            "code": code,
            "stem": str(stem)[:self.MAX_STEM_LENGTH],
            "level": level,
        }
        with self._lock:
            self._data.setdefault(key, []).append(entry)

    def format_context(self, chapter: str, lesson: str, q_type: str) -> str:
        """Return a formatted history block to inject into a prompt.
        Returns empty string if no history exists for this key."""
        key = (str(chapter), str(lesson), q_type)
        with self._lock:
            items = list(self._data.get(key, []))
        if not items:
            return ""

        sep = "=" * 65
        if q_type == "DS":
            header = (
                "DANH SÁCH TƯ LIỆU/ĐỀ BÀI (DS) ĐÃ SINH TRONG ĐỀ NÀY\n"
                "⛔ KHÔNG dùng nguồn tư liệu, sự kiện hoặc nhân vật tương tự:"
            )
            lines = [f"  - [{q['code']}]: {q['stem']}" for q in items]
        else:
            header = (
                f"DANH SÁCH CÂU HỎI ({q_type}) ĐÃ SINH TRONG ĐỀ NÀY\n"
                "⛔ KHÔNG tạo câu tương tự về nội dung, sự kiện, nhân vật hoặc cách đặt câu:"
            )
            lines = [f"  - [{q['code']}] ({q['level']}): {q['stem']}" for q in items]

        return (
            f"\n\n{sep}\n"
            "⚠️  LỊCH SỬ SINH ĐỀ — ĐỌC KỸ TRƯỚC KHI SINH CÂU TIẾP THEO\n"
            f"{sep}\n"
            f"{header}\n"
            + "\n".join(lines)
            + f"\n{sep}\n"
        )

    @staticmethod
    def extract_stem(generated_question) -> str:
        """Extract a plain-text stem/source from a generated question object."""
        # DS questions have source_text; TN/TLN/TL have question_stem
        raw = (
            getattr(generated_question, 'source_text', None)
            or getattr(generated_question, 'question_stem', None)
            or ""
        )
        return SessionGenerationHistory._flatten(raw)

    @staticmethod
    def _flatten(value) -> str:
        """Recursively flatten rich-content dicts/lists to plain text."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            content = value.get('content', value.get('text', ''))
            if isinstance(content, list):
                parts = [SessionGenerationHistory._flatten(c) for c in content if c]
                return ' '.join(p for p in parts if p).strip()
            return SessionGenerationHistory._flatten(content)
        if isinstance(value, list):
            parts = [SessionGenerationHistory._flatten(c) for c in value if c]
            return ' '.join(p for p in parts if p).strip()
        return str(value) if value else ""

    @staticmethod
    def build_context_from_question_dicts(question_type: str, questions: list) -> str:
        """
        Build a formatted history context string from a list of existing question dicts
        (e.g. loaded from session JSON).  Used by the regenerate API.

        Args:
            question_type: 'TN', 'DS', 'TLN', 'TL'
            questions: list of question dicts from session data
        """
        if not questions:
            return ""

        items = []
        for q in questions:
            code = q.get('question_code', '')
            level = q.get('level', q.get('difficulty', ''))
            if question_type == 'DS':
                raw_stem = q.get('source_text', '')
            else:
                raw_stem = q.get('question_stem', '')
            stem = SessionGenerationHistory._flatten(raw_stem)
            if stem or code:
                items.append({
                    'code': code,
                    'stem': str(stem)[:SessionGenerationHistory.MAX_STEM_LENGTH],
                    'level': level,
                })

        if not items:
            return ""

        sep = "=" * 65
        if question_type == "DS":
            header = (
                "DANH SÁCH TƯ LIỆU/ĐỀ BÀI (DS) ĐÃ TỒN TẠI TRONG ĐỀ NÀY\n"
                "⛔ KHÔNG dùng nguồn tư liệu, sự kiện hoặc nhân vật tương tự:"
            )
            lines = [f"  - [{q['code']}]: {q['stem']}" for q in items]
        else:
            header = (
                f"DANH SÁCH CÂU HỎI ({question_type}) ĐÃ TỒN TẠI TRONG ĐỀ NÀY\n"
                "⛔ KHÔNG tạo câu tương tự về nội dung, sự kiện, nhân vật hoặc cách đặt câu:"
            )
            lines = [f"  - [{q['code']}] ({q['level']}): {q['stem']}" for q in items]

        return (
            f"\n\n{sep}\n"
            "⚠️  CÂU HỎI ĐÃ CÓ TRONG ĐỀ — ĐỌC KỸ TRƯỚC KHI SINH CÂU MỚI\n"
            f"{sep}\n"
            f"{header}\n"
            + "\n".join(lines)
            + f"\n{sep}\n"
        )
