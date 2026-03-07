"""
Custom PyInstaller hook for uvicorn.
uvicorn uses importlib.import_module() at runtime to load protocol handlers,
so PyInstaller cannot auto-detect them through static analysis.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('uvicorn')

# Ensure all submodules are explicitly listed as fallback
hiddenimports += collect_submodules('uvicorn')

# Remove duplicates
hiddenimports = list(set(hiddenimports))
