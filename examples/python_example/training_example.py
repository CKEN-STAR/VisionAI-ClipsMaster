"""
ClipsMaster Python 训练示例

演示如何使用投喂训练功能来优化大模型生成爆款视频的能力:
1. 准备原片字幕和对应的爆款字幕
2. 创建训练样本
3. 对模型进行微调训练
4. 验证训练效果

使用说明:
- 需准备 test_data/sample.srt (原片字幕) 和 test_data/sample_hit.srt (爆款字幕)
- 确保系统已正确安装配置 (内存≥4GB)
"""
import sys
import os
import time
import json
from pathlib import Path

# 添加SDK路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sdk')))
from clipsmaster_sdk import ClipsMasterClient

# 添加核心模块路径（专用于训练功能）
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from training.zh_trainer import ZhTrainer
from training.data_augment import DataAugmenter
from training.data_splitter import DataSplitter
from utils.memory_guard import MemoryGuard

# 文件路径
SAMPLE_SRT = "test_data/sample.srt"           # 原片字幕
SAMPLE_HIT_SRT = "test_data/sample_hit.srt"   # 爆款字幕
TRAINING_DIR = "test_data/training_output"    # 训练输出目录
MODEL_OUTPUT_DIR = "test_data/trained_model"  # 训练后模型保存目录

def prepare_directories():
    """准备训练相关目录"""
    os.makedirs(TRAINING_DIR, exist_ok=True)
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(TRAINING_DIR, "augmented"), exist_ok=True)

def create_training_sample():
    """创建训练样本对"""
    print("=== 创建训练样本 ===")
    
    if not os.path.exists(SAMPLE_SRT) or not os.path.exists(SAMPLE_HIT_SRT):
        print(f"错误: 未找到示例字幕文件")
        return False
    
    # 读取字幕内容
    with open(SAMPLE_SRT, "r", encoding="utf-8") as f:
        original_content = f.read()
    
    with open(SAMPLE_HIT_SRT, "r", encoding="utf-8") as f:
        hit_content = f.read()
    
    # 创建训练样本
    sample = {
        "original_srt": original_content,
        "hit_srt": hit_content,
        "metadata": {
            "source": "demo",
            "difficulty": "basic",
            "language": "zh",
            "style": "viral"
        }
    }
    
    # 保存样本文件
    sample_path = os.path.join(TRAINING_DIR, "sample_pair.json")
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    
    print(f"样本创建完成，保存至: {sample_path}")
    return sample_path

def augment_training_data(sample_path):
    """数据增强"""
    print("\n=== 数据增强 ===")
    
    augmenter = DataAugmenter()
    augmented_samples = []
    
    # 加载原始样本
    with open(sample_path, "r", encoding="utf-8") as f:
        original_sample = json.load(f)
    
    # 数据增强 (演示模式)
    print("正在进行数据增强...")
    
    # 增强方式1: 同义词替换
    aug_sample1 = augmenter.synonym_replacement(original_sample)
    aug_path1 = os.path.join(TRAINING_DIR, "augmented", "aug_synonym.json")
    with open(aug_path1, "w", encoding="utf-8") as f:
        json.dump(aug_sample1, f, ensure_ascii=False, indent=2)
    augmented_samples.append(aug_path1)
    
    # 增强方式2: 情节变异
    aug_sample2 = augmenter.plot_variation(original_sample)
    aug_path2 = os.path.join(TRAINING_DIR, "augmented", "aug_plot.json")
    with open(aug_path2, "w", encoding="utf-8") as f:
        json.dump(aug_sample2, f, ensure_ascii=False, indent=2)
    augmented_samples.append(aug_path2)
    
    print(f"数据增强完成，生成 {len(augmented_samples)} 个增强样本")
    return [sample_path] + augmented_samples

