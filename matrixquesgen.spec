# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all server files
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all uvicorn and starlette submodules (PyInstaller misses dynamic imports)
uvicorn_imports = collect_submodules('uvicorn')
starlette_imports = collect_submodules('starlette')
fastapi_imports = collect_submodules('fastapi')

server_datas = []
server_src = 'server/src'
# Add entire server/src directory structure
if os.path.exists(server_src):
    for root, dirs, files in os.walk(server_src):
        for file in files:
            if file.endswith(('.py', '.txt', '.md', '.json')):
                src_path = os.path.join(root, file)
                # Preserve the directory structure
                dest_dir = os.path.dirname(src_path)
                server_datas.append((src_path, dest_dir))

# Add data directories and files
# Note: Không đóng gói data/prompts để user có thể tùy chỉnh
added_files = [
    ('client/dist', 'client/dist'),
    ('tray_icon.py', '.'),
    ('version.py', '.'),
    ('update.py', '.'),
]

# .env: only bundle if it exists (not present in CI – user provides it after install)
if os.path.exists('.env'):
    added_files.append(('.env', '.'))

# Add icon file if exists
if os.path.exists('favicon.ico'):
    added_files.append(('favicon.ico', '.'))

# Collect latex2mathml data files (unimathsymbols.txt and other assets)
latex2mathml_datas = []
try:
    latex2mathml_datas = collect_data_files('latex2mathml')
except Exception:
    pass

# Collect mml2omml data files (MML2OMML.XSL - no Office required)
mml2omml_datas = []
try:
    mml2omml_datas = collect_data_files('mml2omml')
except Exception:
    pass

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=server_datas + added_files + latex2mathml_datas + mml2omml_datas,
    hiddenimports=uvicorn_imports + starlette_imports + fastapi_imports + [
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        'starlette',
        'starlette.middleware.base',
        'pydantic',
        'google.cloud.aiplatform',
        'vertexai',
        'vertexai.generative_models',
        'vertexai.generative_models._generative_models',
        'google.genai',
        'google.genai.types',
        'google.api_core',
        'google.api_core.exceptions',
        # Google API Client
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.errors',
        'googleapiclient.http',
        'googleapiclient.model',
        'google_auth_oauthlib',
        'google_auth_oauthlib.flow',
        'google.auth',
        'google.auth.transport',
        'google.auth.transport.requests',
        'google.oauth2',
        'google.oauth2.credentials',
        'google.oauth2.service_account',
        # Other dependencies
        'pandas',
        'openpyxl',
        'pdfplumber',
        'pdf2image',
        'docx',
        'python_docx',
        'PIL',
        'pymupdf',
        'dotenv',
        # API Routes (all routes must be explicitly imported)
        'api.routes.generate',
        'api.routes.questions',
        'api.routes.export',
        'api.routes.regenerate',
        'api.routes.google_drive',
        'api.routes.images',
        'api.routes.update',
        'api.models',
        'api.models.schemas',
        # Legacy route imports
        'routes.generate',
        'routes.questions',
        'routes.export',
        'routes.regenerate',
        'routes.google_drive',
        'routes.images',
        'routes.docx_reader',
        # New services (English generator)
        'services.english_generator_service.english_generator_service',
        'services.english_generator_service.matrix_workflow_service',
        'services.english_generator_service.vertex_async_client',
        'services.exporters.english_docx_generator',
        # Phase APIs
        'api.phase_apis',
        'api.custom_prompts_api',
        # Config
        'config.settings',
        # Services - REMOVED (already included via datas)
        # System tray
        'pystray',
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageEnhance',
        'PIL.ImageFont',
        # Additional dependencies for new features
        'io',
        'pathlib',
        'typing',
        'collections',
        'datetime',
        'json',
        'uuid',
        # LaTeX → OMML math conversion (DOCX equation rendering)
        'latex2mathml',
        'latex2mathml.converter',
        'latex2mathml.commands',
        'latex2mathml.aggregator',
        'latex2mathml.unimathsymbols',
        'latex2mathml.exceptions',
        'latex2mathml.element',
        'latex2mathml.exporter',
        'latex2mathml.math_object',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'mml2omml',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MatrixQuesGen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Show console for logs and debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='favicon.ico',  # Commented out - invalid icon format
)