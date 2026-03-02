"""
Helper utilities cho xử lý hình ảnh trong câu hỏi
"""
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from PIL import Image
import json


class ImageHelper:
    """Helper class cho các thao tác với hình ảnh"""
    
    @staticmethod
    def save_image(
        image_data: bytes,
        save_path: Union[str, Path],
        format: str = 'PNG'
    ) -> str:
        """
        Lưu image data vào file
        
        Args:
            image_data: Binary image data
            save_path: Đường dẫn lưu file
            format: Format ảnh (PNG, JPEG, etc.)
            
        Returns:
            str: Đường dẫn file đã lưu
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(image_data)
        
        return str(save_path)
    
    @staticmethod
    def load_image(image_path: Union[str, Path]) -> bytes:
        """
        Load image từ file
        
        Args:
            image_path: Đường dẫn file
            
        Returns:
            bytes: Binary image data
        """
        with open(image_path, 'rb') as f:
            return f.read()
    
    @staticmethod
    def encode_image_base64(image_path: Union[str, Path]) -> str:
        """
        Encode image thành base64 string
        
        Args:
            image_path: Đường dẫn file
            
        Returns:
            str: Base64 encoded string
        """
        image_data = ImageHelper.load_image(image_path)
        return base64.b64encode(image_data).decode('utf-8')
    
    @staticmethod
    def decode_image_base64(base64_str: str) -> bytes:
        """
        Decode base64 string thành image data
        
        Args:
            base64_str: Base64 encoded string
            
        Returns:
            bytes: Binary image data
        """
        return base64.b64decode(base64_str)
    
    @staticmethod
    def get_image_info(image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Lấy thông tin về hình ảnh
        
        Args:
            image_path: Đường dẫn file
            
        Returns:
            Dict: Thông tin hình ảnh (width, height, format, size)
        """
        img = Image.open(image_path)
        return {
            'width': img.width,
            'height': img.height,
            'format': img.format,
            'mode': img.mode,
            'size_bytes': os.path.getsize(image_path)
        }
    
    @staticmethod
    def resize_image(
        image_path: Union[str, Path],
        output_path: Union[str, Path],
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect_ratio: bool = True
    ):
        """
        Resize hình ảnh
        
        Args:
            image_path: Đường dẫn file gốc
            output_path: Đường dẫn file output
            width: Chiều rộng mới (optional)
            height: Chiều cao mới (optional)
            keep_aspect_ratio: Giữ tỷ lệ khung hình
        """
        img = Image.open(image_path)
        
        if keep_aspect_ratio:
            if width and not height:
                ratio = width / img.width
                height = int(img.height * ratio)
            elif height and not width:
                ratio = height / img.height
                width = int(img.width * ratio)
        
        if width and height:
            img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
            img_resized.save(output_path)
        else:
            raise ValueError("Must provide at least width or height")


