"""
剪映导出助手

提供一键导出到剪映的功能：
1. 生成草稿文件
2. 复制到剪映草稿目录
3. 启动剪映应用
"""

import os
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from .jianying_path_detector import get_detector
    from .jianying_draft_generator import JianyingDraftGenerator
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from src.exporters.jianying_path_detector import get_detector
    from src.exporters.jianying_draft_generator import JianyingDraftGenerator

logger = logging.getLogger(__name__)


class JianyingExportHelper:
    """剪映导出助手"""
    
    def __init__(self):
        """初始化导出助手"""
        self.detector = get_detector()
    
    def export_and_launch(
        self,
        draft_generator: JianyingDraftGenerator,
        project_name: Optional[str] = None,
        auto_launch: bool = True
    ) -> Dict[str, Any]:
        """
        导出草稿并启动剪映
        
        Args:
            draft_generator: 草稿生成器实例
            project_name: 项目名称（如果为None，自动生成）
            auto_launch: 是否自动启动剪映
            
        Returns:
            包含导出结果的字典：
            {
                'success': bool,
                'draft_path': str,  # 草稿文件夹路径
                'message': str,     # 结果消息
                'launched': bool    # 是否成功启动剪映
            }
        """
        result = {
            'success': False,
            'draft_path': None,
            'message': '',
            'launched': False
        }
        
        try:
            # 1. 检测剪映草稿目录
            logger.info("检测剪映草稿目录...")
            draft_dir = self.detector.detect_draft_directory()
            
            if not draft_dir:
                result['message'] = "无法检测到剪映草稿目录，请手动设置"
                logger.error(result['message'])
                return result
            
            logger.info(f"检测到剪映草稿目录: {draft_dir}")
            
            # 2. 生成项目名称
            if not project_name:
                project_name = f"VisionAI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 3. 创建临时草稿文件夹
            logger.info(f"创建草稿文件夹: {project_name}")
            temp_dir = Path("data/output/temp_jianying_drafts")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            temp_draft_path = temp_dir / project_name
            draft_generator.create_draft_folder(str(temp_dir), project_name)
            
            # 4. 复制到剪映草稿目录
            logger.info(f"复制草稿到剪映目录: {draft_dir}")
            target_draft_path = Path(draft_dir) / project_name
            
            # 如果目标已存在，先删除
            if target_draft_path.exists():
                logger.warning(f"目标草稿已存在，将被覆盖: {target_draft_path}")
                shutil.rmtree(target_draft_path)
            
            # 复制草稿文件夹
            shutil.copytree(temp_draft_path, target_draft_path)
            logger.info(f"草稿已复制到: {target_draft_path}")
            
            result['success'] = True
            result['draft_path'] = str(target_draft_path)
            result['message'] = f"草稿已成功导出到剪映目录: {target_draft_path}"
            
            # 5. 清理临时文件
            try:
                shutil.rmtree(temp_draft_path)
                logger.info("临时草稿文件已清理")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            
            # 6. 启动剪映（如果需要）
            if auto_launch:
                logger.info("尝试启动剪映...")
                launched = self.launch_jianying()
                result['launched'] = launched
                
                if launched:
                    result['message'] += "\n剪映已成功启动"
                else:
                    result['message'] += "\n剪映启动失败，请手动打开剪映"
            
            return result
            
        except Exception as e:
            logger.error(f"导出失败: {e}", exc_info=True)
            result['success'] = False
            result['message'] = f"导出失败: {str(e)}"
            return result
    
    def launch_jianying(self) -> bool:
        """
        启动剪映应用
        
        Returns:
            是否成功启动
        """
        try:
            # 检测剪映安装路径
            install_path = self.detector.detect_install_path()
            
            if not install_path:
                logger.warning("无法检测到剪映安装路径")
                return False
            
            logger.info(f"启动剪映: {install_path}")
            
            # 启动剪映
            subprocess.Popen([install_path], shell=False)
            logger.info("剪映已成功启动")
            return True
            
        except Exception as e:
            logger.error(f"启动剪映失败: {e}", exc_info=True)
            return False
    
    def copy_draft_to_jianying(
        self,
        source_draft_path: str,
        project_name: Optional[str] = None
    ) -> Optional[str]:
        """
        将已生成的草稿复制到剪映目录
        
        Args:
            source_draft_path: 源草稿文件夹路径
            project_name: 目标项目名称（如果为None，使用源文件夹名称）
            
        Returns:
            目标草稿路径，如果失败返回None
        """
        try:
            # 检测剪映草稿目录
            draft_dir = self.detector.detect_draft_directory()
            
            if not draft_dir:
                logger.error("无法检测到剪映草稿目录")
                return None
            
            # 确定项目名称
            if not project_name:
                project_name = Path(source_draft_path).name
            
            # 目标路径
            target_draft_path = Path(draft_dir) / project_name
            
            # 如果目标已存在，先删除
            if target_draft_path.exists():
                logger.warning(f"目标草稿已存在，将被覆盖: {target_draft_path}")
                shutil.rmtree(target_draft_path)
            
            # 复制草稿文件夹
            shutil.copytree(source_draft_path, target_draft_path)
            logger.info(f"草稿已复制到: {target_draft_path}")
            
            return str(target_draft_path)
            
        except Exception as e:
            logger.error(f"复制草稿失败: {e}", exc_info=True)
            return None
    
    def get_draft_directory(self) -> Optional[str]:
        """
        获取剪映草稿目录
        
        Returns:
            草稿目录路径，如果检测失败返回None
        """
        return self.detector.detect_draft_directory()
    
    def get_install_path(self) -> Optional[str]:
        """
        获取剪映安装路径
        
        Returns:
            安装路径，如果检测失败返回None
        """
        return self.detector.detect_install_path()
    
    def set_draft_directory(self, path: str):
        """
        手动设置草稿目录
        
        Args:
            path: 草稿目录路径
        """
        self.detector.set_draft_directory(path)
    
    def set_install_path(self, path: str):
        """
        手动设置安装路径
        
        Args:
            path: 剪映可执行文件路径
        """
        self.detector.set_install_path(path)


# 便捷函数
def export_to_jianying_and_launch(
    draft_generator: JianyingDraftGenerator,
    project_name: Optional[str] = None,
    auto_launch: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：导出草稿并启动剪映
    
    Args:
        draft_generator: 草稿生成器实例
        project_name: 项目名称
        auto_launch: 是否自动启动剪映
        
    Returns:
        导出结果字典
    """
    helper = JianyingExportHelper()
    return helper.export_and_launch(draft_generator, project_name, auto_launch)


def copy_draft_to_jianying(
    source_draft_path: str,
    project_name: Optional[str] = None
) -> Optional[str]:
    """
    便捷函数：将草稿复制到剪映目录
    
    Args:
        source_draft_path: 源草稿文件夹路径
        project_name: 目标项目名称
        
    Returns:
        目标草稿路径
    """
    helper = JianyingExportHelper()
    return helper.copy_draft_to_jianying(source_draft_path, project_name)


def launch_jianying() -> bool:
    """
    便捷函数：启动剪映
    
    Returns:
        是否成功启动
    """
    helper = JianyingExportHelper()
    return helper.launch_jianying()

