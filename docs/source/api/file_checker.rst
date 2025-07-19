文件验证器
=========

基础文件验证器
------------

.. autoclass:: src.utils.file_checker.FileValidator
   :members:
   :undoc-members:
   :special-members: __init__
   :show-inheritance:

视频验证器
--------

.. autoclass:: src.utils.file_checker.VideoValidator
   :members:
   :undoc-members:
   :special-members: __init__
   :show-inheritance:

图片验证器
--------

.. autoclass:: src.utils.file_checker.ImageValidator
   :members:
   :undoc-members:
   :special-members: __init__
   :show-inheritance:

工具函数
-------

.. autofunction:: src.utils.file_checker.validate_video_srt_sync

配置示例
-------

.. code-block:: json

   {
       "content_security": {
           "input_validation": {
               "allowed_formats": ["jpg", "png", "mp4", "mov"],
               "min_image_resolution": {
                   "width": 1280,
                   "height": 720
               },
               "min_video_resolution": {
                   "width": 1280,
                   "height": 720
               }
           }
       },
       "resource_limits": {
           "max_file_size": 104857600
       }
   }

使用示例
-------

视频验证示例
^^^^^^^^^^

.. code-block:: python

   from src.utils.file_checker import VideoValidator

   validator = VideoValidator()

   # 检查视频质量
   is_valid, quality_info = validator.validate_video_quality("video.mp4")
   print(f"视频质量检查结果: {quality_info}")

   # 验证视频和字幕同步
   is_synced = validator.validate_video_srt_sync("video.mp4", "subtitle.srt")
   print(f"字幕同步状态: {is_synced}")

图片验证示例
^^^^^^^^^^

.. code-block:: python

   from src.utils.file_checker import ImageValidator

   validator = ImageValidator()

   # 检查图片质量
   is_valid, quality_info = validator.validate_image_quality("image.jpg")
   print(f"图片质量检查结果: {quality_info}")

   # 检测水印
   has_watermark = validator.check_image_watermark("image.jpg")
   print(f"是否包含水印: {has_watermark}")

注意事项
-------

1. 文件格式验证
   - 支持的视频格式：MP4、MOV
   - 支持的图片格式：JPG、PNG
   - 可通过配置文件扩展支持的格式

2. 性能考虑
   - 视频质量检测可能需要较长时间
   - 建议对大文件进行异步处理
   - 可以通过配置文件调整资源限制

3. 错误处理
   - 所有验证方法都会优雅处理异常
   - 详细的错误信息会记录在日志中
   - 建议使用 try-except 块处理可能的异常 