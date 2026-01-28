"""
API endpoints cho Case 2: Custom Prompts Workflow
Upload prompts với {{VARIABLES}} và generate questions
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Dict, Optional
import uuid
from pydantic import BaseModel

from services.prompts.prompt_parser import PromptParserService

router = APIRouter(
    prefix="/prompts",
    tags=["Custom Prompts"]
)

# In-memory storage cho uploaded prompts sessions
uploaded_prompts_store: Dict[str, Dict] = {}


class VariableValue(BaseModel):
    """Model cho variable value"""
    name: str
    value: str


class GenerateRequest(BaseModel):
    """Request để generate với custom prompts"""
    session_id: str
    variable_values: List[VariableValue]
    num_questions: int = 10


@router.post("/upload")
async def upload_prompts(files: List[UploadFile] = File(...)):
    """
    Upload prompt files (.txt) và parse variables
    
    Args:
        files: List các file .txt (max 10)
        
    Returns:
        Session info với detected variables
    """
    # Validate số lượng files
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Chỉ được upload tối đa 10 files"
        )
    
    # Validate file types
    for file in files:
        if not file.filename.endswith('.txt'):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} không phải .txt"
            )
    
    # Parse prompts
    session_id = str(uuid.uuid4())
    prompts = {}
    all_variables = set()
    
    for file in files:
        content = (await file.read()).decode('utf-8')
        prompt_name = file.filename.replace('.txt', '')
        
        # Parse prompt
        parsed = PromptParserService.parse_prompt_content(content)
        
        if not parsed['is_valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt {file.filename} có cú pháp không hợp lệ"
            )
        
        prompts[prompt_name] = {
            "content": content,
            "variables": parsed['variables'],
            "variable_count": parsed['variable_count']
        }
        
        all_variables.update(parsed['variables'])
    
    # Lấy context cho từng variable
    variable_contexts = {}
    for var in all_variables:
        contexts = []
        for prompt_name, prompt_data in prompts.items():
            prompt_contexts = PromptParserService.get_variable_context(
                prompt_data['content'], 
                var, 
                context_chars=80
            )
            if prompt_contexts:
                contexts.extend([
                    {"prompt": prompt_name, "context": ctx}
                    for ctx in prompt_contexts
                ])
        variable_contexts[var] = contexts
    
    # Lưu session
    session_data = {
        "session_id": session_id,
        "prompts": prompts,
        "variables": sorted(list(all_variables)),
        "variable_contexts": variable_contexts,
        "prompt_count": len(prompts)
    }
    
    uploaded_prompts_store[session_id] = session_data
    
    return session_data


@router.post("/generate")
async def generate_with_custom_prompts(request: GenerateRequest):
    """
    Generate questions với custom prompts và variable values
    
    Args:
        request: GenerateRequest với session_id và variable values
        
    Returns:
        Generated questions
    """
    # Lấy session
    session = uploaded_prompts_store.get(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session không tồn tại hoặc đã hết hạn"
        )
    
    # Convert variable values to dict
    var_dict = {v.name: v.value for v in request.variable_values}
    
    # Validate tất cả variables đã được provide
    missing_vars = set(session['variables']) - set(var_dict.keys())
    if missing_vars:
        raise HTTPException(
            status_code=400,
            detail=f"Thiếu giá trị cho variables: {', '.join(missing_vars)}"
        )
    
    # Fill variables vào prompts
    filled_prompts = {}
    for prompt_name, prompt_data in session['prompts'].items():
        filled_content = PromptParserService.fill_variables(
            prompt_data['content'],
            var_dict
        )
        filled_prompts[prompt_name] = filled_content
    
    # TODO: Tích hợp với question generator
    # Hiện tại return filled prompts để test
    return {
        "session_id": request.session_id,
        "filled_prompts": filled_prompts,
        "num_questions": request.num_questions,
        "status": "success",
        "message": "Prompts đã được fill. TODO: Tích hợp generation logic"
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Lấy thông tin session
    
    Args:
        session_id: ID của session
        
    Returns:
        Session data
    """
    session = uploaded_prompts_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session không tồn tại"
        )
    
    return session


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Xóa session
    
    Args:
        session_id: ID của session
        
    Returns:
        Success message
    """
    if session_id in uploaded_prompts_store:
        del uploaded_prompts_store[session_id]
        return {"message": "Session đã được xóa"}
    
    raise HTTPException(
        status_code=404,
        detail="Session không tồn tại"
    )


@router.post("/validate")
async def validate_prompt_file(file: UploadFile = File(...)):
    """
    Validate một prompt file trước khi upload
    
    Args:
        file: File .txt cần validate
        
    Returns:
        Validation result
    """
    if not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=400,
            detail="File phải có định dạng .txt"
        )
    
    content = (await file.read()).decode('utf-8')
    parsed = PromptParserService.parse_prompt_content(content)
    
    return {
        "filename": file.filename,
        "is_valid": parsed['is_valid'],
        "variables": parsed['variables'],
        "variable_count": parsed['variable_count']
    }