def train_model(sample_paths):
    """模型训练"""
    print("\n=== 模型训练 ===")
    
    # 初始化训练器 (仅中文示例)
    trainer = ZhTrainer()
    
    # 设置训练参数
    train_params = {
        "epochs": 3,
        "batch_size": 1,
        "learning_rate": 2e-5,
        "weight_decay": 0.01,
        "max_steps": 10,
        "eval_steps": 5,
        "save_steps": 10,
        "output_dir": MODEL_OUTPUT_DIR
    }
    
    # 设置内存优化
    memory_guard = MemoryGuard()
    memory_guard.set_optimization_level("high")
    
    # 数据分割
    data_splitter = DataSplitter()
    train_data, eval_data = data_splitter.split_data(sample_paths, ratio=0.7)
    
    # 开始训练 (演示模式)
    print("\n模拟训练过程 (实际训练需要更多样本):")
    print(f"训练样本数: {len(train_data)}")
    print(f"验证样本数: {len(eval_data)}")
    print("训练参数:", json.dumps(train_params, indent=2))
    
    # 模拟训练循环
    for epoch in range(1, train_params["epochs"] + 1):
        print(f"\nEpoch {epoch}/{train_params['epochs']}:")
        
        # 模拟每个样本的训练
        for i, sample_path in enumerate(train_data, 1):
            # 模拟批次训练
            for step in range(1, min(5, train_params["max_steps"]) + 1):
                loss = 0.5 / (epoch + step * 0.1)  # 模拟损失下降
                print(f"  步骤 {step}: 样本={os.path.basename(sample_path)}, 损失={loss:.4f}")
                time.sleep(0.2)  # 模拟训练时间
        
        # 模拟验证
        eval_loss = 0.4 / epoch  # 模拟验证损失
        print(f"  验证损失: {eval_loss:.4f}")
    
    # 模拟保存模型
    model_path = os.path.join(MODEL_OUTPUT_DIR, "model_final.safetensors")
    with open(model_path, "w") as f:
        f.write("# 模拟训练后模型文件 (仅用于演示)")
    
    print(f"\n训练完成! 模型保存至: {model_path}")
    print("注意: 这是演示模式，实际训练需要更多样本数据和更长时间")
    
    return model_path

def verify_training_effect():
    """验证训练效果"""
    print("\n=== 训练效果验证 ===")
    
    # 在实际系统中，这里会加载原始模型和训练后的模型进行对比测试
    # 为了演示，我们只是模拟测试过程
    
    test_cases = [
        "男主角面临人生抉择",
        "两个角色发生激烈冲突",
        "感人的和解场景"
    ]
    
    print("测试用例:")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: '{test}'")
        
        # 模拟原始模型输出
        print("  原始模型: '主角需要做决定，情节发展...'")
        
        # 模拟训练后模型输出
        print("  训练后模型: '【震撼】主角5秒内必须抉择！结局惊人...'")
        
        # 模拟评分提升
        original_score = 6.5
        new_score = 8.7
        print(f"  爆款指数: {original_score} → {new_score} (+{new_score-original_score:.1f})")
        
        time.sleep(0.5)  # 演示暂停
    
    print("\n验证结论: 训练后的模型在爆款指数上平均提升 2.1 分")
    return True

def export_trained_model():
    """导出训练模型"""
    print("\n=== 导出训练模型 ===")
    
    # 模拟导出过程
    print("正在导出训练模型...")
    time.sleep(1)
    
    # 创建量化版本
    quantized_path = os.path.join(MODEL_OUTPUT_DIR, "model_final_q4.bin")
    with open(quantized_path, "w") as f:
        f.write("# 模拟量化后模型文件 (仅用于演示)")
    
    # 创建配置文件
    config_path = os.path.join(MODEL_OUTPUT_DIR, "config.json")
    config = {
        "model_type": "viral_generator",
        "language": "zh",
        "training_samples": 3,
        "style": "viral",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "performance": {
            "viral_score_improvement": 2.1,
            "memory_usage": "3.7GB"
        }
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"模型导出完成!")
    print(f"- 量化模型: {quantized_path}")
    print(f"- 配置文件: {config_path}")
    
    # 提示如何使用
    print("\n使用方式: 将训练后的模型复制到 models/qwen/finetuned/ 目录")
    
    return True

if __name__ == "__main__":
    print("====== ClipsMaster 训练示例 ======\n")
    
    # 准备目录
    prepare_directories()
    
    # 创建训练样本
    sample_path = create_training_sample()
    if not sample_path:
        print("无法创建训练样本，退出")
        sys.exit(1)
    
    # 数据增强
    all_samples = augment_training_data(sample_path)
    
    # 训练模型
    model_path = train_model(all_samples)
    
    # 验证训练效果
    verify_training_effect()
    
    # 导出训练模型
    export_trained_model()
    
    print("\n====== 训练示例完成 ======")
    print("注意: 这是演示程序，完整功能需在实际系统中使用")
    print(f"输出目录: {os.path.abspath(TRAINING_DIR)}")
    print(f"模型目录: {os.path.abspath(MODEL_OUTPUT_DIR)}") 