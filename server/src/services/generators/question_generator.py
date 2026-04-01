"""
Module sinh câu hỏi tự động sử dụng Vertex AI
"""
import json
import re
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, asdict

from ..core.matrix_parser import QuestionSpec, TrueFalseQuestionSpec
from ..core.schemas import (
    get_multiple_choice_array_schema,
    get_true_false_schema,
    get_short_answer_array_schema,
    get_essay_array_schema,
    get_essay_with_sub_items_array_schema,
    get_content_schema_by_rich_types
)
from services.generators.helpers.chart_generation_helper import (
    get_chart_data_schema,
    build_chart_generation_prompt,
    build_question_with_chart_prompt,
    merge_chart_into_question,
    validate_chart_completeness,
    extract_chart_summary
)
from .prompt_builder_service import PromptBuilderService
from config.settings import Config

@dataclass
class GeneratedQuestion:
    """Câu hỏi đã được sinh"""
    question_code: str  # Mã câu (VD: C1)
    question_stem: str  # Nội dung câu hỏi
    options: Dict[str, str]  # Các lựa chọn A, B, C, D
    correct_answer: str  # Đáp án đúng
    level: str  # Cấp độ (NB/TH/VD/VDC)
    explanation: str  # Giải thích
    lesson_name: str  # Tên bài học
    question_type: str  # Loại câu hỏi (TN/DS/TLN)


@dataclass
class GeneratedTrueFalseQuestion:
    """Câu hỏi Đúng/Sai đã được sinh"""
    question_code: str  # Mã câu (VD: C1)
    source_text: str  # Đoạn tư liệu
    statements: Dict[str, Dict]  # 4 mệnh đề {a: {text, level, correct_answer}, ...}
    explanation: Dict[str, str]  # Giải thích cho mỗi mệnh đề {a: "...", b: "...", ...}
    lesson_name: str  # Tên bài học
    question_type: str = "DS"  # Loại câu hỏi
    # Metadata fields for source citation (REQUIRED per schema)
    source_citation: str = ""  # Trích dẫn nguồn học thuật
    source_origin: str = ""  # Loại nguồn (academic_journal/scholarly_book/official_document/reputable_media)
    source_type: str = ""  # Loại tư liệu (primary_source/historical_description/analytical_summary/contextual_scenario)
    pedagogical_approach: str = ""  # Cách tiếp cận sư phạm
    search_evidence: str = ""  # Ghi chú quá trình tìm kiếm


@dataclass
class GeneratedEssayQuestion:
    """Câu hỏi Tự luận đã được sinh"""
    question_code: str  # Mã câu (VD: C1)
    question_stem: str  # Nội dung câu hỏi
    question_type: str  # Loại câu hỏi tự luận (analysis/comparison/evaluation/explanation/synthesis/argumentation)
    answer_structure: Dict  # Cấu trúc câu trả lời mong đợi (trống nếu có sub_questions)
    level: str  # Cấp độ (NB/TH/VD/VDC)
    lesson_name: str  # Tên bài học
    question_type_main: str = "TL"  # Loại câu hỏi chính
    chapter_number: int = 0  # Số chương
    lesson_number: int = 0  # Số bài
    sub_questions: Optional[List[Dict]] = None  # Ý nhỏ a, b, c ... (nếu có)


