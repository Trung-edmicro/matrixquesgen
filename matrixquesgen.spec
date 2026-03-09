# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all server files
import os
import sys
import sysconfig
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# ── Reliable site-packages discovery ──────────────────────────────────────────
# Use sysconfig instead of importlib.util.find_spec() because find_spec can
# behave unexpectedly inside PyInstaller's spec execution context.
_site_packages = sysconfig.get_path('purelib')
print(f"[spec] Python: {sys.executable}")
print(f"[spec] site-packages: {_site_packages}")

def _pkg_tree_data(pkg_name):
    """
    Walk the package directory directly in site-packages.
    Returns list of (src_file, dest_dir) tuples for ALL files in the package tree.
    dest_dir is relative to site-packages so files land at _MEIPASS/<pkg>/<subdir>.
    """
    pkg_dir = os.path.join(_site_packages, pkg_name)
    if not os.path.isdir(pkg_dir):
        print(f"  [tree] ERROR: {pkg_name} NOT FOUND at {pkg_dir} — build will be broken!")
        return []
    result = []
    for root, dirs, files in os.walk(pkg_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fname in files:
            src  = os.path.join(root, fname)
            dest = os.path.relpath(root, _site_packages)
            result.append((src, dest))
    print(f"  [tree] {pkg_name}: {len(result)} files from {pkg_dir}")
    return result

# collect_all: hiddenimports (PYZ bytecode) + binaries + data files
uvicorn_datas, uvicorn_binaries, uvicorn_hidden = collect_all('uvicorn')
starlette_datas, starlette_binaries, starlette_hidden = collect_all('starlette')
fastapi_datas, fastapi_binaries, fastapi_hidden = collect_all('fastapi')

# PIL (Pillow): must use collect_all to pick up binary extension _imaging.pyd.
# Adding only to hiddenimports is not enough — the .pyd needs to be in binaries.
pil_datas, pil_binaries, pil_hidden = collect_all('PIL')

# pystray: collect binaries/data (Win32 backend DLLs etc.)
try:
    pystray_datas, pystray_binaries, pystray_hidden = collect_all('pystray')
except Exception:
    pystray_datas, pystray_binaries, pystray_hidden = [], [], []

# Walk every required package tree and copy all .py files directly into _MEIPASS.
# This guarantees imports work even if PYZ bytecode collection misses something.
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

# Bundle MML2OMML.XSL directly from assets/ (copied from Office at dev time).
# In CI (no Office), this file won't exist and math OMML conversion degrades gracefully.
mml2omml_datas = []
_xsl_src = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'assets', 'MML2OMML.XSL')
if os.path.exists(_xsl_src):
    mml2omml_datas = [(_xsl_src, 'mml2omml')]
    print(f'  [xsl] Bundling MML2OMML.XSL from {_xsl_src}')
else:
    print('  [xsl] WARNING: assets/MML2OMML.XSL not found — math OMML disabled in frozen exe')

# Add server/src to pathex so PyInstaller can analyze server code imports.
# Without this, all api.*, services.*, config.* hiddenimports fail with ERROR.
_server_src = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'server', 'src')

a = Analysis(
    ['launcher.py'],
    pathex=[_server_src],
    binaries=uvicorn_binaries + starlette_binaries + fastapi_binaries
        + pil_binaries + pystray_binaries,
    datas=server_datas + added_files + latex2mathml_datas + mml2omml_datas  # mml2omml = XSL file
        + uvicorn_datas + starlette_datas + fastapi_datas
        + pil_datas + pystray_datas
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
        'docx',          # python-docx installs as 'docx'
        'PIL',
        'dotenv',
        # Server modules — pathex includes server/src so these resolve correctly
        # collect_submodules walks each package and finds all sub-modules
        *collect_submodules('api'),
        *collect_submodules('services'),
        *collect_submodules('config'),
        # System tray (binaries/datas collected above via collect_all)
        # Note: pystray._win32 is covered by *pystray_hidden; explicit entry fails
        # during analysis because PIL's C extension isn't resolved yet at that point.
        'pystray',
        # PIL hidden imports from collect_all (includes _imaging, Image, Draw, etc.)
        *pil_hidden,
        *pystray_hidden,
        # Additional dependencies for new features
        'io',
        'pathlib',
        'typing',
        'collections',
        'datetime',
        'json',
        'uuid',
        # LaTeX → OMML math conversion (DOCX equation rendering)
        # Use collect_submodules for correct list — the old explicit list had wrong
        # names (aggregator, element, exporter, math_object don't exist; real modules
        # are commands, tokenizer, walker, symbols_parser).
        *collect_submodules('latex2mathml'),
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
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
    console=True,  # Show console for logs and debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='favicon.ico',  # Commented out - invalid icon format
)