#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 真实训练转换器
将模拟训练转换为真实机器学习训练
"""

import os
import re
import time
import torch
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

class RealTrainingConverter:
    """真实训练转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
        print("🔄 VisionAI-ClipsMaster 真实训练转换器")
        print("=" * 50)
    
    def generate_real_zh_trainer_code(self) -> str:
        """生成真实的中文训练器代码"""
        return '''
    def train(self, training_data: List[Dict[str, Any]], 
              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """执行真实的中文模型训练"""
        start_time = time.time()
        
        try:
            # 检查依赖
            try:
                from transformers import (
                    AutoTokenizer, AutoModelForCausalLM, 
                    Trainer, TrainingArguments, DataCollatorForLanguageModeling
                )
                from peft import LoraConfig, get_peft_model, TaskType
                from datasets import Dataset
                import torch
            except ImportError as e:
                return {"success": False, "error": f"缺少必需依赖: {e}"}
            
            if progress_callback:
                progress_callback(0.05, "初始化中文训练环境...")
            
            # 验证训练数据
            if not training_data or len(training_data) == 0:
                return {"success": False, "error": "训练数据为空"}
            
            if progress_callback:
                progress_callback(0.1, "加载中文模型...")
            
            # 1. 加载模型和分词器 - 使用较小的模型以适配4GB内存
            model_name = "Qwen/Qwen2-1.5B-Instruct"  # 使用1.5B版本以适配内存限制
            
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    cache_dir="./models/cache"
                )
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.use_gpu and torch.cuda.is_available() else torch.float32,
                    device_map="auto" if self.use_gpu and torch.cuda.is_available() else None,
                    trust_remote_code=True,
                    cache_dir="./models/cache"
                )
                
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                    
            except Exception as e:
                return {"success": False, "error": f"模型加载失败: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.2, "配置LoRA微调...")
            
            # 2. 配置LoRA - 使用项目配置的参数
            try:
                lora_config = LoraConfig(
                    r=16,  # 项目配置的rank
                    lora_alpha=32,  # 项目配置的alpha
                    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
                    lora_dropout=0.1,
                    bias="none",
                    task_type=TaskType.CAUSAL_LM
                )
                model = get_peft_model(model, lora_config)
                model.print_trainable_parameters()
                
            except Exception as e:
                return {"success": False, "error": f"LoRA配置失败: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.3, "准备训练数据...")
            
            # 3. 准备数据集 - 使用项目的数据处理逻辑
            try:
                processed_data = self.prepare_chinese_data(training_data)
                texts = []
                
                for item in processed_data["samples"]:
                    # 构建训练文本 - 原片→爆款的学习格式
                    text = f"原始剧本: {item['original']}\\n爆款剧本: {item['viral']}{tokenizer.eos_token}"
                    texts.append(text)
                
                if len(texts) == 0:
                    return {"success": False, "error": "没有有效的训练样本"}
                
                def tokenize_function(examples):
                    return tokenizer(
                        examples["text"],
                        truncation=True,
                        padding=True,
                        max_length=512,  # 适配内存限制
                        return_tensors="pt"
                    )
                
                dataset = Dataset.from_dict({"text": texts})
                tokenized_dataset = dataset.map(
                    tokenize_function, 
                    batched=True,
                    remove_columns=dataset.column_names
                )
                
            except Exception as e:
                return {"success": False, "error": f"数据准备失败: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.4, "配置训练参数...")
            
            # 4. 配置训练参数 - 适配4GB内存
            try:
                training_args = TrainingArguments(
                    output_dir="./results_zh",
                    num_train_epochs=3,
                    per_device_train_batch_size=1,  # 4GB内存兼容
                    gradient_accumulation_steps=8,  # 项目配置
                    learning_rate=2e-5,
                    warmup_steps=100,
                    logging_steps=10,
                    save_steps=500,
                    save_total_limit=2,
                    prediction_loss_only=True,
                    remove_unused_columns=False,
                    dataloader_pin_memory=False,
                    fp16=self.use_gpu and torch.cuda.is_available(),
                    report_to=None,  # 禁用wandb等报告
                    load_best_model_at_end=False,
                    metric_for_best_model=None
                )
                
                # 数据整理器
                data_collator = DataCollatorForLanguageModeling(
                    tokenizer=tokenizer,
                    mlm=False,  # 因果语言模型
                )
                
            except Exception as e:
                return {"success": False, "error": f"训练参数配置失败: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.5, "开始真实训练...")
            
            # 5. 创建训练器并执行真实训练
            try:
                trainer = Trainer(
                    model=model,
                    args=training_args,
                    train_dataset=tokenized_dataset,
                    tokenizer=tokenizer,
                    data_collator=data_collator
                )
                
                # 执行真实训练 - 这里是关键的真实机器学习过程
                train_result = trainer.train()
                
            except Exception as e:
                return {"success": False, "error": f"训练执行失败: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.9, "保存训练模型...")
            
            # 6. 保存模型
            try:
                os.makedirs("./results_zh", exist_ok=True)
                trainer.save_model()
                tokenizer.save_pretrained("./results_zh")
                
            except Exception as e:
                return {"success": False, "error": f"模型保存失败: {str(e)}"}
            
            end_time = time.time()
            
            # 7. 生成训练结果
            result = {
                "success": True,
                "training_type": "REAL_ML_TRAINING",
                "model_name": self.model_name,
                "language": self.language,
                "training_duration": end_time - start_time,
                "train_loss": float(train_result.training_loss),
                "global_step": train_result.global_step,
                "samples_processed": len(training_data),
                "device": "cuda" if self.use_gpu and torch.cuda.is_available() else "cpu",
                "lora_config": {
                    "r": 16,
                    "lora_alpha": 32,
                    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"]
                },
                "created_at": datetime.now().isoformat()
            }
            
            if progress_callback:
                progress_callback(1.0, "中文模型训练完成!")
            
            self.logger.info(f"中文模型训练完成: 损失={train_result.training_loss:.4f}, 步数={train_result.global_step}")
            
            return result
            
        except Exception as e:
            error_msg = f"中文模型训练异常: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "training_type": "REAL_ML_TRAINING_FAILED"
            }
'''
    
    def generate_real_en_trainer_code(self) -> str:
        """生成真实的英文训练器代码"""
        return '''
    def train(self, training_data: List[Dict[str, Any]], 
              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """执行真实的英文模型训练"""
        start_time = time.time()
        
        try:
            # 检查依赖
            try:
                from transformers import (
                    AutoTokenizer, AutoModelForCausalLM, 
                    Trainer, TrainingArguments, DataCollatorForLanguageModeling
                )
                from peft import LoraConfig, get_peft_model, TaskType
                from datasets import Dataset
                import torch
            except ImportError as e:
                return {"success": False, "error": f"Missing required dependencies: {e}"}
            
            if progress_callback:
                progress_callback(0.05, "Initializing English training environment...")
            
            # 验证训练数据
            if not training_data or len(training_data) == 0:
                return {"success": False, "error": "Training data is empty"}
            
            if progress_callback:
                progress_callback(0.1, "Loading English model...")
            
            # 1. 加载模型和分词器 - 使用较小的模型以适配4GB内存
            model_name = "microsoft/DialoGPT-medium"  # 使用medium版本以适配内存限制
            
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir="./models/cache"
                )
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.use_gpu and torch.cuda.is_available() else torch.float32,
                    device_map="auto" if self.use_gpu and torch.cuda.is_available() else None,
                    cache_dir="./models/cache"
                )
                
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                    
            except Exception as e:
                return {"success": False, "error": f"Model loading failed: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.2, "Configuring LoRA fine-tuning...")
            
            # 2. 配置LoRA - 使用项目配置的参数
            try:
                lora_config = LoraConfig(
                    r=16,  # 项目配置的rank
                    lora_alpha=32,  # 项目配置的alpha
                    target_modules=["c_attn"],  # DialoGPT的注意力模块
                    lora_dropout=0.1,
                    bias="none",
                    task_type=TaskType.CAUSAL_LM
                )
                model = get_peft_model(model, lora_config)
                model.print_trainable_parameters()
                
            except Exception as e:
                return {"success": False, "error": f"LoRA configuration failed: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.3, "Preparing training data...")
            
            # 3. 准备数据集 - 使用项目的数据处理逻辑
            try:
                processed_data = self.prepare_english_data(training_data)
                texts = []
                
                for item in processed_data["samples"]:
                    # 构建训练文本 - 原片→爆款的学习格式
                    text = f"Original script: {item['original']}\\nViral script: {item['viral']}{tokenizer.eos_token}"
                    texts.append(text)
                
                if len(texts) == 0:
                    return {"success": False, "error": "No valid training samples"}
                
                def tokenize_function(examples):
                    return tokenizer(
                        examples["text"],
                        truncation=True,
                        padding=True,
                        max_length=512,  # 适配内存限制
                        return_tensors="pt"
                    )
                
                dataset = Dataset.from_dict({"text": texts})
                tokenized_dataset = dataset.map(
                    tokenize_function, 
                    batched=True,
                    remove_columns=dataset.column_names
                )
                
            except Exception as e:
                return {"success": False, "error": f"Data preparation failed: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.4, "Configuring training parameters...")
            
            # 4. 配置训练参数 - 适配4GB内存
            try:
                training_args = TrainingArguments(
                    output_dir="./results_en",
                    num_train_epochs=3,
                    per_device_train_batch_size=1,  # 4GB内存兼容
                    gradient_accumulation_steps=8,  # 项目配置
                    learning_rate=2e-5,
                    warmup_steps=100,
                    logging_steps=10,
                    save_steps=500,
                    save_total_limit=2,
                    prediction_loss_only=True,
                    remove_unused_columns=False,
                    dataloader_pin_memory=False,
                    fp16=self.use_gpu and torch.cuda.is_available(),
                    report_to=None,  # 禁用wandb等报告
                    load_best_model_at_end=False,
                    metric_for_best_model=None
                )
                
                # 数据整理器
                data_collator = DataCollatorForLanguageModeling(
                    tokenizer=tokenizer,
                    mlm=False,  # 因果语言模型
                )
                
            except Exception as e:
                return {"success": False, "error": f"Training arguments configuration failed: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.5, "Starting real training...")
            
            # 5. 创建训练器并执行真实训练
            try:
                trainer = Trainer(
                    model=model,
                    args=training_args,
                    train_dataset=tokenized_dataset,
                    tokenizer=tokenizer,
                    data_collator=data_collator
                )
                
                # 执行真实训练 - 这里是关键的真实机器学习过程
                train_result = trainer.train()
                
            except Exception as e:
                return {"success": False, "error": f"Training execution failed: {str(e)}"}
            
            if progress_callback:
                progress_callback(0.9, "Saving trained model...")
            
            # 6. 保存模型
            try:
                os.makedirs("./results_en", exist_ok=True)
                trainer.save_model()
                tokenizer.save_pretrained("./results_en")
                
            except Exception as e:
                return {"success": False, "error": f"Model saving failed: {str(e)}"}
            
            end_time = time.time()
            
            # 7. 生成训练结果
            result = {
                "success": True,
                "training_type": "REAL_ML_TRAINING",
                "model_name": self.model_name,
                "language": self.language,
                "training_duration": end_time - start_time,
                "train_loss": float(train_result.training_loss),
                "global_step": train_result.global_step,
                "samples_processed": len(training_data),
                "device": "cuda" if self.use_gpu and torch.cuda.is_available() else "cpu",
                "lora_config": {
                    "r": 16,
                    "lora_alpha": 32,
                    "target_modules": ["c_attn"]
                },
                "created_at": datetime.now().isoformat()
            }
            
            if progress_callback:
                progress_callback(1.0, "English model training completed!")
            
            self.logger.info(f"English model training completed: loss={train_result.training_loss:.4f}, steps={train_result.global_step}")
            
            return result
            
        except Exception as e:
            error_msg = f"English model training error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "training_type": "REAL_ML_TRAINING_FAILED"
            }
'''

    def apply_real_training_to_zh_trainer(self) -> bool:
        """将真实训练代码应用到中文训练器"""
        print("🔄 更新中文训练器...")

        zh_trainer_path = "src/training/zh_trainer.py"

        try:
            # 读取当前文件
            with open(zh_trainer_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 添加必要的导入
            import_additions = '''import torch
from datetime import datetime
'''

            # 在现有导入后添加新导入
            if "import torch" not in content:
                content = content.replace(
                    "import logging",
                    f"import logging\n{import_additions}"
                )

            # 替换train方法
            real_train_code = self.generate_real_zh_trainer_code()

            # 使用正则表达式替换train方法
            pattern = r'def train\(self, training_data.*?(?=\n    def|\nclass|\Z)'
            new_content = re.sub(pattern, real_train_code.strip(), content, flags=re.DOTALL)

            # 写回文件
            with open(zh_trainer_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print("  ✅ 中文训练器更新成功")
            return True

        except Exception as e:
            print(f"  ❌ 中文训练器更新失败: {e}")
            return False

    def apply_real_training_to_en_trainer(self) -> bool:
        """将真实训练代码应用到英文训练器"""
        print("🔄 更新英文训练器...")

        en_trainer_path = "src/training/en_trainer.py"

        try:
            # 读取当前文件
            with open(en_trainer_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 添加必要的导入
            import_additions = '''import torch
from datetime import datetime
'''

            # 在现有导入后添加新导入
            if "import torch" not in content:
                content = content.replace(
                    "import logging",
                    f"import logging\n{import_additions}"
                )

            # 替换train方法
            real_train_code = self.generate_real_en_trainer_code()

            # 使用正则表达式替换train方法
            pattern = r'def train\(self, training_data.*?(?=\n    def|\nclass|\Z)'
            new_content = re.sub(pattern, real_train_code.strip(), content, flags=re.DOTALL)

            # 写回文件
            with open(en_trainer_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print("  ✅ 英文训练器更新成功")
            return True

        except Exception as e:
            print(f"  ❌ 英文训练器更新失败: {e}")
            return False

    def test_real_training_integration(self) -> Dict[str, Any]:
        """测试真实训练集成"""
        print("🧪 测试真实训练集成...")

        test_result = {
            "success": False,
            "tests": {},
            "errors": []
        }

        try:
            # 测试导入
            print("  📦 测试模块导入...")
            try:
                from src.training.zh_trainer import ZhTrainer
                from src.training.en_trainer import EnTrainer
                test_result["tests"]["import"] = True
                print("    ✅ 模块导入成功")
            except Exception as e:
                test_result["tests"]["import"] = False
                test_result["errors"].append(f"模块导入失败: {e}")
                print(f"    ❌ 模块导入失败: {e}")

            # 测试训练器初始化
            print("  🤖 测试训练器初始化...")
            try:
                zh_trainer = ZhTrainer(use_gpu=False)
                en_trainer = EnTrainer(use_gpu=False)
                test_result["tests"]["initialization"] = True
                print("    ✅ 训练器初始化成功")
            except Exception as e:
                test_result["tests"]["initialization"] = False
                test_result["errors"].append(f"训练器初始化失败: {e}")
                print(f"    ❌ 训练器初始化失败: {e}")

            # 测试数据处理
            print("  📊 测试数据处理...")
            try:
                test_data = [
                    {"original": "这是一个测试剧本", "viral": "震惊！这个剧本太精彩了"},
                    {"original": "主角面临选择", "viral": "不敢相信！主角的选择改变一切"}
                ]

                zh_processed = zh_trainer.prepare_chinese_data(test_data)
                en_processed = en_trainer.prepare_english_data(test_data)

                if zh_processed and en_processed:
                    test_result["tests"]["data_processing"] = True
                    print("    ✅ 数据处理成功")
                else:
                    test_result["tests"]["data_processing"] = False
                    test_result["errors"].append("数据处理返回空结果")
                    print("    ❌ 数据处理返回空结果")

            except Exception as e:
                test_result["tests"]["data_processing"] = False
                test_result["errors"].append(f"数据处理失败: {e}")
                print(f"    ❌ 数据处理失败: {e}")

            # 计算成功率
            success_count = sum(test_result["tests"].values())
            total_tests = len(test_result["tests"])
            success_rate = success_count / total_tests if total_tests > 0 else 0

            test_result["success"] = success_rate >= 0.8  # 80%以上成功率
            test_result["success_rate"] = success_rate

            print(f"📊 测试结果: {success_count}/{total_tests} 成功 ({success_rate*100:.1f}%)")

        except Exception as e:
            test_result["errors"].append(f"测试过程异常: {e}")
            print(f"❌ 测试过程异常: {e}")

        return test_result

    def run_conversion(self) -> Dict[str, Any]:
        """运行完整的转换流程"""
        print("🚀 开始真实训练转换...")

        conversion_result = {
            "success": False,
            "steps_completed": [],
            "errors": [],
            "test_result": None
        }

        try:
            # 步骤1: 更新中文训练器
            if self.apply_real_training_to_zh_trainer():
                conversion_result["steps_completed"].append("中文训练器更新")
            else:
                conversion_result["errors"].append("中文训练器更新失败")

            # 步骤2: 更新英文训练器
            if self.apply_real_training_to_en_trainer():
                conversion_result["steps_completed"].append("英文训练器更新")
            else:
                conversion_result["errors"].append("英文训练器更新失败")

            # 步骤3: 测试集成
            test_result = self.test_real_training_integration()
            conversion_result["test_result"] = test_result

            if test_result["success"]:
                conversion_result["steps_completed"].append("集成测试")
                conversion_result["success"] = True
            else:
                conversion_result["errors"].append("集成测试失败")
                conversion_result["errors"].extend(test_result["errors"])

            return conversion_result

        except Exception as e:
            conversion_result["errors"].append(f"转换流程异常: {str(e)}")
            return conversion_result

def main():
    """主函数"""
    print("🎯 VisionAI-ClipsMaster 真实训练转换")
    print("=" * 50)

    converter = RealTrainingConverter()
    result = converter.run_conversion()

    print("\n📊 转换结果:")
    print(f"✅ 成功: {'是' if result['success'] else '否'}")
    print(f"📋 完成步骤: {', '.join(result['steps_completed'])}")

    if result["errors"]:
        print("❌ 错误:")
        for error in result["errors"]:
            print(f"  • {error}")

    if result["test_result"]:
        print(f"🧪 测试成功率: {result['test_result']['success_rate']*100:.1f}%")

    if result["success"]:
        print("\n🎉 真实训练转换成功！")
        print("💡 现在可以使用真实的机器学习训练了。")
    else:
        print("\n⚠️ 转换过程中遇到问题，请检查错误信息。")

    return result

if __name__ == "__main__":
    main()