class QuestionGenerator:
    """Class sinh câu hỏi tự động"""
    
    def __init__(self, ai_client, prompt_template_path: str, verbose: bool = False, matrix_parser=None):
        """
        Khởi tạo Question Generator
        
        Args:
            ai_client: VertexAIClient đã được khởi tạo
            prompt_template_path: Đường dẫn đến file prompt template
            verbose: Hiển thị logs chi tiết
            matrix_parser: MatrixParser (optional) - để access SampleQuestionBank
        """
        self.ai_client = ai_client
        self.prompt_template = self._load_prompt_template(prompt_template_path)
        self.verbose = verbose
        self.matrix_parser = matrix_parser
        self.max_retries = 5
        self.retry_delay = 5.0  # seconds
        self.fallback_model = Config.VERTEX_AI_FALLBACK_MODEL  # Fallback khi rate limit
        # Single source of truth for prompt building
        self.prompt_builder = PromptBuilderService(
            prompt_dir=str(Path(prompt_template_path).parent),
            verbose=verbose
        )
        self._prompt_builder_dir = str(Path(prompt_template_path).parent)
    
    def _convert_content_to_string(self, content) -> str:
        """
        Convert content to string, handling list/str/None cases
        
        Args:
            content: Content from PDF/DOCX (can be str, list, or None)
            
        Returns:
            str: Formatted content string
        """
        if isinstance(content, list):
            # Join list items into formatted string
            return "\n".join(str(item) for item in content)
        elif content:
            return str(content)
        else:
            return "Hãy tự động lấy dữ liệu nội dung theo tên bài của sách Lịch sử theo Chương trình GDPT 2018 của Việt Nam_"
    
    def _load_prompt_template(self, template_path: str) -> str:
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise Exception(f"Không thể đọc prompt template: {e}")
    
    def _generate_chart_separately(self, spec: QuestionSpec, num_charts: int = 1) -> List[Dict]:
        """
        BƯỚC 1: Tạo chart data RIÊNG BIỆT (giảm nested complexity)
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            num_charts: Số lượng chart cần tạo
        
        Returns:
            List[Dict]: Danh sách chart data với chart_id, title, chartType, echarts
        """
        # Lấy supplementary_materials từ spec (hỗ trợ cả tên cũ và mới)
        supplementary_materials = getattr(spec, 'supplementary_material', None) or getattr(spec, 'materials', None)
        
        # Build prompt sử dụng helper
        prompt = build_chart_generation_prompt(
            lesson_name=spec.lesson_name,
            num_charts=num_charts,
            supplementary_materials=supplementary_materials
        )
        
        # Lấy schema từ helper
        chart_schema = get_chart_data_schema()
        
        if self.verbose:
            print(f"🔄 STEP 1: Tạo {num_charts} chart riêng...")
            if supplementary_materials:
                print(f"   📄 Có tài liệu bổ sung: {len(supplementary_materials)} chars")
            else:
                print(f"   🔍 Sẽ tìm kiếm dữ liệu")
        
        response = self.ai_client.generate_content_with_schema(
            prompt=prompt,
            response_schema=chart_schema,
            enable_search=True  # Bật search để tìm dữ liệu nếu cần
        )
        
        data = json.loads(response) if isinstance(response, str) else response
        charts = data.get("charts", [])
        
        # Validate charts
        for chart in charts:
            is_valid, error_msg = validate_chart_completeness(chart)
            if not is_valid:
                if self.verbose:
                    print(f"   ⚠️ Chart {chart.get('chart_id')} thiếu dữ liệu: {error_msg}")
                raise ValueError(f"Chart {chart.get('chart_id')} không đầy đủ: {error_msg}")
        
        if self.verbose:
            print(f"✅ Đã tạo {len(charts)} chart đầy đủ")
            for chart in charts:
                print(f"   - {chart.get('chart_id')}: {chart.get('title')}")
        
        return charts
    
    def _generate_chart_data_then_convert(
        self, 
        spec: QuestionSpec, 
        chart_type: str, 
        dimensions: str,
        question_code: str = "C1"
    ) -> Dict:
        """
        🔥 LUỒNG MỚI: Tạo chart theo luồng GenChart
        1. AI sinh DỮ LIỆU chart (không phải option)
        2. Backend validate data
        3. Backend convert data → ECharts option bằng GenChart utilities
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            chart_type: Loại chart (bar, line, pie, area, combo)
            dimensions: Kích thước "XxY" (VD: "2x3" = 2 hàng 3 cột)
            question_code: Mã câu (VD: "C1")
        
        Returns:
            Dict: ECharts option đầy đủ
        """
        from services.core.schemas import get_chart_data_generation_schema
        from services.generators.helpers.chart_generation_helper import (
            build_chart_data_generation_prompt,
            validate_chart_data_generation,
            process_chart_data_to_option
        )
        
        # Lấy supplementary_materials từ spec
        supplementary_materials = getattr(spec, 'supplementary_material', None) or getattr(spec, 'materials', None) or ""
        
        # Build prompt từ template gen_data_chart.md
        prompt = build_chart_data_generation_prompt(
            lesson_name=spec.lesson_name,
            chart_type=chart_type,
            dimensions=dimensions,
            cognitive_level=spec.cognitive_level,
            expected_learning_outcome=spec.learning_outcome,
            supplementary_materials=supplementary_materials
        )
        
        if self.verbose:
            print(f"🔄 Sinh chart data cho {question_code}: {chart_type} {dimensions}")
            if supplementary_materials:
                print(f"   📄 Có tài liệu bổ sung: {len(supplementary_materials)} chars")
        
        # Gọi AI sinh chart DATA (không phải option)
        chart_data_schema = get_chart_data_generation_schema()
        response = self.ai_client.generate_content_with_schema(
            prompt=prompt,
            response_schema=chart_data_schema,
            enable_search=True  # Search để tìm dữ liệu nếu không có tài liệu bổ sung
        )
        
        # Parse response
        chart_data = json.loads(response) if isinstance(response, str) else response
        
        print(f">>> Chart data raw response: {chart_data}")
        
        if self.verbose:
            print(f"   ✅ AI đã sinh chart data: chart_type={chart_data.get('chart_type')}")
        
        # Validate chart data
        validate_chart_data_generation(chart_data, chart_type=chart_type, dimensions=dimensions)
        
        if self.verbose:
            print(f"   ✅ Validate chart data thành công")
        
        # Convert data → ECharts option bằng GenChart
        echarts_option = process_chart_data_to_option(chart_data)
        
        if self.verbose:
            print(f"   ✅ Convert thành ECharts option thành công")
        
        return echarts_option
    
    def generate_questions_for_spec(self, spec: QuestionSpec, 
                                   prompt_template_path: str = None,
                                   question_template: str = "",
                                   content: str = "",
                                   history_context: str = "") -> List[GeneratedQuestion]:
        """
        Sinh câu hỏi cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template (nếu khác với default)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            List[GeneratedQuestion]: Danh sách câu hỏi đã sinh
        """        
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        last_error = None
        tried_fallback = False
        
        # Build prompt + chart ONCE before retry loop
        # (chart generation is expensive: separate API call; must not repeat on each retry)
        if prompt_template_path:
            new_dir = str(Path(prompt_template_path).parent)
            if str(self.prompt_builder.prompt_dir) != new_dir:
                self.prompt_builder.set_prompt_dir(new_dir)
        prepared = self.prompt_builder.build_prompt_for_tn(spec, content, question_template)
        has_chart = prepared.has_chart

        # ✨ STEP 1: Tạo chart riêng nếu có 'BD' trong rich_content_types (dùng GenChart flow)
        charts_map = {}
        base_prompt_text = prepared.prompt_text
        if has_chart:
            # Detect chart specifications từ rich_content_types
            charts_to_generate = {}
            for code, types_list in spec.rich_content_types.items():
                if isinstance(types_list, list):
                    for type_obj in types_list:
                        # Check NEW FORMAT: {"type": "BD", "chart_type": "bar", "dimensions": "2x3"}
                        if isinstance(type_obj, dict) and type_obj.get('type') == 'BD':
                            chart_type = type_obj.get('chart_type', 'bar').lower()
                            dimensions = type_obj.get('dimensions', '')
                            
                            if chart_type and dimensions:
                                charts_to_generate[code] = {
                                    'chart_type': chart_type,
                                    'dimensions': dimensions
                                }
                                print(f"📊 {code}: Detected chart {chart_type} {dimensions}")
                            break
                        # Check OLD FORMAT: Just "BD" string (fallback to generic chart)
                        elif type_obj == 'BD':
                            print(f"⚠️  {code}: Old format chart (BD string only), fallback to generic")
                            charts_to_generate[code] = {
                                'chart_type': 'bar',
                                'dimensions': '2x3'  # Default dimensions
                            }
                            break
            
            if charts_to_generate:
                print(f"🎨 Phát hiện {len(charts_to_generate)} câu cần chart (BD)")
                
                # Generate chart cho mỗi question code
                for question_code, chart_spec in charts_to_generate.items():
                    chart_type = chart_spec['chart_type']
                    dimensions = chart_spec['dimensions']
                    
                    # Retry chart generation independent
                    echarts_option = None
                    for chart_attempt in range(self.max_retries):
                        try:
                            if self.verbose:
                                print(f"   🔄 Sinh chart {question_code}: {chart_type} {dimensions} (lần {chart_attempt + 1})")
                            
                            echarts_option = self._generate_chart_data_then_convert(
                                spec=spec,
                                chart_type=chart_type,
                                dimensions=dimensions,
                                question_code=question_code
                            )
                            
                            if self.verbose:
                                print(f"   ✅ Đã sinh chart {question_code}")
                            break
                            
                        except Exception as chart_err:
                            if chart_attempt < self.max_retries - 1:
                                if self.verbose:
                                    print(f"   ⚠️  Chart lần thử {chart_attempt + 1}/{self.max_retries} thất bại: {str(chart_err)[:80]}")
                                    print(f"      Thử lại sau {self.retry_delay}s...")
                                time.sleep(self.retry_delay)
                            else:
                                # All retries exhausted
                                print(f"   ❌ Lỗi sinh chart {question_code} sau {self.max_retries} lần thử: {str(chart_err)[:100]}")
                                raise
                    
                    if echarts_option:
                        # Store chart với question_code làm ID
                        charts_map[question_code] = {
                            'chart_id': question_code,
                            'title': f"Chart cho {question_code}",
                            'chartType': chart_type,
                            'echarts': echarts_option
                        }
                
                # Build chart instruction cho prompt
                if charts_map:
                    charts_info = []
                    for cid, cdata in charts_map.items():
                        # Tạo base chart info
                        chart_item = {
                            'chart_id': cid,
                            'title': cdata.get('title', cid)
                        }
                        
                        # Trích xuất thông tin chi tiết từ echarts
                        echarts = cdata.get('echarts', {})
                        if echarts:
                            summary = extract_chart_summary(echarts)
                            chart_item.update(summary)  # Thêm xAxis_labels, yAxis_unit, series_names, data_summary
                        
                        charts_info.append(chart_item)
                    
                    chart_instruction = build_question_with_chart_prompt(
                        lesson_name=spec.lesson_name,
                        charts_info=charts_info,
                        num_questions=spec.num_questions,
                        cognitive_level=spec.cognitive_level
                    )
                    
                    # Strip supplementary_material từ base prompt nếu quá dài
                    supp = spec.supplementary_material or ''
                    if supp and len(supp) > 200:
                        base_prompt_text = base_prompt_text.replace(
                            supp,
                            '→ Dữ liệu đã được trích xuất vào biểu đồ được cung cấp bên dưới.'
                        )
                    base_prompt_text = f"{base_prompt_text}\n\n{chart_instruction}"

        # history_context is passed as system_instruction (higher priority than prompt body)
        _sys_instruction = history_context if history_context else None

        # Retry loop - chỉ retry AI call, chart đã được tạo sẵn
        for attempt in range(self.max_retries):
            try:
                prompt_text = base_prompt_text

                # Chọn content schema phù hợp dựa trên rich_content_types
                content_schema = get_content_schema_by_rich_types(spec.rich_content_types)
                tn_schema = get_multiple_choice_array_schema(content_schema)
                
                # Gọi AI với array schema - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    # Gemini-2.5-pro doesn't support controlled generation with Search tool
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt_text,
                        response_schema=tn_schema,
                        model_name=self.fallback_model,
                        system_instruction=_sys_instruction,
                        enable_search=False,
                        enable_thinking=False  # Fallback model doesn't support thinking_config
                    )
                else:
                    response = self.ai_client.generate_content_with_schema(
                        prompt=prompt_text,
                        response_schema=tn_schema,
                        system_instruction=_sys_instruction,
                        enable_search=True
                    )
                
                # Parse response
                data = json.loads(response) if isinstance(response, str) else response
                # print(f">>>>>>{data}")
                questions_data = data.get("questions", [])
                
                # Kiểm tra nếu không có câu hỏi nào được sinh
                if not questions_data or len(questions_data) == 0:
                    raise ValueError("AI không trả về câu hỏi nào")
                
                # ⚠️ VALIDATION: AI có thể generate nhiều hơn yêu cầu → chỉ lấy đúng số lượng
                if len(questions_data) > spec.num_questions:
                    print(f"⚠️ WARNING: AI generated {len(questions_data)} TN questions, but only {spec.num_questions} requested. Taking first {spec.num_questions}.")
                    questions_data = questions_data[:spec.num_questions]
                
                # VALIDATION: Nếu không có rich_content_types, chuyển sang text-only
                if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
                    for q_data in questions_data:
                        if 'question_stem' in q_data and isinstance(q_data['question_stem'], dict):
                            if q_data['question_stem'].get('type') != 'text':
                                print(f"⚠️  FORCE TEXT-ONLY: Câu {q_data.get('question_code', '?')} có type={q_data['question_stem'].get('type')}, chuyển sang text")
                                # Chuyển sang text thuần
                                if q_data['question_stem'].get('type') == 'mixed':
                                    # Trích xuất text từ mixed
                                    content = q_data['question_stem'].get('content', [])
                                    text_parts = [item if isinstance(item, str) else '' for item in content]
                                    q_data['question_stem'] = {"type": "text", "content": ' '.join(text_parts).strip()}
                                else:
                                    # Có thể là table/chart/image, không thể chuyển đổi -> reject
                                    raise ValueError(f"Câu hỏi có rich content không mong muốn (type={q_data['question_stem'].get('type')}) khi ma trận không yêu cầu")
                
                # VALIDATION: Kiểm tra chart content
                for q_data in questions_data:
                    if 'question_stem' in q_data and isinstance(q_data['question_stem'], dict):
                        if q_data['question_stem'].get('type') == 'mixed':
                            content = q_data['question_stem'].get('content', [])
                            for idx, item in enumerate(content):
                                if isinstance(item, dict) and item.get('type') == 'chart':
                                    chart_content = item.get('content', {})
                                    echarts = chart_content.get('echarts', {})
                                    
                                    # Check if echarts is empty or missing required fields
                                    if not echarts or len(echarts) == 0:
                                        print(f"⚠️  WARNING: Câu {question_code} có chart với echarts rỗng!")
                                        print(f"   → AI chưa generate được chart data.")
                                        raise ValueError(f"Chart echarts rỗng - AI chưa generate được data")
                
                # ✨ STEP 3: Merge chart vào câu hỏi (nếu có)
                if has_chart and charts_map:
                    print(f"🔄 STEP 3: Merging charts vào {len(questions_data)} câu hỏi...")
                    
                    for i, q_data in enumerate(questions_data):
                        # Get question_code để match với charts_map
                        question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"Q{i+1}"
                        
                        # Nếu có chart cho câu này, merge vào
                        if question_code in charts_map:
                            # Tạo charts_map_for_this_question chỉ chứa chart cho câu này
                            single_chart_map = {question_code: charts_map[question_code]}
                            q_data = merge_chart_into_question(q_data, single_chart_map)
                            
                            if self.verbose:
                                print(f"   ✅ Merged chart vào câu hỏi {question_code}")
                        elif self.verbose:
                            print(f"   ℹ️  Không có chart cho câu {question_code}")
                        
                        # Update q_data với question_code để dùng sau
                        q_data['question_code'] = question_code
                        
                        if self.verbose:
                            # Check xem đã merge thành công chưa
                            if 'question_stem' in q_data and isinstance(q_data['question_stem'], dict):
                                content = q_data['question_stem'].get('content', [])
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'chart':
                                        if 'echarts' in item.get('content', {}):
                                            print(f"      ✓ Chart echarts confirmed in question_stem")
                
                # Tạo GeneratedQuestion cho mỗi câu
                for i, question_data in enumerate(questions_data):
                    # Ưu tiên sử dụng question_code từ merged data, fallback to spec.question_codes
                    question_code = question_data.get('question_code') or (spec.question_codes[i] if i < len(spec.question_codes) else f"Q{i+1}")
                    
                    question = GeneratedQuestion(
                        question_code=question_code,
                        question_stem=question_data.get("question_stem", ""),
                        options=question_data.get("options", {}),
                        correct_answer=question_data.get("correct_answer", ""),
                        level=question_data.get("level", spec.cognitive_level),
                        explanation=question_data.get("explanation", ""),
                        lesson_name=spec.lesson_name,
                        question_type=spec.question_type
                    )
                    
                    generated_questions.append(question)
                
                # Thành công, thoát retry loop
                break
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Kiểm tra nếu là lỗi 429 và chưa thử fallback
                is_rate_limit = "429" in error_str and "RESOURCE_EXHAUSTED" in error_str
                
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                elif is_rate_limit and not tried_fallback:
                    # Thử fallback model
                    tried_fallback = True
                    print(f"🔄 Hết {self.max_retries} lần thử với model chính, chuyển sang fallback model: {self.fallback_model}")
                    # Reset attempt counter cho fallback
                    attempt = -1  # Sẽ tăng lên 0 ở vòng lặp tiếp theo
                    continue
                else:
                    # Hết retry và hết fallback, tạo dummy questions
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu hỏi sau {self.max_retries} lần thử")
                        if tried_fallback:
                            print(f"   (đã thử cả fallback model {self.fallback_model})")
                        print(f"   Error: {error_str}")
                        import traceback
                        traceback.print_exc()
                    
                    # Tạo dummy questions với error message
                    error_msg = f"Lỗi sinh câu hỏi: {error_str}"
                    for question_code in spec.question_codes:
                        question = GeneratedQuestion(
                            question_code=question_code,
                            question_stem=error_msg,
                            options={"A": "", "B": "", "C": "", "D": ""},
                            correct_answer="A",
                            level=spec.cognitive_level,
                            explanation=f"Lỗi: {error_str}",
                            lesson_name=spec.lesson_name,
                            question_type=spec.question_type
                        )
                        generated_questions.append(question)
                    break  # Thoát loop sau khi tạo dummy questions
        return generated_questions
    
    def generate_true_false_question(self, tf_spec: TrueFalseQuestionSpec, 
                                     prompt_template_path: str,
                                     question_template: str = "",
                                     content: str = "",
                                     history_context: str = "") -> GeneratedTrueFalseQuestion:
        """
        Sinh 1 câu hỏi Đúng/Sai hoàn chỉnh (4 mệnh đề cùng lúc)
        
        Args:
            tf_spec: TrueFalseQuestionSpec chứa 4 mệnh đề
            prompt_template_path: Đường dẫn đến prompt template DS
            question_template: Template câu hỏi mẫu từ DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            GeneratedTrueFalseQuestion: Câu hỏi DS đã sinh
        """
        tried_fallback = False
        attempt = 0
        
        # Retry logic với fallback model - dùng while để có thể reset attempt cho fallback
        while attempt < self.max_retries:
            try:
                # Build DS prompt via PromptBuilderService
                new_dir = str(Path(prompt_template_path).parent)
                if str(self.prompt_builder.prompt_dir) != new_dir:
                    self.prompt_builder.set_prompt_dir(new_dir)
                prepared_ds = self.prompt_builder.build_prompt_for_ds(tf_spec, content, question_template)
                prompt = prepared_ds.prompt_text
                # history_context passed as system_instruction (higher priority than prompt body)
                _sys_instruction = history_context if history_context else None

                # Debug: Kiểm tra content từ PDF
                # content_info = f"Content từ PDF: {len(content)} chars" if content else "❌ KHÔNG CÓ CONTENT TỪ PDF"
                # print(f"\n📤 Gửi prompt DS: {tf_spec.question_code} (Template={len(question_template)} chars, {content_info})")
                # if content:
                #     print(f"📄 Preview content: {content[:200]}...")
                # print(f"--- PROMPT START DS ---\n{prompt}\n--- PROMPT END ---")
                # print("content", content)
                # print("question_template:", question_template)

                # Chọn content schema phù hợp dựa trên rich_content_types
                content_schema = get_content_schema_by_rich_types(tf_spec.rich_content_types)
                ds_schema = get_true_false_schema(content_schema)
                
                # Gọi AI với JSON schema + Google Search - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    # Gemini-2.5-pro doesn't support controlled generation with Search tool
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt,
                        response_schema=ds_schema,
                        model_name=self.fallback_model,
                        system_instruction=_sys_instruction,
                        enable_search=False,
                        enable_thinking=False  # Fallback model doesn't support thinking_config
                    )
                else:
                    response = self.ai_client.generate_content_with_schema(
                        prompt=prompt,
                        response_schema=ds_schema,
                        system_instruction=_sys_instruction,
                        enable_search=True
                    )
                
                # Kiểm tra response
                if not response or response.strip() == "":
                    raise ValueError("Response từ AI trống")
                
                # Response đã là JSON từ schema
                data = json.loads(response) if isinstance(response, str) else response
                
                # Kiểm tra dữ liệu cần thiết
                if not data.get("source_text") or not data.get("statements"):
                    raise ValueError("Response thiếu dữ liệu bắt buộc (source_text hoặc statements)")
                
                # Clean statements - remove reasoning_type if present
                statements = data.get("statements", {})
                for key in statements:
                    if 'reasoning_type' in statements[key]:
                        del statements[key]['reasoning_type']
                
                # DEBUG: Kiểm tra source_citation
                source_citation = data.get("source_citation", "")
                source_origin = data.get("source_origin", "")
                if not source_citation or not source_origin:
                    print(f"⚠️  DS {tf_spec.question_code}: Thiếu source_citation={bool(source_citation)}, source_origin={bool(source_origin)}")
                    print(f"   AI Response keys: {list(data.keys())}")
                    # FALLBACK: Tạo citation mặc định nếu thiếu
                    if not source_citation:
                        source_citation = "(Nguồn: SGK Lịch sử 12, Chương trình Kết nối tri thức, 2024)"
                        print(f"   ➡️  Sử dụng citation mặc định")
                    if not source_origin:
                        source_origin = "scholarly_book"  # Default to textbook
                        print(f"   ➡️  Sử dụng origin mặc định: {source_origin}")
                
                # VALIDATION: Nếu không có rich_content_types, force text-only cho source_text
                source_text = data.get("source_text", "")
                if not hasattr(tf_spec, 'rich_content_types') or not tf_spec.rich_content_types:
                    if isinstance(source_text, dict) and source_text.get('type') != 'text':
                        print(f"⚠️  FORCE TEXT-ONLY DS: source_text có type={source_text.get('type')}, chuyển sang text")
                        if source_text.get('type') == 'mixed':
                            content = source_text.get('content', [])
                            text_parts = [item if isinstance(item, str) else '' for item in content]
                            source_text = {"type": "text", "content": ' '.join(text_parts).strip()}
                        else:
                            raise ValueError(f"DS source_text có rich content không mong muốn (type={source_text.get('type')})")
                else:
                    # VALIDATION: Nếu có rich_content_types, clean up mixed content
                    if isinstance(source_text, dict) and source_text.get('type') == 'mixed':
                        content = source_text.get('content', [])
                        if isinstance(content, list):
                            # Xác định loại content được yêu cầu
                            required_type = None
                            for code, types_list in tf_spec.rich_content_types.items():
                                if isinstance(types_list, list) and types_list:
                                    first_type = types_list[0]
                                    if isinstance(first_type, dict):
                                        code_val = first_type.get('code')
                                    else:
                                        code_val = first_type
                                    
                                    if code_val == 'BK':
                                        required_type = 'table'
                                    elif code_val == 'BD':
                                        required_type = 'chart'
                                    elif code_val == 'HA':
                                        required_type = 'image'
                                    break
                            
                            if required_type:
                                # Lọc content: chỉ giữ text và 1 element của required_type
                                cleaned_content = []
                                found_required = False
                                
                                for item in content:
                                    if isinstance(item, str):
                                        # Giữ text
                                        cleaned_content.append(item)
                                    elif isinstance(item, dict):
                                        item_type = item.get('type')
                                        if item_type == required_type and not found_required:
                                            # Giữ element đầu tiên của loại yêu cầu
                                            cleaned_content.append(item)
                                            found_required = True
                                        elif item_type != required_type:
                                            # Bỏ qua các loại content không mong muốn
                                            if self.verbose:
                                                print(f"   🗑️  Loại bỏ {item_type} không mong muốn (yêu cầu: {required_type})")
                                
                                if len(cleaned_content) != len(content):
                                    if self.verbose:
                                        print(f"⚠️  DS {tf_spec.question_code}: Cleaned mixed content từ {len(content)} → {len(cleaned_content)} items")
                                    source_text['content'] = cleaned_content
                                
                                if not found_required:
                                    print(f"⚠️  WARNING DS {tf_spec.question_code}: Không tìm thấy {required_type} trong mixed content!")
                
                # Tạo GeneratedTrueFalseQuestion với tất cả metadata fields
                question = GeneratedTrueFalseQuestion(
                    question_code=tf_spec.question_code,
                    source_text=source_text,
                    statements=statements,
                    explanation=data.get("explanation", {}),
                    lesson_name=tf_spec.lesson_name,
                    source_citation=source_citation,
                    source_origin=source_origin,
                    source_type=data.get("source_type", ""),
                    pedagogical_approach=data.get("pedagogical_approach", ""),
                    search_evidence=data.get("search_evidence", "")
                )
                
                return question
                
            except Exception as e:
                error_str = str(e)
                
                # Kiểm tra nếu là lỗi 429 (rate limit) và chưa thử fallback
                is_rate_limit = "429" in error_str and "RESOURCE_EXHAUSTED" in error_str
                
                if attempt < self.max_retries - 1:
                    # Còn lần thử, retry
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    attempt += 1
                    time.sleep(self.retry_delay)
                elif is_rate_limit and not tried_fallback:
                    # Hết lần thử nhưng là rate limit và chưa thử fallback
                    tried_fallback = True
                    attempt = 0  # Reset về 0 để thử lại với fallback model
                    print(f"🔄 Hết {self.max_retries} lần thử với model chính, chuyển sang fallback model: {self.fallback_model}")
                else:
                    # Hết retry và (đã fallback hoặc không phải rate limit), tạo dummy question
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu {tf_spec.question_code} sau {self.max_retries} lần thử")
                        if tried_fallback:
                            print(f"   (đã thử cả fallback model {self.fallback_model})")
                        print(f"   Error: {error_str}")
                        import traceback
                        traceback.print_exc()
                    
                    # Tạo dummy DS question với error message trong source_text
                    error_msg = f"Lỗi sinh câu hỏi: {error_str}"
                    question = GeneratedTrueFalseQuestion(
                        question_code=tf_spec.question_code,
                        source_text=error_msg,
                        statements={},
                        explanation={},
                        lesson_name=tf_spec.lesson_name
                    )
                    return question
    
    def generate_tln_questions(self, 
                              spec: QuestionSpec,
                              prompt_template_path: str = None,
                              question_template: str = "",
                              content: str = "",
                              history_context: str = "") -> List[GeneratedQuestion]:
        """
        Sinh câu hỏi TLN (Trắc nghiệm luận) cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template TLN (nếu khác với default)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            List[GeneratedQuestion]: Danh sách câu hỏi TLN đã sinh
        """        
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        last_error = None
        tried_fallback = False
        
        # Retry logic với fallback model
        for attempt in range(self.max_retries):
            try:
                # Build TLN prompt via PromptBuilderService
                if prompt_template_path:
                    new_dir = str(Path(prompt_template_path).parent)
                    if str(self.prompt_builder.prompt_dir) != new_dir:
                        self.prompt_builder.set_prompt_dir(new_dir)
                prepared_tln = self.prompt_builder.build_prompt_for_tln(spec, content, question_template)
                prompt_text = prepared_tln.prompt_text
                # history_context passed as system_instruction (higher priority than prompt body)
                _sys_instruction = history_context if history_context else None

                # Chọn content schema phù hợp dựa trên rich_content_types
                content_schema = get_content_schema_by_rich_types(spec.rich_content_types)
                tln_schema = get_short_answer_array_schema(content_schema)
                
                # Gọi AI với TLN array schema - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    # Gemini-2.5-pro doesn't support controlled generation with Search tool
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt_text,
                        response_schema=tln_schema,
                        model_name=self.fallback_model,
                        system_instruction=_sys_instruction,
                        enable_search=False,
                        enable_thinking=False  # Fallback model doesn't support thinking_config
                    )
                else:
                    response = self.ai_client.generate_content_with_schema(
                        prompt=prompt_text,
                        response_schema=tln_schema,
                        system_instruction=_sys_instruction,
                        enable_search=True
                    )
                
                # Parse response
                data = json.loads(response) if isinstance(response, str) else response
                questions_data = data.get("questions", [])
                
                # Kiểm tra nếu không có câu hỏi nào được sinh
                if not questions_data or len(questions_data) == 0:
                    raise ValueError("AI không trả về câu hỏi nào")
                
                # ⚠️ VALIDATION: AI có thể generate nhiều hơn yêu cầu → chỉ lấy đúng số lượng
                if len(questions_data) > spec.num_questions:
                    print(f"⚠️ WARNING: AI generated {len(questions_data)} TLN questions, but only {spec.num_questions} requested. Taking first {spec.num_questions}.")
                    questions_data = questions_data[:spec.num_questions]
                
                # Tạo GeneratedQuestion cho mỗi câu TLN
                for i, question_data in enumerate(questions_data):
                    question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"Q{i+1}"
                    
                    # TLN không có options (A/B/C/D), chỉ có correct_answer
                    question = GeneratedQuestion(
                        question_code=question_code,
                        question_stem=question_data.get("question_stem", ""),
                        options={},  # Empty dict for TLN
                        correct_answer=question_data.get("correct_answer", ""),
                        level=question_data.get("level", spec.cognitive_level),
                        explanation=question_data.get("explanation", ""),
                        lesson_name=spec.lesson_name,
                        question_type=spec.question_type
                    )
                    
                    generated_questions.append(question)
                
                # Thành công, thoát retry loop
                break
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Kiểm tra nếu là lỗi 429 và chưa thử fallback
                is_rate_limit = "429" in error_str and "RESOURCE_EXHAUSTED" in error_str
                
                if attempt < self.max_retries - 1:
                    if self.verbose:
                        print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str[:80]}")
                        print(f"   Thử lại sau {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                elif is_rate_limit and not tried_fallback:
                    # Thử fallback model
                    tried_fallback = True
                    print(f"🔄 Hết {self.max_retries} lần thử với model chính, chuyển sang fallback model: {self.fallback_model}")
                    # Reset attempt counter cho fallback
                    attempt = -1  # Sẽ tăng lên 0 ở vòng lặp tiếp theo
                    continue
                else:
                    # Hết retry và hết fallback, tạo dummy questions
                    if self.verbose:
                        print(f"\n❌ Lỗi khi sinh câu hỏi TLN sau {self.max_retries} lần thử")
                        if tried_fallback:
                            print(f"   (đã thử cả fallback model {self.fallback_model})")
                        print(f"   Error: {error_str}")
                        import traceback
                        traceback.print_exc()
                    
                    # Tạo dummy questions với error message
                    error_msg = f"Lỗi sinh câu hỏi: {error_str}"
                    for question_code in spec.question_codes:
                        question = GeneratedQuestion(
                            question_code=question_code,
                            question_stem=error_msg,
                            options={},  # Empty for TLN
                            correct_answer="",
                            level=spec.cognitive_level,
                            explanation=f"Lỗi: {error_str}",
                            lesson_name=spec.lesson_name,
                            question_type=spec.question_type
                        )
                        generated_questions.append(question)
                    break  # Thoát loop sau khi tạo dummy questions
        
        return generated_questions

    def generate_tl_questions(self, 
                             spec: QuestionSpec,
                             prompt_template_path: str = None,
                             question_template: str = "",
                             content: str = "",
                             history_context: str = "") -> List[GeneratedEssayQuestion]:
        """
        Sinh câu hỏi TL (Tự luận) cho một QuestionSpec
        
        Args:
            spec: QuestionSpec chứa thông tin câu hỏi
            prompt_template_path: Đường dẫn đến prompt template TL (nếu khác với default)
            question_template: Template câu hỏi mẫu từ file DOCX (optional)
            content: Nội dung từ PDF đã extract (optional)
            
        Returns:
            List[GeneratedEssayQuestion]: Danh sách câu hỏi TL đã sinh
        """        
        # Load template nếu cần
        if prompt_template_path and prompt_template_path != self.prompt_template:
            template = self._load_prompt_template(prompt_template_path)
        else:
            template = self.prompt_template
        
        generated_questions = []
        last_error = None
        tried_fallback = False
        
        # Retry logic với fallback model
        for attempt in range(self.max_retries):
            try:
                # Build TL prompt via PromptBuilderService
                if prompt_template_path:
                    new_dir = str(Path(prompt_template_path).parent)
                    if str(self.prompt_builder.prompt_dir) != new_dir:
                        self.prompt_builder.set_prompt_dir(new_dir)
                prepared_tl = self.prompt_builder.build_prompt_for_tl(spec, content, question_template)
                prompt_text = prepared_tl.prompt_text
                # history_context passed as system_instruction (higher priority than prompt body)
                _sys_instruction = history_context if history_context else None

                if self.verbose:
                    print(f"📝 Generating {spec.num_questions} TL questions for lesson: {spec.lesson_name}")
                    print(f"🎯 Cognitive level: {spec.cognitive_level}")
                
                # Chọn content schema phù hợp dựa trên rich_content_types
                content_schema = get_content_schema_by_rich_types(spec.rich_content_types)
                spec_sub_items = getattr(spec, 'sub_items', None)
                if spec_sub_items:
                    tl_schema = get_essay_with_sub_items_array_schema(spec_sub_items, content_schema)
                else:
                    tl_schema = get_essay_array_schema(content_schema)
                
                # Gọi AI với TL array schema - sử dụng fallback model nếu đã thử
                if tried_fallback:
                    print(f"🔄 Thử fallback model: {self.fallback_model}")
                    # Gemini-2.5-pro doesn't support controlled generation with Search tool
                    response = self.ai_client.generate_content_with_schema_with_model(
                        prompt=prompt_text,
                        response_schema=tl_schema,
                        model_name=self.fallback_model,
                        system_instruction=_sys_instruction,
                        enable_search=False,
                        enable_thinking=False  # Fallback model doesn't support thinking_config
                    )
                else:
                    response = self.ai_client.generate_content_with_schema(
                        prompt=prompt_text,
                        response_schema=tl_schema,
                        system_instruction=_sys_instruction,
                        enable_search=True
                    )
                
                # Parse response
                data = json.loads(response) if isinstance(response, str) else response
                questions_data = data.get("questions", [])
                
                # Kiểm tra nếu không có câu hỏi nào được sinh
                if not questions_data or len(questions_data) == 0:
                    raise ValueError("AI không trả về câu hỏi nào")
                
                # ⚠️ VALIDATION: AI có thể generate nhiều hơn yêu cầu → chỉ lấy đúng số lượng
                if self.verbose:
                    print(f"📊 AI returned {len(questions_data)} TL questions, spec.num_questions={spec.num_questions}")
                
                if len(questions_data) > spec.num_questions:
                    print(f"⚠️ WARNING: AI generated {len(questions_data)} questions, but only {spec.num_questions} requested. Taking first {spec.num_questions}.")
                    questions_data = questions_data[:spec.num_questions]
                
                # Tạo GeneratedEssayQuestion cho mỗi câu TL
                for i, question_data in enumerate(questions_data):
                    try:
                        question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"TL{spec.row_index + 1 + i}"
                        
                        # Validate question_stem structure to catch unhashable errors early
                        q_stem = question_data.get("question_stem", "")
                        if not isinstance(q_stem, (str, dict)):
                            print(f"⚠️ WARNING: Invalid question_stem type: {type(q_stem)}, converting to string")
                            q_stem = str(q_stem)
                        
                        # Validate answer_structure
                        answer_structure_raw = question_data.get("answer_structure", {})
                        if isinstance(answer_structure_raw, dict):
                            answer_structure = answer_structure_raw
                        else:
                            answer_structure = {}

                        # Extract sub_questions (TL with sub-items)
                        sub_questions_raw = question_data.get("sub_questions", None)
                        sub_questions = sub_questions_raw if isinstance(sub_questions_raw, list) else None

                        # Tạo question object - ĐẶT TRONG TRY-CATCH để bắt mọi lỗi
                        question = GeneratedEssayQuestion(
                            question_code=question_code,
                            question_stem=q_stem,
                            question_type=question_data.get("question_type", "analysis"),
                            answer_structure=answer_structure,
                            level=spec.cognitive_level,
                            lesson_name=spec.lesson_name,
                            sub_questions=sub_questions,
                        )
                        generated_questions.append(question)
                        
                        if self.verbose:
                            stem_preview = (question.question_stem if isinstance(question.question_stem, str)
                                           else str(question.question_stem.get('content', question.question_stem)))[:50]
                            print(f"✅ Generated TL question {i+1}/{len(questions_data)}: {stem_preview}...")
                    
                    except (TypeError, KeyError, AttributeError, ValueError, Exception) as parse_error:
                        print(f"⚠️ ERROR parsing question {i}: {parse_error}")
                        # print(f"   Raw data: {question_data}")
                        # Skip this question - KHÔNG append vào array
                
                # Thành công, thoát loop
                break
                
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                
                if self.verbose:
                    print(f"⚠️  Lần thử {attempt + 1}/{self.max_retries} thất bại: {error_str}")
                
                # Thử fallback model nếu chưa thử và còn attempt
                if not tried_fallback and self.fallback_model:
                    if self.verbose:
                        print(f"🔄 Thử fallback model: {self.fallback_model}")
                    
                    # Đánh dấu đã thử fallback để không thử lại
                    tried_fallback = True
                    
                    try:
                        # Chọn content schema phù hợp dựa trên rich_content_types
                        content_schema = get_content_schema_by_rich_types(spec.rich_content_types)
                        tl_schema_fallback = get_essay_array_schema(content_schema)
                        
                        # Retry with fallback model using array schema
                        # ⚠️ CRITICAL: gemini-2.5-pro KHÔNG hỗ trợ Search + JSON schema
                        if self.verbose:
                            print(f"🔧 Calling fallback with enable_search=False, model={self.fallback_model}")
                        response = self.ai_client.generate_content_with_schema_with_model(
                            prompt=prompt_text,
                            response_schema=tl_schema_fallback,
                            model_name=self.fallback_model,
                            enable_search=False,
                            enable_thinking=False  # Fallback model doesn't support thinking_config
                        )
                        
                        # Parse response
                        data = json.loads(response) if isinstance(response, str) else response
                        questions_data = data.get("questions", [])
                        
                        if not questions_data or len(questions_data) == 0:
                            raise ValueError("AI không trả về câu hỏi nào với fallback model")
                        
                        # ⚠️ VALIDATION: AI có thể generate nhiều hơn yêu cầu → chỉ lấy đúng số lượng
                        if self.verbose:
                            print(f"📊 Fallback AI returned {len(questions_data)} TL questions, spec.num_questions={spec.num_questions}")
                        
                        if len(questions_data) > spec.num_questions:
                            print(f"⚠️ WARNING (fallback): AI generated {len(questions_data)} questions, but only {spec.num_questions} requested. Taking first {spec.num_questions}.")
                            questions_data = questions_data[:spec.num_questions]
                        
                        # Tạo GeneratedEssayQuestion cho mỗi câu TL
                        for i, question_data in enumerate(questions_data):
                            try:
                                question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"TL{spec.row_index + 1 + i}"
                                
                                # Validate question_stem structure to catch unhashable errors early
                                q_stem = question_data.get("question_stem", "")
                                if not isinstance(q_stem, (str, dict)):
                                    print(f"⚠️ WARNING: Invalid question_stem type: {type(q_stem)}, converting to string")
                                    q_stem = str(q_stem)
                                
                                # Parse scoring_rubric - schema trả về string nhưng dataclass expect Dict
                                scoring_rubric_raw = question_data.get("scoring_rubric", "")
                                if isinstance(scoring_rubric_raw, str):
                                    # Convert string to dict format
                                    scoring_rubric = {"description": scoring_rubric_raw}
                                elif isinstance(scoring_rubric_raw, dict):
                                    scoring_rubric = scoring_rubric_raw
                                else:
                                    scoring_rubric = {}
                                
                                # Validate and sanitize key_points to prevent unhashable errors
                                key_points_raw = question_data.get("key_points", [])
                                if isinstance(key_points_raw, list):
                                    key_points = []
                                    for kp in key_points_raw:
                                        if isinstance(kp, dict):
                                            key_points.append(kp)
                                        else:
                                            print(f"⚠️ WARNING (fallback): Invalid key_point format: {type(kp)}, skipping")
                                else:
                                    print(f"⚠️ WARNING (fallback): key_points is not a list: {type(key_points_raw)}, using empty list")
                                    key_points = []
                                
                                # Validate required_elements
                                required_elements_raw = question_data.get("required_elements", [])
                                if isinstance(required_elements_raw, list):
                                    required_elements = [str(e) for e in required_elements_raw]
                                else:
                                    required_elements = []
                                
                                # Validate answer_structure
                                answer_structure_raw = question_data.get("answer_structure", {})
                                if isinstance(answer_structure_raw, dict):
                                    answer_structure = answer_structure_raw
                                else:
                                    answer_structure = {}
                                
                                # Tạo question object - ĐẶT TRONG TRY-CATCH để bắt mọi lỗi
                                question = GeneratedEssayQuestion(
                                    question_code=question_code,
                                    question_stem=q_stem,
                                    question_type=question_data.get("question_type", "analysis"),
                                    historical_context=question_data.get("historical_context", ""),
                                    required_elements=required_elements,
                                    answer_structure=answer_structure,
                                    sample_answer=question_data.get("sample_answer", ""),
                                    key_points=key_points,
                                    scoring_rubric=scoring_rubric,
                                    level=spec.cognitive_level,
                                    lesson_name=spec.lesson_name
                                )
                                generated_questions.append(question)
                                
                                if self.verbose:
                                    print(f"✅ Generated TL question {i+1}/{len(questions_data)} with fallback: {question.question_stem[:50]}...")
                            
                            except (TypeError, KeyError, AttributeError, ValueError, Exception) as parse_error:
                                print(f"⚠️ ERROR parsing fallback question {i}: {parse_error}")
                                print(f"   Raw data: {question_data}")
                                # Skip this question - KHÔNG append vào array
                        
                        # Thành công với fallback, thoát loop
                        break
                        
                    except Exception as fallback_e:
                        if self.verbose:
                            print(f"❌ Fallback cũng thất bại: {str(fallback_e)}")
                        # Fallback fail → thoát luôn, tạo dummy questions
                        last_error = str(fallback_e)
                        break
                
                # Chờ trước khi retry
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # Nếu tất cả attempts thất bại, tạo dummy question
        if not generated_questions:
            if self.verbose:
                print(f"❌ Tất cả {self.max_retries} lần thử đều thất bại. Tạo dummy TL question.")
            
            for i in range(spec.num_questions):
                question_code = spec.question_codes[i] if i < len(spec.question_codes) else f"TL{spec.row_index + 1 + i}"
                question = GeneratedEssayQuestion(
                    question_code=question_code,
                    question_stem=f"Câu hỏi tự luận cho bài: {spec.lesson_name} (Cognitive level: {spec.cognitive_level})",
                    question_type="analysis",
                    historical_context="",
                    required_elements=["Nguyên nhân", "Diễn biến", "Ý nghĩa"],
                    answer_structure={
                        "introduction": "Giới thiệu vấn đề",
                        "body": ["Nguyên nhân", "Diễn biến", "Ý nghĩa"],
                        "conclusion": "Kết luận và bài học"
                    },
                    sample_answer="Đây là câu trả lời mẫu cho câu hỏi tự luận.",
                    key_points=[
                        {"point": "Nguyên nhân", "weight": 3, "description": "Phân tích nguyên nhân"},
                        {"point": "Diễn biến", "weight": 4, "description": "Mô tả diễn biến"},
                        {"point": "Ý nghĩa", "weight": 3, "description": "Đánh giá ý nghĩa"}
                    ],
                    scoring_rubric={
                        "excellent": "Trả lời đầy đủ, logic, có dẫn chứng (9-10 điểm)",
                        "good": "Trả lời khá đầy đủ, có lập luận (7-8 điểm)",
                        "average": "Trả lời cơ bản, thiếu lập luận (5-6 điểm)",
                        "weak": "Trả lời sai hoặc thiếu nhiều (dưới 5 điểm)"
                    },
                    level=spec.cognitive_level,
                    lesson_name=spec.lesson_name
                )
                generated_questions.append(question)
        
        if self.verbose:
            print(f"📤 generate_tl_questions returning {len(generated_questions)} questions (spec.num_questions={spec.num_questions})")
        
        return generated_questions

    def generate_questions_batch(self, 
                                specs: List[QuestionSpec],
                                output_dir: Optional[str] = None) -> Dict[str, List[GeneratedQuestion]]:
        """
        Sinh câu hỏi cho nhiều QuestionSpec
        
        Args:
            specs: Danh sách QuestionSpec
            output_dir: Thư mục lưu kết quả (nếu có)
            
        Returns:
            Dict[str, List[GeneratedQuestion]]: Dict với key là loại câu hỏi
        """
        print(f"\n{'#'*80}")
        print(f"BẮT ĐẦU SINH {len(specs)} NHÓM CÂU HỎI")
        print(f"{'#'*80}")
        
        all_questions = {}
        
        for idx, spec in enumerate(specs, 1):
            print(f"\n>>> Nhóm {idx}/{len(specs)}")
            
            questions = self.generate_questions_for_spec(spec)
            
            # Lưu theo loại câu hỏi
            question_type = spec.question_type
            if question_type not in all_questions:
                all_questions[question_type] = []
            
            all_questions[question_type].extend(questions)
        
        # Lưu kết quả nếu có output_dir
        if output_dir:
            self.save_questions_to_json(all_questions, output_dir)
        
        print(f"\n{'#'*80}")
        print(f"HOÀN THÀNH SINH CÂU HỎI")
        print(f"Tổng số câu: {sum(len(qs) for qs in all_questions.values())}")
        print(f"{'#'*80}")
        
        return all_questions
    
    def save_questions_to_json(self, 
                              questions: Dict[str, List[GeneratedQuestion]], 
                              output_dir: str):
        """
        Lưu câu hỏi ra file JSON
        
        Args:
            questions: Dict chứa câu hỏi theo loại
            output_dir: Thư mục output
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for question_type, question_list in questions.items():
            # Convert to dict
            questions_dict = [asdict(q) for q in question_list]
            
            # Tạo file name
            file_name = f"questions_{question_type}.json"
            file_path = output_path / file_name
            
            # Lưu file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(questions_dict, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Đã lưu {len(question_list)} câu hỏi {question_type} vào: {file_path}")
        
    def generate_questions_with_custom_prompt(self, prompt_template: str, content: str, num_questions: int, rich_content_types: Optional[List[str]] = None) -> List[GeneratedQuestion]:
        """
        Generate questions using a custom prompt template
        
        Args:
            prompt_template: The full prompt template with placeholders already filled
            content: Lesson content
            num_questions: Number of questions to generate
            rich_content_types: List of rich content types (e.g. ['BK', 'BD'])
            
        Returns:
            List[GeneratedQuestion]: Generated questions
        """
        try:
            # Chọn content schema phù hợp dựa trên rich_content_types
            content_schema = get_content_schema_by_rich_types(rich_content_types)
            tn_schema = get_multiple_choice_array_schema(content_schema)
            
            # Call AI with the custom prompt
            response = self.ai_client.generate_content_with_schema(
                prompt=prompt_template,
                response_schema=tn_schema,
                enable_search=True
            )
            
            # Validate response
            if not response:
                print("❌ AI returned empty response")
                return []
            
            # Check if response is truncated (common sign: doesn't end with } or ])
            response_str = response if isinstance(response, str) else str(response)
            if not response_str.rstrip().endswith('}') and not response_str.rstrip().endswith(']'):
                print(f"⚠️ Response appears truncated (length: {len(response_str)})")
                print(f"⚠️ Response ends with: ...{response_str[-100:]}")
            
            # Parse response
            data = json.loads(response) if isinstance(response, str) else response
            questions_data = data.get("questions", [])
            
            generated_questions = []
            for i, question_data in enumerate(questions_data):
                question_code = f"C{i+1}"
                
                question = GeneratedQuestion(
                    question_code=question_code,
                    question_stem=question_data.get("question_stem", ""),
                    options=question_data.get("options", {}),
                    correct_answer=question_data.get("correct_answer", ""),
                    level=question_data.get("level", "medium"),
                    explanation=question_data.get("explanation", ""),
                    lesson_name="",  # Will be set by caller
                    question_type="TN"
                )
                
                generated_questions.append(question)
            
            return generated_questions
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"❌ Raw response: {response[:500] if response else 'None'}")
            return []
        except Exception as e:
            print(f"❌ Error generating questions with custom prompt: {e}")
            return []
    
    def generate_ds_with_custom_prompt(self, prompt_template: str, content: str, question_code: str, rich_content_types: Optional[List[str]] = None) -> Optional[GeneratedTrueFalseQuestion]:
        """
        Generate DS question using a custom prompt template
        
        Args:
            prompt_template: The full prompt template with placeholders already filled
            content: Lesson content
            question_code: Question code for the DS question
            rich_content_types: List of allowed rich content types from matrix (e.g. ['BK', 'BD'])
            
        Returns:
            GeneratedTrueFalseQuestion or None
        """
        try:
            # Chọn content schema phù hợp dựa trên rich_content_types
            content_schema = get_content_schema_by_rich_types(rich_content_types)
            ds_schema = get_true_false_schema(content_schema)
            
            # Call AI with the custom prompt
            response = self.ai_client.generate_content_with_schema(
                prompt=prompt_template,
                response_schema=ds_schema,
                enable_search=True
            )
            
            # Debug: Log response
            print(f"🔍 DEBUG DS: AI Response length: {len(response) if response else 0}")
            if response:
                print(f"🔍 DEBUG DS: AI Response preview: {response[:200]}...")
            else:
                print("🔍 DEBUG DS: AI Response is empty!")
            
            # Parse response
            data = json.loads(response) if isinstance(response, str) else response
            
            # VALIDATION: If no rich_content_types specified, force text-only for source_text
            source_text = data.get("source_text", "")
            if not rich_content_types:
                if isinstance(source_text, dict) and source_text.get('type') != 'text':
                    print(f"⚠️  FORCE TEXT-ONLY DS (alternative): source_text có type={source_text.get('type')}, chuyển sang text")
                    if source_text.get('type') == 'mixed':
                        content_items = source_text.get('content', [])
                        text_parts = []
                        for item in content_items:
                            if isinstance(item, str):
                                text_parts.append(item)
                            elif isinstance(item, dict) and item.get('type') == 'text':
                                text_parts.append(item.get('content', ''))
                        source_text = {"type": "text", "content": ' '.join(text_parts).strip()}
                    else:
                        # If it's other rich content type, extract text content or use fallback
                        if isinstance(source_text, dict):
                            source_text = {"type": "text", "content": source_text.get('content', '')}
            
            # Create GeneratedTrueFalseQuestion with all metadata fields
            question = GeneratedTrueFalseQuestion(
                question_code=question_code,
                source_text=source_text,
                statements=data.get("statements", {}),
                explanation=data.get("explanation", {}),
                lesson_name="",  # Will be set by caller
                question_type="DS",
                source_citation=data.get("source_citation", ""),
                source_origin=data.get("source_origin", ""),
                source_type=data.get("source_type", ""),
                pedagogical_approach=data.get("pedagogical_approach", ""),
                search_evidence=data.get("search_evidence", "")
            )
            
            return question
            
        except json.JSONDecodeError as e:
            print(f"❌ DS JSON Parse Error: {e}")
            print(f"❌ DS Raw response: {response[:500] if response else 'None'}")
            return None
        except Exception as e:
            print(f"❌ Error generating DS question with custom prompt: {e}")
            return None
        
    def print_question_summary(self, question: GeneratedQuestion):
        """
        In tóm tắt một câu hỏi
        
        Args:
            question: GeneratedQuestion cần in
        """
        print(f"\n{'='*80}")
        print(f"[{question.question_code}] {question.question_stem}")
        print(f"{'-'*80}")
        for key, value in question.options.items():
            marker = " ← ĐÚNG" if key == question.correct_answer else ""
            print(f"  {key}. {value}{marker}")
        print(f"{'-'*80}")
        print(f"Cấp độ: {question.level} | Bài: {question.lesson_name}")
        print(f"Giải thích: {question.explanation[:100]}...")
        print(f"{'='*80}")
