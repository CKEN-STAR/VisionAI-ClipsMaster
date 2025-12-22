#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, shutil
out = {}
# Torch CUDA
try:
    import torch
    out['torch'] = {
        'version': torch.__version__,
        'cuda_available': bool(torch.cuda.is_available()),
        'cuda_version': getattr(torch.version, 'cuda', None),
        'device_count': int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        'current_device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() and torch.cuda.device_count()>0 else None,
    }
except Exception as e:
    out['torch_error'] = str(e)
# nvidia-smi
out['nvidia_smi'] = shutil.which('nvidia-smi')
# llama_cpp build info
llama = {}
try:
    import llama_cpp
    llama['version'] = getattr(llama_cpp, '__version__', None)
    info = None
    try:
        from llama_cpp import _build_info as bi
        if hasattr(bi, 'build_info'):
            info = bi.build_info()
    except Exception as e:
        llama['build_info_error'] = str(e)
    try:
        if info is None and hasattr(llama_cpp, 'build_info'):
            info = llama_cpp.build_info()  # type: ignore[attr-defined]
    except Exception as e:
        llama['build_info_call_error'] = str(e)
    llama['build_info'] = info
except Exception as e:
    llama['import_error'] = str(e)
out['llama_cpp'] = llama
print(json.dumps(out, ensure_ascii=False))

