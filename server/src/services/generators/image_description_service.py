"""
Module sinh mô tả hình ảnh cho câu hỏi
Hỗ trợ 2 loại:
- HA_MH: Hình ảnh minh họa (không bắt buộc để trả lời câu hỏi)
- HA_TL: Hình ảnh tư liệu (nguồn dữ liệu trực tiếp, bắt buộc để trả lời)
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ImageDescriptionResult:
    """Kết quả sinh mô tả hình ảnh"""
    description: str  # Mô tả hình ảnh
    image_type: str  # 'HA_MH' hoặc 'HA_TL'
    metadata: Dict[str, Any]  # Thông tin bổ sung


class ImageDescriptionService:
    """
    Service sinh mô tả hình ảnh sử dụng Gemini AI
    """
    
    def __init__(self, ai_client, prompts_dir: Optional[Path] = None):
        """
        Khởi tạo ImageDescriptionService
        
        Args:
            ai_client: GenAI client (VertexAI hoặc GenAI)
            prompts_dir: Thư mục chứa prompt templates
        """
        self.ai_client = ai_client
        
        # Set prompts directory
        if prompts_dir:
            self.prompts_dir = prompts_dir
        else:
            # Default to server/src/services/prompts
            self.prompts_dir = Path(__file__).parent.parent / "prompts" / "image_description"
        
        # Load prompt templates
        self.illustrative_prompt = self._load_prompt_template("illustrative_image.txt")
        self.data_source_prompt = self._load_prompt_template("data_source_image.txt")
    
    def _load_prompt_template(self, filename: str) -> str:
        """Load prompt template từ file"""
        try:
            prompt_path = self.prompts_dir / filename
            if not prompt_path.exists():
                print(f"⚠️ Prompt template not found: {prompt_path}")
                print(f"   Using default prompt for {filename}")
                return self._get_default_prompt(filename)
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error loading prompt template {filename}: {e}")
            return self._get_default_prompt(filename)
    
    def _get_default_prompt(self, filename: str) -> str:
        """Get default prompt template when file not found"""
        if filename == "illustrative_image.txt":
            return """Bạn là chuyên gia về {{SUBJECT}} lớp {{CLASS}}.

Hãy tạo mô tả chi tiết cho một hình ảnh MINH HỌA về nội dung sau:

**Chương:** {{CHAPTER}}
**Bài học:** {{LESSON_NAME}}
**Nội dung:** {{CONTENT}}
**Kết quả học được mong đợi:** {{EXPECTED_LEARNING_OUTCOME}}

Yêu cầu mô tả hình ảnh:
- Hình ảnh chỉ mang tính minh họa, giúp học sinh hình dung khái niệm
- Mô tả ngắn gọn, rõ ràng, dễ hình dung
- Phù hợp với trình độ học sinh lớp {{CLASS}}
- Không cần số liệu chi tiết, chỉ cần hình ảnh tổng quan

Trả về MÔ TẢ HÌNH ẢNH (không tạo câu hỏi):"""
        
        elif filename == "data_source_image.txt":
            return """Bạn là chuyên gia về {{SUBJECT}} lớp {{CLASS}}.

Hãy tạo mô tả CHI TIẾT cho một hình ảnh TƯ LIỆU về nội dung sau:

**Chương:** {{CHAPTER}}
**Bài học:** {{LESSON_NAME}}
**Nội dung:** {{CONTENT}}
**Kết quả học được mong đợi:** {{EXPECTED_LEARNING_OUTCOME}}

Yêu cầu mô tả hình ảnh TƯ LIỆU:
- Hình ảnh là NGUỒN DỮ LIỆU TRỰC TIẾP để trả lời câu hỏi
- Mô tả phải CỰC KỲ CHI TIẾT với:
  * Tất cả số liệu chính xác
  * Tên các thành phần đầy đủ
  * Đơn vị đo lường rõ ràng
  * Nhãn, ký hiệu cụ thể
- Học sinh sẽ dựa vào hình ảnh này để trả lời câu hỏi
- Phù hợp với trình độ học sinh lớp {{CLASS}}

