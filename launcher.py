"""
MatrixQuesGen Launcher
Khởi động server và tự động mở browser
"""
import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# Set up paths
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).parent
else:
    # Running as script
    BASE_DIR = Path(__file__).parent
    APP_DIR = BASE_DIR

# Add server to path
server_dir = BASE_DIR / "server" / "src" / "api"
sys.path.insert(0, str(server_dir))

# Set environment variables for data paths
os.environ['DATA_DIR'] = str(APP_DIR / "data")
os.environ['BASE_DIR'] = str(BASE_DIR)
os.environ['APP_DIR'] = str(APP_DIR)

def open_browser():
    """Mở browser sau 2 giây"""
    time.sleep(2)
    webbrowser.open("http://localhost:8000")
    print("\n✓ Đã mở trình duyệt tự động")
    print("  Nếu không tự động mở, vui lòng truy cập: http://localhost:8000")

def main():
    """Main launcher function"""
    print("=" * 60)
    print(" MatrixQuesGen - Hệ thống sinh câu hỏi tự động")
    print("=" * 60)
    print()
    print("→ Đang khởi động server...")
    
    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Import and run FastAPI app
    try:
        import uvicorn
        from fastapi import FastAPI, Request, Response
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        from starlette.middleware.base import BaseHTTPMiddleware
        from dotenv import load_dotenv
        
        # Load environment variables
        env_file = APP_DIR / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        # Import pyarmor runtime for obfuscated code
        try:
            import pyarmor_runtime_000000
        except ImportError:
            pass  # Not obfuscated
        
        # Import routes
        try:
            from routes import generate, questions, export
            print("✓ Đã import routes thành công")
        except Exception as e:
            print(f"✗ Lỗi khi import routes: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Initialize FastAPI app
        app = FastAPI(
            title="MatrixQuesGen API",
            description="API sinh câu hỏi tự động từ ma trận",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Determine static directory path
        if getattr(sys, 'frozen', False):
            static_dir = BASE_DIR / "client" / "dist"
        else:
            static_dir = APP_DIR / "client" / "dist"
        
        # SPA Middleware - serve index.html for non-API routes
        class SPAMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                response = await call_next(request)
                
                # If 404 and not an API call, serve index.html
                if response.status_code == 404 and not request.url.path.startswith("/api"):
                    index_file = static_dir / "index.html"
                    if index_file.exists():
                        return FileResponse(index_file)
                
                return response
        
        # CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add SPA middleware if static files exist
        if static_dir.exists() and static_dir.is_dir():
            app.add_middleware(SPAMiddleware)
        
        # Include API routers (routers đã có prefix /api sẵn)
        try:
            app.include_router(generate.router)
            print("✓ Đã mount generate router")
            app.include_router(questions.router)
            print("✓ Đã mount questions router")
            app.include_router(export.router)
            print("✓ Đã mount export router")
        except Exception as e:
            print(f"✗ Lỗi khi mount routers: {e}")
            import traceback
            traceback.print_exc()
        
        # Health check endpoint
        @app.get("/api/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "matrixquesgen-api"
            }
        
        # Serve static files
        if static_dir.exists() and static_dir.is_dir():
            # Mount assets
            assets_dir = static_dir / "assets"
            if assets_dir.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            
            # Serve index.html at root
            @app.get("/")
            async def serve_root():
                index_file = static_dir / "index.html"
                if index_file.exists():
                    return FileResponse(index_file)
                return {"error": "index.html not found"}
            
            print(f"✓ Đã mount static files từ: {static_dir}")
        else:
            print(f"⚠ Cảnh báo: Không tìm thấy thư mục static: {static_dir}")
            print(f"  BASE_DIR: {BASE_DIR}")
            print(f"  APP_DIR: {APP_DIR}")
            
            @app.get("/")
            async def root():
                return {
                    "message": "MatrixQuesGen API đang hoạt động",
                    "version": "1.0.0",
                    "docs": "/api/docs"
                }
        
        print()
        print("=" * 60)
        print("✓ Server đã sẵn sàng!")
        print("  - URL: http://localhost:8000")
        print("  - API Docs: http://localhost:8000/api/docs")
        print("=" * 60)
        print()
        print("Nhấn Ctrl+C để thoát...")
        print()
        
        # Run server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n✓ Đang tắt server...")
        print("Cảm ơn bạn đã sử dụng MatrixQuesGen!")
    except Exception as e:
        print(f"\n✗ Lỗi khi khởi động server: {e}")
        import traceback
        traceback.print_exc()
        input("\nNhấn Enter để thoát...")
        sys.exit(1)

if __name__ == "__main__":
    main()
