"""
MatrixQuesGen Launcher
Khởi động server và tự động mở browser
"""
import sys
import os
import time
import webbrowser
import threading
import logging
from logging.handlers import RotatingFileHandler
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
server_dir = BASE_DIR / "server" / "src"
sys.path.insert(0, str(server_dir))

# Set environment variables for data paths
os.environ['DATA_DIR'] = str(APP_DIR / "data")
os.environ['BASE_DIR'] = str(BASE_DIR)
os.environ['APP_DIR'] = str(APP_DIR)

# Fix Playwright Chromium path when running as frozen .exe
# Playwright resolves browser paths relative to its own __file__, which in a
# frozen app points to _MEIPASS (wrong). PLAYWRIGHT_BROWSERS_PATH overrides this.
if getattr(sys, 'frozen', False):
    localappdata = os.environ.get('LOCALAPPDATA', '') or str(Path.home() / 'AppData' / 'Local')
    pw_browsers = Path(localappdata) / 'ms-playwright'
    if pw_browsers.exists():
        os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(pw_browsers))
        print(f'✓ Playwright browsers path: {pw_browsers}')
    else:
        print(f'⚠ Playwright browsers not found at {pw_browsers}')
        print('  Chart rendering in DOCX will be disabled.')
        print('  Run install_playwright.bat to enable chart rendering.')

# Import update module if running as exe
if getattr(sys, 'frozen', False):
    try:
        import update
    except ImportError:
        pass

def open_browser():
    """Mở browser sau 2 giây"""
    time.sleep(2)
    webbrowser.open("http://localhost:8000")
    print("\n✓ Đã mở trình duyệt tự động")
    print("  Nếu không tự động mở, vui lòng truy cập: http://localhost:8000")

def main():
    """Main launcher function"""
    # Setup logging to file first
    log_dir = APP_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("Starting MatrixQuesGen Application")
    logger.info(f"Base Directory: {BASE_DIR}")
    logger.info(f"App Directory: {APP_DIR}")
    logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    logger.info("="*60)

    # === Frozen-mode diagnostics: log sys.path & key package presence ===
    if getattr(sys, 'frozen', False):
        logger.info(f"sys.path: {sys.path}")
        meipass = str(BASE_DIR)
        for _pkg in ['fastapi', 'uvicorn', 'starlette', 'pydantic']:
            _init = os.path.join(meipass, _pkg, '__init__.py')
            logger.info(f"  _MEIPASS/{_pkg}/__init__.py exists: {os.path.exists(_init)}")
    # ==================================================================
    
    # Update check is done on-demand via Settings page (not at startup)
    print("=" * 60)
    print(" MatrixQuesGen - Hệ thống sinh câu hỏi tự động")
    print("=" * 60)
    print()
    print("→ Đang khởi động server...")
    
    # Start system tray icon if running as frozen exe
    tray = None
    if getattr(sys, 'frozen', False):
        try:
            from tray_icon import start_tray_icon
            logger.info("Starting system tray icon...")
            tray = start_tray_icon(APP_DIR)
            logger.info("✓ System tray icon started")
            print("✓ System tray icon đã khởi động (xem ở 'show hidden icons')")
        except Exception as e:
            logger.warning(f"Could not start tray icon: {e}")
            print(f"⚠ Could not start tray icon: {e}")
    
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
            from api.routes import generate, questions, export, regenerate, google_drive, images
            from api.routes import update as update_route
            print("✓ Đã import routes thành công")
        except Exception as e:
            logger.error(f"Lỗi khi import routes: {e}", exc_info=True)
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
            app.include_router(regenerate.router)
            print("✓ Đã mount regenerate router")
            app.include_router(google_drive.router)
            print("✓ Đã mount google_drive router")
            app.include_router(images.router)
            print("✓ Đã mount images router")
            app.include_router(update_route.router)
            print("✓ Đã mount update router")
            app.include_router(export.routerEnglish)
            print("✓ Đã mount routerEnglish")
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
        # Disable default logging config when frozen (console=False)
        # to avoid 'NoneType' has no attribute 'isatty' error
        log_config = None if getattr(sys, 'frozen', False) else uvicorn.config.LOGGING_CONFIG
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            log_config=log_config
        )
        
    except KeyboardInterrupt:
        print("\n\n✓ Đang tắt server...")
        print("Cảm ơn bạn đã sử dụng MatrixQuesGen!")
    except Exception as e:
        import traceback
        logger.error(f"Lỗi khi khởi động server: {e}", exc_info=True)
        logger.error(traceback.format_exc())
        print(f"\n✗ Lỗi khi khởi động server: {e}")
        print(f"Chi tiết lỗi đã được ghi vào: {APP_DIR / 'logs' / 'app.log'}")
        traceback.print_exc()
        # Don't use input() in frozen exe mode (sys.stdin not available)
        if not getattr(sys, 'frozen', False):
            input("\nNhấn Enter để thoát...")
        else:
            import time
            time.sleep(10)  # Wait 10 seconds so user can see the error path
        sys.exit(1)

if __name__ == "__main__":
    main()
