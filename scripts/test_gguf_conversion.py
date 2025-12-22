#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试GGUF转换功能
用于验证llama.cpp转换工具是否正确安装和配置
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.converters.model_converter import ModelConverter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_conversion_script():
    """测试转换脚本是否存在"""
    logger.info("=" * 70)
    logger.info("测试1: 检查llama.cpp转换脚本")
    logger.info("=" * 70)
    
    convert_script = project_root / "llama.cpp" / "convert_hf_to_gguf.py"
    
    if convert_script.exists():
        logger.info(f"✅ 转换脚本存在: {convert_script}")
        return True
    else:
        logger.error(f"❌ 转换脚本不存在: {convert_script}")
        logger.error("请运行: git clone https://github.com/ggerganov/llama.cpp.git")
        return False

def test_python_dependencies():
    """测试Python依赖是否安装"""
    logger.info("=" * 70)
    logger.info("测试2: 检查Python依赖")
    logger.info("=" * 70)
    
    required_packages = {
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'numpy': 'NumPy',
        'gguf': 'GGUF',
        'sentencepiece': 'SentencePiece'
    }
    
    all_installed = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            logger.info(f"✅ {name} 已安装")
        except ImportError:
            logger.error(f"❌ {name} 未安装")
            logger.error(f"   请运行: pip install {package}")
            all_installed = False
    
    return all_installed

def test_model_converter():
    """测试ModelConverter类"""
    logger.info("=" * 70)
    logger.info("测试3: 测试ModelConverter类")
    logger.info("=" * 70)
    
    try:
        converter = ModelConverter()
        logger.info(f"✅ ModelConverter初始化成功")
        logger.info(f"   支持的格式: {converter.supported_formats}")
        logger.info(f"   支持的量化: {list(converter.supported_quant.keys())}")
        return True
    except Exception as e:
        logger.error(f"❌ ModelConverter初始化失败: {e}")
        return False

def find_test_model():
    """查找可用的测试模型"""
    logger.info("=" * 70)
    logger.info("测试4: 查找可用的HF模型")
    logger.info("=" * 70)
    
    # 可能的模型路径
    possible_paths = [
        project_root / "models" / "qwen" / "base",
        project_root / "models" / "qwen" / "Qwen3-1.7B-Instruct-INT4-128",
        project_root / "models" / "mistral" / "base",
    ]
    
    for model_path in possible_paths:
        if model_path.exists() and (model_path / "config.json").exists():
            logger.info(f"✅ 找到模型: {model_path}")
            return str(model_path)
    
    logger.warning("⚠️ 未找到可用的HF模型")
    logger.warning("   跳过实际转换测试")
    return None

def test_actual_conversion(model_path: str):
    """测试实际的模型转换"""
    logger.info("=" * 70)
    logger.info("测试5: 执行实际转换（F16格式）")
    logger.info("=" * 70)
    
    try:
        converter = ModelConverter()
        
        # 创建输出目录
        output_dir = project_root / "models" / "test_conversion"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "test_model_f16.gguf"
        
        logger.info(f"输入模型: {model_path}")
        logger.info(f"输出路径: {output_path}")
        logger.info(f"量化类型: F16")
        logger.info("开始转换...")
        
        result = converter.convert_format(
            model_path=model_path,
            output_format='gguf',
            output_path=str(output_path),
            quant_type='F16'
        )
        
        logger.info(f"✅ 转换成功: {result}")
        
        # 验证转换结果
        if os.path.exists(result):
            size_mb = os.path.getsize(result) / 1024 / 1024
            logger.info(f"   文件大小: {size_mb:.2f} MB")
            
            # 清理测试文件
            logger.info("清理测试文件...")
            os.remove(result)
            logger.info("✅ 测试文件已删除")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 转换失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始GGUF转换功能测试")
    logger.info("")
    
    results = []
    
    # 测试1: 检查转换脚本
    results.append(("转换脚本检查", test_conversion_script()))
    
    # 测试2: 检查Python依赖
    results.append(("Python依赖检查", test_python_dependencies()))
    
    # 测试3: 测试ModelConverter
    results.append(("ModelConverter测试", test_model_converter()))
    
    # 测试4: 查找测试模型
    model_path = find_test_model()
    
    # 测试5: 实际转换（如果有模型）
    if model_path:
        results.append(("实际转换测试", test_actual_conversion(model_path)))
    else:
        logger.info("=" * 70)
        logger.info("跳过实际转换测试（无可用模型）")
        logger.info("=" * 70)
    
    # 输出测试结果
    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 测试结果汇总")
    logger.info("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 70)
    
    if all_passed:
        logger.info("🎉 所有测试通过！GGUF转换功能已就绪")
        return 0
    else:
        logger.error("⚠️ 部分测试失败，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())

