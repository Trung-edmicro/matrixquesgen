# 🔧 Image Workflow Methods - CODE FIX

## ⚠️ Vấn Đề

File `phase4_question_generation.py` có lỗi syntax do escape quotes sai (`\"` instead of `"`).

## ✅ Giải Pháp

Replace các methods từ line ~1658 đến line ~2090 với code dưới đây:

---

## 📝 Code Đúng - Copy và Paste

```python
    def _process_ha_mh_workflow(self, spec, content: str, questions: List) -> List:
        """
        Process HA_MH workflow: PARALLEL (Ảnh minh họa)

        Flow:
        B1. Sinh mô tả hình ảnh minh họa (illustrative_image.txt)
        B2. Song song:
            - Sinh ảnh từ mô tả → lưu local
            - Câu hỏi đã sinh rồi (passed in)
        B3. Merge ảnh vào câu hỏi

        Args:
            spec: QuestionSpec
            content: Nội dung SGK
            questions: Câu hỏi đã sinh (từ QuestionGenerator)

        Returns:
            List of questions với ảnh đã merge
        """
        if not self.image_workflow_service:
            print("  ⚠️ ImageWorkflowService not initialized, skipping image generation")
            return questions

        try:
            # B1: Sinh mô tả hình ảnh minh họa
            print("    Step 1: Generate illustrative image description...")
            desc_result = self.image_workflow_service.description_service.generate_illustrative_description(
                subject=spec.lesson_name.split('.')[0] if hasattr(spec, 'lesson_name') else '',
                class_level=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                chapter=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=spec.learning_outcome if hasattr(spec, 'learning_outcome') else ''
            )

            print(f"    ✓ Description: {desc_result.description[:80]}...")

            # B2: Sinh ảnh (câu hỏi đã có)
            print("    Step 2: Generate image (parallel logic - question already done)...")
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_MH'
            )

            print(f"    ✓ Image saved: {image_result['image_path']}")

            # B3: Merge ảnh vào câu hỏi
            print("    Step 3: Merge image into questions...")
            merged_questions = self._merge_images_into_questions(
                questions=questions,
                images=[image_result],
                image_description=desc_result.description
            )

            print("    ✓ HA_MH workflow completed!")
            return merged_questions

        except Exception as e:
            print(f"    ❌ Error in HA_MH workflow: {e}")
            print(f"    Continuing with original questions...")
            return questions

    def _process_ha_tl_workflow(self, spec, prompt_path: Path, content: str, question_template: str) -> List:
        """
        Process HA_TL workflow: SEQUENTIAL (Ảnh tư liệu)

        Flow:
        B1. Sinh mô tả hình ảnh chi tiết (data_source_image.txt)
        B2. Sinh ảnh từ mô tả → lưu local
        B3. Sinh câu hỏi GỬI KÈM ảnh (QuestionGenerator với ảnh)
        B4. Merge ảnh vào câu hỏi

        Args:
            spec: QuestionSpec
            prompt_path: Path to prompt template
            content: Nội dung SGK
            question_template: Question template string

        Returns:
            List of questions với ảnh đã merge
        """
        if not self.image_workflow_service:
            print("  ⚠️ ImageWorkflowService not initialized, using default generation")
            return self.question_generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )

        try:
            # B1: Sinh mô tả hình ảnh CHI TIẾT
            print("    Step 1: Generate detailed data source description...")
            desc_result = self.image_workflow_service.description_service.generate_data_source_description(
                subject=spec.lesson_name.split('.')[0] if hasattr(spec, 'lesson_name') else '',
                class_level=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                chapter=str(spec.chapter_number) if hasattr(spec, 'chapter_number') else '',
                lesson_name=spec.lesson_name if has attr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=spec.learning_outcome if hasattr(spec, 'learning_outcome') else ''
            )

            print(f"    ✓ Description: {desc_result.description[:80]}...")

            # B2: Sinh ảnh từ mô tả
            print("    Step 2: Generate image from description...")
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_TL'
            )

            print(f"    ✓ Image saved: {image_result['image_path']}")

            # B3: Sinh câu hỏi GỬI KÈM ảnh
            print("    Step 3: Generate questions WITH image...")
            questions = self.question_generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template,
                image_path=image_result['image_path'],
                image_description=desc_result.description
            )

            # B4: Merge ảnh vào câu hỏi (nếu chưa merge)
            print("    Step 4: Ensure image is merged...")
            merged_questions = self._merge_images_into_questions(
                questions=questions,
                images=[image_result],
                image_description=desc_result.description
            )

            print("    ✓ HA_TL workflow completed!")
            return merged_questions

        except Exception as e:
            print(f"    ❌ Error in HA_TL workflow: {e}")
            print(f"    Falling back to default generation...")
            return self.question_generator.generate_questions_for_spec(
                spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )

    def _process_ha_mh_workflow_ds(self, spec, content: str, question) -> Any:
        """Process HA_MH workflow for DS questions"""
        if not self.image_workflow_service:
            return question

        try:
            desc_result = self.image_workflow_service.description_service.generate_illustrative_description(
                subject='',
                class_level='',
                chapter='',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=''
            )

            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_MH'
            )

            merged = self._merge_image_into_single_question(
                question=question,
                image=image_result,
                image_description=desc_result.description
            )

            return merged
        except Exception as e:
            print(f"    ❌ Error in DS HA_MH workflow: {e}")
            return question

    def _process_ha_tl_workflow_ds(self, spec, prompt_path: Path, content: str, question_template: str) -> Any:
        """Process HA_TL workflow for DS questions"""
        if not self.image_workflow_service:
            return self.question_generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )

        try:
            # B1: Sinh mô tả
            desc_result = self.image_workflow_service.description_service.generate_data_source_description(
                subject='',
                class_level='',
                chapter='',
                lesson_name=spec.lesson_name if hasattr(spec, 'lesson_name') else '',
                content=content,
                learning_outcome=''
            )

            # B2: Sinh ảnh
            image_result = self._generate_and_save_image(
                description=desc_result.description,
                image_type='HA_TL'
            )

            # B3: Sinh câu hỏi với ảnh
            question = self.question_generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template,
                image_path=image_result['image_path'],
                image_description=desc_result.description
            )

            # B4: Merge
            merged = self._merge_image_into_single_question(
                question=question,
                image=image_result,
                image_description=desc_result.description
            )

            return merged
        except Exception as e:
            print(f"    ❌ Error in DS HA_TL workflow: {e}")
            return self.question_generator.generate_true_false_question(
                tf_spec=spec,
                prompt_template_path=str(prompt_path),
                content=content,
                question_template=question_template
            )

    def _generate_and_save_image(self, description: str, image_type: str) -> Dict[str, Any]:
        """
        Generate image và lưu vào local

        Args:
            description: Mô tả hình ảnh
            image_type: 'HA_MH' hoặc 'HA_TL'

        Returns:
            Dict với keys: image_path, image_data, description
        """
        from ..core.image_generation import ImageGenerator

        # Initialize ImageGenerator
        image_gen = ImageGenerator(num_images=1, aspect_ratio="16:9")

        # Generate image
        print(f"      Generating {image_type} image...")
        image_bytes_list = image_gen.generate(
            prompt=description,
            num_images=1,
            aspect_ratio="16:9"
        )

        if not image_bytes_list or len(image_bytes_list) == 0:
            raise Exception("Image generation returned empty")

        # Save to E:\App\matrixquesgen\server\data\images
        image_id = str(uuid.uuid4())[:8]

        if os.getenv('APP_DIR'):
            images_dir = Path(os.getenv('APP_DIR')) / "server" / "data" / "images"
        else:
            images_dir = Path(__file__).parent.parent.parent.parent.parent / "server" / "data" / "images"

        images_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{image_type.lower()}_{image_id}.png"

        # Write image bytes
        with open(image_path, 'wb') as f:
            f.write(image_bytes_list[0])

        return {
            'image_path': str(image_path),
            'image_data': image_bytes_list[0],
            'description': description,
            'image_type': image_type
        }

    def _merge_images_into_questions(self, questions: List, images: List[Dict], image_description: str) -> List:
        """
        Merge images vào questions tại vị trí [IMAGE_PLACEHOLDER]

        Args:
            questions: List of generated questions
            images: List of image results
            image_description: Description của hình ảnh

        Returns:
            List of questions với ảnh đã merge
        """
        if not images:
            return questions

        image_result = images[0]  # Use first image

        for question in questions:
            # Merge into question_stem hoặc source_text
            if hasattr(question, 'question'):
                question.question = self._replace_placeholder_in_content(
                    content_obj=question.question,
                    image_path=image_result['image_path'],
                    image_description=image_description
                )

            if hasattr(question, 'source_text') and question.source_text:
                question.source_text = self._replace_placeholder_in_content(
                    content_obj=question.source_text,
                    image_path=image_result['image_path'],
                    image_description=image_description
                )

        return questions

    def _merge_image_into_single_question(self, question, image: Dict, image_description: str):
        """Merge image into a single question (for DS)"""
        if hasattr(question, 'source_text') and question.source_text:
            question.source_text = self._replace_placeholder_in_content(
                content_obj=question.source_text,
                image_path=image['image_path'],
                image_description=image_description
            )
        return question

    def _replace_placeholder_in_content(self, content_obj: Any, image_path: str, image_description: str) -> Any:
        """
        Replace [IMAGE_PLACEHOLDER] in content object with actual image

        Args:
            content_obj: Content object (dict or string)
            image_path: Path to generated image
            image_description: Description of the image

        Returns:
            Updated content object
        """
        if not isinstance(content_obj, dict):
            return content_obj

        content_data = content_obj.get('content')

        # Only process if content is array
        if not isinstance(content_data, list):
            return content_obj

        # Replace [IMAGE_PLACEHOLDER] with image object
        new_content = []
        for item in content_data:
            if item == '[IMAGE_PLACEHOLDER]':
                # Replace with actual image object
                new_content.append({
                    "type": "image",
                    "content": image_path,
                    "metadata": {
                        "caption": content_obj.get('metadata', {}).get('caption', 'Generated image'),
                        "description": image_description,
                        "generated": True
                    }
                })
            else:
                new_content.append(item)

        # Update content
        content_obj['content'] = new_content
        return content_obj
```

---

## 🔍 Cách Sửa

1. Mở `phase4_question_generation.py`
2. Tìm method `_process_ha_mh_workflow` (line ~1658)
3. Delete tất cả code từ đó đến trước `def _deduplicate_questions` (line ~2090)
4. Paste code ở trên vào chỗ đó
5. Save file
6. Check errors

---

## ⚠️ Lưu Ý

- Code này thay thế các methods:
  - `_process_ha_mh_workflow()`
  - `_process_ha_tl_workflow()`
  - `_process_ha_mh_workflow_ds()`
  - `_process_ha_tl_workflow_ds()`
  - `_generate_and_save_image()`
  - `_merge_images_into_questions()`
  - `_merge_image_into_single_question()`
  - `_replace_placeholder_in_content()`

- Xóa các duplicate methods nếu có
- Đảm bảo import `uuid` ở đầu file đã có

---

**Status**: Ready to apply
