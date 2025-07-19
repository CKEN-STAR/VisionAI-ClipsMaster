异常类
=====

基础异常
-------

.. autoclass:: src.utils.exceptions.FileError
   :members:
   :show-inheritance:

文件验证异常
----------

.. autoclass:: src.utils.exceptions.FileValidationError
   :members:
   :show-inheritance:

视频处理异常
----------

.. autoclass:: src.utils.exceptions.VideoError
   :members:
   :show-inheritance:

异常层次结构
----------

.. code-block:: text

   Exception
   └── FileError
       ├── FileValidationError
       │   ├── InvalidFormatError
       │   ├── FileSizeError
       │   └── SecurityViolationError
       └── VideoError
           ├── VideoQualityError
           ├── VideoProcessingError
           └── SyncValidationError

使用示例
-------

.. code-block:: python

   from src.utils.exceptions import FileValidationError, VideoError
   from src.utils.file_checker import VideoValidator

   validator = VideoValidator()

   try:
       is_valid, quality_info = validator.validate_video_quality("video.mp4")
   except FileValidationError as e:
       print(f"文件验证失败: {e}")
   except VideoError as e:
       print(f"视频处理失败: {e}")
   except Exception as e:
       print(f"未知错误: {e}")

错误处理最佳实践
-------------

1. 异常捕获顺序
   - 始终从最具体的异常开始捕获
   - 将通用异常放在最后捕获
   - 避免捕获所有异常后静默处理

2. 错误信息
   - 提供清晰的错误描述
   - 包含相关的上下文信息
   - 记录详细的错误日志

3. 资源清理
   - 使用 try-finally 确保资源释放
   - 优先使用上下文管理器（with 语句）
   - 在异常处理中进行必要的清理工作

4. 异常传播
   - 只在适当的层级处理异常
   - 必要时重新抛出异常
   - 保持异常链的完整性 