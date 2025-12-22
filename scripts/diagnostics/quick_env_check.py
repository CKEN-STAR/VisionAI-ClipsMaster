import json

info = {}

# llama-cpp-python
try:
    import llama_cpp  # type: ignore
    from llama_cpp import Llama  # noqa: F401
    info['llama_cpp_import'] = True
    info['llama_cpp_version'] = getattr(llama_cpp, '__version__', 'unknown')
except Exception as e:
    info['llama_cpp_import'] = False
    info['llama_cpp_error'] = str(e)

# torch
try:
    import torch  # type: ignore
    info['torch_version'] = torch.__version__
    info['cuda_available'] = bool(torch.cuda.is_available())
    info['cuda_device_count'] = int(torch.cuda.device_count()) if hasattr(torch.cuda, 'device_count') else None
    if hasattr(torch.cuda, 'get_device_name') and torch.cuda.is_available():
        info['cuda_device_0'] = torch.cuda.get_device_name(0)
except Exception as e:
    info['torch_error'] = str(e)

print(json.dumps(info, ensure_ascii=False))

