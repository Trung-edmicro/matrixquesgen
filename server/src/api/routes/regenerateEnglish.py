from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from server.src.services.english_generator_service.regenerate_english_service import regenerate_english_question

routerRegenerateEnglish = APIRouter(prefix="/api/regenerate-english",tags=["Regenerate English"])

class RegenerateRequest(BaseModel):
    type:str
    topic:str
    spec:str
    level:str
    diff:str
    passage:str
    passage_title:str
    question_number:Optional[int]
    text_type:str|None = None
    user_feedback:str
    current_question_data:dict

@routerRegenerateEnglish.post("/regenerate-one-question")
async def regenerate_question(req:RegenerateRequest):

    print(f">>>> debug req {req}")
    try:
        result = await regenerate_english_question(req.dict())

        return {
            "status": "success",
            "parsed": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
