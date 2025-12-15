"""
Module tạo file DOCX từ dữ liệu JSON
"""
import json
from pathlib import Path
from typing import Dict, List, Union, Optional, Any
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE


class DocxGenerator:
    """Class tạo file DOCX từ dữ liệu JSON"""
    
    def __init__(self):
        self.document = None
        self.output_path = None
    
    def create_new_document(self):
        """Tạo document mới"""
        self.document = Document()
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
            print("⚠ Không có dữ liệu để tạo bảng")
            return
        
        # Lấy headers
        if headers is None and auto_headers:
            headers = list(data[0].keys())
        
        # Tạo bảng
        table = self.document.add_table(rows=1, cols=len(headers))
        table.style = 'Light Grid Accent 1'
        
        # Thêm header
        header_cells = table.rows[0].cells
        for idx, header in enumerate(headers):
            header_cells[idx].text = str(header)
            # Format header
            for paragraph in header_cells[idx].paragraphs:
                for run in paragraph.runs:
                    run.bold = True
        
        # Thêm dữ liệu
        for item in data:
            row_cells = table.add_row().cells
            for idx, header in enumerate(headers):
                value = item.get(header, "")
                row_cells[idx].text = str(value)
        
        print(f"✓ Đã thêm bảng {len(data)} hàng x {len(headers)} cột")
        return table
    
    def add_page_break(self):
        """Thêm ngắt trang"""
        if self.document is None:
            self.create_new_document()
        
        self.document.add_page_break()
    
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
            
            print(f"✓ Đã lưu file: {output_path}")
        
        except Exception as e:
            print(f"✗ Lỗi khi lưu file: {str(e)}")
            raise
    
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
            
            print(f"✓ Đã tạo DOCX từ JSON: {json_path} -> {output_path}")
        
        except Exception as e:
            print(f"✗ Lỗi khi tạo DOCX từ JSON: {str(e)}")
            raise
