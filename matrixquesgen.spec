# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all server files
import os
import importlib.util
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# collect_all: hiddenimports (PYZ bytecode) + binaries
uvicorn_datas, uvicorn_binaries, uvicorn_hidden = collect_all('uvicorn')
starlette_datas, starlette_binaries, starlette_hidden = collect_all('starlette')
fastapi_datas, fastapi_binaries, fastapi_hidden = collect_all('fastapi')

# Bulletproof approach: recursively walk the entire package directory tree and
# add EVERY file individually with correct relative dest path.
# (pkg_dir, pkg_name) only copies top-level — subdirs like fastapi/routing.py
# or uvicorn/protocols/http/ would be MISSING without the recursive walk.
import importlib.util

def _pkg_tree_data(pkg_name):
    """Walk entire package tree, return list of (src_file, dest_dir) tuples."""
    try:
        spec = importlib.util.find_spec(pkg_name)
        if spec and spec.submodule_search_locations:
            pkg_dir = list(spec.submodule_search_locations)[0]
            parent  = os.path.dirname(pkg_dir)  # = site-packages
            result  = []
            for root, dirs, files in os.walk(pkg_dir):
                # Skip __pycache__ dirs – not needed
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for fname in files:
                    src  = os.path.join(root, fname)
                    dest = os.path.relpath(root, parent)  # e.g. 'fastapi' or 'fastapi\middleware'
                    result.append((src, dest))
            print(f"  [tree] {pkg_name}: {len(result)} files from {pkg_dir}")
            return result
    except Exception as e:
        print(f"  [tree] WARN {pkg_name}: {e}")
    return []

pkg_dirs = []
for _pkg in ['uvicorn', 'fastapi', 'starlette', 'anyio', 'h11', 'httptools',
             'pydantic', 'pydantic_core', 'click', 'sniffio']:
    pkg_dirs += _pkg_tree_data(_pkg)

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
    binaries=uvicorn_binaries + starlette_binaries + fastapi_binaries,
    datas=server_datas + added_files + latex2mathml_datas + mml2omml_datas
        + uvicorn_datas + starlette_datas + fastapi_datas
        + pkg_dirs,
    hiddenimports=uvicorn_hidden + starlette_hidden + fastapi_hidden + [
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
    runtime_hooks=['hooks/rthook_syspath.py'],
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