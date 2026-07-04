# PyInstaller spec for the EXO backend (onedir bundle).
#
# Build from this directory:
#   pyinstaller --clean --noconfirm exo-backend.spec
#
# Produces dist/exo-backend/ containing the exo-backend executable, which the
# packaged Electron app ships as an extraResource and spawns at startup.

from PyInstaller.utils.hooks import collect_submodules

# uvicorn and the app package rely on dynamic imports; collect them explicitly.
hidden_imports = (
    collect_submodules("app")
    + collect_submodules("uvicorn")
    + [
        "aiosqlite",
        "anyio",
        "websockets",
        "tzdata",
        "sqlalchemy.dialects.sqlite",
    ]
)

analysis = Analysis(
    ["exo_backend.py"],
    pathex=[".."],  # make the top-level ``app`` package importable
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "mypy", "black", "ruff"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="exo-backend",
    console=True,
    disable_windowed_traceback=False,
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    name="exo-backend",
)
