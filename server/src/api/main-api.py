import sys
import os
from pathlib import Path

# Add API directory to Python path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import generate, questions, export, docx_reader

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
app.include_router(docx_reader.router)


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
