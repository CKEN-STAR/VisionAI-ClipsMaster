#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小化 GPU 加载烟测：仅加载中文 GGUF 模型并立即卸载，不做长文本生成。
依赖：llama-cpp-python (CUBLAS 构建)、存在可用的 GGUF 模型文件。
"""
import sys, time
from src.core.real_ai_engine import RealAIEngine

if __name__ == "__main__":
    try:
        engine = RealAIEngine()
        ok = engine.load_model('zh')
        print("LOAD_OK=", bool(ok))
        # 记录当前语言与设备
        print("DEVICE=", engine.device)
        # 立即卸载，释放资源
        engine._unload_current_model()
        print("UNLOAD_OK=True")
        sys.exit(0 if ok else 1)
    except Exception as e:
        print("ERROR:", e)
        sys.exit(2)

