"""测试镜像源连接和URL格式"""
import requests
from huggingface_hub import HfApi

# 测试配置
repo_id = "Qwen/Qwen2.5-0.5B"  # 使用一个小模型测试
test_file = "README.md"  # 测试一个小文件

# 镜像源配置
mirror_sources = [
    {'name': 'HF-Mirror', 'endpoint': 'https://hf-mirror.com'},
    {'name': 'ModelScope', 'endpoint': 'https://www.modelscope.cn'},
    {'name': 'HuggingFace官方', 'endpoint': None},
]

print("=" * 80)
print("测试镜像源连接和URL格式")
print("=" * 80)
print(f"测试模型: {repo_id}")
print(f"测试文件: {test_file}")
print()

for source in mirror_sources:
    source_name = source['name']
    endpoint = source['endpoint']
    
    print(f"\n{'=' * 80}")
    print(f"测试镜像源: {source_name}")
    print(f"Endpoint: {endpoint}")
    print(f"{'=' * 80}")
    
    # 测试1：API调用（获取模型信息）
    print(f"\n[测试1] API调用 - 获取模型信息")
    try:
        if endpoint:
            api = HfApi(endpoint=endpoint)
        else:
            api = HfApi()
        
        model_info = api.model_info(repo_id)
        print(f"✅ API调用成功")
        print(f"   模型ID: {model_info.id}")
        print(f"   文件数量: {len(model_info.siblings)}")
        
        # 获取文件列表
        files = [f.rfilename for f in model_info.siblings if not f.rfilename.startswith('.')]
        print(f"   文件列表（前5个）: {files[:5]}")
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        continue
    
    # 测试2：构建文件URL并测试下载
    print(f"\n[测试2] 文件下载 - 测试URL格式")
    try:
        # 构建URL
        if endpoint:
            if 'modelscope.cn' in endpoint:
                file_url = f"{endpoint}/models/{repo_id}/resolve/main/{test_file}"
            else:
                file_url = f"{endpoint}/{repo_id}/resolve/main/{test_file}"
        else:
            file_url = f"https://huggingface.co/{repo_id}/resolve/main/{test_file}"
        
        print(f"   URL: {file_url}")
        
        # 发送HEAD请求测试连接
        response = requests.head(file_url, timeout=10)
        print(f"   HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 文件URL可访问")
            content_length = response.headers.get('content-length', '未知')
            print(f"   文件大小: {content_length} 字节")
        else:
            print(f"❌ 文件URL不可访问（状态码: {response.status_code}）")
            
    except Exception as e:
        print(f"❌ 文件下载测试失败: {e}")

print(f"\n{'=' * 80}")
print("测试完成")
print(f"{'=' * 80}")

