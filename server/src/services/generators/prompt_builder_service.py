"""
Prompt Builder Service
Single source of truth for building all prompt strings before AI generation.
Replaces the duplicate prompt-building logic that was scattered in QuestionGenerator.
"""
import re
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from ..core.matrix_parser import QuestionSpec, TrueFalseQuestionSpec

# Types that require rich content (table/chart/image)
PRIMARY_RICH_TYPES = ['BD', 'BK']   # Biểu đồ, Bảng khảo


@dataclass
class PreparedPrompt:
    """Fully assembled prompt string ready to send to the AI."""
    prompt_text: str
    question_type: str          # TN | DS | TLN | TL
    lesson_name: str
    question_spec: object       # QuestionSpec or TrueFalseQuestionSpec
    has_content: bool
    content_length: int
    question_template: str = ""
    has_chart: bool = False     # True when BD type detected → chart pre-generation needed
    template_path: str = ""    # Resolved template file name (for logging/debug)


class PromptBuilderService:
    """
    Builds all prompt strings for question generation.
    Single source of truth — replaces duplicate logic in QuestionGenerator.
    """

    def __init__(self, prompt_dir: str = None, verbose: bool = False):
        self.verbose = verbose
        self.prompt_dir = Path(prompt_dir) if prompt_dir else None
        self.templates: Dict[str, str] = {}
        self._rich_guide_cache: Optional[str] = None
        self._cognitive_level_cache: Dict[str, str] = {}
        self._cognitive_level_dir = Path(__file__).parent.parent / "prompts" / "cognitive_level"
        if self.prompt_dir:
            self.load_templates()

    def set_prompt_dir(self, prompt_dir: str):
        """Update directory and reload templates."""
        self.prompt_dir = Path(prompt_dir)
        self.templates = {}
        self._rich_guide_cache = None
        self._cognitive_level_cache = {}
        self.load_templates()

    def load_templates(self):
        """Load TN/DS/TLN/TL prompt files. Tries TN2.txt before TN.txt."""
        files = {
            'TN':  ['TN2.txt', 'TN.txt'],
            'DS':  ['DS.txt'],
            'TLN': ['TLN.txt'],
            'TL':  ['TL.txt'],
        }
        for q_type, candidates in files.items():
            for filename in candidates:
                path = self.prompt_dir / filename
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        self.templates[q_type] = f.read()
                    if self.verbose:
                        print(f"✓ PromptBuilderService loaded: {filename}")
                    break

    def get_template(self, q_type: str) -> str:
        return self.templates.get(q_type, '')

    def _load_cognitive_level_desc(self, level: str) -> str:
        """Load cognitive level description from cognitive_level/<LEVEL>.md. Cached."""
        if not level:
            return ""
        level_upper = level.strip().upper()
        if level_upper in self._cognitive_level_cache:
            return self._cognitive_level_cache[level_upper]
        path = self._cognitive_level_dir / f"{level_upper}.md"
        if path.exists():
            content = path.read_text(encoding='utf-8').strip()
            self._cognitive_level_cache[level_upper] = content
            return content
        self._cognitive_level_cache[level_upper] = ""
        return ""

    def _load_rich_content_guide(self) -> str:
        """Load rich_content_guide.txt. Cached."""
        if self._rich_guide_cache is not None:
            return self._rich_guide_cache
        base = Path(__file__).parent.parent / "prompts" / "rich_content_guide"
        path = base / "rich_content_guide.txt"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                guide = f.read()
            self._rich_guide_cache = guide
            return guide
        self._rich_guide_cache = ""
        return ""

    @staticmethod
    def _convert_content_to_string(content) -> str:
        if isinstance(content, list):
            return "\n".join(str(item) for item in content)
        if content:
            return str(content)
        return "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách giáo khoa theo Chương trình GDPT 2018 của Việt Nam."

    def _should_inject_rich_guide(self, spec) -> bool:
        """Inject rich_content_guide only when the question spec contains BK (bảng khảo).
        BD (biểu đồ) is generated separately in its own step, so it does not need this guide.
        LT/TT are text-only types and never need the guide.
        """
        rct = getattr(spec, 'rich_content_types', None)
        if not rct or not isinstance(rct, dict):
            return False
        for types_list in rct.values():
            if not isinstance(types_list, list):
                continue
            for type_obj in types_list:
                code = type_obj.get('code', '') if isinstance(type_obj, dict) else str(type_obj)
                if code == 'BK':
                    return True
        return False

    def _format_supplementary(self, supplementary_materials: str, for_ds: bool = False) -> str:
        if supplementary_materials:
            hint = ("Hãy ưu tiên sử dụng các thông tin từ tài liệu này để tạo đoạn tư liệu sinh động."
                    if for_ds else
                    "Hãy tham khảo các thông tin này khi tạo câu hỏi.")
            return f"```\n{supplementary_materials}\n```\n\n**✓ Có tài liệu bổ sung** - {hint}"
        return "_Không có tài liệu bổ sung. Tự tổng hợp từ kiến thức INPUT DATA._"

    def _format_rich_content_types(self, spec: QuestionSpec) -> str:
        """Full rich_content_types formatter for TN/TLN/TL."""
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return ('**YÊU CẦU NỘI DUNG**: Câu hỏi này không có đánh dấu BD/BK/HA trong ma trận.\n'
                    '⏩ **BẮT BUỘC**: Chỉ dùng **text thuần** (type="text"), KHÔNG dùng table/chart/image/mixed.\n'
                    '⏩ question_stem PHẢI là: {"type": "text", "content": "..."}\n'
                    '⚠️ **NỘI DUNG CÂU HỎI**: KHÔNG viết câu hỏi yêu cầu học sinh "dựa vào bảng số liệu", "nhìn vào biểu đồ", "căn cứ vào hình" hay bất kỳ tư liệu nào không được nhúng trực tiếp trong câu hỏi. Câu hỏi phải tự đủ – chỉ dựa trên kiến thức SGK và lý thuyết.\n'
                    '⚠️ **CÔNG THỨC TOÁN**: BẮT BUỘC dùng LaTeX (bọc trong $...$). VD: $x^2 + 2x + 1$')
        SECONDARY_TYPES = {'LT', 'TT'}
        primary_found: Dict[str, List[str]] = {}
        secondary_found: Dict[str, List[str]] = {}
        try:
            if not isinstance(spec.rich_content_types, dict):
                return '**YÊU CẦU NỘI DUNG**: Câu hỏi thuần text.'
            for code, types_list in spec.rich_content_types.items():
                if not isinstance(types_list, list):
                    continue
                for type_obj in types_list:
                    # Xử lý cả format cũ (code) và format mới (type)
                    if isinstance(type_obj, dict):
                        # Format mới: {"type": "BD", "chart_type": "bar", ...}
                        # Format cũ: {"code": "BD", "name": "...", ...}
                        type_code = type_obj.get('type') or type_obj.get('code', '')
                        type_name_val = type_obj.get('name', type_code)
                        type_name = f"{type_code} ({type_name_val})" if type_name_val else type_code
                    else:
                        # String format (rất hiếm)
                        type_code = str(type_obj)
                        type_name = type_code
                    if type_code in SECONDARY_TYPES:
                        secondary_found.setdefault(code, []).append(type_name)
                    else:
                        primary_found.setdefault(code, []).append(type_name)
        except Exception as exc:
            print(f"⚠️ PromptBuilderService._format_rich_content_types error: {exc}")
            traceback.print_exc()
            return '**YÊU CẦU NỘI DUNG**: Câu hỏi thuần text (lỗi xử lý).'
        if not primary_found:
            lines = ["**YÊU CẦU NỘI DUNG**: Câu hỏi thuần text (không có BD/BK/HA)"]
            if secondary_found:
                for code, names in secondary_found.items():
                    lines.append(f"  • Câu {code}: {', '.join(names)} (chỉ dạng text)")
            lines += ["",
                      '⏩ **BẮT BUỘC**: Tất cả câu hỏi dùng **text thuần** (type="text").',
                      '⏩ question_stem PHẢI là: {"type": "text", "content": "..."}',
                      '⚠️ **CÔNG THỨC TOÁN**: BẮT BUỘC dùng LaTeX (bọc trong $...$). VD: $x^2 + 2x + 1$']
            return "\n".join(lines)
        lines = ["**YÊU CẦU:** Các câu hỏi sau cần tạo với rich content (BD/BK/HA):"]
        for code, names in primary_found.items():
            suffix = f" + {', '.join(secondary_found[code])}" if code in secondary_found else ""
            lines.append(f"  • Câu **{code}**: {', '.join(names)}{suffix}")
        lines += ["",
                  "⚠️ **QUAN TRỌNG**: Đối với các câu có BD/BK/HA:",
                  "- question_stem PHẢI có cấu trúc: {type: 'table'/'chart'/'image'/'mixed', content: {...}}",
                  "- KHÔNG dùng {type: 'text', content: '...'} cho những câu này",
                  "- Tham khảo schema để tạo đúng cấu trúc table/chart/image",
                  r"⚠️ **CÔNG THỨC TOÁN**: BẮT BUỘC dùng LaTeX (bọc trong $...$). VD: $\dfrac{a}{b}$"]
        return "\n".join(lines)

    def _format_rich_content_types_tf(self, spec: TrueFalseQuestionSpec) -> str:
        """Full rich_content_types formatter for DS."""
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return ('**YÊU CẦU NỘI DUNG**: Câu hỏi này không có đánh dấu BD/BK/HA trong ma trận.\n'
                    '⏩ **BẮT BUỘC**: Chỉ dùng **text thuần** (type="text") cho source_text.\n'
                    '⏩ source_text PHẢI là: {"type": "text", "content": "..."}')
        SECONDARY_TYPES = {'LT', 'TT'}
        primary_found: List[str] = []
        secondary_found: List[str] = []
        try:
            if not isinstance(spec.rich_content_types, dict):
                return '**YÊU CẦU NỘI DUNG**: Câu hỏi thuần text.'
            for types_list in spec.rich_content_types.values():
                if not isinstance(types_list, list):
                    continue
                for type_obj in types_list:
                    # Xử lý cả format cũ (code) và format mới (type)
                    if isinstance(type_obj, dict):
                        type_code = type_obj.get('type') or type_obj.get('code', '')
                        type_name_val = type_obj.get('name', type_code)
                        type_name = f"{type_code} ({type_name_val})" if type_name_val else type_code
                    else:
                        type_code = str(type_obj)
                        type_name = type_code
                    (secondary_found if type_code in SECONDARY_TYPES else primary_found).append(type_name)
        except Exception as exc:
            print(f"⚠️ PromptBuilderService._format_rich_content_types_tf error: {exc}")
            traceback.print_exc()
            return '**YÊU CẦU NỘI DUNG**: Câu hỏi thuần text (lỗi xử lý).'
        if not primary_found:
            lines = ["**YÊU CẦU NỘI DUNG**: Câu hỏi thuần text (không có BD/BK/HA)"]
            if secondary_found:
                lines.append(f"  • {', '.join(secondary_found)} (chỉ dạng text)")
            lines += ["", '⏩ **BẮT BUỘC**: Dùng text thuần cho source_text.',
                      '⏩ source_text PHẢI là: {"type": "text", "content": "..."}']
            return "\n".join(lines)
        suffix = f" + {', '.join(secondary_found)}" if secondary_found else ""
        return "\n".join([f"**YÊU CẦU:** Câu hỏi cần rich content: {', '.join(primary_found)}{suffix}", "",
                          "⚠️ source_text PHẢI là: {type: 'table'/'chart'/'image'/'mixed', content: {...}}",
                          "- KHÔNG dùng {type: 'text', content: '...'}"])

    def _detect_chart(self, spec) -> bool:
        """Return True if any question code has BD type."""
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            print(f"🔍 _detect_chart: NO rich_content_types - {getattr(spec, 'rich_content_types', 'KHÔNG CÓ')}")
            return False
        if not isinstance(spec.rich_content_types, dict):
            print(f"🔍 _detect_chart: rich_content_types type={type(spec.rich_content_types)} (expected dict)")
            return False
        
        print(f"🔍 _detect_chart: rich_content_types keys={list(spec.rich_content_types.keys())}")
        
        for code, types_list in spec.rich_content_types.items():
            if not isinstance(types_list, list):
                print(f"  - {code}: NOT a list, type={type(types_list)}")
                continue
            for type_obj in types_list:
                print(f"    • type_obj={type_obj}, type={type(type_obj)}")
                # Xử lý cả format cũ (code) và format mới (type)
                if isinstance(type_obj, dict):
                    type_code = type_obj.get('type') or type_obj.get('code', '')
                    if type_code == 'BD':
                        print(f"      ✅ Found BD chart: {type_obj}")
                        return True
                elif type_obj == 'BD':
                    print(f"      ✅ Found BD (string format)")
                    return True
        
        print(f"🔍 _detect_chart: NO BD types found")
        return False

    def _apply_rich_guide(self, prompt_text: str, spec, label: str = '') -> str:
        """Append rich_content_guide block to prompt if needed."""
        if self._should_inject_rich_guide(spec):
            guide = self._load_rich_content_guide()
            if guide:
                prompt_text = (f"{prompt_text}\n\n{'=' * 70}\n"
                               f"# HƯỚNG DẪN CHI TIẾT VỀ RICH CONTENT\n{'=' * 70}\n\n{guide}")
                if self.verbose:
                    print(f"✓ Đã inject rich_content_guide{' (' + label + ')' if label else ''}")
        return prompt_text

    def _get_primary_content_type(self, spec) -> Optional[str]:
        """Extract the first primary content type code from spec."""
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return None
        if not isinstance(spec.rich_content_types, dict):
            return None
        for types_list in spec.rich_content_types.values():
            if isinstance(types_list, list) and types_list:
                first = types_list[0]
                return first.get('code') if isinstance(first, dict) else str(first)
        return None

    def classify_lesson_topic_type(self, content: str) -> int:
        """
        Classify lesson topic type based on content for DS prompt selection.
        Returns:
          1 → situation-based  → DS_case.txt
          2 → material-based   → DS_material.txt / DS_học liệu AI gen.txt
          3 → mixed/balanced   → default DS_case.txt
        """
        content_lower = (content or '').lower()

        situation_keywords = [
            'tình huống', 'thực tế', 'cuộc sống', 'xã hội', 'pháp luật',
            'kinh tế', 'quyền', 'nghĩa vụ', 'trách nhiệm', 'vi phạm',
            'hành vi', 'chủ thể', 'bảo vệ', 'thực thi',
        ]
        material_keywords = [
            'chỉ số', 'thống kê', 'báo cáo', 'dữ liệu', 'số liệu',
            'tăng trưởng', 'phát triển', 'chính sách', 'quy hoạch',
            'kế hoạch', 'chi tiêu', 'thu nhập', 'ngân sách',
        ]

        sit_cnt = sum(1 for kw in situation_keywords if kw in content_lower)
        mat_cnt = sum(1 for kw in material_keywords if kw in content_lower)

        if sit_cnt > mat_cnt * 2:
            return 1
        elif mat_cnt > sit_cnt * 2:
            return 2
        return 3

    def select_ds_prompt_path(self, content: str) -> Optional[str]:
        """
        Return the absolute path to the DS prompt file that matches the topic type.
        Candidate order:
          situation  → DS_case.txt
          material   → DS_material.txt  OR  DS_học liệu AI gen.txt
          fallback   → DS_case.txt  (if preferred file missing)
        Returns None if no DS prompt file is found at all.
        """
        base = self.prompt_dir or Path('.')
        topic_type = self.classify_lesson_topic_type(content)

        if topic_type == 2:
            candidates = [
                base / "DS_material.txt",
                base / "DS_học liệu AI gen.txt",
                base / "DS_case.txt",
            ]
        else:
            candidates = [
                base / "DS_case.txt",
                base / "DS_material.txt",
                base / "DS_học liệu AI gen.txt",
            ]

        for p in candidates:
            if p.exists():
                return str(p)
        return None

    @staticmethod
    def _extract_first_type_code(rich_content_types) -> Optional[str]:
        """Return the first rich-content type code string from a rich_content_types dict."""
        if not rich_content_types or not isinstance(rich_content_types, dict):
            return None
        try:
            for types_list in rich_content_types.values():
                if isinstance(types_list, list) and types_list:
                    first = types_list[0]
                    return first.get('code') if isinstance(first, dict) else str(first)
        except Exception:
            pass
        return None

    def _append_cognitive_level_guide(self, prompt_text: str, cognitive_level: str) -> str:
        """
        Tier-3 fallback: when only Dạng.txt is used (no level/type variant exists),
        append the cognitive-level guide from server/src/services/prompts/cognitive_level/<LEVEL>.md
        as a clearly separated section.
        """
        if not cognitive_level:
            return prompt_text
        desc = self._load_cognitive_level_desc(cognitive_level)
        if not desc:
            return prompt_text
        sep = '=' * 70
        block = (f"\n\n{sep}\n"
                 f"# MỨC ĐỘ NHẬN THỨC: {cognitive_level.strip().upper()}\n"
                 f"{sep}\n\n{desc}\n{sep}\n")
        return prompt_text + block

    def _build_ds_rich_instruction(self, primary_content_type: str) -> str:
        """Strict DS rich-content instruction block."""
        type_map = {'BK': 'table (bảng khảo)', 'BD': 'chart (biểu đồ)', 'HA': 'image (hình ảnh)'}
        type_label = type_map.get(primary_content_type, primary_content_type)
        sep = '=' * 70
        return (f"\n{sep}\n⚠️ YÊU CẦU NỘI DUNG NGHIÊM NGẶT\n{sep}\n\n"
                f"Câu hỏi DS này yêu cầu chỉ sử dụng: {type_label}\n\n"
                f"**BẮT BUỘC:**\n"
                f"- source_text.type = \"mixed\"\n"
                f"- source_text.content chỉ chứa: [text_intro, {primary_content_type}_object, text_conclusion]\n"
                f"- KHÔNG được thêm các loại content khác\n"
                f"- Mỗi loại content CHỈ xuất hiện 1 LẦN\n{sep}\n")

    # ─────────────────────────── Public build methods ────────────────────────

    def build_prompt_for_tn(self, spec: QuestionSpec, content: str = "",
                            question_template: str = "") -> PreparedPrompt:
        template_text, template_name, tier = self.resolve_template_for_spec(
            'TN', spec.cognitive_level,
            getattr(spec, 'rich_content_types', None))
        self.templates['TN'] = template_text
        prompt_text = template_text

        # For TN2.txt: map NB/TH specific placeholders based on cognitive_level
        # For TN.txt: map generic placeholders (backward compatible)
        if 'TN2.txt' in template_name:
            # TN2.txt requires separate NB and TH mappings
            _lo = spec.learning_outcome or '[Không có]'
            _level_desc = self._load_cognitive_level_desc(spec.cognitive_level)
            _lo_with_desc = f"{_lo}\n\n{_level_desc}" if _level_desc else _lo

            if spec.cognitive_level.upper() == 'NB':
                prompt_text = prompt_text.replace("{{NUM_NB}}", str(spec.num_questions))
                prompt_text = prompt_text.replace("{{NUM_TH}}", "0")
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME_NB}}", _lo_with_desc)
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME_TH}}", "")
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE_NB}}", question_template)
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE_TH}}", "")
            else:  # TH or other levels
                prompt_text = prompt_text.replace("{{NUM_NB}}", "0")
                prompt_text = prompt_text.replace("{{NUM_TH}}", str(spec.num_questions))
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME_NB}}", "")
                prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME_TH}}", _lo_with_desc)
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE_NB}}", "")
                prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE_TH}}", question_template)

            # Common TN2.txt placeholders
            prompt_text = prompt_text.replace("{{NB}}", "Nhận biết")
            prompt_text = prompt_text.replace("{{TH}}", "Thông hiểu")
        else:
            # Legacy TN.txt format - backward compatible
            _lo = spec.learning_outcome or '[Không có]'
            _level_desc = self._load_cognitive_level_desc(spec.cognitive_level)
            _lo_with_desc = f"{_lo}\n\n{_level_desc}" if _level_desc else _lo
            prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", _lo_with_desc)
            prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)

        # Common placeholders for both TN.txt and TN2.txt
        prompt_text = prompt_text.replace("{{NUM}}", str(spec.num_questions))
        prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
        prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
        prompt_text = prompt_text.replace("{{CONTENT}}", self._convert_content_to_string(content))
        prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", self._format_rich_content_types(spec))
        prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIAL}}", spec.supplementary_material or "")

        if tier == 3:
            prompt_text = self._append_cognitive_level_guide(prompt_text, spec.cognitive_level)
        if self._should_inject_rich_guide(spec):
            prompt_text = self._apply_rich_guide(prompt_text, spec, 'TN')
        return PreparedPrompt(
            prompt_text=prompt_text, question_type='TN', lesson_name=spec.lesson_name,
            question_spec=spec, has_content=bool(content),
            content_length=len(content) if content else 0,
            question_template=question_template, has_chart=self._detect_chart(spec),
            template_path=template_name)

    def build_prompt_for_ds(self, spec: TrueFalseQuestionSpec, content: str = "",
                            question_template: str = "",
                            template_path_override: str = None) -> PreparedPrompt:
        # DS may span multiple cognitive levels — pick the dominant level for template selection
        _ds_level = ""
        if spec.statements:
            _ds_level = spec.statements[0].cognitive_level

        if template_path_override:
            _p = Path(template_path_override)
            template_text = _p.read_text(encoding='utf-8') if _p.exists() else ''
            template_name = _p.name
            tier = 2
        else:
            template_text, template_name, tier = self.resolve_template_for_spec(
                'DS', _ds_level,
                getattr(spec, 'rich_content_types', None))
        self.templates['DS'] = template_text
        prompt_text = template_text
        prompt_text = prompt_text.replace("{{NUM}}", "1")
        prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
        prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
        prompt_text = prompt_text.replace("{{CONTENT}}", self._convert_content_to_string(content))
        prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", self._format_rich_content_types_tf(spec))
        prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIAL}}", spec.supplementary_material or "")
        prompt_text = prompt_text.replace("{{MATERIALS}}", spec.materials or "")
        # For DS: inject level description only once — after the LAST statement of each level
        _level_last_label: Dict[str, str] = {}
        for stmt in spec.statements:
            _level_last_label[stmt.cognitive_level.strip().upper()] = stmt.label.upper()

        for stmt in spec.statements:
            lbl = stmt.label.upper()
            prompt_text = prompt_text.replace(f"{{{{COGNITIVE_LEVEL_{lbl}}}}}", stmt.cognitive_level)
            _lo = stmt.learning_outcome
            _is_last_of_level = (_level_last_label.get(stmt.cognitive_level.strip().upper()) == lbl)
            if _is_last_of_level:
                _level_desc = self._load_cognitive_level_desc(stmt.cognitive_level)
                _lo_with_desc = f"{_lo}\n\n{_level_desc}" if _level_desc else _lo
            else:
                _lo_with_desc = _lo
            prompt_text = prompt_text.replace(f"{{{{EXPECTED_LEARNING_OUTCOME_{lbl}}}}}", _lo_with_desc)
        if tier == 3 and _ds_level:
            prompt_text = self._append_cognitive_level_guide(prompt_text, _ds_level)
        if self._should_inject_rich_guide(spec):
            prompt_text = self._apply_rich_guide(prompt_text, spec, 'DS')
        primary_type = self._get_primary_content_type(spec)
        if primary_type:
            prompt_text = f"{prompt_text}\n{self._build_ds_rich_instruction(primary_type)}"
        return PreparedPrompt(
            prompt_text=prompt_text, question_type='DS', lesson_name=spec.lesson_name,
            question_spec=spec, has_content=bool(content),
            content_length=len(content) if content else 0,
            question_template=question_template, has_chart=self._detect_chart(spec),
            template_path=template_name)

    def build_prompt_for_tln(self, spec: QuestionSpec, content: str = "",
                             question_template: str = "") -> PreparedPrompt:
        template_text, template_name, tier = self.resolve_template_for_spec(
            'TLN', spec.cognitive_level,
            getattr(spec, 'rich_content_types', None))
        self.templates['TLN'] = template_text
        prompt_text = template_text
        prompt_text = prompt_text.replace("{{NUM}}", str(spec.num_questions))
        prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
        prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
        prompt_text = prompt_text.replace("{{LEVEL}}", spec.cognitive_level)
        _lo = spec.learning_outcome or '[Không có]'
        _level_desc = self._load_cognitive_level_desc(spec.cognitive_level)
        _lo_with_desc = f"{_lo}\n\n{_level_desc}" if _level_desc else _lo
        prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", _lo_with_desc)
        prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
        prompt_text = prompt_text.replace("{{CONTENT}}", self._convert_content_to_string(content))
        prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", self._format_rich_content_types(spec))
        prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIAL}}", spec.supplementary_material or "")
        if tier == 3:
            prompt_text = self._append_cognitive_level_guide(prompt_text, spec.cognitive_level)
        if self._should_inject_rich_guide(spec):
            prompt_text = self._apply_rich_guide(prompt_text, spec, 'TLN')
        return PreparedPrompt(
            prompt_text=prompt_text, question_type='TLN', lesson_name=spec.lesson_name,
            question_spec=spec, has_content=bool(content),
            content_length=len(content) if content else 0,
            question_template=question_template, has_chart=self._detect_chart(spec),
            template_path=template_name)

    def build_prompt_for_tl(self, spec: QuestionSpec, content: str = "",
                            question_template: str = "") -> PreparedPrompt:
        template_text, template_name, tier = self.resolve_template_for_spec(
            'TL', spec.cognitive_level,
            getattr(spec, 'rich_content_types', None))
        self.templates['TL'] = template_text
        prompt_text = template_text
        prompt_text = prompt_text.replace("{{NUM}}", str(spec.num_questions))
        prompt_text = prompt_text.replace("{{LESSON_NAME}}", spec.lesson_name)
        prompt_text = prompt_text.replace("{{COGNITIVE_LEVEL}}", spec.cognitive_level)
        _lo = spec.learning_outcome or '[Không có]'
        _level_desc = self._load_cognitive_level_desc(spec.cognitive_level)
        _lo_with_desc = f"{_lo}\n\n{_level_desc}" if _level_desc else _lo
        prompt_text = prompt_text.replace("{{EXPECTED_LEARNING_OUTCOME}}", _lo_with_desc)
        prompt_text = prompt_text.replace("{{QUESTION_TEMPLATE}}", question_template)
        prompt_text = prompt_text.replace("{{CONTENT}}", self._convert_content_to_string(content))
        prompt_text = prompt_text.replace("{{RICH_CONTENT_TYPES}}", self._format_rich_content_types(spec))
        prompt_text = prompt_text.replace("{{SUPPLEMENTARY_MATERIAL}}", spec.supplementary_material or "")
        if tier == 3:
            prompt_text = self._append_cognitive_level_guide(prompt_text, spec.cognitive_level)
        if self._should_inject_rich_guide(spec):
            prompt_text = self._apply_rich_guide(prompt_text, spec, 'TL')
        # Append sub-items instruction if TL has ý nhỏ (a, b, c ...)
        _sub_items = getattr(spec, 'sub_items', None)
        if _sub_items:
            prompt_text += self._format_tl_sub_items_instruction(_sub_items)
        return PreparedPrompt(
            prompt_text=prompt_text, question_type='TL', lesson_name=spec.lesson_name,
            question_spec=spec, has_content=bool(content),
            content_length=len(content) if content else 0,
            question_template=question_template, has_chart=self._detect_chart(spec),
            template_path=template_name)

    def _format_tl_sub_items_instruction(self, sub_items: Dict[str, List[str]]) -> str:
        """
        Build an instruction block that tells the AI which sub-items (a, b, c ...)
        each TL question code must produce.

        This block is appended at the END of the prompt so it takes priority
        over any earlier generic answer-structure instructions.
        """
        sep = '=' * 70
        lines = [
            f"\n\n{sep}",
            "# YÊu CẦU Ý NHỏ CHO CÂU TỰ LUẪN",
            sep,
            "",
        ]
        for code, labels in sub_items.items():
            lines.append(
                f"Câu {code} có {len(labels)} ý nhỏ: {', '.join(labels)}"
            )
        lines += [
            "",
            "**BẮT BUỘC — Cấu trúc JSON output cho mỗi câu:**",
            "- question_stem: Đoạn dẫn / bối cảnh CHUNG cho toàn bộ câu",
            "- sub_questions: Mảng gồm các ý nhỏ, mỗi ý gồm:",
            "  - label      : 'a' / 'b' / ... (thứ tự như đã liệt kê ở trên)",
            "  - question_stem: Nội dung yêu cầu của ý đó",
            "  - question_type: phân tích / so sánh / ...",
            "  - answer_structure: {intro, body, conclusion}",
            "  - explanation : Lời giải gợi ý (≤ 300 ký tự)",
            "",
            f"{sep}\n",
        ]
        return "\n".join(lines)

    # ─────────────── 3-tier prompt selection ──────────────────────────────────

    def resolve_template_for_spec(
        self,
        question_type: str,
        cognitive_level: str = "",
        rich_content_types=None,
    ) -> tuple:  # (template_text: str, template_name: str, tier: int)
        """
        Select the best-matching prompt file using 3-tier priority:

        Tier 1 — Dạng_Level_Type.txt   (e.g. TN_NB_BK.txt)
        Tier 2 — Dạng_Level.txt        (e.g. TN_NB.txt)   OR   Dạng_Type.txt (e.g. TN_BK.txt)
                  Level variant is preferred over Type variant within tier 2.
        Tier 3 — Dạng.txt              (e.g. TN.txt / TN2.txt)
                  Cognitive-level guide is appended automatically.

        Returns (template_text, template_filename, tier_used).
        """
        base = self.prompt_dir or Path('.')
        level = cognitive_level.strip().upper() if cognitive_level else ""
        type_code = self._extract_first_type_code(rich_content_types) or ""
        # Strip qualifier suffix for broad matching (e.g. "HA_MH" → "HA")
        type_base = type_code.split('_')[0] if '_' in type_code else type_code

        def _read(path: Path) -> Optional[str]:
            if path.exists():
                return path.read_text(encoding='utf-8')
            return None

        # ── Tier 1: Dạng_Level_Type.txt ───────────────────────────────────
        if level and type_code:
            for tc in ([type_code] if type_code == type_base else [type_code, type_base]):
                text = _read(base / f"{question_type}_{level}_{tc}.txt")
                if text is not None:
                    fname = f"{question_type}_{level}_{tc}.txt"
                    if self.verbose:
                        print(f"✓ Tier-1 template: {fname}")
                    return text, fname, 1

        # ── Tier 2a: Dạng_Level.txt ───────────────────────────────────────
        if level:
            text = _read(base / f"{question_type}_{level}.txt")
            if text is not None:
                fname = f"{question_type}_{level}.txt"
                if self.verbose:
                    print(f"✓ Tier-2a template: {fname}")
                return text, fname, 2

        # ── Tier 2b: Dạng_Type.txt ────────────────────────────────────────
        if type_code:
            for tc in ([type_code] if type_code == type_base else [type_code, type_base]):
                text = _read(base / f"{question_type}_{tc}.txt")
                if text is not None:
                    fname = f"{question_type}_{tc}.txt"
                    if self.verbose:
                        print(f"✓ Tier-2b template: {fname}")
                    return text, fname, 2

        # ── Tier 3: Dạng.txt (TN prefers TN2.txt) ────────────────────────
        for candidate in (['TN2.txt', 'TN.txt'] if question_type == 'TN'
                          else [f'{question_type}.txt']):
            text = _read(base / candidate)
            if text is not None:
                if self.verbose:
                    print(f"✓ Tier-3 template: {candidate}")
                return text, candidate, 3

        # Nothing found — return empty
        fname = f"{question_type}.txt (not found)"
        if self.verbose:
            print(f"⚠️  No template found for {question_type} level={level} type={type_code}")
        return '', fname, 0

    # ─────────────── Batch helper / offline usage ────────────────────────────

    def build_prompts_from_matrix(self, matrix_file: str, pdf_content_map: Dict[str, str] = None,
                                  sheet_name: str = "sheet1") -> Dict[str, List[PreparedPrompt]]:
        from ..core.matrix_parser import MatrixParser
        parser = MatrixParser()
        parser.load_excel(matrix_file, sheet_name)
        all_specs = parser.get_all_question_specs()
        pdf_content_map = pdf_content_map or {}
        result: Dict[str, List[PreparedPrompt]] = {'TN': [], 'DS': [], 'TLN': [], 'TL': []}
        for spec in all_specs.get('TN', []):
            result['TN'].append(self.build_prompt_for_tn(spec, pdf_content_map.get(spec.lesson_name, '')))
        for spec in parser.group_true_false_questions():
            result['DS'].append(self.build_prompt_for_ds(spec, pdf_content_map.get(spec.lesson_name, '')))
        for spec in all_specs.get('TLN', []):
            result['TLN'].append(self.build_prompt_for_tln(spec, pdf_content_map.get(spec.lesson_name, '')))
        for spec in all_specs.get('TL', []):
            result['TL'].append(self.build_prompt_for_tl(spec, pdf_content_map.get(spec.lesson_name, '')))
        return result

    def save_prompts_to_files(self, prompts: Dict[str, List[PreparedPrompt]],
                              output_dir: str = None) -> Dict[str, str]:
        base = Path(output_dir) if output_dir else Path(__file__).parent.parent.parent.parent / "data" / "output" / "prompts"
        base.mkdir(parents=True, exist_ok=True)
        saved = {}
        for q_type, prompt_list in prompts.items():
            if not prompt_list:
                continue
            type_dir = base / q_type
            type_dir.mkdir(exist_ok=True)
            for idx, p in enumerate(prompt_list, 1):
                safe = re.sub(r'[^\w\s-]', '', p.lesson_name).replace(' ', '_')
                path = type_dir / f"{idx:03d}_{safe}_{q_type}.txt"
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f"{'=' * 70}\nPROMPT FOR: {p.lesson_name}\nType: {q_type}\n"
                            f"Has Content: {p.has_content}\n{'=' * 70}\n\n{p.prompt_text}")
                saved[f"{q_type}_{idx}"] = str(path)
        print(f"\n💾 Saved {len(saved)} prompt files to: {base}")
        return saved

    # ─────────────── Legacy compat (kept so old callers don't crash) ──────────

    def export_prompts_from_enriched_json(
        self,
        enriched_matrix_path: str,
        output_path: str = None,
        question_types: List[str] = None,
        prompts_base_dir: str = None,
    ) -> str:
        """
        Đọc enriched matrix JSON và xuất toàn bộ prompt ĐÃ MAPPING (chính xác như gửi AI)
        ra file .txt — mỗi câu hỏi một khối phân cách.

        Hành vi giống hệt phase4:
          - Tự phát hiện thư mục prompt từ metadata: <base>/SUBJECT_CURRICULUM_GRADE/
          - Chọn template đúng per-question theo rich_content_types (_get_prompt_path logic)
          - Với câu BD: ghi thêm placeholder chart-instruction (dữ liệu thật sinh lúc runtime)

        Args:
            enriched_matrix_path: Đường dẫn tới enriched_matrix_*.json
            output_path: File đầu ra .txt (mặc định: data/test_output/<name>_prompts_<ts>.txt)
            question_types: Lọc loại câu ['TN','DS','TLN','TL'] (mặc định: tất cả)
            prompts_base_dir: Thư mục gốc chứa các subdir prompt. Mặc định: data/prompts/
        """
        enriched_path = Path(enriched_matrix_path)
        if not enriched_path.exists():
            raise FileNotFoundError(f"Enriched matrix not found: {enriched_matrix_path}")

        with open(enriched_path, 'r', encoding='utf-8') as f:
            matrix_data = json.load(f)

        meta       = matrix_data.get('metadata', {})
        subject    = meta.get('subject', '')
        curriculum = meta.get('curriculum', '')
        grade      = meta.get('grade', '')

        # ── Resolve prompt dir ─────────────────────────────────────────────
        if prompts_base_dir:
            base_dir = Path(prompts_base_dir)
        else:
            base_dir = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'prompts'

        subdir_name = f"{subject}_{curriculum}_{grade}"
        prompt_dir  = base_dir / subdir_name
        if not prompt_dir.exists():
            print(f"⚠️  Prompt dir not found: {prompt_dir}  → falling back to base")
            prompt_dir = base_dir

        # Load templates from subject-specific dir
        self.set_prompt_dir(str(prompt_dir))

        # ── Output file ────────────────────────────────────────────────────
        if output_path is None:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            out_dir = enriched_path.parent.parent / 'test_output'
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(out_dir / f"{enriched_path.stem}_prompts_{ts}.txt")

        allowed_types = set(question_types) if question_types else {'TN', 'DS', 'TLN', 'TL'}
        lessons = matrix_data.get('lessons', [])
        total   = 0

        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(f"PROMPT EXPORT  |  {enriched_path.name}\n")
            out.write(f"Subject: {subject}  Curriculum: {curriculum}  Grade: {grade}\n")
            out.write(f"Prompt dir: {prompt_dir}\n")
            out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            out.write('=' * 80 + '\n\n')

            for lesson_data in lessons:
                chapter  = lesson_data.get('chapter_number', '')
                lesson   = lesson_data.get('lesson_number', '')
                lesson_name = lesson_data.get('lesson_name', '')
                content  = lesson_data.get('content', '')
                lesson_supplementary = lesson_data.get('supplementary_material', '')

                # ── TN ──────────────────────────────────────────────────────
                if 'TN' in allowed_types:
                    tn_data = lesson_data.get('TN', {})
                    nb_specs = tn_data.get('NB', [])
                    th_specs = tn_data.get('TH', [])
                    vd_specs = tn_data.get('VD', [])

                    # If both NB and TH exist, combine them into ONE TN2 prompt
                    if nb_specs and th_specs:
                        try:
                            # Collect all NB codes, learning outcomes, and templates
                            nb_codes = []
                            nb_outcomes = []
                            nb_templates = []
                            for spec_data in nb_specs:
                                codes = spec_data.get('code', [])
                                nb_codes.extend(codes if isinstance(codes, list) else [codes])
                                nb_outcomes.append(spec_data.get('learning_outcome', ''))
                                templates = spec_data.get('question_template', [])
                                if templates:
                                    nb_templates.extend(templates)

                            # Collect all TH codes, learning outcomes, and templates
                            th_codes = []
                            th_outcomes = []
                            th_templates = []
                            for spec_data in th_specs:
                                codes = spec_data.get('code', [])
                                th_codes.extend(codes if isinstance(codes, list) else [codes])
                                th_outcomes.append(spec_data.get('learning_outcome', ''))
                                templates = spec_data.get('question_template', [])
                                if templates:
                                    th_templates.extend(templates)

                            num_nb = len(nb_codes)
                            num_th = len(th_codes)

                            # Combine learning outcomes
                            combined_nb_outcome = "\n".join([f"- {o}" for o in nb_outcomes if o])
                            combined_th_outcome = "\n".join([f"- {o}" for o in th_outcomes if o])

                            # Load TN2 template directly from file (not from cache which may be overwritten by VD)
                            tn2_path = self.prompt_dir / 'TN2.txt'
                            template_filename = 'TN2.txt'
                            if not tn2_path.exists():
                                tn2_path = self.prompt_dir / 'TN.txt'  # Fallback
                                template_filename = 'TN.txt'

                            if tn2_path.exists():
                                with open(tn2_path, 'r', encoding='utf-8') as f:
                                    template = f.read()
                            else:
                                template = None

                            if template:
                                # Replace placeholders
                                template_vars = {
                                    "NUM_NB": num_nb,
                                    "NUM_TH": num_th,
                                    "NB": "Nhận biết",
                                    "TH": "Thông hiểu",
                                    "EXPECTED_LEARNING_OUTCOME_NB": combined_nb_outcome,
                                    "EXPECTED_LEARNING_OUTCOME_TH": combined_th_outcome,
                                    "LESSON_NAME": lesson_name,
                                    "CONTENT": content,
                                    "QUESTION_TEMPLATE_NB": "\n".join(nb_templates) if nb_templates else "",
                                    "QUESTION_TEMPLATE_TH": "\n".join(th_templates) if th_templates else ""
                                }

                                prompt_text = template
                                for var, value in template_vars.items():
                                    prompt_text = prompt_text.replace("{{" + var + "}}", str(value))

                                # Create PreparedPrompt
                                spec = QuestionSpec(
                                    lesson_name=lesson_name, competency_level=1,
                                    cognitive_level="NB+TH", question_type='TN',
                                    num_questions=num_nb + num_th,
                                    question_codes=nb_codes + th_codes,
                                    learning_outcome=f"{combined_nb_outcome}\n{combined_th_outcome}",
                                    row_index=0,
                                    chapter_number=int(chapter) if chapter else None,
                                    supplementary_material=lesson_supplementary,
                                    rich_content_types=None,
                                )
                                prepared = PreparedPrompt(
                                    prompt_text=prompt_text,
                                    question_type='TN',
                                    lesson_name=lesson_name,
                                    question_spec=spec,
                                    has_content=bool(content),
                                    content_length=len(content),
                                    template_path=template_filename
                                )

                                all_codes = nb_codes + th_codes
                                label = (f"[Ch.{chapter} L.{lesson}] TN NB+TH"
                                         f"  {', '.join(all_codes)}  [{template_filename}]")
                                self._write_prompt_block(out, label, prepared)
                                total += 1
                        except Exception as e:
                            out.write(f"  ERROR building combined TN prompt: {e}\n"
                                      f"  {traceback.format_exc()}\n\n")
                    else:
                        # Process NB and TH separately if only one exists
                        for level in ['NB', 'TH']:
                            specs = tn_data.get(level, [])
                            for spec_data in (specs or []):
                                try:
                                    codes    = spec_data.get('code', [])
                                    qt       = '\n'.join(spec_data.get('question_template', []))
                                    rich     = spec_data.get('rich_content_types', None)
                                    spec = QuestionSpec(
                                        lesson_name=lesson_name, competency_level=1,
                                        cognitive_level=level, question_type='TN',
                                        num_questions=spec_data.get('num', len(codes)),
                                        question_codes=codes,
                                        learning_outcome=spec_data.get('learning_outcome', ''),
                                        row_index=0,
                                        chapter_number=int(chapter) if chapter else None,
                                        supplementary_material=lesson_supplementary,
                                        rich_content_types=rich,
                                    )
                                    prepared = self.build_prompt_for_tn(spec, content, qt)
                                    if prepared.has_chart:
                                        prepared = self._append_chart_placeholder(prepared, spec)
                                    label = (f"[Ch.{chapter} L.{lesson}] TN {level}"
                                             f"  {', '.join(codes)}  [{prepared.template_path}]")
                                    self._write_prompt_block(out, label, prepared)
                                    total += 1
                                except Exception as e:
                                    out.write(f"  ERROR building TN prompt ({spec_data.get('code','')}): {e}\n"
                                              f"  {traceback.format_exc()}\n\n")

                    # Process VD separately (never combined)
                    for spec_data in (vd_specs or []):
                        try:
                            codes    = spec_data.get('code', [])
                            qt       = '\n'.join(spec_data.get('question_template', []))
                            rich     = spec_data.get('rich_content_types', None)
                            spec = QuestionSpec(
                                lesson_name=lesson_name, competency_level=1,
                                cognitive_level='VD', question_type='TN',
                                num_questions=spec_data.get('num', len(codes)),
                                question_codes=codes,
                                learning_outcome=spec_data.get('learning_outcome', ''),
                                row_index=0,
                                chapter_number=int(chapter) if chapter else None,
                                supplementary_material=lesson_supplementary,
                                rich_content_types=rich,
                            )
                            prepared = self.build_prompt_for_tn(spec, content, qt)
                            if prepared.has_chart:
                                prepared = self._append_chart_placeholder(prepared, spec)
                            label = (f"[Ch.{chapter} L.{lesson}] TN VD"
                                     f"  {', '.join(codes)}  [{prepared.template_path}]")
                            self._write_prompt_block(out, label, prepared)
                            total += 1
                        except Exception as e:
                            out.write(f"  ERROR building TN VD prompt ({spec_data.get('code','')}): {e}\n"
                                      f"  {traceback.format_exc()}\n\n")

                # ── DS ──────────────────────────────────────────────────────
                if 'DS' in allowed_types:
                    for spec_data in lesson_data.get('DS', []):
                        try:
                            qcode    = spec_data.get('question_code', 'DS?')
                            qt       = '\n'.join(spec_data.get('question_template', []))
                            rich     = spec_data.get('rich_content_types', None)
                            raw_stmts = spec_data.get('statements', [])
                            statements = []
                            for stmt in raw_stmts:
                                from ..core.matrix_parser import StatementSpec
                                statements.append(StatementSpec(
                                    statement_code=f"{qcode}{stmt['label'].upper()}",
                                    label=stmt['label'],
                                    cognitive_level=stmt['cognitive_level'],
                                    learning_outcome=stmt.get('learning_outcome', ''),
                                    materials=spec_data.get('materials', ''),
                                ))
                            spec = TrueFalseQuestionSpec(
                                question_code=qcode, lesson_name=lesson_name,
                                statements=statements, question_type='DS',
                                chapter_number=int(chapter) if chapter else None,
                                supplementary_material=lesson_supplementary,
                                materials=spec_data.get('materials', ''),
                                rich_content_types=rich,
                            )
                            prepared = self.build_prompt_for_ds(
                                spec, content, qt,
                                template_path_override=self.select_ds_prompt_path(content)
                            )
                            label = (f"[Ch.{chapter} L.{lesson}] DS  {qcode}"
                                     f"  [{prepared.template_path}]  stmts={len(statements)}")
                            self._write_prompt_block(out, label, prepared)
                            total += 1
                        except Exception as e:
                            out.write(f"  ERROR building DS prompt ({spec_data.get('question_code','')}): {e}\n"
                                      f"  {traceback.format_exc()}\n\n")

                # ── TLN ─────────────────────────────────────────────────────
                if 'TLN' in allowed_types:
                    for level, specs in lesson_data.get('TLN', {}).items():
                        for spec_data in (specs or []):
                            try:
                                codes    = spec_data.get('code', [])
                                qt       = '\n'.join(spec_data.get('question_template', []))
                                rich     = spec_data.get('rich_content_types', None)
                                spec = QuestionSpec(
                                    lesson_name=lesson_name, competency_level=1,
                                    cognitive_level=level, question_type='TLN',
                                    num_questions=spec_data.get('num', len(codes)),
                                    question_codes=codes,
                                    learning_outcome=spec_data.get('learning_outcome', ''),
                                    row_index=0,
                                    chapter_number=int(chapter) if chapter else None,
                                    supplementary_material=lesson_supplementary,
                                    rich_content_types=rich,
                                )
                                prepared = self.build_prompt_for_tln(spec, content, qt)
                                label = (f"[Ch.{chapter} L.{lesson}] TLN {level}"
                                         f"  {', '.join(codes)}  [{prepared.template_path}]")
                                self._write_prompt_block(out, label, prepared)
                                total += 1
                            except Exception as e:
                                out.write(f"  ERROR building TLN prompt ({spec_data.get('code','')}): {e}\n"
                                          f"  {traceback.format_exc()}\n\n")

                # ── TL ──────────────────────────────────────────────────────
                if 'TL' in allowed_types:
                    for level, specs in lesson_data.get('TL', {}).items():
                        for spec_data in (specs or []):
                            try:
                                codes    = spec_data.get('code', [])
                                qt       = '\n'.join(spec_data.get('question_template', []))
                                rich     = spec_data.get('rich_content_types', None)
                                spec = QuestionSpec(
                                    lesson_name=lesson_name, competency_level=1,
                                    cognitive_level=level, question_type='TL',
                                    num_questions=spec_data.get('num', len(codes)),
                                    question_codes=codes,
                                    learning_outcome=spec_data.get('learning_outcome', ''),
                                    row_index=0,
                                    chapter_number=int(chapter) if chapter else None,
                                    supplementary_material=lesson_supplementary,
                                    rich_content_types=rich,
                                    sub_items=spec_data.get('sub_items', None),
                                )
                                prepared = self.build_prompt_for_tl(spec, content, qt)
                                label = (f"[Ch.{chapter} L.{lesson}] TL {level}"
                                         f"  {', '.join(codes)}  [{prepared.template_path}]")
                                self._write_prompt_block(out, label, prepared)
                                total += 1
                            except Exception as e:
                                out.write(f"  ERROR building TL prompt ({spec_data.get('code','')}): {e}\n"
                                          f"  {traceback.format_exc()}\n\n")

        print(f"✅ Exported {total} prompts → {output_path}")
        return output_path

    # ── Helpers for export ───────────────────────────────────────────────────

    def _resolve_template_path(self, question_type: str,
                                rich_content_types: Optional[Dict]) -> Path:
        """
        Replicates phase4._get_prompt_path: select the correct .txt for a question.
        TN prefers TN2.txt > TN.txt. Rich-type questions try TN_BD.txt etc. first.
        """
        base = self.prompt_dir or Path('.')
        generic = (base / 'TN2.txt' if question_type == 'TN' and (base / 'TN2.txt').exists()
                   else base / f'{question_type}.txt')

        if not rich_content_types or not isinstance(rich_content_types, dict):
            return generic
        try:
            first_key  = next(iter(rich_content_types))
            type_array = rich_content_types[first_key]
            if not isinstance(type_array, list) or not type_array:
                return generic
            first_obj  = type_array[0]
            type_code  = first_obj.get('code', '') if isinstance(first_obj, dict) else str(first_obj)
            # Full code (e.g. TN_HA_MH.txt)
            candidate = base / f'{question_type}_{type_code}.txt'
            if candidate.exists():
                return candidate
            # Stripped prefix (HA_MH → HA)
            if '_' in type_code:
                candidate = base / f'{question_type}_{type_code.split("_")[0]}.txt'
                if candidate.exists():
                    return candidate
        except Exception:
            pass
        return generic

    def _load_template_from_path(self, q_type: str, path: Path) -> None:
        """Load a single template file into self.templates[q_type]."""
        if path.exists():
            self.templates[q_type] = path.read_text(encoding='utf-8')
        elif q_type not in self.templates:
            self.templates[q_type] = ''

    def _append_chart_placeholder(self, prepared: 'PreparedPrompt',
                                   spec: QuestionSpec) -> 'PreparedPrompt':
        """
        BD questions get a real chart-instruction appended at runtime.
        Here we add a clearly marked placeholder showing where + what data it uses.
        """
        num_bd = 0
        if spec.rich_content_types and isinstance(spec.rich_content_types, dict):
            for types_list in spec.rich_content_types.values():
                if isinstance(types_list, list):
                    for t in types_list:
                        code = t.get('code', '') if isinstance(t, dict) else str(t)
                        if code == 'BD':
                            num_bd += 1
        placeholder = (
            f"\n\n{'─' * 70}\n"
            f"⚙️  [CHART INSTRUCTION — appended at runtime by phase4]\n"
            f"   Số chart cần sinh: {num_bd}\n"
            f"   Lesson: {spec.lesson_name}\n"
            f"   supplementary_material: "
            f"{'(có dữ liệu)' if getattr(spec, 'supplementary_material', '') else '(trống — AI tìm số liệu)'}\n"
            f"{'─' * 70}\n"
        )
        from dataclasses import replace as dc_replace
        return dc_replace(prepared, prompt_text=prepared.prompt_text + placeholder)

    def _write_prompt_block(self, out, label: str, prepared: 'PreparedPrompt') -> None:
        """Write a single prompt block with header/footer to an open file handle."""
        sep = '─' * 80
        out.write(f"{sep}\n")
        out.write(f"{label}\n")
        out.write(
            f"Type: {prepared.question_type}  |  "
            f"Content: {'yes' if prepared.has_content else 'NO'} ({prepared.content_length} chars)  |  "
            f"Template: {prepared.template_path or 'n/a'}  |  "
            f"Chart: {'yes (BD)' if prepared.has_chart else 'no'}\n"
        )
        out.write(f"{sep}\n")
        out.write(prepared.prompt_text)
        out.write('\n\n')

    def replace_variables(self, template: str, variables: Dict[str, str]) -> str:
        """Deprecated: inline replacement now done directly in build_prompt_for_* methods."""
        result = template
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        return result

    def _format_rich_content_types_compat(self, spec: QuestionSpec, current_question_code: str = None) -> str:
        """Deprecated compat: delegates to new full formatter (ignores current_question_code filter)."""
        return self._format_rich_content_types(spec)

    # ─────────────────────────────────────────────────────────────────────────
    # NOTE: The following old stubs are intentionally removed:
    #   load_templates (old single-file version) — replaced above
    #   _format_rich_content_types (old trivial version) — replaced above
    #   _format_rich_content_types_tf (old trivial version) — replaced above
    #   build_prompt_for_tn/ds/tln/tl (old replace_variables version) — replaced above
    #   build_prompts_from_matrix (old verbose print version) — replaced above
    # ─────────────────────────────────────────────────────────────────────────

