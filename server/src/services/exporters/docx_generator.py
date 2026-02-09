import json
from pathlib import Path
from typing import Dict, List, Union, Optional, Any
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import tempfile
import os
import base64
from io import BytesIO
from PIL import Image
import threading
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    # Use ASCII-safe print to avoid UnicodeEncodeError in Windows CP1252 console
    try:
        print("✓ Playwright available for chart rendering")
    except UnicodeEncodeError:
        print("[OK] Playwright available for chart rendering")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    try:
        print("⚠️  Playwright not available. Charts will be rendered as text placeholders.")
    except UnicodeEncodeError:
        print("[WARN] Playwright not available. Charts will be rendered as text placeholders.")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import Config
from services.generators.helpers.chart_generation_helper import apply_layout


class DocxGenerator:
    """Class tạo file DOCX từ dữ liệu JSON"""
    
    def __init__(self, verbose: bool = False):
        self.document = None
        self.output_path = None
        self.verbose = verbose
        
        # Màu nền theo level
        self.level_colors = {
            'NB': 'ADFF2F',  # Bright green
            'TH': '40E0D0',  # Turquoise
            'VD': 'FFFF00'   # Yellow
        }
    
    def create_new_document(self):
        """Tạo document mới"""
        self.document = Document()
        if self.verbose:
            print("✓ Đã tạo document mới")
    
    def set_document_style(self, 
                          font_name: str = "Times New Roman",
                          font_size: int = 12):
        """
        Thiết lập style mặc định cho document
        
        Args:
            font_name (str): Tên font chữ
            font_size (int): Kích thước font
        """
        if self.document is None:
            self.create_new_document()
        
        # Thiết lập style cho Normal
        style = self.document.styles['Normal']
        font = style.font
        font.name = font_name
        font.size = Pt(font_size)
        
        if self.verbose:
            print(f"✓ Đã thiết lập style: {font_name}, {font_size}pt")
    
    def add_heading(self, 
                   text: str, 
                   level: int = 1,
                   alignment: str = "left"):
        """
        Thêm tiêu đề
        
        Args:
            text (str): Nội dung tiêu đề
            level (int): Cấp độ tiêu đề (1-9)
            alignment (str): Căn lề (left, center, right)
        """
        if self.document is None:
            self.create_new_document()
        
        heading = self.document.add_heading(text, level=level)
        
        if alignment == "center":
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif alignment == "right":
            heading.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        return heading
    
    def add_paragraph(self, 
                     text: str,
                     bold: bool = False,
                     italic: bool = False,
                     alignment: str = "left"):
        """
        Thêm đoạn văn
        
        Args:
            text (str): Nội dung
            bold (bool): In đậm
            italic (bool): In nghiêng
            alignment (str): Căn lề
        """
        if self.document is None:
            self.create_new_document()
        
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
        
        if alignment == "center":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif alignment == "right":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif alignment == "justify":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        return paragraph
    
    def add_table_from_dict(self, 
                           data: List[Dict],
                           headers: Optional[List[str]] = None,
                           auto_headers: bool = True):
        """
        Thêm bảng từ dữ liệu dictionary
        
        Args:
            data (List[Dict]): Dữ liệu dạng list of dict
            headers (List[str], optional): Tiêu đề cột
            auto_headers (bool): Tự động lấy headers từ dict keys
        """
        if self.document is None:
            self.create_new_document()
        
        if not data:
            if self.verbose:
                print("⚠ Không có dữ liệu để tạo bảng")
            return
        
        # Lấy headers
        if headers is None and auto_headers:
            headers = list(data[0].keys())
        
        # Tạo bảng với border đơn giản, không tô màu
        table = self.document.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'  # Border đơn giản, không màu
        
        # Thêm header
        header_cells = table.rows[0].cells
        for idx, header in enumerate(headers):
            header_cells[idx].text = str(header)
            # Format header: CHỈ BOLD, không tô màu nền
            for paragraph in header_cells[idx].paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(11)
        
        # Thêm dữ liệu
        for item in data:
            row_cells = table.add_row().cells
            for idx, header in enumerate(headers):
                value = item.get(header, "")
                row_cells[idx].text = str(value)
        
        if self.verbose:
            print(f"✓ Đã thêm bảng {len(data)} hàng x {len(headers)} cột")
        return table
    
    def add_page_break(self):
        """Thêm ngắt trang"""
        if self.document is None:
            self.create_new_document()
        
        self.document.add_page_break()
    
    def _set_run_background(self, run, level: str):
        """Tô màu nền cho run dựa vào level"""
        color = self.level_colors.get(level, 'FFFFFF')
        
        # Tạo shading element
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), color)
        run._element.get_or_add_rPr().append(shading_elm)
    
    def _add_mixed_content(self, para, content: List):
        """Xử lý mixed content: text + table + chart"""
        for item in content:
            if isinstance(item, str):
                # Text content
                para.add_run(item)
            elif isinstance(item, dict):
                item_type = item.get('type', '')
                
                if item_type == 'table':
                    # Add line break before table
                    para.add_run('\n')
                    self._add_inline_table(item.get('content', {}))
                    
                elif item_type == 'chart':
                    # Add line break before chart
                    para.add_run('\n')
                    self._add_inline_chart(item.get('content', {}))
                    
                elif item_type == 'image':
                    # Add line break before image
                    para.add_run('\n')
                    caption = item.get('metadata', {}).get('caption', '')
                    if caption:
                        para.add_run(f"[Hình ảnh: {caption}]")
                    else:
                        para.add_run(f"[Hình ảnh: {item.get('content', '')}]")
                    para.add_run('\n')
                    
                elif item_type == 'chart' and 'chart_id' in item:
                    # Chart reference (không có echarts data, chỉ có chart_id)
                    para.add_run('\n')
                    para.add_run(f"[Biểu đồ {item.get('chart_id')}]")
                    para.add_run('\n')
    
    def _add_inline_table(self, table_data: Dict):
        """Thêm bảng inline vào document"""
        if not table_data:
            return
        
        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])
        
        if not headers or not rows:
            return
        
        # Tạo bảng với border đơn giản, không tô màu
        table = self.document.add_table(rows=1, cols=len(headers))
        table.style = 'Table Grid'  # Border đơn giản, không màu
        
        # Thêm header
        header_cells = table.rows[0].cells
        for idx, header in enumerate(headers):
            header_cells[idx].text = str(header)
            # Format header: CHỈ BOLD, không tô màu nền
            for paragraph in header_cells[idx].paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(11)
        
        # Thêm dữ liệu
        for row_data in rows:
            row_cells = table.add_row().cells
            for idx, cell_value in enumerate(row_data):
                if idx < len(row_cells):
                    row_cells[idx].text = str(cell_value)
                    # Format cell
                    for paragraph in row_cells[idx].paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(11)
        
        # Thêm caption nếu có
        metadata = table_data.get('metadata', {})
        caption = metadata.get('caption', '')
        source = metadata.get('source', '')
        
        if caption:
            para = self.document.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(caption)
            run.italic = True
            run.font.size = Pt(10)
        
        if source:
            para = self.document.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(f"(Nguồn: {source})")
            run.italic = True
            run.font.size = Pt(10)
    
    def _add_inline_chart(self, chart_data: Dict):
        """Thêm chart vào document - render thành PNG nếu có playwright"""
        if not chart_data:
            if self.verbose:
                print("⚠️  Chart data is empty")
            return
        
        chart_type = chart_data.get('chartType', 'bar')
        echarts = chart_data.get('echarts', {})
        
        if self.verbose:
            print(f"📊 Processing chart: type={chart_type}, has_echarts={bool(echarts)}")
            print(f"  PLAYWRIGHT_AVAILABLE: {PLAYWRIGHT_AVAILABLE}")
        
        # Lấy thông tin cơ bản từ echarts
        title = echarts.get('title', {}).get('text', 'Biểu đồ')
        
        # Render chart thành ảnh nếu có playwright
        if PLAYWRIGHT_AVAILABLE:
            try:
                if self.verbose:
                    print(f"  Attempting to render chart to image...")
                image_path = self._render_chart_to_image(echarts)
                if image_path:
                    # Thêm ảnh vào document
                    para = self.document.add_paragraph()
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = para.add_run()
                    run.add_picture(image_path, width=Inches(5.5))
                    
                    # Xóa file tạm
                    try:
                        os.remove(image_path)
                    except:
                        pass
                    
                    if self.verbose:
                        print(f"✓ Đã chèn chart vào DOCX: {title}")
                    return
                else:
                    if self.verbose:
                        print(f"⚠️  _render_chart_to_image returned None")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Không thể render chart thành ảnh: {e}")
                    import traceback
                    traceback.print_exc()
                # Fall through to placeholder
        else:
            if self.verbose:
                print(f"⚠️  PLAYWRIGHT_AVAILABLE is False, using placeholder")
        
        # Fallback: Placeholder text nếu không có playwright hoặc lỗi
        para = self.document.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(title)
        run.bold = True
        run.font.size = Pt(12)
        
        para = self.document.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(f"[{chart_type.upper()} CHART - Cần cài playwright để xuất ảnh]")
        run.italic = True
        run.font.color.rgb = RGBColor(128, 128, 128)
        
        # Thêm graphic source nếu có
        graphic = echarts.get('graphic', [])
        if graphic and len(graphic) > 0:
            source_text = graphic[0].get('style', {}).get('text', '')
            if source_text:
                para = self.document.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = para.add_run(source_text)
                run.italic = True
                run.font.size = Pt(10)
    
    def _render_chart_to_image(self, echarts_config: Dict) -> Optional[str]:
        """
        Render ECharts config thành PNG image sử dụng Playwright
        
        Args:
            echarts_config: ECharts configuration dict
            
        Returns:
            Path đến file PNG tạm, hoặc None nếu thất bại
        """
        if not PLAYWRIGHT_AVAILABLE:
            return None
        
        try:
            # Apply layout resolution (tính grid.bottom nếu chưa có)
            echarts_config = apply_layout(echarts_config)
            
            # Tắt animation để đảm bảo screenshot đầy đủ
            if 'animation' not in echarts_config:
                echarts_config['animation'] = False
            
            # Tạo HTML chứa ECharts với animation tắt
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/echarts@6.0.0/dist/echarts.min.js"></script>
    <style>
        body {{ margin: 0; padding: 30px; background: white; }}
        #chart {{ width: 900px; height: 850px; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var chartDom = document.getElementById('chart');
        var myChart = echarts.init(chartDom);
        var option = {json.dumps(echarts_config, ensure_ascii=False)};
        
        // Set option với animation tắt
        myChart.setOption(option);
        
        // Đợi render hoàn tất
        setTimeout(function() {{
            window.chartReady = true;
        }}, 500);
    </script>
