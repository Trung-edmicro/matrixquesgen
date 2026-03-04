"""
Rich Content Data Classes for Question Generation
Supports text, images, tables, charts, LaTeX, and mixed content
"""

from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
from enum import Enum


class ContentType(Enum):
    """Types of content blocks"""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"
    LATEX = "latex"
    MIXED = "mixed"


class ChartType(Enum):
    """Types of ECharts"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    RADAR = "radar"


@dataclass
class ContentMetadata:
    """Metadata for content blocks"""
    # Image metadata
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[str] = None
    source: Optional[str] = None  # Source citation for tables
    
    # Table metadata
    bordered: bool = True
    striped: bool = True
    
    # Chart metadata
    display: str = "block"  # "inline" or "block" for LaTeX
    
    # Generic metadata
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableContent:
    """Table structure"""
    headers: List[str]
    rows: List[List[str]]


@dataclass
class ChartContent:
    """Chart structure with ECharts config"""
    chartType: ChartType
    echarts: Dict[str, Any]  # Full ECharts configuration


@dataclass
class ContentBlock:
    """Single content block"""
    type: ContentType
    content: Union[str, TableContent, ChartContent, List['ContentBlock']]
    metadata: Optional[ContentMetadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "type": self.type.value if isinstance(self.type, ContentType) else self.type
        }
        
        # Handle content based on type
        if self.type == ContentType.TEXT or self.type == ContentType.IMAGE or self.type == ContentType.LATEX:
            result["content"] = self.content
        elif self.type == ContentType.TABLE:
            if isinstance(self.content, TableContent):
                result["content"] = {
                    "headers": self.content.headers,
                    "rows": self.content.rows
                }
            else:
                result["content"] = self.content
        elif self.type == ContentType.CHART:
            if isinstance(self.content, ChartContent):
                result["content"] = {
                    "chartType": self.content.chartType.value if isinstance(self.content.chartType, ChartType) else self.content.chartType,
                    "echarts": self.content.echarts
                }
            else:
                result["content"] = self.content
        elif self.type == ContentType.MIXED:
            if isinstance(self.content, list):
                result["content"] = [
                    block.to_dict() if isinstance(block, ContentBlock) else block
                    for block in self.content
                ]
            else:
                result["content"] = self.content
        
        # Add metadata if present
        if self.metadata:
            metadata_dict = {}
            if self.metadata.alt:
                metadata_dict["alt"] = self.metadata.alt
            if self.metadata.width:
                metadata_dict["width"] = self.metadata.width
            if self.metadata.height:
                metadata_dict["height"] = self.metadata.height
            if self.metadata.caption:
                metadata_dict["caption"] = self.metadata.caption
            if self.metadata.source:
                metadata_dict["source"] = self.metadata.source
            if not self.metadata.bordered:
                metadata_dict["bordered"] = self.metadata.bordered
            if not self.metadata.striped:
                metadata_dict["striped"] = self.metadata.striped
            if self.metadata.display != "block":
                metadata_dict["display"] = self.metadata.display
            if self.metadata.custom:
                metadata_dict.update(self.metadata.custom)
            
            if metadata_dict:
                result["metadata"] = metadata_dict
        
        return result
    
    @staticmethod
    def from_dict(data: Union[str, Dict[str, Any]]) -> 'ContentBlock':
        """Create ContentBlock from dictionary (for parsing JSON)"""
        # Simple text (backward compatibility)
        if isinstance(data, str):
            return ContentBlock(type=ContentType.TEXT, content=data)
        
        # Rich content
        content_type = ContentType(data.get("type", "text"))
        content = data.get("content")
        metadata_dict = data.get("metadata")
        
        # Parse metadata
        metadata = None
        if metadata_dict:
            metadata = ContentMetadata(
                alt=metadata_dict.get("alt"),
                width=metadata_dict.get("width"),
                height=metadata_dict.get("height"),
                caption=metadata_dict.get("caption"),
                bordered=metadata_dict.get("bordered", True),
                striped=metadata_dict.get("striped", True),
                display=metadata_dict.get("display", "block"),
                custom={k: v for k, v in metadata_dict.items() if k not in ["alt", "width", "height", "caption", "bordered", "striped", "display"]}
            )
        
        # Parse content based on type
        if content_type == ContentType.TABLE and isinstance(content, dict):
            content = TableContent(
                headers=content.get("headers", []),
                rows=content.get("rows", [])
            )
        elif content_type == ContentType.CHART and isinstance(content, dict):
            content = ChartContent(
                chartType=ChartType(content.get("chartType", "line")),
                echarts=content.get("echarts", {})
            )
        elif content_type == ContentType.MIXED and isinstance(content, list):
            content = [ContentBlock.from_dict(block) for block in content]
        
        return ContentBlock(type=content_type, content=content, metadata=metadata)


@dataclass
class RichQuestion:
    """Question with rich content support"""
    question_code: str
    question_type: str
    lesson_name: str
    chapter_number: str
    lesson_number: str
    level: str
    
    # Rich content fields (can be simple text or ContentBlock)
    question_stem: Union[str, ContentBlock]
    options: Optional[Dict[str, Union[str, ContentBlock]]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[Union[str, ContentBlock, Dict[str, Union[str, ContentBlock]]]] = None
    
    # For DS questions
    source_text: Optional[Union[str, ContentBlock]] = None
    statements: Optional[Dict[str, Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "question_code": self.question_code,
            "question_type": self.question_type,
            "lesson_name": self.lesson_name,
            "chapter_number": self.chapter_number,
            "lesson_number": self.lesson_number,
            "level": self.level
        }
        
        # Convert question_stem
        if isinstance(self.question_stem, ContentBlock):
            result["question_stem"] = self.question_stem.to_dict()
        else:
            result["question_stem"] = self.question_stem
        
        # Convert options
        if self.options:
            result["options"] = {}
            for key, value in self.options.items():
                if isinstance(value, ContentBlock):
                    result["options"][key] = value.to_dict()
                else:
                    result["options"][key] = value
        
        # Convert correct_answer
        if self.correct_answer:
            result["correct_answer"] = self.correct_answer
        
        # Convert explanation
        if self.explanation:
            if isinstance(self.explanation, ContentBlock):
                result["explanation"] = self.explanation.to_dict()
            elif isinstance(self.explanation, dict):
                result["explanation"] = {}
                for key, value in self.explanation.items():
                    if isinstance(value, ContentBlock):
                        result["explanation"][key] = value.to_dict()
                    else:
                        result["explanation"][key] = value
            else:
                result["explanation"] = self.explanation
        
        # Convert source_text (for DS)
        if self.source_text:
            if isinstance(self.source_text, ContentBlock):
                result["source_text"] = self.source_text.to_dict()
            else:
                result["source_text"] = self.source_text
        
        # Convert statements (for DS)
        if self.statements:
            result["statements"] = self.statements
        
        return result


# Helper functions to create content blocks easily

def text(content: str) -> ContentBlock:
    """Create a text block"""
    return ContentBlock(type=ContentType.TEXT, content=content)


def image(url: str, alt: str = None, width: int = None, height: int = None, caption: str = None) -> ContentBlock:
    """Create an image block"""
    metadata = ContentMetadata(alt=alt, width=width, height=height, caption=caption)
    return ContentBlock(type=ContentType.IMAGE, content=url, metadata=metadata)


def table(headers: List[str], rows: List[List[str]], caption: str = None, bordered: bool = True, striped: bool = True) -> ContentBlock:
    """Create a table block"""
    metadata = ContentMetadata(caption=caption, bordered=bordered, striped=striped)
    content = TableContent(headers=headers, rows=rows)
    return ContentBlock(type=ContentType.TABLE, content=content, metadata=metadata)


def chart(chart_type: ChartType, echarts_config: Dict[str, Any], caption: str = None, width: str = "100%", height: int = 400) -> ContentBlock:
    """Create a chart block"""
    metadata = ContentMetadata(caption=caption, custom={"width": width, "height": height})
    content = ChartContent(chartType=chart_type, echarts=echarts_config)
    return ContentBlock(type=ContentType.CHART, content=content, metadata=metadata)


def latex(formula: str, display: str = "inline") -> ContentBlock:
    """Create a LaTeX block"""
    metadata = ContentMetadata(display=display)
    return ContentBlock(type=ContentType.LATEX, content=formula, metadata=metadata)


def mixed(*blocks: ContentBlock) -> ContentBlock:
    """Create a mixed content block"""
    return ContentBlock(type=ContentType.MIXED, content=list(blocks))
