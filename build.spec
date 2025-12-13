# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将Python脚本批量执行工具打包成可执行文件
Python 3.8+ / PyQt5
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 导入版本信息
sys.path.insert(0, os.path.abspath('.'))
from version import get_version_string, APP_INFO

# 应用信息
app_name = 'OBC-DCDC-AutoTest'  # 使用固定名称，避免空格问题
app_version = get_version_string()

# 数据文件
datas = [
    ('AppCode/config/app_config.json', 'AppCode/config'),
    ('config/app_config.json', 'config'),
    ('version.py', '.'),
    ('README.md', '.'),
    ('requirements.txt', '.'),
]

# 隐藏导入
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.sip',
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'bcrypt',
    'cryptography',
]

# 收集所有AppCode子模块
hiddenimports.extend(collect_submodules('AppCode'))

# 二进制文件
binaries = []

# 排除的模块（减小打包体积）
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    # 'tkinter',  # 不排除tkinter，某些模块可能需要它
    'test',
    'unittest',
    'pytest',
    'PyQt6',  # 排除PyQt6
]

# Analysis配置
a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ配置
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

# EXE配置
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    version_file='version_info.txt' if os.path.exists('version_info.txt') else None,
)

# COLLECT配置（目录模式）
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# 如果是Windows平台，可以创建单文件模式
if sys.platform == 'win32':
    # 单文件模式（可选）
    # exe_onefile = EXE(
    #     pyz,
    #     a.scripts,
    #     a.binaries,
    #     a.zipfiles,
    #     a.datas,
    #     [],
    #     name=f'{app_name}_Portable',
    #     debug=False,
    #     bootloader_ignore_signals=False,
    #     strip=False,
    #     upx=True,
    #     upx_exclude=[],
    #     runtime_tmpdir=None,
    #     console=False,
    #     disable_windowed_traceback=False,
    #     argv_emulation=False,
    #     target_arch=None,
    #     codesign_identity=None,
    #     entitlements_file=None,
    #     icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
    # )
    pass

# macOS应用包配置
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
        bundle_identifier=f'com.{app_name.lower()}.app',
        version=app_version,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': app_version,
            'CFBundleVersion': app_version,
        },
    )