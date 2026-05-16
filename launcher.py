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
import shutil
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

# Migrate bundled English resources to APP_DIR if running as frozen exe
if getattr(sys, 'frozen', False):
    import shutil
    
    # Migrate English prompts and vocabulary
    english_resource_dirs = [
        'data/prompts/prompts_english',
        'data/vocabulary_english',
    ]
    
    for resource_dir in english_resource_dirs:
        src = BASE_DIR / resource_dir
        dst = APP_DIR / resource_dir
        
        if src.exists() and not dst.exists():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst)
                print(f'✓ Migrated resource: {resource_dir}')
            except Exception as e:
                print(f'⚠ Could not migrate {resource_dir}: {e}')
        elif src.exists() and dst.exists():
            # Merge: copy missing files from src to dst without overwriting
            try:
                for src_file in src.rglob('*'):
                    if src_file.is_file():
                        rel_path = src_file.relative_to(src)
                        dst_file = dst / rel_path
                        if not dst_file.exists():
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dst_file)
            except Exception as e:
                print(f'⚠ Could not merge {resource_dir}: {e}')

    # ── SA credential files: extract to TEMP, never write to APP_DIR ───────────
    # Credential JSONs are extracted to a per-session temp dir so they never
    # appear in the installation folder.  atexit removes them when app exits.
    import tempfile as _tempfile
    import atexit as _atexit
    _sa_src = BASE_DIR / 'data' / 'SA'
    if _sa_src.exists():
        _sa_tmp = Path(_tempfile.mkdtemp(prefix='mqg_sa_'))
        os.environ['SA_DIR'] = str(_sa_tmp)
        _PREF_ONLY = {'ai-provider-settings.json'}
        for _f in _sa_src.iterdir():
            if _f.is_file() and _f.name not in _PREF_ONLY:
                shutil.copy2(_f, _sa_tmp / _f.name)
        _sa_tmp_ref = str(_sa_tmp)  # capture for closure
        def _cleanup_sa(_d=_sa_tmp_ref):
            shutil.rmtree(_d, ignore_errors=True)
        _atexit.register(_cleanup_sa)
        print('✓ SA credentials loaded to secure temp (hidden from install folder)')
        # Migrate ONLY preference file (ai-provider-settings.json) to APP_DIR —
        # it is not sensitive and must survive across restarts so the user's
        # Gemini / OpenAI choice is remembered.
        _sa_dst = APP_DIR / 'data' / 'SA'
        _sa_dst.mkdir(parents=True, exist_ok=True)
        for _f in _sa_src.iterdir():
            if _f.is_file() and _f.name in _PREF_ONLY:
                _dst_f = _sa_dst / _f.name
                if not _dst_f.exists():
                    shutil.copy2(_f, _dst_f)

    # ── Load bundled .env directly into os.environ (zero files in APP_DIR) ─────
    # BASE_DIR == _MEIPASS, which is a system temp directory automatically
    # created when the exe starts and deleted when it exits — no files are ever
    # written to the installation folder.
    # All subsequent load_dotenv() calls (in callApi.py, main(), etc.) are
    # silent no-ops because load_dotenv() never overrides already-set env vars.
    _bundled_env = BASE_DIR / '.env'
    if _bundled_env.exists():
        try:
            from dotenv import dotenv_values as _dv
            for _k, _v in _dv(_bundled_env).items():
                os.environ.setdefault(_k, _v)
            # Remap credential file paths from build-machine absolute path
            # to the per-session temp SA dir (primary) or _MEIPASS/credentials/ (fallback).
            _sa_dir_env = os.environ.get('SA_DIR', '')
            for _cvar in ['GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_DRIVE_CREDENTIALS_PATH']:
                _val = os.environ.get(_cvar, '')
                if _val:
                    _fname = Path(_val).name
                    _found = False
                    for _cbase in filter(None, [
                        Path(_sa_dir_env) if _sa_dir_env else None,
                        BASE_DIR / 'credentials',
                    ]):
                        _candidate = _cbase / _fname
                        if _candidate.exists():
                            os.environ[_cvar] = str(_candidate)
                            print(f'✓ Using embedded credential for {_cvar}: {_fname}')
                            _found = True
                            break
            # Cross-fallback: if only GOOGLE_APPLICATION_CREDENTIALS is set (no separate
            # GOOGLE_DRIVE_CREDENTIALS_PATH), point Drive to the same SA file.
            _gac = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
            if _gac and not os.environ.get('GOOGLE_DRIVE_CREDENTIALS_PATH', ''):
                os.environ['GOOGLE_DRIVE_CREDENTIALS_PATH'] = _gac
                print('✓ GOOGLE_DRIVE_CREDENTIALS_PATH set from GOOGLE_APPLICATION_CREDENTIALS')
            print('✓ Loaded bundled configuration')
        except Exception as e:
            print(f'⚠ Could not load bundled config: {e}')

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

    # === Frozen-mode diagnostics: check if key packages are importable ===
    if getattr(sys, 'frozen', False):
        import importlib.util as _iutil
        logger.info(f"sys.path: {sys.path}")
        meipass = str(BASE_DIR)
        for _pkg in ['fastapi', 'uvicorn', 'starlette', 'pydantic', 'fitz']:
            _init_py = os.path.join(meipass, _pkg, '__init__.py')
            _spec = _iutil.find_spec(_pkg)
            logger.info(
                f"  {_pkg}: .py in _MEIPASS={os.path.exists(_init_py)}, "
                f"importable={_spec is not None}"
            )
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
            from api.routes import generate, questions, export, regenerate, google_drive, images, solute, chart_regenerate, math_template_selection, history_material_selection
            from api.routes import update as update_route
            from api.routes.ai_settings import router as ai_settings_router
            from api.routes.export import routerEnglish
            from api.routes.regenerateEnglish import routerRegenerateEnglish
            from api.phase_apis import phase1_router, phase2_router, phase3_router, phase4_router, workflow_router
            from api.custom_prompts_api import router as custom_prompts_router
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
            app.include_router(chart_regenerate.router)
            print("✓ Đã mount chart_regenerate router")
            app.include_router(google_drive.router)
            print("✓ Đã mount google_drive router")
            app.include_router(images.router)
            print("✓ Đã mount images router")
            app.include_router(update_route.router)
            print("✓ Đã mount update router")
            app.include_router(routerEnglish)
            print("✓ Đã mount routerEnglish")
            app.include_router(routerRegenerateEnglish)
            print("✓ Đã mount routerRegenerateEnglish")
            app.include_router(solute.routerSolute)
            print("✓ Đã mount solute router")
            app.include_router(math_template_selection.router)
            print("✓ Đã mount math_template_selection router (TOAN workflow)")
            app.include_router(history_material_selection.router)
            print("✓ Đã mount history_material_selection router (LICHSU workflow)")
            app.include_router(ai_settings_router)
            print("✓ Đã mount ai_settings router")
            # Include phase-specific routers
            app.include_router(phase1_router)
            app.include_router(phase2_router)
            app.include_router(phase3_router)
            app.include_router(phase4_router)
            app.include_router(workflow_router)
            print("✓ Đã mount phase routers")
            # Include custom prompts router
            app.include_router(custom_prompts_router, prefix="/api")
            print("✓ Đã mount custom_prompts router")
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