class ImageContentBuilder:
    """Builder cho tạo rich content với hình ảnh"""
    
    @staticmethod
    def build_image_content(
        text_before: str,
        image_path: str,
        text_after: str,
        image_caption: Optional[str] = None,
        image_alt: Optional[str] = None,
        image_width: Optional[int] = None,
        image_height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build rich content structure cho câu hỏi có hình ảnh
        
        Format:
        {
          "type": "image",
          "content": [
            "Text before image",
            {
              "type": "image",
              "content": "path/to/image.png",
              "metadata": {...}
            },
            "Text after image"
          ]
        }
        
        Args:
            text_before: Text trước hình
            image_path: Đường dẫn hình ảnh
            text_after: Text sau hình
            image_caption: Caption cho hình
            image_alt: Alt text cho hình
            image_width: Chiều rộng display
            image_height: Chiều cao display
            
        Returns:
            Dict: Rich content structure
        """
        content = []
        
        # Add text before (nếu có)
        if text_before.strip():
            content.append(text_before.strip())
        
        # Add image object
        image_obj = {
            "type": "image",
            "content": image_path,
            "metadata": {}
        }
        
        if image_caption:
            image_obj["metadata"]["caption"] = image_caption
        if image_alt:
            image_obj["metadata"]["alt"] = image_alt
        if image_width:
            image_obj["metadata"]["width"] = image_width
        if image_height:
            image_obj["metadata"]["height"] = image_height
        
        content.append(image_obj)
        
        # Add text after (nếu có)
        if text_after.strip():
            content.append(text_after.strip())
        
        return {
            "type": "image",
            "content": content
        }
    
    @staticmethod
    def extract_images_from_content(rich_content: Dict[str, Any]) -> List[str]:
        """
        Extract tất cả image paths từ rich content
        
        Args:
            rich_content: Rich content structure
            
        Returns:
            List[str]: Danh sách image paths
        """
        images = []
        
        if rich_content.get('type') == 'image':
            content = rich_content.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        images.append(item.get('content'))
        
        elif rich_content.get('type') == 'mixed':
            content = rich_content.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        # Image object
                        images.append(item.get('content'))
        
        return images
    
    @staticmethod
    def replace_image_paths(
        rich_content: Dict[str, Any],
        path_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Thay thế image paths trong rich content
        
        Useful khi upload images lên server và cần update paths
        
        Args:
            rich_content: Rich content structure
            path_mapping: Mapping từ local path -> server URL
                         {"local/path.png": "https://server.com/image.png"}
            
        Returns:
            Dict: Rich content với paths đã update
        """
        import copy
        result = copy.deepcopy(rich_content)
        
        if result.get('type') == 'image':
            content = result.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        old_path = item.get('content')
                        if old_path in path_mapping:
                            item['content'] = path_mapping[old_path]
        
        elif result.get('type') == 'mixed':
            content = result.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image':
                        old_path = item.get('content')
                        if old_path in path_mapping:
                            item['content'] = path_mapping[old_path]
        
        return result


class ImageMarkerParser:
    """Parser cho các marker hình ảnh trong text"""
    
    @staticmethod
    def replace_markers_with_images(
        text: str,
        images: List[str]
    ) -> List[Any]:
        """
        Thay thế markers [IMAGE_PLACEHOLDER] trong text bằng image objects
        
        Args:
            text: Text chứa markers
            images: Danh sách image paths để thay thế
            
        Returns:
            List: Content array [text, image_obj, text, ...]
        """
        parts = text.split('[IMAGE_PLACEHOLDER]')
        content = []
        
        for i, part in enumerate(parts):
            if part.strip():
                content.append(part.strip())
            
            # Add image nếu còn
            if i < len(images):
                content.append({
                    "type": "image",
                    "content": images[i],
                    "metadata": {}
                })
        
        return content
    
    @staticmethod
    def extract_image_markers(text: str) -> int:
        """
        Đếm số lượng image markers trong text
        
        Args:
            text: Text chứa markers
            
        Returns:
            int: Số lượng markers
        """
        return text.count('[IMAGE_PLACEHOLDER]') + text.count('[IMAGE]')


class ImageMetadataManager:
    """Manager cho metadata của hình ảnh"""
    
    @staticmethod
    def create_metadata(
        question_code: str,
        image_type: str,  # 'HA_MH' hoặc 'HA_TL'
        description: str,
        image_path: str,
        **extra_fields
    ) -> Dict[str, Any]:
        """
        Tạo metadata cho hình ảnh
        
        Args:
            question_code: Mã câu hỏi
            image_type: Loại hình ảnh
            description: Mô tả hình ảnh
            image_path: Đường dẫn file
            **extra_fields: Các fields bổ sung
            
        Returns:
            Dict: Metadata
        """
        from datetime import datetime
        
        metadata = {
            'question_code': question_code,
            'image_type': image_type,
            'description': description,
            'image_path': image_path,
            'created_at': datetime.now().isoformat(),
            **extra_fields
        }
        
        # Add image info
        try:
            img_info = ImageHelper.get_image_info(image_path)
            metadata['image_info'] = img_info
        except Exception as e:
            metadata['image_info'] = {'error': str(e)}
        
        return metadata
    
    @staticmethod
    def save_metadata(metadata: Dict[str, Any], output_path: Union[str, Path]):
        """Lưu metadata vào file JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_metadata(metadata_path: Union[str, Path]) -> Dict[str, Any]:
        """Load metadata từ file JSON"""
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class ImageValidator:
    """Validator cho hình ảnh"""
    
    @staticmethod
    def validate_image_file(image_path: Union[str, Path]) -> tuple[bool, str]:
        """
        Validate image file
        
        Args:
            image_path: Đường dẫn file
            
        Returns:
            (bool, str): (is_valid, error_message)
        """
        image_path = Path(image_path)
        
        # Check exists
        if not image_path.exists():
            return False, f"File not found: {image_path}"
        
        # Check extension
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        if image_path.suffix.lower() not in valid_extensions:
            return False, f"Invalid extension: {image_path.suffix}"
        
        # Check readable
        try:
            img = Image.open(image_path)
            img.verify()
            return True, ""
        except Exception as e:
            return False, f"Cannot open image: {str(e)}"
    
    @staticmethod
    def validate_image_content(
        rich_content: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Validate rich content có chứa hình ảnh hợp lệ
        
        Args:
            rich_content: Rich content structure
            
        Returns:
            (bool, str): (is_valid, error_message)
        """
        if not isinstance(rich_content, dict):
            return False, "Content must be a dict"
        
        content_type = rich_content.get('type')
        if content_type not in ['image', 'mixed']:
            return False, f"Invalid content type for image: {content_type}"
        
        content = rich_content.get('content', [])
        if not isinstance(content, list):
            return False, "Content must be a list"
        
        # Check có ít nhất 1 image object
        has_image = False
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'image':
                has_image = True
                image_path = item.get('content')
                if not image_path:
                    return False, "Image object missing content (path)"
                # Validate path nếu là local file
                if not image_path.startswith('http'):
                    is_valid, error = ImageValidator.validate_image_file(image_path)
                    if not is_valid:
                        return False, error
        
        if not has_image:
            return False, "No image object found in content"
        
        return True, ""
