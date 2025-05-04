import pytest

@pytest.fixture(scope="session")
def base_config():
    """初始化测试配置（高级配额）"""
    return {
        "max_memory": 8192,  # 8GB设备内存上限，适配高配环境
        "timeout": 60,       # 单用例超时时间（秒）
        "golden_samples": "tests/golden_samples/",  # 黄金样本路径
        "max_threads": 16,   # 最大并发线程数
        "device_preference": ["cuda", "mps", "cpu"],  # 设备优先级
        "quant_levels": ["Q8_0", "Q6_K", "Q5_K", "Q4_K_M", "Q2_K"],  # 支持的量化等级
        "log_level": "INFO",  # 日志等级
        # 可扩展更多全局测试参数
    } 