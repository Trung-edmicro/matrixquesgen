"""
AI Response Parser for Rich Content
Parses AI-generated responses and converts them to rich content format
"""

import re
import json
from typing import Dict, List, Any, Union, Optional
from services.core.rich_content import (
    ContentBlock, ContentType, TableContent, ChartContent, ChartType,
    text, image, table, chart, latex, mixed
)


class RichContentParser:
    """Parse AI responses and convert to rich content blocks"""
    
    @staticmethod
    def parse_text_with_markers(text_str: str) -> ContentBlock:
        """
        Parse text containing markers for images, tables, charts, and latex
        
        Markers format:
        [IMAGE:url alt="..." width=500]
        [TABLE:headers|row1|row2]
        [CHART:type {...echarts_config...}]
        [LATEX:formula display=block]
        """
        if not text_str:
            return text(text_str)
        
        # Check if text contains markers
        if not any(marker in text_str for marker in ['[IMAGE:', '[TABLE:', '[CHART:', '[LATEX:']):
            return text(text_str)
        
        blocks = []
        current_pos = 0
        
        # Pattern to find all markers
        pattern = r'\[(IMAGE|TABLE|CHART|LATEX):([^\]]+)\]'
        
        for match in re.finditer(pattern, text_str):
            # Add text before marker
            if match.start() > current_pos:
                before_text = text_str[current_pos:match.start()].strip()
                if before_text:
                    blocks.append(text(before_text))
            
            marker_type = match.group(1)
            marker_content = match.group(2)
            
            # Parse marker based on type
            if marker_type == 'IMAGE':
                blocks.append(RichContentParser._parse_image_marker(marker_content))
            elif marker_type == 'TABLE':
                blocks.append(RichContentParser._parse_table_marker(marker_content))
            elif marker_type == 'CHART':
                blocks.append(RichContentParser._parse_chart_marker(marker_content))
            elif marker_type == 'LATEX':
                blocks.append(RichContentParser._parse_latex_marker(marker_content))
            
            current_pos = match.end()
        
        # Add remaining text
        if current_pos < len(text_str):
            after_text = text_str[current_pos:].strip()
            if after_text:
                blocks.append(text(after_text))
        
        # Return single block or mixed block
        if len(blocks) == 0:
            return text("")
        elif len(blocks) == 1:
            return blocks[0]
        else:
            return mixed(*blocks)
    
    @staticmethod
    def _parse_image_marker(content: str) -> ContentBlock:
        """Parse [IMAGE:url alt="..." width=500]"""
        parts = content.split()
        url = parts[0] if parts else ""
        
        # Parse attributes
        alt = None
        width = None
        height = None
        caption = None
        
        attr_pattern = r'(\w+)=(?:"([^"]+)"|(\d+))'
        for match in re.finditer(attr_pattern, content):
            key = match.group(1)
            value = match.group(2) or match.group(3)
            
            if key == 'alt':
                alt = value
            elif key == 'width':
                width = int(value)
            elif key == 'height':
                height = int(value)
            elif key == 'caption':
                caption = value
        
        return image(url, alt=alt, width=width, height=height, caption=caption)
    
    @staticmethod
    def _parse_table_marker(content: str) -> ContentBlock:
        """Parse [TABLE:headers|row1|row2]"""
        rows_data = content.split('|')
        if not rows_data:
            return text("[Invalid table]")
        
        # First row is headers
        headers = [h.strip() for h in rows_data[0].split(',')]
        
        # Remaining rows are data
        rows = []
        for row_str in rows_data[1:]:
            row = [cell.strip() for cell in row_str.split(',')]
            rows.append(row)
        
        return table(headers, rows)
    
    @staticmethod
    def _parse_chart_marker(content: str) -> ContentBlock:
        """Parse [CHART:type {...echarts_config...}]"""
        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            return text("[Invalid chart]")
        
        chart_type_str = parts[0]
        config_str = parts[1]
        
        try:
            # Parse chart type
            chart_type = ChartType(chart_type_str.lower())
            
            # Parse echarts config (JSON)
            echarts_config = json.loads(config_str)
            
            return chart(chart_type, echarts_config)
        except Exception as e:
            return text(f"[Invalid chart: {e}]")
    
    @staticmethod
    def _parse_latex_marker(content: str) -> ContentBlock:
        """Parse [LATEX:formula display=block]"""
        # Check for display mode
        display_mode = "inline"
        if "display=block" in content:
            display_mode = "block"
            content = content.replace("display=block", "").strip()
        elif "display=inline" in content:
            content = content.replace("display=inline", "").strip()
        
        return latex(content, display=display_mode)
    
    @staticmethod
    def detect_and_convert_simple_tables(text_str: str) -> Union[str, ContentBlock]:
        """
        Detect simple markdown-style tables in text and convert to table blocks
        
        Example:
        | Header 1 | Header 2 |
        |----------|----------|
        | Cell 1   | Cell 2   |
        """
        # Pattern for markdown tables
        table_pattern = r'\|(.+)\|\n\|[-:\s|]+\|\n(\|.+\|\n)+'
        
        match = re.search(table_pattern, text_str)
        if not match:
            return text_str
        
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        
        # Parse headers
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        
        # Parse rows (skip separator line)
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            rows.append(cells)
        
        # Create table block
        table_block = table(headers, rows)
        
        # Replace table in text with marker
        before = text_str[:match.start()]
        after = text_str[match.end():]
        
        # If there's text before or after, return mixed content
        blocks = []
        if before.strip():
            blocks.append(text(before.strip()))
        blocks.append(table_block)
        if after.strip():
            blocks.append(text(after.strip()))
        
        if len(blocks) == 1:
            return blocks[0]
        else:
            return mixed(*blocks)
    
    @staticmethod
    def auto_detect_content_type(text_content: str) -> Union[str, ContentBlock]:
        """
        Automatically detect content type and convert to appropriate block
        
        Checks for:
        - Markers ([IMAGE:], [TABLE:], etc.)
        - Markdown tables
        - LaTeX formulas ($ ... $)
        - Plain text
        """
        if not text_content or not isinstance(text_content, str):
            return text_content
        
        # Check for explicit markers
        if any(marker in text_content for marker in ['[IMAGE:', '[TABLE:', '[CHART:', '[LATEX:']):
            return RichContentParser.parse_text_with_markers(text_content)
        
        # Check for markdown tables
        if '|' in text_content and '\n' in text_content:
            result = RichContentParser.detect_and_convert_simple_tables(text_content)
            if isinstance(result, ContentBlock):
                return result
        
        # Check for LaTeX formulas
        if '$' in text_content:
            return RichContentParser._convert_inline_latex(text_content)
        
        # Default: return as text
        return text_content
    
    @staticmethod
    def _convert_inline_latex(text_content: str) -> Union[str, ContentBlock]:
        """Convert inline LaTeX formulas ($...$) to latex blocks"""
        # Pattern for inline latex: $formula$
        pattern = r'\$([^\$]+)\$'
        
        matches = list(re.finditer(pattern, text_content))
        if not matches:
            return text_content
        
        blocks = []
        current_pos = 0
        
        for match in matches:
            # Add text before formula
            if match.start() > current_pos:
                before = text_content[current_pos:match.start()]
                if before:
                    blocks.append(text(before))
            
            # Add latex formula
            formula = match.group(1)
            blocks.append(latex(formula, display="inline"))
            
            current_pos = match.end()
        
        # Add remaining text
        if current_pos < len(text_content):
            after = text_content[current_pos:]
            if after:
                blocks.append(text(after))
        
        if len(blocks) == 1:
            return blocks[0]
        else:
            return mixed(*blocks)


# Helper function for easy use
def parse_ai_response(response: Union[str, Dict]) -> Union[str, Dict, ContentBlock]:
    """
    Parse AI response and convert to rich content format
    
    Args:
        response: String or dict from AI
        
    Returns:
        Parsed content (can be string, dict, or ContentBlock)
    """
    if isinstance(response, str):
        return RichContentParser.auto_detect_content_type(response)
    elif isinstance(response, dict):
        # Parse each field recursively
        result = {}
        for key, value in response.items():
            if isinstance(value, str):
                result[key] = parse_ai_response(value)
            elif isinstance(value, dict):
                result[key] = parse_ai_response(value)
            else:
                result[key] = value
        return result
    else:
        return response
