import sys
import os
from pathlib import Path

# Add server/src directory to Python path
server_src_dir = Path(__file__).parent.parent  # server/src
sys.path.insert(0, str(server_src_dir))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Use absolute imports
from api.routes import generate, questions, export, google_drive
from api.phase_apis import phase1_router, phase2_router, phase3_router, phase4_router, workflow_router
from api.custom_prompts_api import router as custom_prompts_router

# Load environment variables
load_dotenv()

# Khởi tạo FastAPI app
app = FastAPI(
    title="MatrixQuesGen API",
    description="API sinh câu hỏi tự động từ ma trận",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(generate.router)
app.include_router(questions.router)
app.include_router(export.router)
app.include_router(google_drive.router)

# Include phase-specific routers
app.include_router(phase1_router)
app.include_router(phase2_router)
app.include_router(phase3_router)
app.include_router(phase4_router)
app.include_router(workflow_router)

# Include custom prompts router (Case 2)
app.include_router(custom_prompts_router, prefix="/api")


@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "message": "MatrixQuesGen API đang hoạt động",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check cho monitoring
    """
    return {
        "status": "healthy",
        "service": "matrixquesgen-api"
    }


if __name__ == "__main__":    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Reload không hoạt động khi pass app object
    )
