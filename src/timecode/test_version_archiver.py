import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

# 添加父目录到Python路径，以便导入模块
current_dir = Path(__file__).resolve().parent
if str(current_dir.parent) not in sys.path:
    sys.path.append(str(current_dir.parent))

from timecode.version_archiver import TimelineArchiver

def test_timeline_archiver():
    """测试时间轴存档功能"""
    
    # 创建临时目录用于测试
    test_dir = tempfile.mkdtemp()
    try:
        print(f"\n测试环境: {test_dir}")
        
        # 初始化存档器
        archiver = TimelineArchiver("test_project", test_dir)
        print("✓ 初始化时间轴存档器完成")
        
        # 创建测试场景数据
        scenes1 = [
            {
                "id": "scene1",
                "start_time": 0.0,
                "end_time": 10.5,
                "text": "这是第一个场景",
                "emotion": "neutral"
            },
            {
                "id": "scene2",
                "start_time": 10.5,
                "end_time": 20.0,
                "text": "这是第二个场景",
                "emotion": "happy"
            }
        ]
        
        # 测试保存版本
        version1_id = archiver.save_version(scenes1, "初始版本")
        print(f"✓ 保存初始版本: {version1_id}")
        
        # 测试加载版本
        loaded_scenes = archiver.load_version(version1_id)
        assert loaded_scenes == scenes1, "加载的场景与保存的不匹配"
        print("✓ 加载版本成功")
        
        # 测试版本列表
        version_list = archiver.get_version_list()
        assert len(version_list) == 1, "版本列表长度应为1"
        assert version_list[0]["version_id"] == version1_id, "版本ID不匹配"
        print("✓ 获取版本列表成功")
        
        # 测试保存修改后的版本
        scenes2 = scenes1.copy()
        scenes2.append({
            "id": "scene3",
            "start_time": 20.0,
            "end_time": 35.0,
            "text": "这是新增的第三个场景",
            "emotion": "excited"
        })
        
        version2_id = archiver.save_version(scenes2, "添加第三个场景")
        print(f"✓ 保存修改版本: {version2_id}")
        
        # 测试重复保存相同内容
        duplicate_id = archiver.save_version(scenes2, "相同内容不同注释")
        assert duplicate_id == version2_id, "相同内容应返回相同版本ID"
        print("✓ 重复保存检测成功")
        
        # 测试版本比较
        comparison = archiver.compare_versions(version1_id, version2_id)
        assert comparison["scene_diff"] == 1, "场景差异应为1"
        assert comparison["total_duration_diff"] == 15.0, "时长差异应为15.0"
        print("✓ 版本比较成功")
        
        # 测试导出版本
        export_path = os.path.join(test_dir, "exported_version.json")
        export_success = archiver.export_version(version2_id, export_path)
        assert export_success, "导出版本失败"
        assert os.path.exists(export_path), "导出文件不存在"
        print("✓ 导出版本成功")
        
        # 测试导入版本
        # 先创建新的存档器
        new_archiver = TimelineArchiver("import_test", test_dir)
        imported_id = new_archiver.import_version(export_path, "从其他项目导入")
        assert imported_id is not None, "导入版本失败"
        imported_scenes = new_archiver.load_version(imported_id)
        assert len(imported_scenes) == len(scenes2), "导入的场景数量不匹配"
        print("✓ 导入版本成功")
        
        # 测试删除版本
        # 先保存一个新版本，以便有多个版本可删除
        scenes3 = scenes2.copy()
        scenes3[0]["text"] = "这是修改后的第一个场景"
        version3_id = new_archiver.save_version(scenes3, "修改第一个场景")
        
        delete_success = new_archiver.delete_version(imported_id)
        assert delete_success, "删除版本失败"
        assert imported_id not in new_archiver.history, "版本未从历史记录中删除"
        print("✓ 删除版本成功")
        
        # 测试获取当前版本
        current_version = new_archiver.get_current_version()
        assert current_version is not None, "获取当前版本失败"
        assert current_version["metadata"]["version_id"] == version3_id, "当前版本ID不匹配"
        print("✓ 获取当前版本成功")
        
        print("\n✅ 所有测试通过!")
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"✓ 清理测试环境: {test_dir}")

if __name__ == "__main__":
    test_timeline_archiver() 