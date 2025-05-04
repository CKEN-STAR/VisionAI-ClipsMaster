#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
灰度发布系统

提供混剪工具新版本的渐进式发布功能，通过用户分组和权重控制，
逐步将新功能、模型或配置推送给不同用户群体，降低风险并收集反馈。
"""

import os
import json
import time
import random
import logging
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

from src.utils.log_handler import get_logger
from src.versioning.evolution_tracker import EvolutionTracker

# 配置日志
logger = get_logger("canary_release")

class UserGroup:
    """用户分组定义类"""
    
    INTERNAL = "internal"  # 内部测试组
    BETA = "beta"          # 测试用户组
    STABLE = "stable"      # 稳定用户组

    @staticmethod
    def get_all_groups() -> List[str]:
        """获取所有用户组"""
        return [UserGroup.INTERNAL, UserGroup.BETA, UserGroup.STABLE]
    
    @staticmethod
    def get_group_by_user_id(user_id: str) -> str:
        """根据用户ID确定用户所属组
        
        Args:
            user_id: 用户唯一标识符
            
        Returns:
            用户组名称
        """
        # 使用用户ID的哈希值确保分配稳定性
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        
        # 根据哈希值分配用户组，确保内部测试组占5%，测试用户占15%，普通用户占80%
        if hash_value % 100 < 5:
            return UserGroup.INTERNAL
        elif hash_value % 100 < 20:
            return UserGroup.BETA
        else:
            return UserGroup.STABLE


class ReleaseStage:
    """发布阶段定义"""
    
    ALPHA = "alpha"       # 内部测试阶段
    BETA = "beta"         # 公测阶段
    STABLE = "stable"     # 稳定发布阶段
    ROLLBACK = "rollback" # 回滚阶段


class VersionStatus:
    """版本状态定义"""
    
    PENDING = "pending"       # 待发布
    RELEASING = "releasing"   # 发布中
    RELEASED = "released"     # 已发布
    SUSPENDED = "suspended"   # 已暂停
    DEPRECATED = "deprecated" # 已废弃
    ROLLBACKED = "rollbacked" # 已回滚


class CanaryDeployer:
    """灰度发布管理器
    
    负责版本的渐进式发布、监控和回滚等功能
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化灰度发布管理器
        
        Args:
            db_path: 数据库文件路径，可选
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "canary_release_db.json"
        )
        self.tracker = EvolutionTracker(db_path)
        self._ensure_db_exists()
        self.releases = self._load_database()
        
    def _ensure_db_exists(self) -> None:
        """确保数据库文件存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "releases": {},
                    "deployments": [],
                    "metrics": {},
                    "last_updated": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
    
    def _load_database(self) -> Dict[str, Any]:
        """加载数据库内容"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"加载灰度发布数据库失败: {str(e)}")
            return {
                "releases": {},
                "deployments": [],
                "metrics": {},
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_database(self) -> None:
        """保存数据库内容"""
        try:
            self.releases["last_updated"] = datetime.now().isoformat()
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.releases, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存灰度发布数据库失败: {str(e)}")
    
    def create_release(self, 
                      release_id: str,
                      versions: List[str],
                      name: str, 
                      description: str = "",
                      stage: str = ReleaseStage.ALPHA,
                      start_time: Optional[str] = None,
                      end_time: Optional[str] = None) -> Dict[str, Any]:
        """创建新的灰度发布计划
        
        Args:
            release_id: 发布计划ID
            versions: 包含的版本ID列表
            name: 发布计划名称
            description: 发布计划描述
            stage: 初始发布阶段
            start_time: 计划开始时间，ISO格式
            end_time: 计划结束时间，ISO格式
            
        Returns:
            创建结果
        """
        if release_id in self.releases["releases"]:
            return {
                "success": False,
                "message": f"发布计划 {release_id} 已存在"
            }
        
        # 检查所有版本是否存在
        for version_id in versions:
            if not self.tracker.get_version(version_id):
                return {
                    "success": False,
                    "message": f"版本 {version_id} 不存在"
                }
        
        # 默认开始时间为当前时间
        if not start_time:
            start_time = datetime.now().isoformat()
        
        # 默认结束时间为30天后
        if not end_time:
            end_time = (datetime.now() + timedelta(days=30)).isoformat()
        
        release_info = {
            "id": release_id,
            "name": name,
            "description": description,
            "versions": versions,
            "stage": stage,
            "status": VersionStatus.PENDING,
            "start_time": start_time,
            "end_time": end_time,
            "deployments": [],
            "metrics": {
                "success_rate": 1.0,
                "error_count": 0,
                "user_feedback": {}
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.releases["releases"][release_id] = release_info
        self._save_database()
        
        logger.info(f"成功创建灰度发布计划 {release_id}")
        return {
            "success": True,
            "message": f"成功创建灰度发布计划 {release_id}",
            "release_info": release_info
        }
    
    def update_release_status(self, release_id: str, status: str) -> Dict[str, Any]:
        """更新发布计划状态
        
        Args:
            release_id: 发布计划ID
            status: 新状态
            
        Returns:
            更新结果
        """
        if release_id not in self.releases["releases"]:
            return {
                "success": False,
                "message": f"发布计划 {release_id} 不存在"
            }
        
        valid_statuses = [
            VersionStatus.PENDING, 
            VersionStatus.RELEASING,
            VersionStatus.RELEASED,
            VersionStatus.SUSPENDED,
            VersionStatus.DEPRECATED,
            VersionStatus.ROLLBACKED
        ]
        
        if status not in valid_statuses:
            return {
                "success": False,
                "message": f"无效的状态 {status}"
            }
        
        self.releases["releases"][release_id]["status"] = status
        self.releases["releases"][release_id]["updated_at"] = datetime.now().isoformat()
        self._save_database()
        
        logger.info(f"已更新发布计划 {release_id} 状态为 {status}")
        return {
            "success": True,
            "message": f"已更新发布计划 {release_id} 状态为 {status}"
        }
    
    def gradual_release(self, release_id: str, user_groups: List[str]) -> Dict[str, Any]:
        """分阶段为不同用户群发布不同版本
        
        Args:
            release_id: 发布计划ID
            user_groups: 用户组列表
            
        Returns:
            发布结果
        """
        if release_id not in self.releases["releases"]:
            return {
                "success": False,
                "message": f"发布计划 {release_id} 不存在"
            }
        
        release_info = self.releases["releases"][release_id]
        versions = release_info["versions"]
        
        if not versions:
            return {
                "success": False,
                "message": "没有可用的版本进行发布"
            }
        
        deployment_results = []
        
        for i, group in enumerate(user_groups):
            if i == 0:  # 内部测试组
                # 发布最新版本给内部测试组，权重10%
                deployment = self._deploy(versions[0], group, weight=0.1)
                deployment_results.append(deployment)
                
            elif i == 1:  # 测试用户组
                # 发布前3个版本给测试用户组，权重30%
                version_slice = versions[1:4] if len(versions) > 3 else versions[1:]
                deployment = self._deploy(version_slice, group, weight=0.3)
                deployment_results.append(deployment)
                
            else:  # 稳定用户组
                # 发布其余版本给稳定用户组，权重60%
                version_slice = versions[3:] if len(versions) > 3 else []
                if not version_slice and len(versions) > 0:
                    version_slice = [versions[-1]]
                deployment = self._deploy(version_slice, group, weight=0.6)
                deployment_results.append(deployment)
        
        # 更新发布计划状态和部署信息
        release_info["status"] = VersionStatus.RELEASING
        release_info["updated_at"] = datetime.now().isoformat()
        for deployment in deployment_results:
            release_info["deployments"].append(deployment)
            
        self.releases["deployments"].extend(deployment_results)
        self._save_database()
        
        logger.info(f"已为发布计划 {release_id} 完成灰度发布设置")
        return {
            "success": True,
            "message": f"已为发布计划 {release_id} 完成灰度发布设置",
            "deployments": deployment_results
        }
    
    def _deploy(self, 
               versions: Union[str, List[str]], 
               group: str, 
               weight: float = 1.0) -> Dict[str, Any]:
        """执行实际部署操作
        
        Args:
            versions: 版本ID或版本ID列表
            group: 目标用户组
            weight: 部署权重
            
        Returns:
            部署信息
        """
        if isinstance(versions, str):
            versions = [versions]
            
        deployment_id = f"deploy_{int(time.time())}_{random.randint(1000, 9999)}"
        
        deployment_info = {
            "id": deployment_id,
            "versions": versions,
            "user_group": group,
            "weight": weight,
            "status": "active",
            "deployed_at": datetime.now().isoformat(),
            "metrics": {
                "success_count": 0,
                "error_count": 0,
                "usage_count": 0
            }
        }
        
        logger.info(f"已部署版本 {versions} 到用户组 {group}，权重 {weight}")
        return deployment_info
    
    def rollback_release(self, release_id: str, target_version: Optional[str] = None) -> Dict[str, Any]:
        """回滚发布
        
        Args:
            release_id: 发布计划ID
            target_version: 目标回滚版本，如果不指定则回滚到前一个稳定版本
            
        Returns:
            回滚结果
        """
        if release_id not in self.releases["releases"]:
            return {
                "success": False,
                "message": f"发布计划 {release_id} 不存在"
            }
        
        release_info = self.releases["releases"][release_id]
        
        # 如果未指定目标版本，寻找前一个稳定版本
        if not target_version:
            # 获取当前版本的前一个稳定版本
            current_versions = release_info["versions"]
            if current_versions:
                latest_version = current_versions[0]
                version_info = self.tracker.get_version(latest_version)
                if version_info and version_info.get("parent"):
                    target_version = version_info["parent"]
                    
        if not target_version:
            return {
                "success": False,
                "message": "无法确定回滚目标版本"
            }
        
        # 验证目标版本存在
        if not self.tracker.get_version(target_version):
            return {
                "success": False,
                "message": f"目标回滚版本 {target_version} 不存在"
            }
        
        # 执行回滚操作
        rollback_id = f"rollback_{int(time.time())}"
        rollback_info = {
            "id": rollback_id,
            "release_id": release_id,
            "from_versions": release_info["versions"],
            "to_version": target_version,
            "reason": "手动触发回滚",
            "status": "completed",
            "rollback_at": datetime.now().isoformat()
        }
        
        # 更新发布计划状态
        release_info["status"] = VersionStatus.ROLLBACKED
        release_info["updated_at"] = datetime.now().isoformat()
        release_info["rollback"] = rollback_info
        
        # 对所有用户组部署回滚版本
        all_groups = UserGroup.get_all_groups()
        for group in all_groups:
            deployment = self._deploy(target_version, group, weight=1.0)
            release_info["deployments"].append(deployment)
            self.releases["deployments"].append(deployment)
        
        self._save_database()
        
        logger.info(f"已将发布计划 {release_id} 回滚到版本 {target_version}")
        return {
            "success": True,
            "message": f"已将发布计划 {release_id} 回滚到版本 {target_version}",
            "rollback_info": rollback_info
        }
    
    def get_release_info(self, release_id: str) -> Dict[str, Any]:
        """获取发布计划信息
        
        Args:
            release_id: 发布计划ID
            
        Returns:
            发布计划信息
        """
        if release_id not in self.releases["releases"]:
            return {
                "success": False,
                "message": f"发布计划 {release_id} 不存在"
            }
        
        return {
            "success": True,
            "release_info": self.releases["releases"][release_id]
        }
    
    def list_releases(self, status: Optional[str] = None) -> Dict[str, Any]:
        """列出所有发布计划
        
        Args:
            status: 可选的状态筛选
            
        Returns:
            发布计划列表
        """
        releases = self.releases["releases"]
        
        if status:
            filtered_releases = {
                release_id: info 
                for release_id, info in releases.items() 
                if info["status"] == status
            }
            return {
                "success": True,
                "releases": filtered_releases
            }
        
        return {
            "success": True,
            "releases": releases
        }
    
    def report_metrics(self, 
                      deployment_id: str, 
                      success: bool, 
                      error_message: Optional[str] = None,
                      user_id: Optional[str] = None) -> Dict[str, Any]:
        """报告部署指标
        
        Args:
            deployment_id: 部署ID
            success: 是否成功
            error_message: 可选的错误信息
            user_id: 可选的用户ID
            
        Returns:
            报告结果
        """
        # 寻找对应的部署记录
        deployment = None
        for item in self.releases["deployments"]:
            if item["id"] == deployment_id:
                deployment = item
                break
        
        if not deployment:
            return {
                "success": False,
                "message": f"部署记录 {deployment_id} 不存在"
            }
        
        # 更新指标统计
        if success:
            deployment["metrics"]["success_count"] += 1
        else:
            deployment["metrics"]["error_count"] += 1
            if error_message:
                if "error_messages" not in deployment["metrics"]:
                    deployment["metrics"]["error_messages"] = []
                deployment["metrics"]["error_messages"].append({
                    "message": error_message,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                })
        
        deployment["metrics"]["usage_count"] += 1
        
        # 更新对应的发布计划
        for release_id, release_info in self.releases["releases"].items():
            for deploy in release_info["deployments"]:
                if deploy["id"] == deployment_id:
                    # 更新发布计划的指标
                    total_success = sum(d["metrics"].get("success_count", 0) for d in release_info["deployments"])
                    total_error = sum(d["metrics"].get("error_count", 0) for d in release_info["deployments"])
                    total = total_success + total_error
                    
                    if total > 0:
                        release_info["metrics"]["success_rate"] = total_success / total
                    release_info["metrics"]["error_count"] = total_error
                    break
        
        self._save_database()
        
        return {
            "success": True,
            "message": "指标已更新"
        }
    
    def get_user_version(self, user_id: str, release_id: Optional[str] = None) -> Dict[str, Any]:
        """获取特定用户应该使用的版本
        
        Args:
            user_id: 用户ID
            release_id: 可选的发布计划ID，如果不指定则使用最新的活跃发布计划
            
        Returns:
            版本信息
        """
        # 确定用户组
        user_group = UserGroup.get_group_by_user_id(user_id)
        
        # 如果指定了发布计划，使用该计划
        if release_id:
            if release_id not in self.releases["releases"]:
                return {
                    "success": False,
                    "message": f"发布计划 {release_id} 不存在"
                }
            
            release_info = self.releases["releases"][release_id]
            
            # 如果发布计划已回滚，返回回滚版本
            if release_info["status"] == VersionStatus.ROLLBACKED and "rollback" in release_info:
                return {
                    "success": True,
                    "version_id": release_info["rollback"]["to_version"],
                    "user_group": user_group,
                    "release_id": release_id,
                    "is_rollback": True
                }
            
            # 寻找适合用户组的部署
            for deployment in release_info["deployments"]:
                if deployment["user_group"] == user_group and deployment["status"] == "active":
                    # 按权重随机选择是否使用该版本
                    if random.random() <= deployment["weight"]:
                        versions = deployment["versions"]
                        # 如果有多个版本，随机选择一个
                        version_id = random.choice(versions) if isinstance(versions, list) else versions
                        return {
                            "success": True,
                            "version_id": version_id,
                            "user_group": user_group,
                            "release_id": release_id,
                            "deployment_id": deployment["id"]
                        }
        
        # 如果没有指定发布计划或未找到适合的部署，查找最新的活跃发布计划
        active_releases = []
        for rid, rinfo in self.releases["releases"].items():
            if rinfo["status"] == VersionStatus.RELEASING:
                active_releases.append((rid, rinfo))
        
        # 按创建时间排序，最新的优先
        active_releases.sort(key=lambda x: x[1]["created_at"], reverse=True)
        
        if active_releases:
            latest_release_id, latest_release = active_releases[0]
            
            # 查找适合用户组的部署
            for deployment in latest_release["deployments"]:
                if deployment["user_group"] == user_group and deployment["status"] == "active":
                    # 按权重随机选择是否使用该版本
                    if random.random() <= deployment["weight"]:
                        versions = deployment["versions"]
                        # 如果有多个版本，随机选择一个
                        version_id = random.choice(versions) if isinstance(versions, list) else versions
                        return {
                            "success": True,
                            "version_id": version_id,
                            "user_group": user_group,
                            "release_id": latest_release_id,
                            "deployment_id": deployment["id"]
                        }
        
        # 如果没有找到合适的版本，返回最稳定的版本
        stable_versions = self._get_stable_versions()
        if stable_versions:
            return {
                "success": True,
                "version_id": stable_versions[0],
                "user_group": user_group,
                "is_fallback": True
            }
        
        return {
            "success": False,
            "message": "无法确定适合用户的版本"
        }
    
    def _get_stable_versions(self) -> List[str]:
        """获取最稳定的版本列表
        
        Returns:
            稳定版本ID列表，按推荐程度排序
        """
        # 查找已发布且成功率高的版本
        stable_versions = []
        
        for release_id, release_info in self.releases["releases"].items():
            if release_info["status"] == VersionStatus.RELEASED:
                if release_info["metrics"]["success_rate"] > 0.95:
                    for version in release_info["versions"]:
                        if version not in stable_versions:
                            stable_versions.append(version)
        
        return stable_versions


# 演示用例
def demo():
    """演示灰度发布系统的基本功能"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_canary_db.json")
    deployer = CanaryDeployer(db_path)
    
    # 创建一些测试版本进化（通过EvolutionTracker）
    tracker = deployer.tracker
    tracker.add_version("v1.0.0", None, {"name": "初始版本", "features": ["基本混剪功能"]})
    tracker.add_version("v1.1.0", "v1.0.0", {"name": "增强版", "features": ["基本混剪功能", "字幕增强"]})
    tracker.add_version("v1.2.0", "v1.1.0", {"name": "稳定版", "features": ["基本混剪功能", "字幕增强", "稳定性提升"]})
    tracker.add_version("v2.0.0-alpha", "v1.2.0", {"name": "2.0测试版", "features": ["基本混剪功能", "字幕增强", "稳定性提升", "AI创意增强"]})
    
    # 创建灰度发布计划
    deployer.create_release(
        release_id="release_2023q4",
        versions=["v2.0.0-alpha", "v1.2.0", "v1.1.0", "v1.0.0"],
        name="2023年Q4版本发布",
        description="引入AI创意增强功能的灰度发布",
        stage=ReleaseStage.BETA
    )
    
    # 执行灰度发布
    user_groups = UserGroup.get_all_groups()
    deployer.gradual_release("release_2023q4", user_groups)
    
    # 模拟用户获取版本
    test_users = [
        "user_internal_1",
        "user_beta_1",
        "user_stable_1"
    ]
    
    print("\n灰度发布版本分配:")
    print("-" * 50)
    for user_id in test_users:
        result = deployer.get_user_version(user_id, "release_2023q4")
        print(f"用户 {user_id} -> 版本: {result.get('version_id', '未分配')}, 用户组: {result.get('user_group', '未知')}")
    
    # 模拟一段时间后进行回滚
    print("\n执行版本回滚:")
    print("-" * 50)
    rollback_result = deployer.rollback_release("release_2023q4", "v1.2.0")
    print(f"回滚结果: {rollback_result['message']}")
    
    # 回滚后的版本分配
    print("\n回滚后版本分配:")
    print("-" * 50)
    for user_id in test_users:
        result = deployer.get_user_version(user_id, "release_2023q4")
        print(f"用户 {user_id} -> 版本: {result.get('version_id', '未分配')}, 用户组: {result.get('user_group', '未知')}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行演示
    demo() 