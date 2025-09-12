#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动增强UI
Start Enhanced UI
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入并启动UI
if __name__ == "__main__":
    try:
        from enhanced_ui import main
        main()
    except Exception as e:
        print(f"UI启动失败: {e}")
        import traceback
        traceback.print_exc()
