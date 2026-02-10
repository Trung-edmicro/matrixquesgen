"""
API routes for image generation
"""
import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.generators.image_generator import ImageGenerator


router = APIRouter(prefix="/api/images", tags=["Images"])


# Helper function for lazy path loading (ensures APP_DIR env var is set)
def _get_app_dir() -> Path:
    """Get APP_DIR with lazy loading to ensure env var is set"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir)
    # Fallback for dev mode
    return Path(__file__).parent.parent.parent.parent


def _get_images_dir() -> Path:
    """Get images directory path with lazy loading"""
    images_dir = _get_app_dir() / "data" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


class ImageGenerateRequest(BaseModel):
    """Request body để sinh ảnh"""
    prompt: str
    num_images: Optional[int] = 1
    aspect_ratio: Optional[str] = "16:9"
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    reference_image_url: Optional[str] = None


class ImageGenerateResponse(BaseModel):
    """Response sau khi sinh ảnh"""
    success: bool
    image_urls: List[str]
    message: str


class ImageUpscaleRequest(BaseModel):
    """Request body để upscale ảnh"""
    image_url: str
    scale_factor: int = 2


class ImageVariationsRequest(BaseModel):
    """Request body để tạo variations"""
    image_url: str
    prompt: Optional[str] = None
    num_variations: int = 3


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    Sinh ảnh từ text prompt bằng Imagen AI
    
    - **prompt**: Mô tả ảnh cần tạo
    - **num_images**: Số lượng ảnh (1-4, mặc định 1)
    - **aspect_ratio**: Tỷ lệ khung hình (1:1, 16:9, 9:16, 4:3, 3:4)
    - **negative_prompt**: Những gì KHÔNG muốn có trong ảnh
    - **seed**: Random seed để tái tạo kết quả
    - **reference_image_url**: URL ảnh mẫu để AI học theo phong cách
    """
    try:
        # Validate aspect ratio
        valid_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        if request.aspect_ratio and request.aspect_ratio not in valid_ratios:
            raise HTTPException(
                status_code=400,
                detail=f"aspect_ratio phải là một trong: {', '.join(valid_ratios)}"
            )
        
        # Validate num_images
        if request.num_images < 1 or request.num_images > 4:
            raise HTTPException(
                status_code=400,
                detail="num_images phải từ 1 đến 4"
            )
        
        # Initialize image generator
        generator = ImageGenerator(
            num_images=request.num_images,
            aspect_ratio=request.aspect_ratio or "16:9"
        )
        
        # Download reference image if URL provided
        reference_image_path = None
        if request.reference_image_url:
            # Download to temp location
            ref_filename = f"ref_{uuid.uuid4().hex}.png"
            reference_image_path = _get_images_dir() / ref_filename
            
            # TODO: Implement image download from URL
            # For now, skip if it's a URL
            if request.reference_image_url.startswith("http"):
                print(f"⚠️ Reference image URL provided but download not implemented yet")
                reference_image_path = None
            else:
                # Assume it's a local path
                reference_image_path = request.reference_image_url if os.path.exists(request.reference_image_url) else None
        
        # Generate images
        images_data = generator.generate(
            prompt=request.prompt,
            num_images=request.num_images,
            aspect_ratio=request.aspect_ratio,
            negative_prompt=request.negative_prompt,
            seed=request.seed,
            reference_image_path=reference_image_path
        )
        
        # Save images and get URLs
        image_urls = []
        for i, img_data in enumerate(images_data):
            # Generate unique filename
            filename = f"img_{uuid.uuid4().hex}_{i}.png"
            filepath = _get_images_dir() / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            # Create URL (relative path for API)
            image_url = f"/api/images/file/{filename}"
            image_urls.append(image_url)
        
        return ImageGenerateResponse(
            success=True,
            image_urls=image_urls,
            message=f"Đã sinh {len(image_urls)} ảnh thành công"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi sinh ảnh: {str(e)}"
        )


@router.post("/upscale", response_model=ImageGenerateResponse)
async def upscale_image(request: ImageUpscaleRequest):
    """
    Upscale ảnh lên độ phân giải cao hơn
    
    - **image_url**: URL hoặc đường dẫn đến ảnh
    - **scale_factor**: Hệ số scale (2x, 4x)
    """
    try:
        # Validate scale factor
        if request.scale_factor not in [2, 4]:
            raise HTTPException(
                status_code=400,
                detail="scale_factor phải là 2 hoặc 4"
            )
        
        # Get image path from URL
        if request.image_url.startswith("/api/images/file/"):
            filename = request.image_url.split("/")[-1]
            image_path = _get_images_dir() / filename
        else:
            # Assume it's a local path
            image_path = Path(request.image_url)
        
        if not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Ảnh không tồn tại"
            )
        
        # Initialize image generator and upscale
        generator = ImageGenerator()
        upscaled_data = generator.upscale_image(
            image_path=str(image_path),
            scale_factor=request.scale_factor
        )
        
        # Save upscaled image
        filename = f"upscaled_{uuid.uuid4().hex}.png"
        filepath = _get_images_dir() / filename
        
        with open(filepath, 'wb') as f:
            f.write(upscaled_data)
        
        image_url = f"/api/images/file/{filename}"
        
        return ImageGenerateResponse(
            success=True,
            image_urls=[image_url],
            message=f"Đã upscale ảnh {request.scale_factor}x thành công"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi upscale ảnh: {str(e)}"
        )


@router.post("/variations", response_model=ImageGenerateResponse)
async def create_variations(request: ImageVariationsRequest):
    """
    Tạo variations từ ảnh gốc
    
    - **image_url**: URL hoặc đường dẫn đến ảnh gốc
    - **prompt**: Prompt bổ sung (optional)
    - **num_variations**: Số lượng variations (1-5)
    """
    try:
        # Validate num_variations
        if request.num_variations < 1 or request.num_variations > 5:
            raise HTTPException(
                status_code=400,
                detail="num_variations phải từ 1 đến 5"
            )
        
        # Get image path from URL
        if request.image_url.startswith("/api/images/file/"):
            filename = request.image_url.split("/")[-1]
            image_path = _get_images_dir() / filename
        else:
            # Assume it's a local path
            image_path = Path(request.image_url)
        
        if not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Ảnh không tồn tại"
            )
        
        # Initialize image generator and create variations
        generator = ImageGenerator()
        variations_data = generator.generate_variations(
            base_image_path=str(image_path),
            prompt=request.prompt,
            num_variations=request.num_variations
        )
        
        # Save variations
        image_urls = []
        for i, var_data in enumerate(variations_data):
            filename = f"var_{uuid.uuid4().hex}_{i}.png"
            filepath = _get_images_dir() / filename
            
            with open(filepath, 'wb') as f:
                f.write(var_data)
            
            image_url = f"/api/images/file/{filename}"
            image_urls.append(image_url)
        
        return ImageGenerateResponse(
            success=True,
            image_urls=image_urls,
            message=f"Đã tạo {len(image_urls)} variations thành công"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo variations: {str(e)}"
        )


@router.get("/file/{filename}")
async def get_image_file(filename: str):
    """
    Lấy file ảnh đã sinh
    
    - **filename**: Tên file ảnh
    """
    filepath = _get_images_dir() / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Ảnh không tồn tại")
    
    return FileResponse(
        filepath,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/model-info")
async def get_model_info():
    """
    Lấy thông tin về model image generation
    """
    generator = ImageGenerator()
    return generator.get_model_info()
