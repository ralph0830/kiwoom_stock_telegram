# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller 설정 파일 - 설정 GUI를 단독 실행 파일로 변환

빌드 명령어:
    pyinstaller setup_gui.spec

생성물:
    dist/setup_gui.exe - 단독 실행 파일 (약 15MB)
"""

block_cipher = None

a = Analysis(
    ['setup_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates/.env.template', 'templates'),  # .env 템플릿 파일 포함
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 모듈 제외 (용량 최적화)
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'setuptools',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='설정하기',  # 한글 실행 파일명
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 압축 사용 (용량 감소)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일 경로 (선택)
)
