"""
API routes để update chart_raw_data và regenerate echarts
"""
import json
import os
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.generators.helpers.chart_generation_helper import process_chart_data_to_option, apply_layout


router = APIRouter(prefix="/api/chart", tags=["Chart"])


class UpdateChartRequest(BaseModel):
    """Request body để update chart_raw_data và regenerate echarts"""
    session_id: str
    question_type: str  # TN, DS, TLN, TL
    question_code: str
    chart_raw_data: Dict  # {chart_type, data, options}


def _get_questions_dir() -> Path:
    """Get questions directory path"""
    app_dir = os.getenv('APP_DIR')
    if app_dir:
        return Path(app_dir) / "data" / "questions"
    # Fallback for dev mode
    return Path(__file__).parent.parent.parent.parent / "data" / "questions"


@router.put("/update")
async def update_chart(request: UpdateChartRequest):
    """
    Update chart_raw_data, regenerate echarts, và update file JSON
    
    Input:
    - session_id: ID phiên làm việc
    - question_type: TN, DS, TLN, TL
    - question_code: C1, C2, ...
    - chart_raw_data: {chart_type, data, options}
    
    Output: {success, chartType, echarts, chart_raw_data}
    """
    try:
        # Validate input
        if not request.session_id or not request.question_code or not request.question_type:
            raise ValueError("session_id, question_code, question_type không được để trống")
        
        if not request.chart_raw_data:
            raise ValueError("chart_raw_data không được để trống")
        
        chart_raw_data = request.chart_raw_data
        chart_type = chart_raw_data.get('chart_type')
        
        if not chart_type:
            raise ValueError("chart_type không được để trống")
        
        # Load questions file
        questions_dir = _get_questions_dir()
        questions_file = questions_dir / f"questions_{request.session_id}.json"
        
        if not questions_file.exists():
            raise FileNotFoundError(f"File không tồn tại: {questions_file}")
        
        with open(questions_file, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
        
        # Tìm câu hỏi
        questions_list = exam_data.get('questions', {}).get(request.question_type, [])
        question = None
        for q in questions_list:
            if q.get('question_code') == request.question_code:
                question = q
                break
        
        if not question:
            raise ValueError(f"Không tìm thấy câu hỏi {request.question_code} loại {request.question_type}")
        
        # Regenerate echarts option
        chart_data_for_gen = {
            'chart_type': chart_type,
            'data': chart_raw_data.get('data', {}),
            'options': chart_raw_data.get('options', {})
        }
        
        echarts_option = process_chart_data_to_option(chart_data_for_gen)
        if not echarts_option:
            raise ValueError("Không thể sinh echarts option")
        
        echarts_option = apply_layout(echarts_option)
        
        # Update question_stem.content
        if question.get('question_stem', {}).get('type') == 'chart':
            for item in question.get('question_stem', {}).get('content', []):
                if item and isinstance(item, dict) and item.get('type') == 'chart':
                    item['content']['chartType'] = chart_type
                    item['content']['echarts'] = echarts_option
                    item['content']['chart_raw_data'] = chart_raw_data
                    break
        
        # Save file
        try:
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(exam_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Lỗi khi lưu file: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi khi lưu file: {str(e)}")
        
        return {
            'success': True,
            'message': f'Chart {request.question_code} đã được cập nhật',
            'chartType': chart_type,
            'echarts': echarts_option,
            'chart_raw_data': chart_raw_data
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Error updating chart: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