Trả về MÔ TẢ HÌNH ẢNH CHI TIẾT (không tạo câu hỏi):"""
        
        else:
            return """Please describe an educational image for:

Subject: {{SUBJECT}}
Class: {{CLASS}}
Chapter: {{CHAPTER}}
Lesson: {{LESSON_NAME}}
Content: {{CONTENT}}
Learning Outcome: {{EXPECTED_LEARNING_OUTCOME}}

Provide a detailed visual description suitable for generating an educational image."""
    
    def generate_illustrative_description(
        self,
        subject: str,
        class_level: str,
        chapter: str,
        lesson_name: str,
        content: str,
        learning_outcome: str,
        reference_image_path: Optional[str] = None
    ) -> ImageDescriptionResult:
        """
        Sinh mô tả hình ảnh minh họa (HA_MH)
        
        Hình ảnh KHÔNG phải là nguồn dữ liệu bắt buộc để trả lời câu hỏi.
        Chỉ đóng vai trò minh họa cho nội dung kiến thức.
        
        Args:
            subject: Môn học
            class_level: Lớp
            chapter: Chương
            lesson_name: Tên bài học
            content: Nội dung cụ thể trong SGK
            learning_outcome: Kết quả học được mong đợi
            reference_image_path: Đường dẫn đến ảnh mẫu (optional)
            
        Returns:
            ImageDescriptionResult: Kết quả mô tả hình ảnh
        """
        try:
            # Build prompt từ template
            prompt = self.illustrative_prompt.replace("{{SUBJECT}}", subject)
            prompt = prompt.replace("{{CLASS}}", class_level)
            prompt = prompt.replace("{{CHAPTER}}", chapter)
            prompt = prompt.replace("{{LESSON_NAME}}", lesson_name)
            prompt = prompt.replace("{{CONTENT}}", content)
            prompt = prompt.replace("{{EXPECTED_LEARNING_OUTCOME}}", learning_outcome)
            
            # Validate prompt không rỗng
            if not prompt or prompt.strip() == "":
                raise ValueError("Prompt template is empty. Cannot generate image description.")
            
            print(f"📝 prompt illustrative (length: {len(prompt)})")
            # Gọi AI để sinh mô tả (có thể kèm reference image)
            if reference_image_path and os.path.exists(reference_image_path):
                # Gửi kèm ảnh mẫu để AI sinh mô tả chuẩn hơn
                description = self._generate_with_reference_image(
                    prompt=prompt,
                    reference_image_path=reference_image_path
                )
            else:
                # Chỉ gửi text prompt
                description = self._generate_text_only(prompt)
            
            return ImageDescriptionResult(
                description=description.strip(),
                image_type="HA_MH",
                metadata={
                    "subject": subject,
                    "class": class_level,
                    "chapter": chapter,
                    "lesson_name": lesson_name,
                    "has_reference": reference_image_path is not None
                }
            )
            
        except Exception as e:
            print(f"❌ Error generating illustrative description: {e}")
            raise
    
    def generate_data_source_description(
        self,
        subject: str,
        class_level: str,
        chapter: str,
        lesson_name: str,
        content: str,
        learning_outcome: str,
        reference_image_path: Optional[str] = None
    ) -> ImageDescriptionResult:
        """
        Sinh mô tả hình ảnh tư liệu (HA_TL)
        
        Hình ảnh là NGUỒN DỮ LIỆU TRỰC TIẾP, bắt buộc để trả lời câu hỏi.
        Mô tả phải chi tiết, chính xác với số liệu, nhãn, đơn vị đầy đủ.
        
        Args:
            subject: Môn học
            class_level: Lớp
            chapter: Chương
            lesson_name: Tên bài học
            content: Nội dung cụ thể trong SGK
            learning_outcome: Kết quả học được mong đợi
            reference_image_path: Đường dẫn đến ảnh mẫu (optional, nên có)
            
        Returns:
            ImageDescriptionResult: Kết quả mô tả hình ảnh chi tiết
        """
        try:
            # Build prompt từ template
            prompt = self.data_source_prompt.replace("{{SUBJECT}}", subject)
            prompt = prompt.replace("{{CLASS}}", class_level)
            prompt = prompt.replace("{{CHAPTER}}", chapter)
            prompt = prompt.replace("{{LESSON_NAME}}", lesson_name)
            prompt = prompt.replace("{{CONTENT}}", content)
            prompt = prompt.replace("{{EXPECTED_LEARNING_OUTCOME}}", learning_outcome)
            
            # Validate prompt không rỗng
            if not prompt or prompt.strip() == "":
                raise ValueError("Prompt template is empty. Cannot generate image description.")
            
            print(f"📝 prompt data source (length: {len(prompt)})")
            
            # Gọi AI để sinh mô tả CHI TIẾT
            if reference_image_path and os.path.exists(reference_image_path):
                # Gửi kèm ảnh mẫu để AI sinh mô tả chuẩn xác hơn
                description = self._generate_with_reference_image(
                    prompt=prompt,
                    reference_image_path=reference_image_path
                )
            else:
                # Chỉ gửi text prompt (không khuyến khích cho HA_TL)
                print("⚠️ HA_TL không có reference image - mô tả có thể không chính xác")
                description = self._generate_text_only(prompt)
            
            return ImageDescriptionResult(
                description=description.strip(),
                image_type="HA_TL",
                metadata={
                    "subject": subject,
                    "class": class_level,
                    "chapter": chapter,
                    "lesson_name": lesson_name,
                    "has_reference": reference_image_path is not None
                }
            )
            
        except Exception as e:
            print(f"❌ Error generating data source description: {e}")
            raise
    
    def _generate_text_only(self, prompt: str) -> str:
        """Generate mô tả chỉ từ text prompt"""
        try:
            # GenAIClient.generate_content() chỉ nhận prompt, không có temperature/max_tokens
            response = self.ai_client.generate_content(prompt=prompt)
            return response.strip()
        except Exception as e:
            print(f"❌ Error in text-only generation: {e}")
            raise
    
    def _generate_with_reference_image(
        self,
        prompt: str,
        reference_image_path: str
    ) -> str:
        """
        Generate mô tả với ảnh mẫu làm reference
        Note: GenAIClient hiện tại không hỗ trợ multimodal, fallback về text-only
        """
        try:
            # GenAIClient chưa hỗ trợ generate_content_with_image
            # Fallback to text-only generation
            print("ℹ️ Reference image provided but GenAIClient doesn't support multimodal yet")
            print("   Using text-only generation as fallback")
            return self._generate_text_only(prompt)
        except Exception as e:
            print(f"❌ Error in generation with reference image: {e}")
            # Fallback to text-only
            print("⚠️ Falling back to text-only generation")
            return self._generate_text_only(prompt)
    
    def batch_generate_descriptions(
        self,
        requests: List[Dict[str, Any]],
        image_type: str  # 'HA_MH' hoặc 'HA_TL'
    ) -> List[ImageDescriptionResult]:
        """
        Sinh mô tả hàng loạt cho nhiều câu hỏi
        
        Args:
            requests: Danh sách các request, mỗi request là dict với keys:
                - subject, class_level, chapter, lesson_name, content, learning_outcome
                - reference_image_path (optional)
            image_type: Loại hình ảnh ('HA_MH' hoặc 'HA_TL')
            
        Returns:
            List[ImageDescriptionResult]: Danh sách kết quả
        """
        results = []
        
        for i, req in enumerate(requests):
            print(f"  📝 Generating description {i+1}/{len(requests)}...")
            
            try:
                if image_type == "HA_MH":
                    result = self.generate_illustrative_description(**req)
                elif image_type == "HA_TL":
                    result = self.generate_data_source_description(**req)
                else:
                    raise ValueError(f"Invalid image_type: {image_type}")
                
                results.append(result)
                
            except Exception as e:
                print(f"  ❌ Failed to generate description {i+1}: {e}")
                # Append error result
                results.append(ImageDescriptionResult(
                    description=f"[ERROR: {str(e)}]",
                    image_type=image_type,
                    metadata={"error": str(e)}
                ))
        
        return results
