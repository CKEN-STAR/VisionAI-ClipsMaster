"""
VisionAI-ClipsMaster SDK

用于与VisionAI-ClipsMaster API进行交互的Python客户端SDK
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Union, Any, Callable
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("clipsmaster-sdk")

@dataclass
class ClipRequest:
    """剪辑请求参数数据类"""
    video_path: str
    srt_path: str
    lang: str = "zh"  # 默认使用中文模型
    quant_level: str = "Q4_K_M"  # 默认中等量化等级
    export_format: str = "both"  # 默认同时导出视频和工程文件
    max_duration: Optional[float] = None  # 最大输出时长，默认不限制
    narrative_focus: Optional[List[str]] = None  # 叙事重点关键词
    temperature: float = 0.7  # 生成温度(0.1-1.0)
    preserve_segments: Optional[List[Dict[str, float]]] = None  # 必须保留的片段时间点

class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"

class APIError(Exception):
    """API错误异常类"""
    def __init__(self, status_code: int, error_message: str, endpoint: str):
        self.status_code = status_code
        self.error_message = error_message
        self.endpoint = endpoint
        super().__init__(f"API错误 ({status_code}): {error_message} [endpoint: {endpoint}]")

class ClipsMasterClient:
    """VisionAI-ClipsMaster API客户端"""
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间(秒)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ClipsMaster-Python-SDK/1.0.0"
        })
        logger.info(f"已初始化客户端: {self.base_url}")
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整的API URL"""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            files: 文件数据
            params: 查询参数
            retry_count: 当前重试次数
            
        Returns:
            API响应数据
            
        Raises:
            APIError: 如果API请求失败
        """
        url = self._build_url(endpoint)
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                if files:
                    # 如果有文件，使用multipart/form-data
                    response = self.session.post(url, data=data, files=files, timeout=self.timeout)
                else:
                    # 否则使用application/json
                    response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查是否成功
            if response.status_code >= 400:
                logger.error(f"API错误: {response.status_code} - {response.text}")
                error_msg = response.json().get("detail", "未知错误") if response.text else "无响应内容"
                raise APIError(response.status_code, error_msg, endpoint)
            
            return response.json()
            
        except (requests.RequestException, json.JSONDecodeError, APIError) as e:
            # 请求失败，尝试重试
            if retry_count < self.max_retries:
                logger.warning(f"请求失败，正在重试 ({retry_count+1}/{self.max_retries}): {str(e)}")
                time.sleep(self.retry_delay)
                return self._request(method, endpoint, data, files, params, retry_count + 1)
            else:
                if isinstance(e, APIError):
                    raise e
                else:
                    logger.error(f"请求失败: {str(e)}")
                    raise APIError(500, str(e), endpoint)
    
    def get_models_status(self) -> Dict:
        """
        获取模型状态
        
        Returns:
            模型状态信息字典
        """
        return self._request("GET", "/api/v1/models/status")
    
    def generate_clip(
        self,
        video_path: str,
        srt_path: str,
        lang: str = "zh",
        quant_level: str = "Q4_K_M",
        export_format: str = "both",
        max_duration: Optional[float] = None,
        narrative_focus: Optional[List[str]] = None,
        temperature: float = 0.7,
        preserve_segments: Optional[List[Dict[str, float]]] = None
    ) -> Dict:
        """
        创建视频剪辑任务
        
        Args:
            video_path: 视频文件路径
            srt_path: 字幕文件路径
            lang: 语言 ('zh' 或 'en')
            quant_level: 量化等级 ('Q2_K', 'Q4_K_M', 'Q5_K_M', 'Q8_0')
            export_format: 导出格式 ('video', 'project', 'both')
            max_duration: 最大输出时长(秒)
            narrative_focus: 叙事重点关键词列表
            temperature: 生成温度(0.1-1.0)
            preserve_segments: 必须保留的片段时间点列表，格式[{'start': 秒, 'end': 秒}]
            
        Returns:
            任务信息字典
        """
        # 验证文件是否存在
        if not os.path.exists(video_path):
            raise ValueError(f"视频文件不存在: {video_path}")
        if not os.path.exists(srt_path):
            raise ValueError(f"字幕文件不存在: {srt_path}")
        
        # 构建请求数据
        request_data = {
            "video_path": os.path.abspath(video_path),
            "srt_path": os.path.abspath(srt_path),
            "lang": lang,
            "quant_level": quant_level,
            "export_format": export_format,
            "temperature": temperature
        }
        
        # 添加可选参数
        if max_duration is not None:
            request_data["max_duration"] = max_duration
        if narrative_focus is not None:
            request_data["narrative_focus"] = narrative_focus
        if preserve_segments is not None:
            request_data["preserve_segments"] = preserve_segments
        
        # 发送请求
        return self._request("POST", "/api/v1/generate", data=request_data)
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息字典
        """
        return self._request("GET", f"/api/v1/task/{task_id}")
    
    def cancel_task(self, task_id: str) -> Dict:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            操作结果字典
        """
        return self._request("DELETE", f"/api/v1/task/{task_id}")
    
    def batch_generate(
        self,
        clip_requests: List[ClipRequest],
        parallel: int = 1
    ) -> Dict:
        """
        批量创建视频剪辑任务
        
        Args:
            clip_requests: 剪辑请求列表
            parallel: 并行处理数量
            
        Returns:
            批量任务信息字典
        """
        # 构建请求数据
        request_data = {
            "clips": [request.__dict__ for request in clip_requests],
            "parallel": parallel
        }
        
        # 发送请求
        return self._request("POST", "/api/v1/batch", data=request_data)
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """
        获取批量任务状态
        
        Args:
            batch_id: 批次ID
            
        Returns:
            批量任务状态信息字典
        """
        return self._request("GET", f"/api/v1/batch/{batch_id}")
    
    def wait_for_task(
        self, 
        task_id: str, 
        poll_interval: int = 2,
        timeout: Optional[int] = 3600,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔时间(秒)
            timeout: 超时时间(秒)，None表示无限等待
            progress_callback: 进度回调函数，接收进度和消息参数
            
        Returns:
            最终任务状态信息字典
            
        Raises:
            TimeoutError: 如果超过指定超时时间
            RuntimeError: 如果任务失败
        """
        start_time = time.time()
        last_progress = -1
        
        while True:
            # 检查是否超时
            if timeout and (time.time() - start_time > timeout):
                raise TimeoutError(f"任务等待超时: {task_id}")
            
            # 获取任务状态
            task_info = self.get_task_status(task_id)
            status = task_info.get("status")
            progress = task_info.get("progress", 0)
            message = task_info.get("message", "")
            
            # 如果进度变化，调用回调函数
            if progress != last_progress and progress_callback:
                progress_callback(progress, message)
                last_progress = progress
            
            # 检查任务是否完成
            if status == TaskStatus.SUCCESS:
                if progress_callback:
                    progress_callback(1.0, "任务完成")
                return task_info
            elif status == TaskStatus.FAILED:
                error_msg = task_info.get("message", "未知错误")
                raise RuntimeError(f"任务失败: {error_msg}")
            
            # 等待一段时间后再次检查
            time.sleep(poll_interval)
    
    def wait_for_batch(
        self, 
        batch_id: str, 
        poll_interval: int = 5,
        timeout: Optional[int] = 7200,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict:
        """
        等待批量任务完成
        
        Args:
            batch_id: 批次ID
            poll_interval: 轮询间隔时间(秒)
            timeout: 超时时间(秒)，None表示无限等待
            progress_callback: 进度回调函数，接收完成数量、总数量和消息参数
            
        Returns:
            最终批量任务状态信息字典
            
        Raises:
            TimeoutError: 如果超过指定超时时间
            RuntimeError: 如果任务失败
        """
        start_time = time.time()
        last_completed = -1
        
        while True:
            # 检查是否超时
            if timeout and (time.time() - start_time > timeout):
                raise TimeoutError(f"批量任务等待超时: {batch_id}")
            
            # 获取批量任务状态
            batch_info = self.get_batch_status(batch_id)
            status = batch_info.get("status")
            completed = batch_info.get("completed", 0)
            total = batch_info.get("total", 0)
            message = batch_info.get("message", "")
            
            # 如果完成数量变化，调用回调函数
            if completed != last_completed and progress_callback:
                progress_callback(completed, total, message)
                last_completed = completed
            
            # 检查批量任务是否完成
            if status == TaskStatus.SUCCESS:
                if progress_callback:
                    progress_callback(total, total, "所有任务完成")
                return batch_info
            elif status == TaskStatus.FAILED:
                # 批量任务可能部分失败，返回结果供调用者进一步处理
                if progress_callback:
                    progress_callback(completed, total, "部分任务失败")
                return batch_info
            
            # 等待一段时间后再次检查
            time.sleep(poll_interval)
    
    def generate_clip_sync(
        self,
        video_path: str,
        srt_path: str,
        lang: str = "zh",
        quant_level: str = "Q4_K_M",
        export_format: str = "both",
        max_duration: Optional[float] = None,
        narrative_focus: Optional[List[str]] = None,
        temperature: float = 0.7,
        preserve_segments: Optional[List[Dict[str, float]]] = None,
        poll_interval: int = 2,
        timeout: Optional[int] = 3600,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict:
        """
        创建视频剪辑任务并同步等待完成
        
        Args:
            video_path: 视频文件路径
            srt_path: 字幕文件路径
            lang: 语言 ('zh' 或 'en')
            quant_level: 量化等级 ('Q2_K', 'Q4_K_M', 'Q5_K_M', 'Q8_0')
            export_format: 导出格式 ('video', 'project', 'both')
            max_duration: 最大输出时长(秒)
            narrative_focus: 叙事重点关键词列表
            temperature: 生成温度(0.1-1.0)
            preserve_segments: 必须保留的片段时间点列表，格式[{'start': 秒, 'end': 秒}]
            poll_interval: 轮询间隔时间(秒)
            timeout: 超时时间(秒)，None表示无限等待
            progress_callback: 进度回调函数，接收进度和消息参数
            
        Returns:
            最终任务状态信息字典
        """
        # 创建任务
        task_response = self.generate_clip(
            video_path=video_path,
            srt_path=srt_path,
            lang=lang,
            quant_level=quant_level,
            export_format=export_format,
            max_duration=max_duration,
            narrative_focus=narrative_focus,
            temperature=temperature,
            preserve_segments=preserve_segments
        )
        
        task_id = task_response.get("task_id")
        logger.info(f"已创建任务: {task_id}")
        
        # 等待任务完成
        return self.wait_for_task(
            task_id=task_id,
            poll_interval=poll_interval,
            timeout=timeout,
            progress_callback=progress_callback
        )

# 示例用法
if __name__ == "__main__":
    # 示例代码（使用时请替换为实际API密钥和文件路径）
    client = ClipsMasterClient(api_key="user_dev_key")
    
    # 检查模型状态
    model_status = client.get_models_status()
    print("模型状态:", json.dumps(model_status, ensure_ascii=False, indent=2))
    
    # 定义进度回调函数
    def on_progress(progress, message):
        print(f"进度: {progress*100:.1f}% - {message}")
    
    # 生成视频剪辑并等待完成
    try:
        result = client.generate_clip_sync(
            video_path="examples/video.mp4",
            srt_path="examples/subtitle.srt",
            progress_callback=on_progress
        )
        print("剪辑完成!")
        print(f"项目文件: {result.get('project_path')}")
        print(f"视频文件: {result.get('video_path')}")
    except Exception as e:
        print(f"剪辑失败: {str(e)}") 