#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 模型下载链接连通性测试
仅进行连接测试，不执行实际下载
"""

import requests
import time
import json
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from datetime import datetime
import sys
import os

class ModelDownloadConnectivityTester:
    """模型下载链接连通性测试器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VisionAI-ClipsMaster/1.0 (Connectivity Test)',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })
        self.timeout = 30  # 30秒超时
        self.test_results = []
        
    def test_url_connectivity(self, url: str, description: str = "") -> Dict:
        """测试单个URL的连通性"""
        print(f"🔍 测试: {description or url}")
        
        result = {
            "url": url,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "accessible": False,
            "status_code": None,
            "response_time": None,
            "content_length": None,
            "content_type": None,
            "error": None,
            "server": None
        }
        
        try:
            start_time = time.time()
            
            # 使用HEAD请求进行连通性测试，避免下载内容
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # 毫秒
            
            result.update({
                "accessible": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "content_length": response.headers.get('Content-Length'),
                "content_type": response.headers.get('Content-Type'),
                "server": response.headers.get('Server')
            })
            
            # 如果HEAD请求失败，尝试GET请求的前几个字节
            if response.status_code >= 400:
                print(f"   ⚠️ HEAD请求失败 ({response.status_code})，尝试GET请求...")
                headers = {'Range': 'bytes=0-1023'}  # 只请求前1KB
                get_response = self.session.get(url, headers=headers, timeout=self.timeout)
                result["status_code"] = get_response.status_code
                result["accessible"] = get_response.status_code < 400
            
            # 状态判断
            if result["status_code"] == 200:
                print(f"   ✅ 可访问 - {response_time}ms")
            elif result["status_code"] == 206:
                print(f"   ✅ 支持范围请求 - {response_time}ms")
            elif result["status_code"] in [301, 302, 303, 307, 308]:
                print(f"   🔄 重定向 ({result['status_code']}) - {response_time}ms")
            else:
                print(f"   ❌ HTTP {result['status_code']} - {response_time}ms")
                
        except requests.exceptions.Timeout:
            result["error"] = "连接超时"
            print(f"   ⏰ 连接超时 (>{self.timeout}s)")
            
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"连接错误: {str(e)}"
            print(f"   🚫 连接失败: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            result["error"] = f"请求异常: {str(e)}"
            print(f"   ❌ 请求异常: {str(e)}")
            
        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"
            print(f"   💥 未知错误: {str(e)}")
        
        return result
    
    def get_model_download_urls(self) -> Dict[str, List[Dict]]:
        """获取所有模型下载URL配置"""
        return {
            "simple_ui_fixed.py": [
                {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf",
                    "description": "Mistral-7B-v0.1 Q4_K_M量化版本",
                    "model": "mistral-7b-en",
                    "quantization": "Q4_K_M",
                    "size": "~4GB"
                },
                {
                    "url": "https://huggingface.co/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/main/qwen1_5-7b-chat-q4_k_m.gguf",
                    "description": "Qwen1.5-7B-Chat Q4_K_M量化版本",
                    "model": "qwen2.5-7b-zh", 
                    "quantization": "Q4_K_M",
                    "size": "~4GB"
                }
            ],
            "intelligent_model_selector.py": [
                {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct",
                    "description": "Qwen2.5-7B-Instruct FP16版本 (ModelScope)",
                    "model": "qwen2.5-7b",
                    "quantization": "FP16",
                    "size": "~14.4GB"
                },
                {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF",
                    "description": "Qwen2.5-7B-Instruct GGUF版本 (ModelScope)",
                    "model": "qwen2.5-7b",
                    "quantization": "Multiple",
                    "size": "Various"
                }
            ],
            "enhanced_model_downloader.py": [
                {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct/resolve/main/model-00001-of-00008.safetensors",
                    "description": "Qwen2.5-7B-Instruct 模型文件1/8",
                    "model": "qwen2.5-7b",
                    "quantization": "FP16",
                    "size": "~1.8GB"
                },
                {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                    "description": "Qwen2.5-7B-Instruct Q4_K_M GGUF",
                    "model": "qwen2.5-7b",
                    "quantization": "Q4_K_M",
                    "size": "~4.1GB"
                },
                {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf",
                    "description": "Qwen2.5-7B-Instruct Q5_K_M GGUF",
                    "model": "qwen2.5-7b", 
                    "quantization": "Q5_K_M",
                    "size": "~5.1GB"
                },
                {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q8_0.gguf",
                    "description": "Qwen2.5-7B-Instruct Q8_0 GGUF",
                    "model": "qwen2.5-7b",
                    "quantization": "Q8_0", 
                    "size": "~7.6GB"
                }
            ],
            "setup_models.py": [
                {
                    "url": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2",
                    "description": "Mistral-7B-Instruct-v0.2 官方仓库",
                    "model": "mistral-7b",
                    "quantization": "FP16",
                    "size": "~14.4GB"
                },
                {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                    "description": "Mistral-7B-Instruct-v0.2 Q4_K_M GGUF",
                    "model": "mistral-7b",
                    "quantization": "Q4_K_M",
                    "size": "~4.1GB"
                },
                {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K.gguf",
                    "description": "Mistral-7B-Instruct-v0.2 Q5_K GGUF",
                    "model": "mistral-7b",
                    "quantization": "Q5_K",
                    "size": "~5.1GB"
                }
            ],
            "external_links": [
                {
                    "url": "https://download.pytorch.org/whl/cu118",
                    "description": "PyTorch CUDA 11.8 下载源",
                    "model": "pytorch",
                    "quantization": "N/A",
                    "size": "Various"
                },
                {
                    "url": "https://ffmpeg.org/download.html",
                    "description": "FFmpeg 官方下载页面",
                    "model": "ffmpeg",
                    "quantization": "N/A", 
                    "size": "Various"
                }
            ]
        }
    
    def run_connectivity_tests(self) -> Dict:
        """运行所有连通性测试"""
        print("🌐 VisionAI-ClipsMaster 模型下载链接连通性测试")
        print("=" * 80)
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ 超时设置: {self.timeout}秒")
        print()
        
        all_urls = self.get_model_download_urls()
        total_tests = 0
        successful_tests = 0
        
        for source, urls in all_urls.items():
            print(f"📂 测试来源: {source}")
            print("-" * 60)
            
            for url_config in urls:
                total_tests += 1
                result = self.test_url_connectivity(
                    url_config["url"], 
                    f"{url_config['description']} ({url_config['model']} - {url_config['quantization']})"
                )
                
                # 添加额外信息
                result.update({
                    "source": source,
                    "model": url_config["model"],
                    "quantization": url_config["quantization"],
                    "expected_size": url_config["size"]
                })
                
                self.test_results.append(result)
                
                if result["accessible"] and result["status_code"] in [200, 206]:
                    successful_tests += 1
                
                time.sleep(1)  # 避免请求过于频繁
            
            print()
        
        # 生成测试摘要
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": round(success_rate, 2),
                "timeout_seconds": self.timeout
            },
            "results": self.test_results
        }
        
        return summary

