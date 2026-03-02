"""
Extension cho QuestionGenerator để hỗ trợ sinh câu hỏi với hình ảnh
Tích hợp ImageWorkflowService vào flow sinh câu hỏi
"""
from typing import Dict, Any, Optional, List
from pathlib import Path

from .image_workflow_service import ImageWorkflowService, QuestionWithImageResult
from .question_generator import QuestionGenerator, GeneratedQuestion
from ..core.matrix_parser import QuestionSpec, TrueFalseQuestionSpec


class QuestionGeneratorWithImage:
    """
    Extension của QuestionGenerator với khả năng xử lý hình ảnh
    Hỗ trợ HA_MH (minh họa) và HA_TL (tư liệu)
    """
    
    def __init__(
        self,
        question_generator: QuestionGenerator,
        image_workflow_service: ImageWorkflowService
    ):
        """
        Khởi tạo
        
        Args:
            question_generator: QuestionGenerator instance
            image_workflow_service: ImageWorkflowService instance
        """
        self.question_generator = question_generator
        self.image_workflow = image_workflow_service
    
    def generate_questions_with_image(
        self,
        spec: QuestionSpec,
        content: str,
        reference_image_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Sinh câu hỏi với hình ảnh
        
        Tự động detect loại hình ảnh (HA_MH hoặc HA_TL) từ rich_content_types
        và gọi workflow phù hợp
        
        Args:
            spec: QuestionSpec
            content: Nội dung SGK
            reference_image_path: Đường dẫn ảnh mẫu (optional)
            
        Returns:
            List[Dict]: Danh sách câu hỏi có kèm hình ảnh
        """
        # Detect image type từ rich_content_types
        image_type = self._detect_image_type(spec)
        
        if not image_type:
            # Không có yêu cầu hình ảnh, generate bình thường
            return self.question_generator.generate_questions_for_spec(
                spec=spec,
                content=content
            )
        
        print(f"\n🖼️ Detected image type: {image_type}")
        
        results = []
        
        # Lặp qua từng câu hỏi trong spec
        for question_code in spec.question_codes:
            # Check nếu câu này cần hình ảnh
            needs_image = self._check_question_needs_image(spec, question_code)
            
            if not needs_image:
                # Câu này không cần hình, skip
                continue
            
            print(f"\n⏳ Generating question with image: {question_code}")
            
            # Build question spec for single question
            single_spec = self._build_single_question_spec(spec, question_code)
            
            # Process workflow based on image type
            if image_type == 'HA_MH':
                result = self.image_workflow.process_ha_mh_workflow(
                    question_spec=single_spec,
                    content=content,
                    reference_image_path=reference_image_path
                )
            elif image_type == 'HA_TL':
                result = self.image_workflow.process_ha_tl_workflow(
                    question_spec=single_spec,
                    content=content,
                    reference_image_path=reference_image_path
                )
            else:
                raise ValueError(f"Unknown image type: {image_type}")
            
            results.append(result.question)
        
        return results
    
    def _detect_image_type(self, spec: QuestionSpec) -> Optional[str]:
        """
        Detect loại hình ảnh từ rich_content_types
        
        Args:
            spec: QuestionSpec
            
        Returns:
            'HA_MH', 'HA_TL', hoặc None
        """
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return None
        
        # Tìm type codes
        for code, types_list in spec.rich_content_types.items():
            if isinstance(types_list, list):
                for type_obj in types_list:
                    type_code = None
                    if isinstance(type_obj, dict):
                        type_code = type_obj.get('code', '')
                    elif isinstance(type_obj, str):
                        type_code = type_obj
                    
                    if type_code:
                        if type_code == 'HA_MH':
                            return 'HA_MH'
                        elif type_code == 'HA_TL':
                            return 'HA_TL'
                        elif type_code == 'HA':  # Generic HA
                            # Default to HA_MH if not specified
                            return 'HA_MH'
        
        return None
    
    def _check_question_needs_image(
        self,
        spec: QuestionSpec,
        question_code: str
    ) -> bool:
        """
        Check nếu một câu hỏi cụ thể cần hình ảnh
        
        Args:
            spec: QuestionSpec
            question_code: Mã câu hỏi (VD: 'C1')
            
        Returns:
            bool
        """
        if not hasattr(spec, 'rich_content_types') or not spec.rich_content_types:
            return False
        
        # Check nếu question_code có HA/HA_MH/HA_TL
        if question_code not in spec.rich_content_types:
            return False
        
        types_list = spec.rich_content_types[question_code]
        for type_obj in types_list:
            type_code = None
            if isinstance(type_obj, dict):
                type_code = type_obj.get('code', '')
            elif isinstance(type_obj, str):
                type_code = type_obj
            
            if type_code and ('HA' in type_code):
                return True
        
        return False
    
    def _build_single_question_spec(
        self,
        spec: QuestionSpec,
        question_code: str
    ) -> Dict[str, Any]:
        """
        Build spec dict cho một câu hỏi đơn
        
        Args:
            spec: QuestionSpec gốc
            question_code: Mã câu hỏi
            
        Returns:
            Dict: Spec cho câu hỏi đơn
        """
        return {
            'question_code': question_code,
            'subject': spec.subject,
            'class': spec.class_level,
            'chapter': spec.chapter_number,
            'lesson_name': spec.lesson_name,
            'learning_outcome': spec.learning_outcome,
            'level': spec.cognitive_level,
            'question_type': spec.question_type
        }


def integrate_image_workflow(
    ai_client,
    question_generator: QuestionGenerator,
    prompts_dir: Optional[Path] = None,
    image_save_dir: Optional[Path] = None
) -> QuestionGeneratorWithImage:
    """
    Helper function để tích hợp ImageWorkflow vào QuestionGenerator
    
    Usage:
        ```python
        from services.generators.question_generator_with_image import integrate_image_workflow
        
        # Khởi tạo AI client và QuestionGenerator như bình thường
        ai_client = GenAIClient(...)
        question_generator = QuestionGenerator(ai_client, ...)
        
        # Tích hợp image workflow
        generator_with_image = integrate_image_workflow(
            ai_client=ai_client,
            question_generator=question_generator
        )
        
        # Sinh câu hỏi có hình ảnh
        questions = generator_with_image.generate_questions_with_image(
            spec=question_spec,
            content=content,
            reference_image_path="path/to/reference.png"  # optional
        )
        ```
    
    Args:
        ai_client: GenAI client
        question_generator: QuestionGenerator instance
        prompts_dir: Thư mục prompts (optional)
        image_save_dir: Thư mục lưu hình (optional)
        
    Returns:
        QuestionGeneratorWithImage: Generator có hỗ trợ hình ảnh
    """
    # Tạo ImageWorkflowService
    image_workflow = ImageWorkflowService(
        ai_client=ai_client,
        image_save_dir=image_save_dir,
        prompts_dir=prompts_dir
    )
    
    # Tạo QuestionGeneratorWithImage
    return QuestionGeneratorWithImage(
        question_generator=question_generator,
        image_workflow=image_workflow
    )


# ==================== EXAMPLE USAGE ====================

def example_usage():
    """
    Ví dụ cách sử dụng QuestionGeneratorWithImage
    """
    from services.core.genai_client import GenAIClient
    from services.generators.question_generator import QuestionGenerator
    from services.core.matrix_parser import MatrixParser, QuestionSpec
    
    # 1. Khởi tạo các components
    ai_client = GenAIClient(
        project_id="your-project",
        credentials_path="path/to/credentials.json"
    )
    
    question_generator = QuestionGenerator(
        ai_client=ai_client,
        prompt_template_path="prompts/TN.txt"
    )
    
    # 2. Tích hợp image workflow
    generator_with_image = integrate_image_workflow(
        ai_client=ai_client,
        question_generator=question_generator
    )
    
    # 3. Tạo QuestionSpec với HA_MH hoặc HA_TL
    spec = QuestionSpec(
        question_codes=['C1', 'C2'],
        question_type='TN',
        num_questions=2,
        cognitive_level='TH',
        learning_outcome='Học sinh hiểu được quá trình quang hợp',
        lesson_name='Quang hợp',
        subject='Sinh học',
        class_level='10',
        chapter_number='2',
        rich_content_types={
            'C1': [{'code': 'HA_MH', 'name': 'Hình ảnh minh họa'}],
            'C2': [{'code': 'HA_TL', 'name': 'Hình ảnh tư liệu'}]
        }
    )
    
    # 4. Sinh câu hỏi với hình ảnh
    content = """
    Quang hợp là quá trình sinh vật sản xuất chất hữu cơ từ CO2 và H2O
    nhờ năng lượng ánh sáng. Quá trình này diễn ra ở lục lạp...
    """
    
    questions = generator_with_image.generate_questions_with_image(
        spec=spec,
        content=content,
        reference_image_path="examples/quang_hop.png"  # optional
    )
    
    # 5. Kết quả
    for q in questions:
        print(f"Question: {q['question_code']}")
        print(f"Image: {q['metadata']['image_path']}")
        print(f"Type: {q['metadata']['image_type']}")


if __name__ == "__main__":
    example_usage()
