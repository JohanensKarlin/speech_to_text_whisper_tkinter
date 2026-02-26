# PyInstaller spec: Build von SpeechToText.exe (einzelne EXE, ohne Konsole)
# Erstellen: build.bat ausfuehren (aus Repo-Root). Ausgabe: dist\SpeechToText.exe
# Hinweis: *.spec ist in .gitignore – bei Bedarf neu generieren mit:
#   pyinstaller --onefile --windowed --name=SpeechToText speech_to_text.py
#   dann manuell recursive-copy-metadata und hidden-import ergaenzen.

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

my_datas = [
    (r'..\.venv\Lib\site-packages\_sounddevice_data\portaudio-binaries\*', '_sounddevice_data/portaudio-binaries')
]
my_datas += collect_data_files('sounddevice')
my_datas += collect_data_files('customtkinter')

my_binaries = []
my_binaries += collect_dynamic_libs('sounddevice')

block_cipher = None

a = Analysis(
    [r'..\speech_to_text.py'],
    pathex=[],
    binaries=my_binaries,
    datas=my_datas,
    hiddenimports=['openai', 'tqdm', 'sounddevice', 'numpy', 'cffi', 'httpx'],
    hookspath=[],
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
    name='SpeechToText',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