def main():
    """主函数"""
    print("🚀 启动VisionAI-ClipsMaster模型下载链接连通性测试")
    print()
    
    tester = ModelDownloadConnectivityTester()
    
    try:
        # 运行测试
        summary = tester.run_connectivity_tests()
        
        # 显示摘要
        print("📊 测试摘要")
        print("=" * 80)
        print(f"📈 总测试数: {summary['test_info']['total_tests']}")
        print(f"✅ 成功连接: {summary['test_info']['successful_tests']}")
        print(f"📊 成功率: {summary['test_info']['success_rate']}%")
        print()
        
        # 按状态分类显示结果
        accessible_urls = [r for r in summary['results'] if r['accessible'] and r['status_code'] in [200, 206]]
        problematic_urls = [r for r in summary['results'] if not r['accessible'] or r['status_code'] not in [200, 206]]
        
        if accessible_urls:
            print("✅ 可访问的下载链接:")
            for result in accessible_urls:
                print(f"   🔗 {result['description']}")
                print(f"      URL: {result['url']}")
                print(f"      状态: HTTP {result['status_code']} ({result['response_time']}ms)")
                if result['content_length']:
                    size_mb = int(result['content_length']) / (1024 * 1024)
                    print(f"      大小: {size_mb:.1f} MB")
                print()
        
        if problematic_urls:
            print("❌ 有问题的下载链接:")
            for result in problematic_urls:
                print(f"   🔗 {result['description']}")
                print(f"      URL: {result['url']}")
                if result['status_code']:
                    print(f"      状态: HTTP {result['status_code']}")
                if result['error']:
                    print(f"      错误: {result['error']}")
                print()
        
        # 保存详细结果
        report_file = f"model_download_connectivity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告已保存: {report_file}")
        
        return summary['test_info']['success_rate'] >= 70  # 70%以上认为测试通过
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        return False
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
