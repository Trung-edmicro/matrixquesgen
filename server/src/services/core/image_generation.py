"""
Module sinh ảnh sử dụng Imagen API
"""

import os
import io
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from google.oauth2 import service_account
from PIL import Image


class ImageGenerator:
    """
    Class xử lý image generation với Imagen
    """
    def __init__(
        self,
        num_images: int = 1,
        aspect_ratio: str = "16:9"
    ):
        """
        Khởi tạo Image Generator
        
        Args:
            num_images: Số lượng ảnh generate (1-4)
            aspect_ratio: Tỷ lệ khung hình (1:1, 16:9, 9:16, 4:3, 3:4)
        """
        # Use Imagen model for image generation (not Gemini)
        # Imagen 3.0 is the latest model for high-quality image generation
        self.model_name = os.getenv('GEMINI_IMAGE_MODEL', 'imagen-3.0-generate-001')
        self.num_images = num_images
        self.aspect_ratio = aspect_ratio
        self.client = None
        
        # Khởi tạo credentials và client
        try:
            credentials = self._get_credentials()
            if credentials:
                # Get project and location from environment
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'onluyen-media')
                location = os.getenv('GCP_LOCATION', 'us-central1')  # Imagen models available in us-central1
                
                self.client = genai.Client(
                    vertexai=True,
                    project=project_id,
                    location=location,
                    credentials=credentials
                )
            
        except Exception as e:
            print(f"Error in initializing client: {e}")
            self.client = None
    
    def _get_credentials(self):
        """
        Tạo credentials từ Service Account
        """
        try:
            service_account_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not service_account_file or not os.path.exists(service_account_file):
                print(f"⚠️ Service account file not found: {service_account_file}")
                return None
            
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            return credentials
        except Exception as e:
            print(f"Error in getting credentials: {e}")
            return None
    
    def generate(
        self,
        prompt: str,
        num_images: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        reference_image_path: Optional[str] = None
    ) -> List[bytes]:
        """
        Generate ảnh từ text prompt
        
        Args:
            prompt: Mô tả ảnh cần tạo
            num_images: Số lượng ảnh (override default)
            aspect_ratio: Tỷ lệ khung hình (override default)
            negative_prompt: Những gì KHÔNG muốn có trong ảnh
            seed: Random seed để tái tạo kết quả
            reference_image_path: Đường dẫn đến ảnh mẫu để AI học theo phong cách
            
        Returns:
            List[bytes]: Danh sách image data (bytes)
        """
        if not self.client:
            print("⚠️ Image generation client not initialized, using placeholder")
            return self._generate_placeholder_images(prompt, num_images or self.num_images)
        
        try:
            ratio = aspect_ratio or self.aspect_ratio
            
            # Prepare contents
            contents = []
            
            # Nếu có reference image, load và thêm vào contents
            if reference_image_path and os.path.exists(reference_image_path):
                with open(reference_image_path, 'rb') as f:
                    ref_image_data = f.read()
                
                # Thêm reference image vào contents với instruction
                contents.append(types.Part.from_bytes(
                    data=ref_image_data,
                    mime_type="image/png"
                ))
                contents.append(types.Part.from_text(
                    text=f"Vẽ hình ảnh minh họa theo phong cách và bố cục của ảnh tham khảo trên. Nội dung cần vẽ: {prompt}"
                ))
            else:
                # Không có reference image, chỉ dùng prompt
                contents.append(types.Part.from_text(
                    text=f"Vẽ hình ảnh minh họa chính xác cho mô tả sau: {prompt}"
                ))
            
            # Gọi API với SDK mới
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    candidate_count=1,
                    image_config=types.ImageConfig(aspect_ratio=ratio),
                )
            )
            
            images = []
            for part in response.parts:
                if part.inline_data and part.inline_data.data:
                    images.append(part.inline_data.data)
            
            if images:
                return images
            else:
                return self._generate_placeholder_images(prompt, 1)
            
        except Exception as e:
            print(f"Error in image generation: {e}")
            return self._generate_placeholder_images(prompt, num_images or self.num_images)
    
    def _generate_placeholder_images(self, prompt: str, num: int) -> List[bytes]:
        """
        Tạo placeholder images khi API không khả dụng
        """
        images = []
        for i in range(num):
            img = self._create_placeholder_image(prompt, i)
            images.append(img)
        return images
    
    def _create_placeholder_image(self, prompt: str, index: int = 0) -> bytes:
        """
        Tạo placeholder image (để test)
        
        Args:
            prompt: Text prompt
            index: Index của ảnh
            
        Returns:
            bytes: Image data
        """
        from PIL import Image, ImageDraw
        
        # Parse aspect ratio
        width, height = 512, 512
        if self.aspect_ratio == "16:9":
            width, height = 768, 432
        elif self.aspect_ratio == "9:16":
            width, height = 432, 768
        elif self.aspect_ratio == "4:3":
            width, height = 640, 480
        elif self.aspect_ratio == "3:4":
            width, height = 480, 640
        
        # Tạo image với gradient
        img = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # Vẽ gradient
        for i in range(height):
            color = int(200 - (i / height) * 50)
            draw.line([(0, i), (width, i)], fill=(color, color, 250))
        
        # Vẽ text
        text_lines = [
            f"Image #{index + 1}",
            f"Prompt: {prompt[:30]}...",
            f"Ratio: {self.aspect_ratio}"
        ]
        
        y_pos = height // 2 - 40
        for line in text_lines:
            # Tính toán vị trí text để center
            bbox = draw.textbbox((0, 0), line)
            text_width = bbox[2] - bbox[0]
            x_pos = (width - text_width) // 2
            draw.text((x_pos, y_pos), line, fill=(50, 50, 50))
            y_pos += 30
        
        # Convert sang bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    def generate_variations(
        self,
        base_image_path: str,
        prompt: Optional[str] = None,
        num_variations: int = 3
    ) -> List[bytes]:
        """
        Tạo variations từ ảnh gốc
        
        Args:
            base_image_path: Đường dẫn đến ảnh gốc
            prompt: Prompt bổ sung (optional)
            num_variations: Số lượng variations
            
        Returns:
            List[bytes]: Danh sách variations
        """
        try:
            # Load base image
            with open(base_image_path, 'rb') as f:
                base_image_data = f.read()
            
            # Generate variations
            # Note: Cần Vertex AI Imagen API
            variations = []
            for i in range(num_variations):
                variation = self._create_variation_placeholder(base_image_path, i)
                variations.append(variation)
        
            return variations
            
        except Exception as e:
            print(f"Error in generating variations: {e}")
            raise
    
    def _create_variation_placeholder(self, base_path: str, index: int) -> bytes:
        """
        Tạo placeholder variation
        """
        from PIL import Image, ImageDraw, ImageEnhance
        
        # Load và modify base image
        img = Image.open(base_path)
        
        # Apply các effects khác nhau
        if index == 0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.2)
        elif index == 1:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)
        else:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.8)
        
        # Thêm watermark
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), f"Variation #{index + 1}", fill=(255, 255, 255))
        
        # Convert sang bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    def upscale_image(
        self,
        image_path: str,
        scale_factor: int = 2
    ) -> bytes:
        """
        Upscale ảnh lên độ phân giải cao hơn
        
        Args:
            image_path: Đường dẫn đến ảnh
            scale_factor: Hệ số scale (2x, 4x)
            
        Returns:
            bytes: Upscaled image data
        """
        try:
            img = Image.open(image_path)
            new_size = (img.width * scale_factor, img.height * scale_factor)
            
            # Sử dụng LANCZOS để upscale chất lượng cao
            upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert sang bytes
            img_byte_arr = io.BytesIO()
            upscaled.save(img_byte_arr, format='PNG')

            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"Error in upscaling image: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin về model
        
        Returns:
            dict: Thông tin model
        """
        return {
            "model_name": self.model_name,
            "num_images": self.num_images,
            "aspect_ratio": self.aspect_ratio,
            "supported_ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
            "client_initialized": self.client is not None
        }
