.. VisionAI-ClipsMaster documentation master file, created by
   sphinx-quickstart on Tue Apr 22 12:28:58 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to VisionAI-ClipsMaster's documentation!
==========================================

VisionAI-ClipsMaster 是一个强大的媒体文件验证和处理工具，专门用于确保视频和图片文件的质量、安全性和合规性。

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   introduction
   installation
   quickstart
   user_guide/index
   api_reference/index
   contributing
   changelog

快速链接
--------

- `GitHub Repository <https://github.com/yourusername/VisionAI-ClipsMaster>`_
- `Issue Tracker <https://github.com/yourusername/VisionAI-ClipsMaster/issues>`_
- `贡献指南 <contributing.html>`_

功能特点
--------

- 文件验证
    - 文件格式验证
    - 文件大小限制
    - 安全策略配置
    - 文件指纹验证

- 视频处理
    - 视频质量检测
    - 视频-字幕同步验证
    - SRT 字幕文件解析
    - 视频帧提取分析

- 图片处理
    - 图片质量验证
    - 水印检测
    - 图片格式支持
    - 图片元数据分析

- 数据管理
    - 训练数据验证
    - 数据集完整性检查
    - 语言隔离验证
    - 自动数据清理

快速开始
--------

安装
^^^^

.. code-block:: bash

   pip install -r requirements.txt

基本使用
^^^^^^^^

.. code-block:: python

   from src.utils.file_checker import VideoValidator

   validator = VideoValidator()
   is_valid, quality_info = validator.validate_video_quality("video.mp4")
   print(f"视频质量检查结果: {quality_info}")

索引和表格
----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

