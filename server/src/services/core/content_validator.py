"""
Post-processor để validate và clean rich content
- Parse JSON strings thành objects
- Validate structure
- Remove duplicates
"""
import json
import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)


def parse_json_string_content(content: Any) -> Any:
    """
    Recursively parse JSON strings trong content thành objects
    
    Args:
        content: Content có thể là string/object/array
        
    Returns:
        Parsed content
    """
    if isinstance(content, str):
        # Try parse nếu là JSON string
        content_stripped = content.strip()
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            try:
                parsed = json.loads(content)
                logger.debug(f"✅ Parsed JSON string to object: {type(parsed)}")
                return parse_json_string_content(parsed)  # Recursive
            except json.JSONDecodeError:
                # Không phải JSON hợp lệ, giữ nguyên string
                return content
        return content
    
    elif isinstance(content, dict):
        # Recursively parse tất cả values trong dict
        return {k: parse_json_string_content(v) for k, v in content.items()}
    
    elif isinstance(content, list):
        # Recursively parse tất cả items trong list
        return [parse_json_string_content(item) for item in content]
    
    else:
        # Giữ nguyên các types khác (int, float, bool, None)
        return content


def validate_rich_content_structure(rich_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate và fix structure của rich content
    
    Args:
        rich_content: Rich content object với type và content
        
    Returns:
        Validated và cleaned rich content
        
    Raises:
        ValueError: Nếu structure không hợp lệ
    """
    if not isinstance(rich_content, dict):
        raise ValueError(f"Rich content phải là dict, nhận được {type(rich_content)}")
    
    if 'type' not in rich_content:
        raise ValueError("Rich content thiếu field 'type'")
    
    if 'content' not in rich_content:
        raise ValueError("Rich content thiếu field 'content'")
    
    content_type = rich_content['type']
    content = rich_content['content']
    
    # Parse JSON strings
    content = parse_json_string_content(content)
    
    # Validate theo type
    if content_type == 'text':
        if not isinstance(content, str):
            logger.warning(f"⚠️ type='text' nhưng content không phải string: {type(content)}")
            # Try convert to string
            content = str(content) if content is not None else ""
    
    elif content_type == 'table':
        if not isinstance(content, dict):
            raise ValueError(f"type='table' nhưng content không phải object: {type(content)}")
        
        if 'headers' not in content:
            raise ValueError("Table content thiếu 'headers'")
        if 'rows' not in content:
            raise ValueError("Table content thiếu 'rows'")
        
        if not isinstance(content['headers'], list):
            raise ValueError(f"Table headers phải là array: {type(content['headers'])}")
        if not isinstance(content['rows'], list):
            raise ValueError(f"Table rows phải là array: {type(content['rows'])}")
    
    elif content_type == 'chart':
        if not isinstance(content, dict):
            raise ValueError(f"type='chart' nhưng content không phải object: {type(content)}")
        
        if 'chartType' not in content:
            raise ValueError("Chart content thiếu 'chartType'")
        if 'echarts' not in content:
            raise ValueError("Chart content thiếu 'echarts'")
        
        # Parse echarts nếu là JSON string
        if isinstance(content['echarts'], str):
            try:
                content['echarts'] = json.loads(content['echarts'])
                logger.info("✅ Converted echarts JSON string → object")
            except json.JSONDecodeError as e:
                raise ValueError(f"Chart echarts không phải JSON hợp lệ: {e}")
        
        if not isinstance(content['echarts'], dict):
            raise ValueError(f"Chart echarts phải là object: {type(content['echarts'])}")
    
    elif content_type == 'image':
        if not isinstance(content, str):
            logger.warning(f"⚠️ type='image' nhưng content không phải string: {type(content)}")
            content = str(content) if content is not None else ""
    
    elif content_type == 'mixed':
        if not isinstance(content, list):
            raise ValueError(f"type='mixed' nhưng content không phải array: {type(content)}")
        
        # Recursively validate nested rich content objects
        validated_items = []
        for i, item in enumerate(content):
            if isinstance(item, dict) and 'type' in item:
                # Nested rich content
                validated_items.append(validate_rich_content_structure(item))
            elif isinstance(item, str):
                validated_items.append(item)
            else:
                logger.warning(f"⚠️ Mixed content item {i} không phải string hoặc rich object: {type(item)}")
                validated_items.append(item)
        
        content = validated_items
    
    else:
        logger.warning(f"⚠️ Unknown content type: {content_type}")
    
    # Parse metadata nếu có và là string
    metadata = rich_content.get('metadata')
    if metadata:
        metadata = parse_json_string_content(metadata)
    
    return {
        'type': content_type,
        'content': content,
        'metadata': metadata
    }


def remove_duplicate_content(mixed_content: List[Any]) -> List[Any]:
    """
    Remove duplicate items trong mixed content array
    
    Args:
        mixed_content: Array chứa strings và objects
        
    Returns:
        Cleaned array không có duplicates
    """
    seen = []
    result = []
    
    for item in mixed_content:
        # Convert to JSON string để compare
        item_str = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        
        if item_str not in seen:
            seen.append(item_str)
            result.append(item)
        else:
            logger.info(f"🗑️ Removed duplicate item: {item_str[:100]}...")
    
    return result


def clean_question_rich_content(question: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean tất cả rich content fields trong một câu hỏi
    
    Args:
        question: Question object
        
    Returns:
        Cleaned question
    """
    fields_to_clean = []
    
    # Xác định fields cần clean theo question_type
    question_type = question.get('question_type')
    
    if question_type == 'TN':
        # Chỉ question_stem có rich content, options và explanation là string
        fields_to_clean = ['question_stem']
    
    elif question_type == 'TL':
        # Chỉ question_stem có rich content, sample_answer là string
        fields_to_clean = ['question_stem']
    
    elif question_type == 'TLN':
        # Chỉ question_stem có rich content
        fields_to_clean = ['question_stem']
    
    elif question_type == 'DS':
        # source_text có rich content
        fields_to_clean = ['source_text']
    
    # Clean từng field
    for field_path in fields_to_clean:
        try:
            if '.' in field_path:
                # Nested field (e.g., options.A)
                parts = field_path.split('.')
                parent = question
                for part in parts[:-1]:
                    parent = parent[part]
                
                field_key = parts[-1]
                if field_key in parent and isinstance(parent[field_key], dict):
                    parent[field_key] = validate_rich_content_structure(parent[field_key])
                    
                    # Remove duplicates nếu là mixed
                    if parent[field_key].get('type') == 'mixed':
                        parent[field_key]['content'] = remove_duplicate_content(
                            parent[field_key]['content']
                        )
            else:
                # Top-level field
                if field_path in question and isinstance(question[field_path], dict):
                    question[field_path] = validate_rich_content_structure(question[field_path])
                    
                    # Remove duplicates nếu là mixed
                    if question[field_path].get('type') == 'mixed':
                        question[field_path]['content'] = remove_duplicate_content(
                            question[field_path]['content']
                        )
        
        except Exception as e:
            logger.error(f"❌ Error cleaning field '{field_path}': {e}")
            # Không raise, tiếp tục clean các fields khác
    
    return question


def clean_all_questions(questions_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean tất cả câu hỏi trong output JSON
    
    Args:
        questions_data: Full questions JSON với metadata và questions
        
    Returns:
        Cleaned questions data
    """
    if 'questions' not in questions_data:
        return questions_data
    
    questions = questions_data['questions']
    
    # Clean từng loại câu hỏi
    for question_type in ['TN', 'TL', 'TLN', 'DS']:
        if question_type in questions and isinstance(questions[question_type], list):
            cleaned = []
            for i, question in enumerate(questions[question_type]):
                try:
                    cleaned_q = clean_question_rich_content(question)
                    cleaned.append(cleaned_q)
                    logger.debug(f"✅ Cleaned {question_type} question {i+1}")
                except Exception as e:
                    logger.error(f"❌ Error cleaning {question_type} question {i+1}: {e}")
                    # Giữ nguyên câu hỏi lỗi
                    cleaned.append(question)
            
            questions[question_type] = cleaned
    
    return questions_data
