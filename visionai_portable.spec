# -*- mode: python ; coding: utf-8 -*-
"""
VisionAI-ClipsMaster 便携版打包配置
版本: v1.2.0
创建完整的可移植整合包，包含所有依赖和资源
"""

import os
import sys
from pathlib import Path

block_cipher = None

# 项目根目录
PROJECT_ROOT = os.path.abspath('.')

# 收集所有数据文件
datas = [
    # 配置文件
    ('configs', 'configs'),
    
    # 资源文件
    ('resources', 'resources'),
    ('themes', 'themes'),
    
    # FFmpeg工具
    ('tools/ffmpeg', 'tools/ffmpeg'),
    
    # UI相关
    ('ui', 'ui'),
    
    # 源代码模块（运行时需要）
    ('src', 'src'),
    
    # 模型配置（不包含大模型文件）
    ('models/__init__.py', 'models'),
    ('models/init_models.py', 'models'),
    ('models/narrative_knowledge_base.yaml', 'models'),
    ('models/converters', 'models/converters'),
    ('models/narrative_patterns', 'models/narrative_patterns'),
    
    # 知识库
    ('knowledge_base', 'knowledge_base'),
    
    # 数据目录结构
    ('data/demo_data', 'data/demo_data'),
    ('data/training', 'data/training'),
]

# 隐藏导入（PyInstaller可能无法自动检测的模块）
hiddenimports = [
    # PyQt6相关
    'PyQt6',
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.sip',
    
    # AI/ML相关
    'torch',
    'torch.cuda',
    'transformers',
    'transformers.models.qwen2',
    'numpy',
    'sklearn',
    'sklearn.preprocessing',
    
    # 视频处理
    'cv2',
    'ffmpeg',
    
    # NLP
    'jieba',
    'spacy',
    
    # 系统监控
    'psutil',
    'GPUtil',
    'pynvml',
    'cpuinfo',
    
    # 网络
    'aiohttp',
    'requests',
    
    # 其他
    'PIL',
    'PIL.Image',
    'yaml',
    'tqdm',
    'plotly',
    'matplotlib',
    
    # 项目模块
    'src.core',
    'src.core.real_ai_engine',
    'src.core.cloud_ai_engine',
    'src.core.video_processor',
    'src.core.screenplay_engineer',
    'src.core.srt_parser',
    'src.config',
    'src.config.cloud_api_config',
    'src.ui',
    'src.utils',
    'ui.responsive',
    'ui.components',
    'ui.hardware',
]

# 排除不需要的模块（减小包体积）
excludes = [
    'tkinter',
    'unittest',
    'test',
    'tests',
    'pytest',
    'IPython',
    'jupyter',
    'notebook',
    'tensorboard',
]

a = Analysis(
    ['simple_ui_fixed.py'],
    pathex=[PROJECT_ROOT, os.path.join(PROJECT_ROOT, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='VisionAI-ClipsMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 保留控制台以便查看日志
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: icon='resources/images/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VisionAI-ClipsMaster-Portable',
)
