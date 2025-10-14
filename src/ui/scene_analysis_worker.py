"""
场景分析后台Worker
在后台线程中执行场景分析,避免阻塞UI
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import List, Dict, Any, Optional

from src.utils.log_handler import get_logger

logger = get_logger("scene_analysis_worker")


class SceneAnalysisWorker(QObject):
    """场景分析后台Worker"""
    
    # 信号
    started = pyqtSignal()  # 开始分析
    progress = pyqtSignal(int, str)  # 进度更新(百分比, 消息)
    finished = pyqtSignal(list)  # 分析完成(场景列表)
    error = pyqtSignal(str)  # 发生错误
    
    def __init__(self, video_path: str, subtitle_data: Optional[List[Dict[str, Any]]] = None):
        """初始化Worker
        
        Args:
            video_path: 视频文件路径
            subtitle_data: 字幕数据(可选)
        """
        super().__init__()
        self.video_path = video_path
        self.subtitle_data = subtitle_data
        self._is_cancelled = False
    
    def run(self):
        """执行场景分析"""
        try:
            logger.info(f"开始后台场景分析: {self.video_path}")
            self.started.emit()
            
            # 延迟导入SceneAnalyzer
            from src.alignment.scene_analyzer import SceneAnalyzer
            
            # 创建分析器
            analyzer = SceneAnalyzer(
                min_scene_duration=1.0,
                scene_threshold=30.0,
                use_external_models=False
            )
            
            # 检查是否取消
            if self._is_cancelled:
                logger.info("场景分析已取消")
                return
            
            # 发送进度
            self.progress.emit(10, "正在检查缓存...")
            
            # 分析视频(自动使用缓存)
            scenes = analyzer.analyze_video(
                video_path=self.video_path,
                subtitle_data=self.subtitle_data,
                use_cache=True
            )
            
            # 检查是否取消
            if self._is_cancelled:
                logger.info("场景分析已取消")
                return
            
            # 发送进度
            self.progress.emit(100, f"分析完成: {len(scenes)}个场景")
            
            # 发送完成信号
            self.finished.emit(scenes)
            logger.info(f"场景分析完成: {len(scenes)}个场景")
            
        except Exception as e:
            logger.error(f"场景分析失败: {e}", exc_info=True)
            self.error.emit(str(e))
    
    def cancel(self):
        """取消分析"""
        self._is_cancelled = True
        logger.info("请求取消场景分析")


def start_background_scene_analysis(
    video_path: str,
    subtitle_data: Optional[List[Dict[str, Any]]] = None,
    on_finished: Optional[callable] = None,
    on_progress: Optional[callable] = None,
    on_error: Optional[callable] = None
) -> tuple[QThread, SceneAnalysisWorker]:
    """启动后台场景分析
    
    Args:
        video_path: 视频文件路径
        subtitle_data: 字幕数据(可选)
        on_finished: 完成回调函数
        on_progress: 进度回调函数
        on_error: 错误回调函数
        
    Returns:
        (线程对象, Worker对象)
    """
    # 创建线程和Worker
    thread = QThread()
    worker = SceneAnalysisWorker(video_path, subtitle_data)
    worker.moveToThread(thread)
    
    # 连接信号
    if on_finished:
        worker.finished.connect(on_finished)
    if on_progress:
        worker.progress.connect(on_progress)
    if on_error:
        worker.error.connect(on_error)
    
    # 连接线程信号
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)
    
    # 启动线程
    thread.start()
    
    logger.info(f"后台场景分析已启动: {video_path}")
    return thread, worker

