
def lazy_import(module_name):
    """延迟导入装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not hasattr(wrapper, '_module'):
                wrapper._module = __import__(module_name, fromlist=[''])
            return func(wrapper._module, *args, **kwargs)
        return wrapper
    return decorator
