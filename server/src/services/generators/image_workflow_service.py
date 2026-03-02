"""
Module xử lý workflow sinh câu hỏi với hình ảnh
Hỗ trợ 2 loại workflow:
1. HA_MH (Hình ảnh minh họa) - Parallel workflow
2. HA_TL (Hình ảnh tư liệu) - Sequential workflow
"""
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .image_description_service import ImageDescriptionService, ImageDescriptionResult
from ..core.image_generation import ImageGenerator


@dataclass
class ImageGenerationResult:
    """Kết quả sinh hình ảnh"""
    description: str  # Mô tả hình ảnh
    image_path: str  # Đường dẫn lưu hình ảnh local
    image_data: bytes  # Binary data của hình ảnh
    metadata: Dict[str, Any]  # Thông tin bổ sung


@dataclass
class QuestionWithImageResult:
    """Kết quả sinh câu hỏi có kèm hình ảnh"""
    question: Dict[str, Any]  # Câu hỏi đã được sinh
    image: ImageGenerationResult  # Hình ảnh đã được sinh
    merged: bool  # Đã merge hình vào câu hỏi chưa
    workflow_type: str  # 'HA_MH' hoặc 'HA_TL'


class ImageWorkflowService:
    """
    Service orchestrate workflow sinh câu hỏi với hình ảnh
    """
    
    def __init__(
        self,
        ai_client,
        image_save_dir: Optional[Path] = None,
        prompts_dir: Optional[Path] = None
    ):
        """
        Khởi tạo ImageWorkflowService
        
        Args:
            ai_client: GenAI client
            image_save_dir: Thư mục lưu hình ảnh (default: server/data/images)
            prompts_dir: Thư mục chứa prompt templates
        """
        self.ai_client = ai_client
        
        # Image save directory
        if image_save_dir:
            self.image_save_dir = image_save_dir
        else:
            # Default: E:\App\matrixquesgen\server\data\images
            default_dir = Path(os.getenv('APP_DIR', 'e:\\App\\matrixquesgen')) / "server" / "data" / "images"
            self.image_save_dir = default_dir
        
        # Ensure directory exists
        self.image_save_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-services
        self.description_service = ImageDescriptionService(
            ai_client=ai_client,
            prompts_dir=prompts_dir
        )
        self.image_generator = ImageGenerator(
            num_images=1,
            aspect_ratio="16:9"
        )
    
    def process_ha_mh_workflow(
        self,
        question_spec: Dict[str, Any],
        content: str,
        reference_image_path: Optional[str] = None
    ) -> QuestionWithImageResult:
        """
        Xử lý workflow HA_MH (Hình ảnh minh họa) - PARALLEL
        
        Flow:
        1. Sinh mô tả hình ảnh minh họa
        2. Chạy 2 tasks song song:
           a. Sinh hình ảnh từ mô tả
           b. Sinh câu hỏi (độc lập với hình)
        3. Merge hình ảnh vào câu hỏi
        
        Args:
            question_spec: Thông tin câu hỏi từ matrix (QuestionSpec)
            content: Nội dung SGK
            reference_image_path: Đường dẫn ảnh mẫu (optional)
            
        Returns:
            QuestionWithImageResult: Kết quả câu hỏi + hình ảnh
        """
        print(f"\n📸 Processing HA_MH workflow for question: {question_spec.get('question_code', 'Unknown')}")
        
        try:
            # B1: Sinh mô tả hình ảnh minh họa
            print("  ➡️ Step 1: Generate image description...")
            desc_result = self.description_service.generate_illustrative_description(
                subject=question_spec.get('subject', ''),
                class_level=question_spec.get('class', ''),
                chapter=question_spec.get('chapter', ''),
                lesson_name=question_spec.get('lesson_name', ''),
                content=content,
                learning_outcome=question_spec.get('learning_outcome', ''),
                reference_image_path=reference_image_path
            )
            
            print(f"  ✓ Description generated: {desc_result.description[:100]}...")
            
            # B2: Chạy 2 tasks song song
            print("  ➡️ Step 2: Parallel execution (image generation + question generation)...")
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Task A: Sinh hình ảnh
                image_future = executor.submit(
                    self._generate_and_save_image,
                    description=desc_result.description,
                    question_code=question_spec.get('question_code', 'unknown'),
                    image_type='HA_MH',
                    reference_image_path=reference_image_path
                )
                
                # Task B: Sinh câu hỏi (độc lập)
                # Note: Câu hỏi sẽ có placeholder cho mô tả hình ảnh
                question_future = executor.submit(
                    self._generate_question_with_image_placeholder,
                    question_spec=question_spec,
                    content=content,
                    image_description=desc_result.description
                )
                
                # Wait for both to complete
                image_result = image_future.result()
                question_result = question_future.result()
            
            print(f"  ✓ Image saved to: {image_result.image_path}")
            print(f"  ✓ Question generated")
            
            # B3: Merge hình ảnh vào câu hỏi
            print("  ➡️ Step 3: Merge image into question...")
            merged_question = self._merge_image_into_question(
                question=question_result,
                image=image_result,
                image_description=desc_result.description
            )
            
            print("  ✓ HA_MH workflow completed!")
            
            return QuestionWithImageResult(
                question=merged_question,
                image=image_result,
                merged=True,
                workflow_type='HA_MH'
            )
            
        except Exception as e:
            print(f"  ❌ Error in HA_MH workflow: {e}")
            raise
    
    def process_ha_tl_workflow(
        self,
        question_spec: Dict[str, Any],
        content: str,
        reference_image_path: Optional[str] = None
    ) -> QuestionWithImageResult:
        """
        Xử lý workflow HA_TL (Hình ảnh tư liệu) - SEQUENTIAL
        
        Flow:
        1. Sinh mô tả hình ảnh chi tiết (có thể gửi kèm ảnh mẫu)
        2. Sinh hình ảnh từ mô tả (có thể gửi kèm ảnh mẫu)
        3. Sinh câu hỏi + đáp án DỰA TRÊN hình ảnh
        4. Merge hình ảnh vào câu hỏi
        
        Args:
            question_spec: Thông tin câu hỏi từ matrix
            content: Nội dung SGK
            reference_image_path: Đường dẫn ảnh mẫu (recommended!)
            
        Returns:
            QuestionWithImageResult: Kết quả câu hỏi + hình ảnh
        """
        print(f"\n📊 Processing HA_TL workflow for question: {question_spec.get('question_code', 'Unknown')}")
        
        try:
            # B1: Sinh mô tả hình ảnh CHI TIẾT
            print("  ➡️ Step 1: Generate detailed image description...")
            desc_result = self.description_service.generate_data_source_description(
                subject=question_spec.get('subject', ''),
                class_level=question_spec.get('class', ''),
                chapter=question_spec.get('chapter', ''),
                lesson_name=question_spec.get('lesson_name', ''),
                content=content,
                learning_outcome=question_spec.get('learning_outcome', ''),
                reference_image_path=reference_image_path
            )
            
            print(f"  ✓ Detailed description generated: {desc_result.description[:100]}...")
            
            # B2: Sinh hình ảnh từ mô tả (có thể kèm reference)
            print("  ➡️ Step 2: Generate image from description...")
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                question_code=question_spec.get('question_code', 'unknown'),
                image_type='HA_TL',
                reference_image_path=reference_image_path
            )
            
            print(f"  ✓ Image saved to: {image_result.image_path}")
            
            # B3: Sinh câu hỏi DỰA TRÊN hình ảnh
            print("  ➡️ Step 3: Generate question based on image...")
            question_result = self._generate_question_based_on_image(
                question_spec=question_spec,
                content=content,
                image_description=desc_result.description,
                image_path=image_result.image_path
            )
            
            print("  ✓ Question generated based on image")
            
            # B4: Merge hình ảnh vào câu hỏi
            print("  ➡️ Step 4: Merge image into question...")
            merged_question = self._merge_image_into_question(
                question=question_result,
                image=image_result,
                image_description=desc_result.description
            )
            
            print("  ✓ HA_TL workflow completed!")
            
            return QuestionWithImageResult(
                question=merged_question,
                image=image_result,
                merged=True,
                workflow_type='HA_TL'
            )
            
        except Exception as e:
            print(f"  ❌ Error in HA_TL workflow: {e}")
            raise
    
    def _generate_and_save_image(
        self,
        description: str,
        question_code: str,
        image_type: str,
        reference_image_path: Optional[str] = None
    ) -> ImageGenerationResult:
        """
        Sinh hình ảnh và lưu vào local
        
        Args:
            description: Mô tả hình ảnh
            question_code: Mã câu hỏi (để tạo tên file)
            image_type: 'HA_MH' hoặc 'HA_TL'
            reference_image_path: Đường dẫn ảnh mẫu (optional)
            
        Returns:
            ImageGenerationResult: Kết quả sinh hình
        """
        try:
            # Generate image using ImageGenerator
            images_data = self.image_generator.generate(
                prompt=description,
                num_images=1,
                reference_image_path=reference_image_path
            )
            
            if not images_data:
                raise ValueError("No image generated")
            
            image_data = images_data[0]
            
            # Create filename: {question_code}_{image_type}_{timestamp}.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{question_code}_{image_type}_{timestamp}.png"
            image_path = self.image_save_dir / filename
            
            # Save image to local
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            return ImageGenerationResult(
                description=description,
                image_path=str(image_path),
                image_data=image_data,
                metadata={
                    'question_code': question_code,
                    'image_type': image_type,
                    'timestamp': timestamp,
                    'has_reference': reference_image_path is not None
                }
            )
            
        except Exception as e:
            print(f"❌ Error generating and saving image: {e}")
            raise
    
    def _generate_question_with_image_placeholder(
        self,
        question_spec: Dict[str, Any],
        content: str,
        image_description: str
    ) -> Dict[str, Any]:
        """
        Sinh câu hỏi với placeholder cho mô tả hình ảnh (HA_MH)
        Câu hỏi KHÔNG phụ thuộc vào hình, nhưng có chỗ để chèn mô tả hình
        
        Args:
            question_spec: Spec câu hỏi
            content: Nội dung SGK
            image_description: Mô tả hình ảnh
            
        Returns:
            Dict: Câu hỏi với image placeholder
        """
        # Gọi AI để sinh câu hỏi
        # Prompt sẽ bao gồm image_description và yêu cầu AI đặt placeholder
        prompt = self._build_ha_mh_question_prompt(
            question_spec=question_spec,
            content=content,
            image_description=image_description
        )
        
        response = self.ai_client.generate_content(
            prompt=prompt
        )
        
        # Parse response thành question object
        question = self._parse_question_response(response)
        
        return question
    
    def _generate_question_based_on_image(
        self,
        question_spec: Dict[str, Any],
        content: str,
        image_description: str,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Sinh câu hỏi DỰA TRÊN hình ảnh (HA_TL)
        Gửi kèm mô tả và hình ảnh cho AI
        
        Args:
            question_spec: Spec câu hỏi
            content: Nội dung SGK
            image_description: Mô tả hình ảnh
            image_path: Đường dẫn hình ảnh đã sinh
            
        Returns:
            Dict: Câu hỏi dựa trên hình
        """
        # Build prompt cho HA_TL
        prompt = self._build_ha_tl_question_prompt(
            question_spec=question_spec,
            content=content,
            image_description=image_description
        )
        
        # Load image
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Gọi AI với cả text + image
        response = self.ai_client.generate_content_with_image(
            prompt=prompt,
            image_data=image_data
        )
        
        # Parse response
        question = self._parse_question_response(response)
        
        return question
    
    def _merge_image_into_question(
        self,
        question: Dict[str, Any],
        image: ImageGenerationResult,
        image_description: str
    ) -> Dict[str, Any]:
        """
        Merge hình ảnh vào câu hỏi tại vị trí mô tả
        
        Tìm vị trí mô tả hình ảnh trong question_stem và thay thế bằng
        image object theo format rich content.
        
        Args:
            question: Câu hỏi đã sinh
            image: Hình ảnh đã sinh
            image_description: Mô tả hình ảnh
            
        Returns:
            Dict: Câu hỏi đã merge hình ảnh
        """
        # Nếu question_stem là string, convert sang rich content format
        question_stem = question.get('question_stem', '')
        
        if isinstance(question_stem, str):
            # Replace image description với image object
            # Format: type='image', content=[text, {image_object}, text]
            merged_stem = {
                "type": "image",
                "content": self._inject_image_into_text(
                    text=question_stem,
                    image_path=image.image_path,
                    image_description=image_description
                )
            }
        else:
            # Already rich content, find and replace
            merged_stem = self._inject_image_into_rich_content(
                rich_content=question_stem,
                image_path=image.image_path,
                image_description=image_description
            )
        
        # Update question
        question['question_stem'] = merged_stem
        
        # Add metadata
        if 'metadata' not in question:
            question['metadata'] = {}
        question['metadata']['has_image'] = True
        question['metadata']['image_path'] = image.image_path
        question['metadata']['image_type'] = image.metadata.get('image_type')
        
        return question
    
    def _inject_image_into_text(
        self,
        text: str,
        image_path: str,
        image_description: str
    ) -> List[Any]:
        """
        Inject image object vào text tại vị trí mô tả
        
        Returns:
            List: [text_part1, {image_object}, text_part2]
        """
        # Tìm vị trí mô tả (hoặc marker như [IMAGE_PLACEHOLDER])
        # Nếu có marker, thay thế
        if "[IMAGE_PLACEHOLDER]" in text:
            parts = text.split("[IMAGE_PLACEHOLDER]")
        elif "[IMAGE]" in text:
            parts = text.split("[IMAGE]")
        else:
            # Không tìm thấy marker, đặt hình ở đầu
            parts = ["", text]
        
        # Build image object
        image_obj = {
            "type": "image",
            "content": image_path,  # Local path (sẽ upload lên server)
            "metadata": {
                "alt": image_description[:100],  # Short alt text
                "caption": image_description
            }
        }
        
        # Build content array
        content = []
        if parts[0].strip():
            content.append(parts[0].strip())
        content.append(image_obj)
        if len(parts) > 1 and parts[1].strip():
            content.append(parts[1].strip())
        
        return content
    
    def _inject_image_into_rich_content(
        self,
        rich_content: Dict[str, Any],
        image_path: str,
        image_description: str
    ) -> Dict[str, Any]:
        """Inject image vào rich content structure"""
        # TODO: Implement rich content injection logic
        # For now, return as is
        return rich_content
    
    def _build_ha_mh_question_prompt(
        self,
        question_spec: Dict[str, Any],
        content: str,
        image_description: str
    ) -> str:
        """Build prompt cho sinh câu hỏi HA_MH"""
        prompt = f"""
# Sinh câu hỏi với hình ảnh minh họa (HA_MH)

## Lưu ý:
- Hình ảnh chỉ để MINH HỌA, KHÔNG phải nguồn dữ liệu bắt buộc
- Câu hỏi phải có thể trả lời KHÔNG CẦN nhìn hình
- Đặt marker [IMAGE_PLACEHOLDER] tại vị trí muốn chèn hình

## Mô tả hình ảnh sẽ minh họa:
{image_description}

## Nội dung kiến thức:
{content}

## Yêu cầu câu hỏi:
- Cấp độ: {question_spec.get('level', 'TH')}
- Loại: {question_spec.get('question_type', 'TN')}
- Kết quả học: {question_spec.get('learning_outcome', '')}

## Hãy sinh câu hỏi theo format JSON schema.
"""
        return prompt
    
    def _build_ha_tl_question_prompt(
        self,
        question_spec: Dict[str, Any],
        content: str,
        image_description: str
    ) -> str:
        """Build prompt cho sinh câu hỏi HA_TL"""
        prompt = f"""
# Sinh câu hỏi DỰA TRÊN hình ảnh tư liệu (HA_TL)

## Lưu ý:
- Hình ảnh là NGUỒN DỮ LIỆU CHÍNH
- Người học BẮT BUỘC phải đọc hình để trả lời
- Câu hỏi phải yêu cầu phân tích, đọc dữ liệu từ hình
- Đặt marker [IMAGE_PLACEHOLDER] tại vị trí cần chèn hình

## Mô tả chi tiết hình ảnh:
{image_description}

## Bối cảnh kiến thức:
{content}

## Yêu cầu câu hỏi:
- Cấp độ: {question_spec.get('level', 'VD')}
- Loại: {question_spec.get('question_type', 'TN')}
- Kết quả học: {question_spec.get('learning_outcome', '')}

## Hãy sinh câu hỏi DỰA VÀO hình ảnh theo format JSON schema.
"""
        return prompt
    
    def _parse_question_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response thành question object
        
        Args:
            response: JSON string từ AI
            
        Returns:
            Dict: Question object
        """
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            raise ValueError("Cannot parse question from response")
