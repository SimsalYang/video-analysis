# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['src/video2text/__main__.py'],
    pathex=['src'],
    binaries=[
        # Bundled FFmpeg — binaries extracted to dist/video2text/ffmpeg/
        ('vendor/ffmpeg', 'ffmpeg',),
    ],
    datas=[
        # .env file for defaults (contains no secrets by design)
        ('.env.example', '.',),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6',
        # Core dependencies
        'faster_whisper',
        'yt_dlp',
        'ollama',
        'openai',
        'google.genai',
        'dotenv',
        'requests',
        # Internal
        'video2text',
        'video2text.core',
        'video2text.ui',
        'video2text.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'test', 'pytest', 'distutils', 'venv',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Video2Text',
    debug=False,
    bootloader_ignore_signals=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='video2text',
)