</body>
</html>
"""
            
            # Tạo file PNG tạm
            with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
                png_path = f.name
            
            # Result container for thread
            result = {'path': None, 'error': None}
            
            def render_in_thread():
                try:
                    # Sử dụng Playwright để render (trong thread riêng để tránh xung đột với asyncio)
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        # Tăng viewport để đủ chứa chart + padding (900x850 + 60px padding = 960x910)
                        # Set deviceScaleFactor = 2 để ảnh sắc nét hơn (Retina-quality)
                        page = browser.new_page(
                            viewport={'width': 960, 'height': 910},
                            device_scale_factor=2
                        )
                        
                        # Load HTML content directly (better than file:// for security)
                        page.set_content(html_content)
                        
                        # Đợi chart render xong
                        page.wait_for_function('window.chartReady === true', timeout=10000)
                        
                        # Đợi thêm để đảm bảo chart render hoàn toàn (tăng từ 1s lên 2s)
                        page.wait_for_timeout(2000)
                        
                        # Screenshot với full quality
                        chart_element = page.locator('#chart')
                        chart_element.screenshot(path=png_path, type='png')
                        
                        browser.close()
                        result['path'] = png_path
                except Exception as e:
                    result['error'] = str(e)
            
            try:
                # Chạy render trong thread riêng (tăng timeout cho lần đầu download playwright)
                thread = threading.Thread(target=render_in_thread)
                thread.start()
                thread.join(timeout=30)  # Wait max 30 seconds (lần đầu cần download browser)
                
                if result['error']:
                    raise Exception(result['error'])
                
                if result['path']:
                    return result['path']
                else:
                    # Timeout or no result
                    try:
                        os.remove(png_path)
                    except:
                        pass
                    return None
            except Exception as e:
                # Cleanup
                try:
                    os.remove(png_path)
                except:
                    pass
                raise
                
        except Exception as e:
            if self.verbose:
                print(f"✗ Lỗi khi render chart: {e}")
            return None
    
    def generate_from_json(self, 
                          json_data: Union[Dict, str],
                          template: Optional[Dict] = None):
        """
        Tạo document từ dữ liệu JSON
        
        Args:
            json_data (Union[Dict, str]): Dữ liệu JSON hoặc đường dẫn file JSON
            template (Dict, optional): Template định nghĩa cấu trúc document
        """
        if self.document is None:
            self.create_new_document()
        
        # Đọc JSON nếu là đường dẫn
        if isinstance(json_data, str):
            with open(json_data, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        
        # Nếu có template, sử dụng template
        if template:
            self._apply_template(json_data, template)
        else:
            # Mặc định: tạo document đơn giản từ JSON
            self._generate_default(json_data)
    
    def _apply_template(self, data: Dict, template: Dict):
        """Áp dụng template để tạo document"""
        for section in template.get('sections', []):
            section_type = section.get('type')
            
            if section_type == 'heading':
                self.add_heading(
                    text=section.get('text', '').format(**data),
                    level=section.get('level', 1),
                    alignment=section.get('alignment', 'left')
                )
            
            elif section_type == 'paragraph':
                self.add_paragraph(
                    text=section.get('text', '').format(**data),
                    bold=section.get('bold', False),
                    italic=section.get('italic', False),
                    alignment=section.get('alignment', 'left')
                )
            
            elif section_type == 'table':
                data_key = section.get('data_key')
                if data_key and data_key in data:
                    self.add_table_from_dict(
                        data=data[data_key],
                        headers=section.get('headers')
                    )
            
            elif section_type == 'page_break':
                self.add_page_break()
    
    def _generate_default(self, data: Dict):
        """Tạo document mặc định từ JSON"""
        for key, value in data.items():
            # Thêm key làm heading
            self.add_heading(str(key).replace('_', ' ').title(), level=2)
            
            # Thêm value
            if isinstance(value, list) and value and isinstance(value[0], dict):
                # Nếu là list of dict, tạo bảng
                self.add_table_from_dict(value)
            elif isinstance(value, dict):
                # Nếu là dict, hiển thị từng cặp key-value
                for k, v in value.items():
                    self.add_paragraph(f"{k}: {v}")
            else:
                # Giá trị đơn giản
                self.add_paragraph(str(value))
            
            self.add_paragraph("")  # Thêm dòng trống
    
    def save(self, output_path: str):
        """
        Lưu document
        
        Args:
            output_path (str): Đường dẫn file output
        """
        if self.document is None:
            print("✗ Chưa có document để lưu")
            return
        
        try:
            # Tạo thư mục nếu chưa tồn tại
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Lưu file
            self.document.save(output_path)
            self.output_path = output_path
            
            if self.verbose:
                print(f"✓ Đã lưu file: {output_path}")
        
        except Exception as e:
            print(f"✗ Lỗi khi lưu file: {str(e)}")
            raise
    
    def generate_questions_document(self, 
                                   json_data: Union[Dict, str],
                                   output_path: str):
        """
        Tạo document câu hỏi từ dữ liệu JSON
        
        Args:
            json_data (Union[Dict, str]): Dữ liệu JSON hoặc đường dẫn file JSON
            output_path (str): Đường dẫn file DOCX output
        """
        # Đọc JSON nếu là đường dẫn
        if isinstance(json_data, str):
            with open(json_data, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        
        # Tạo document mới
        self.create_new_document()
        self.set_document_style()
        
        # Thêm tiêu đề
        metadata = json_data.get('metadata', {})
        self.add_heading('ĐỀ THI TRẮC NGHIỆM', level=1, alignment='center')
        
        matrix_file = metadata.get('matrix_file', 'N/A')
        generated_at = metadata.get('generated_at', 'N/A')
        if isinstance(generated_at, str) and len(generated_at) >= 10:
            generated_at = generated_at[:10]
        total_questions = metadata.get('total_questions', 0)
        
        self.add_paragraph(f"Ma trận: {matrix_file}", alignment='center')
        self.add_paragraph(f"Ngày tạo: {generated_at}", alignment='center')
        self.add_paragraph(f"Tổng số câu: {total_questions}", alignment='center')
        self.add_paragraph("")
        
        questions_data = json_data.get('questions', {})
        
        # Lấy subject từ metadata
        subject = metadata.get('subject', '')
        
        # Xuất câu hỏi TN
        tn_questions = questions_data.get('TN', [])
        if tn_questions:
            try:
                tn_questions_sorted = sorted(tn_questions, key=lambda x: int(x.get('question_code', 'C0')[1:]))
            except (ValueError, TypeError, AttributeError) as e:
                tn_questions_sorted = tn_questions
            
            self.add_heading('PHẦN I. Thí sinh trả lời từ câu 1 đến câu 24. Mỗi câu hỏi thí sinh chỉ chọn một phương án.', level=2)
            
            for idx, q in enumerate(tn_questions_sorted, 1):
                self._add_tn_question(q, idx)
            
            self.add_paragraph("")
        
        # Xuất câu hỏi DS
        ds_questions = questions_data.get('DS', [])
        if ds_questions:
            try:
                ds_questions_sorted = sorted(ds_questions, key=lambda x: int(x.get('question_code', 'C0')[1:]))
            except (ValueError, TypeError, AttributeError) as e:
                ds_questions_sorted = ds_questions
            
            self.add_heading('PHẦN II. Thí sinh trả lời từ câu 1 đến 4. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.', level=2)
            
            for idx, q in enumerate(ds_questions_sorted, 1):
                self._add_ds_question(q, idx, subject)
            
            self.add_paragraph("")
        
        # Xuất câu hỏi TLN
        tln_questions = questions_data.get('TLN', [])
        if tln_questions:
            try:
                tln_questions_sorted = sorted(tln_questions, key=lambda x: int(x.get('question_code', 'C0')[1:]))
            except (ValueError, TypeError, AttributeError) as e:
                tln_questions_sorted = tln_questions
            
            self.add_heading('PHẦN III. Câu trả lời ngắn. Thí sinh viết đáp án vào chỗ trống.', level=2)
            
            for idx, q in enumerate(tln_questions_sorted, 1):
                self._add_tln_question(q, idx)
            
            self.add_paragraph("")
        
        # Xuất câu hỏi TL
        tl_questions = questions_data.get('TL', [])
        if tl_questions:
            try:
                tl_questions_sorted = sorted(tl_questions, key=lambda x: int(x.get('question_code', 'C0')[1:]))
            except (ValueError, TypeError, AttributeError) as e:
                tl_questions_sorted = tl_questions
            
            self.add_heading('PHẦN IV. Câu tự luận. Thí sinh trình bày lập luận đầy đủ.', level=2)
            
            for idx, q in enumerate(tl_questions_sorted, 1):
                self._add_tl_question(q, idx)
            
            self.add_paragraph("")
        
        # Thêm phần đáp án
        self.add_page_break()
        self.add_heading('ĐÁP ÁN VÀ GIẢI THÍCH', level=1, alignment='center')
        self.add_paragraph("")
        
        # Đáp án TN
        if tn_questions:
            self.add_heading('PHẦN I: TRẮC NGHIỆM', level=2)
            
            for idx, q in enumerate(tn_questions_sorted, 1):
                self._add_tn_answer(q, idx)
        
        # Đáp án DS
        if ds_questions:
            self.add_heading('PHẦN II: ĐÚNG/SAI', level=2)
            
            for idx, q in enumerate(ds_questions_sorted, 1):
                self._add_ds_answer(q, idx)
        
        # Đáp án TLN
        if tln_questions:
            self.add_heading('PHẦN III: TRẢ LỜI NGẮN', level=2)
            
            for idx, q in enumerate(tln_questions_sorted, 1):
                self._add_tln_answer(q, idx)
        
        # Đáp án TL
        if tl_questions:
            self.add_heading('PHẦN IV: TỰ LUẬN', level=2)
            
            for idx, q in enumerate(tl_questions_sorted, 1):
                self._add_tl_answer(q, idx)
        
        # Lưu file
        self.save(output_path)
    
    def _add_tn_question(self, question: Dict, number: int):
        """Thêm câu hỏi trắc nghiệm"""
        try:
            # Câu hỏi
            para = self.document.add_paragraph()
            
            level = question.get('level', 'NB')
            
            run = para.add_run(f"Câu {number} ")
            run.bold = True
            run = para.add_run(f"({level})")
            run.bold = True
            self._set_run_background(run, level)
            
            para.add_run(". ")
            
            # Handle question_stem - can be string or dict
            question_stem = question.get('question_stem', '')
            if isinstance(question_stem, dict):
                stem_type = question_stem.get('type', 'text')
                
                if stem_type == 'mixed':
                    # Mixed content: text + table + chart - process sequentially
                    content = question_stem.get('content', [])
                    first_text_added_to_para = False
                    for item in content:
                        if isinstance(item, str):
                            # Text content
                            if not first_text_added_to_para:
                                # First text goes to the question paragraph
                                para.add_run(item)
                                first_text_added_to_para = True
                            else:
                                # Subsequent text creates new paragraph
                                para_text = self.document.add_paragraph()
                                para_text.add_run(item)
                        elif isinstance(item, dict):
                            item_type = item.get('type', '')
                            if item_type == 'table':
                                # Add table as separate element
                                self._add_inline_table(item.get('content', {}))
                            elif item_type == 'chart':
                                # Add chart as separate element
                                self._add_inline_chart(item.get('content', {}))
                            elif item_type == 'image':
                                # Add image placeholder
                                caption = item.get('metadata', {}).get('caption', '')
                                para_img = self.document.add_paragraph()
                                if caption:
                                    run = para_img.add_run(f"[Hình ảnh: {caption}]")
                                else:
                                    run = para_img.add_run(f"[Hình ảnh: {item.get('content', '')}]")
                                run.italic = True
                elif stem_type == 'chart':
                    # Chart with before/after text
                    content = question_stem.get('content', [])
                    for item in content:
                        if isinstance(item, str):
                            para.add_run(item)
                        elif isinstance(item, dict):
                            item_type = item.get('type', '')
                            if item_type == 'chart':
                                self._add_inline_chart(item.get('content', {}))
                else:
                    # Simple text
                    question_stem = question_stem.get('content', '')
                    para.add_run(question_stem)
            else:
                para.add_run(question_stem)
            
            # Các lựa chọn
            options = question.get('options', {})
            correct_answer = question.get('correct_answer', '')
            
            # Ensure options is a dict
            if not isinstance(options, dict):
                options = {}
            
            for key in ['A', 'B', 'C', 'D']:
                if key in options:
                    option_text = options[key]
                    if not isinstance(option_text, str):
                        option_text = str(option_text)
                    
                    para = self.document.add_paragraph()
                    
                    # Tô đỏ nếu là đáp án đúng
                    if key == correct_answer:
                        run = para.add_run(f"{key}. {option_text}")
                        run.font.color.rgb = RGBColor(255, 0, 0)
                    else:
                        para.add_run(f"{key}. {option_text}")
        except Exception as e:
            print(f"Error in _add_tn_question {number}: {e}")
            print(f"Question data: {question}")
            raise
    
    def _add_ds_question(self, question: Dict, number: int, subject: str = ''):
        """Thêm câu hỏi đúng/sai"""
        try:
            # Tiêu đề câu
            para = self.document.add_paragraph()
            para.add_run(f"Câu {number}. ").bold = True
            para.add_run("Cho đoạn tư liệu sau:")
            
            # Always display source_text.content for DS questions
            source_text = question.get('source_text', '')
            source_metadata = None
            if isinstance(source_text, dict):
                source_metadata = source_text.get('metadata', {})
                source_text = source_text.get('content', '')
            
            # Handle mixed content or plain text
            if isinstance(source_text, list):
                # Mixed content: process each item separately to preserve order
                for item in source_text:
                    if isinstance(item, str):
                        # Plain text - create new paragraph
                        para = self.document.add_paragraph()
                        run = para.add_run(item)
                        run.italic = True
                    elif isinstance(item, dict):
                        item_type = item.get('type', '')
                        if item_type == 'table':
                            self._add_inline_table(item.get('content', {}))
                        elif item_type == 'image':
                            caption = item.get('metadata', {}).get('caption', '')
                            para = self.document.add_paragraph()
                            if caption:
                                run = para.add_run(f"[Hình ảnh: {caption}]")
                            else:
                                run = para.add_run(f"[Hình ảnh: {item.get('content', '')}]")
                            run.italic = True
                        elif item_type == 'chart':
                            self._add_inline_chart(item.get('content', {}))
                        else:
                            para = self.document.add_paragraph()
                            run = para.add_run(str(item))
                            run.italic = True
            else:
                # Plain text
                self.add_paragraph(source_text, italic=True)
            
            # Only display source citation if subject needs source display
            should_display_source = Config.should_display_source(subject)
            if should_display_source:
                # Thêm nguồn tư liệu (căn lề phải, bọc trong ngoặc đơn)
                # Ưu tiên source_citation, nếu không có thì dùng source từ metadata
                source_citation = question.get('source_citation', '')
                if not source_citation and source_metadata:
                    source_citation = source_metadata.get('source', '')
                
                if source_citation:
                    para_source = self.document.add_paragraph()
                    para_source.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    para_source.add_run(f"({source_citation})").italic = True
            
            statements = question.get('statements', {})
            
            # Ensure statements is a dict
            if not isinstance(statements, dict):
                statements = {}
            
            for label in ['a', 'b', 'c', 'd']:
                if label in statements:
                    stmt = statements[label]
                    level = stmt.get('level', 'NB')
                    text = stmt.get('text', '')
                    if not isinstance(text, str):
                        text = str(text)
                    is_correct = stmt.get('correct_answer', False)
                    
                    para = self.document.add_paragraph()
                    
                    # "(level)" - tô màu nền
                    run_level = para.add_run(f"({level})")
                    self._set_run_background(run_level, level)
                    
                    # " label. text" - tô đỏ nếu đúng
                    run_content = para.add_run(f" {label}) {text}")
                    if is_correct:
                        run_content.font.color.rgb = RGBColor(255, 0, 0)
        except Exception as e:
            print(f"Error in _add_ds_question {number}: {e}")
            print(f"Question data: {question}")
            raise
    
    def _add_tn_answer(self, question: Dict, number: int):
        """Thêm đáp án trắc nghiệm"""
        para = self.document.add_paragraph()
        para.add_run(f"Câu {number}. ").bold = True
        
        # Đáp án đúng tô đỏ
        run = para.add_run(f"Đáp án: {question.get('correct_answer', 'N/A')}")
        run.bold = True
        run.font.color.rgb = RGBColor(255, 0, 0)
        
        # Giải thích
        explanation = question.get('explanation', '')
        if explanation:
            self.add_paragraph(f"{explanation}")
        
        self.add_paragraph("")
    
    def _add_ds_answer(self, question: Dict, number: int):
        """Thêm đáp án đúng/sai"""
        para = self.document.add_paragraph()
        para.add_run(f"Câu {number}. ").bold = True
        
        # Đáp án từng mệnh đề
        statements = question.get('statements', {})
        answer_parts = []
        for label in ['a', 'b', 'c', 'd']:
            if label in statements:
                stmt = statements[label]
                is_correct = stmt.get('correct_answer', False)
                answer_text = "Đ" if is_correct else "S"
                answer_parts.append(f"{label}. {answer_text}")
        
        # Tô đỏ đáp án
        run = para.add_run(", ".join(answer_parts))
        run.font.color.rgb = RGBColor(255, 0, 0)
        
        # Giải thích
        explanations = question.get('explanation', {})
        
        # Ensure explanations is a dict
        if not isinstance(explanations, dict):
            explanations = {}
        
        if explanations:
            self.add_paragraph("Giải thích:")
            for label in ['a', 'b', 'c', 'd']:
                if label in explanations:
                    explanation_text = explanations[label]
                    if not isinstance(explanation_text, str):
                        explanation_text = str(explanation_text)
                    self.add_paragraph(f"{label}. {explanation_text}")
        
        self.add_paragraph("")
    
    def _add_tl_question(self, question: Dict, number: int):
        """Thêm câu hỏi tự luận"""
        try:
            # Câu hỏi
            para = self.document.add_paragraph()
            
            level = question.get('level', 'NB')
            
            run = para.add_run(f"Câu {number} ")
            run.bold = True
            run = para.add_run(f"({level})")
            run.bold = True
            self._set_run_background(run, level)
            
            para.add_run(". ")
            
            # Handle question_stem - can be string or dict
            question_stem = question.get('question_stem', '')
            if isinstance(question_stem, dict):
                stem_type = question_stem.get('type', 'text')
                
                if stem_type == 'mixed':
                    # Mixed content: text + table + chart - process sequentially like DS
                    content = question_stem.get('content', [])
                    first_text_added_to_para = False
                    for item in content:
                        if isinstance(item, str):
                            # Text content
                            if not first_text_added_to_para:
                                # First text goes to the question paragraph
                                para.add_run(item)
                                first_text_added_to_para = True
                            else:
                                # Subsequent text creates new paragraph
                                para_text = self.document.add_paragraph()
                                para_text.add_run(item)
                        elif isinstance(item, dict):
                            item_type = item.get('type', '')
                            if item_type == 'table':
                                # Add table as separate element
                                self._add_inline_table(item.get('content', {}))
                            elif item_type == 'chart':
                                # Add chart as separate element
                                self._add_inline_chart(item.get('content', {}))
                            elif item_type == 'image':
                                # Add image placeholder
                                caption = item.get('metadata', {}).get('caption', '')
                                para_img = self.document.add_paragraph()
                                if caption:
                                    run = para_img.add_run(f"[Hình ảnh: {caption}]")
                                else:
                                    run = para_img.add_run(f"[Hình ảnh: {item.get('content', '')}]")
                                run.italic = True
                elif stem_type == 'chart':
                    # Chart with before/after text
                    content = question_stem.get('content', [])
                    for item in content:
                        if isinstance(item, str):
                            para.add_run(item)
                        elif isinstance(item, dict):
                            item_type = item.get('type', '')
                            if item_type == 'chart':
                                self._add_inline_chart(item.get('content', {}))
                else:
                    # Simple text
                    question_stem = question_stem.get('content', '')
                    para.add_run(question_stem)
            else:
                para.add_run(question_stem)
            
        except Exception as e:
            print(f"Error in _add_tl_question {number}: {e}")
            print(f"Question data: {question}")
            raise
    
    def _add_tl_answer(self, question: Dict, number: int):
        """Thêm đáp án câu hỏi TL"""
        para = self.document.add_paragraph()
        para.add_run(f"Câu {number}. ").bold = True
        
        # Đáp án mẫu
        correct_answer = question.get('correct_answer', '')
        if correct_answer:
            run_label = para.add_run("Đáp án mẫu: ")
            run_label.bold = True
            run_label.font.color.rgb = RGBColor(255, 0, 0)
            self.add_paragraph(correct_answer)
        
        # Hướng dẫn chấm điểm
        explanation = question.get('explanation', '')
        if explanation:
            para_exp = self.document.add_paragraph()
            run_exp = para_exp.add_run("Hướng dẫn chấm điểm: ")
            run_exp.bold = True
            self.add_paragraph(f"{explanation}")
        
        self.add_paragraph("")
    
    def _add_tln_question(self, question: Dict, number: int):
        """Thêm câu hỏi trắc nghiệm luận (trả lời ngắn)"""
        try:
            # Câu hỏi
            para = self.document.add_paragraph()
            
            level = question.get('level', 'NB')
            
            run = para.add_run(f"Câu {number} ")
            run.bold = True
            run = para.add_run(f"({level})")
            run.bold = True
            self._set_run_background(run, level)
            
            para.add_run(". ")
            
            # Handle question_stem - can be string or dict
            question_stem = question.get('question_stem', '')
            if isinstance(question_stem, dict):
                stem_type = question_stem.get('type', 'text')
                
                if stem_type == 'mixed':
                    # Mixed content: text + table + chart - process sequentially like DS
                    content = question_stem.get('content', [])
                    first_text_added_to_para = False
                    for item in content:
                        if isinstance(item, str):
                            # Text content
                            if not first_text_added_to_para:
                                # First text goes to the question paragraph
                                para.add_run(item)
                                first_text_added_to_para = True
                            else:
                                # Subsequent text creates new paragraph
                                para_text = self.document.add_paragraph()
                                para_text.add_run(item)
                        elif isinstance(item, dict):
                            item_type = item.get('type', '')
                            if item_type == 'table':
                                # Add table as separate element
                                self._add_inline_table(item.get('content', {}))
                            elif item_type == 'chart':
                                # Add chart as separate element
                                self._add_inline_chart(item.get('content', {}))
                            elif item_type == 'image':
                                # Add image placeholder
                                caption = item.get('metadata', {}).get('caption', '')
                                para_img = self.document.add_paragraph()
                                if caption:
                                    run = para_img.add_run(f"[Hình ảnh: {caption}]")
                                else:
                                    run = para_img.add_run(f"[Hình ảnh: {item.get('content', '')}]")
                                run.italic = True
                elif stem_type == 'chart':
                    # Chart with before/after text
                    content = question_stem.get('content', [])
                    for item in content:
                        if isinstance(item, str):
                            para.add_run(item)
                        elif isinstance(item, dict):
                            item_type = item.get('type', '')
                            if item_type == 'chart':
                                self._add_inline_chart(item.get('content', {}))
                else:
                    # Simple text
                    question_stem = question_stem.get('content', '')
                    para.add_run(question_stem)
            else:
                para.add_run(question_stem)
            
        except Exception as e:
            print(f"Error in _add_tln_question {number}: {e}")
            print(f"Question data: {question}")
            raise
    
    def _add_tln_answer(self, question: Dict, number: int):
        """Thêm đáp án câu hỏi TLN"""
        para = self.document.add_paragraph()
        para.add_run(f"Câu {number}. ").bold = True
        
        # Đáp án tô đỏ
        run = para.add_run(f"Đáp án: {question.get('correct_answer', 'N/A')}")
        run.bold = True
        run.font.color.rgb = RGBColor(255, 0, 0)
        
        # Giải thích
        explanation = question.get('explanation', '')
        if explanation:
            self.add_paragraph(f"{explanation}")
        
        self.add_paragraph("")
    
    def create_from_json_file(self, 
                             json_path: str,
                             output_path: str,
                             template: Optional[Dict] = None):
        """
        Tạo DOCX từ file JSON
        
        Args:
            json_path (str): Đường dẫn file JSON
            output_path (str): Đường dẫn file DOCX output
            template (Dict, optional): Template
        """
        try:
            # Đọc JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Tạo document
            self.create_new_document()
            self.set_document_style()
            self.generate_from_json(data, template)
            
            # Lưu file
            self.save(output_path)
            
            if self.verbose:
                print(f"✓ Đã tạo DOCX: {json_path} -> {output_path}")
        
        except Exception as e:
            print(f"✗ Lỗi khi tạo DOCX: {str(e)}")
            raise
