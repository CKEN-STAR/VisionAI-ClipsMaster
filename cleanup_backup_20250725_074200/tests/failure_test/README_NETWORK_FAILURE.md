# 网络故障测试模块使用指南

本模块用于模拟各种网络故障场景，测试 VisionAI-ClipsMaster 在不可靠网络环境下的表现。支持模拟网络延迟、数据包丢失、带宽限制等故障条件。

## 功能特点

- **跨平台支持**：同时支持 Windows、Linux 和 macOS
- **多种网络故障模拟**：
  - 网络延迟（Network Latency）
  - 数据包丢失（Packet Loss）
  - 带宽限制（Bandwidth Limitation）
  - 连接重置（Connection Reset）
- **丰富的运行模式**：
  - 交互式菜单驱动模式
  - 命令行参数模式
  - 批量自动化测试模式
- **结果导出**：支持将测试结果导出为 JSON 文件
- **彩色输出**：使用彩色文本提升使用体验

## 安装依赖

Windows 系统无需额外安装依赖，模块会自动下载并配置 [Clumsy](https://jagt.github.io/clumsy/) 工具来模拟网络故障。

Linux 和 macOS 系统需要安装 TC（Traffic Control）工具：

```bash
# Ubuntu/Debian
sudo apt-get install iproute2

# CentOS/RHEL
sudo yum install iproute-tc

# macOS
brew install iproute2mac
```

## 使用方法

### 1. 交互式模式

最简单的使用方法是运行交互式模式，通过菜单选择要执行的测试：

```bash
python tests/failure_test/run_network_failure_test.py
```

### 2. 命令行模式

#### 运行单个测试

```bash
# 模拟网络延迟 
python tests/failure_test/run_network_failure_test.py --mode single --test latency --delay 1000ms --duration 20

# 模拟丢包
python tests/failure_test/run_network_failure_test.py --mode single --test packet_loss --loss 50% --duration 15

# 模拟带宽限制
python tests/failure_test/run_network_failure_test.py --mode single --test bandwidth --bandwidth 128 --duration 30
```

#### 运行所有测试并保存结果

```bash
python tests/failure_test/run_network_failure_test.py --mode auto --duration 15 --save
```

### 3. 使用配置文件运行测试

创建一个 JSON 格式的配置文件，例如 `network_test_config.json`：

```json
{
  "tests": [
    {
      "type": "latency",
      "delay": "800ms",
      "duration": 15
    },
    {
      "type": "packet_loss",
      "loss_percent": "25%",
      "duration": 20
    },
    {
      "type": "bandwidth_limit",
      "limit_kbps": 512,
      "duration": 30
    }
  ]
}
```

然后使用此配置文件运行测试：

```bash
python tests/failure_test/run_network_failure_test.py --mode auto --config network_test_config.json --save
```

## 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--mode` | `-m` | 测试模式（interactive/auto/single） | interactive |
| `--test` | `-t` | 测试类型（latency/packet_loss/bandwidth） | - |
| `--delay` | - | 网络延迟值 | 500ms |
| `--loss` | - | 丢包率 | 30% |
| `--bandwidth` | - | 带宽限制(kbps) | 256 |
| `--duration` | `-d` | 测试持续时间(秒) | 10 |
| `--save` | `-s` | 保存测试结果到文件 | false |
| `--output` | `-o` | 结果输出文件名 | 自动生成 |
| `--config` | `-c` | 测试配置文件路径 | - |

## 测试结果示例

```json
{
  "test_time": "2023-06-15T14:30:25.123456",
  "results": [
    {
      "type": "latency",
      "delay": "500ms",
      "start_time": "2023-06-15T14:30:10.123456",
      "end_time": "2023-06-15T14:30:20.123456",
      "success": true,
      "duration": 10
    },
    {
      "type": "packet_loss",
      "loss_percent": "30%",
      "start_time": "2023-06-15T14:30:21.123456",
      "end_time": "2023-06-15T14:30:25.123456",
      "success": true,
      "duration": 4
    }
  ]
}
```

## 集成到项目中使用

可以将网络故障测试模块集成到您自己的测试代码中：

```python
from tests.failure_test.network_failure import NetworkChaos

# 创建混沌网络实例
nc = NetworkChaos()
nc.initialize()

try:
    # 添加500ms网络延迟
    nc.add_latency(delay="500ms")
    
    # 执行您的测试代码...
    your_function_to_test()
    
    # 添加30%丢包率
    nc.packet_loss(percent="30%")
    
    # 继续测试...
    another_function_to_test()
    
finally:
    # 测试完成后，确保清理网络设置
    nc.stop_chaos()
```

## 故障排除

1. **Windows 上找不到 Clumsy**

   尝试手动下载 [Clumsy](https://github.com/jagt/clumsy/releases/download/0.3/clumsy-0.3-win64.zip)，并将 `clumsy.exe` 放入 `tools` 目录。

2. **Linux 上权限不足**

   TC 命令需要 root 权限，请使用 sudo 运行测试：
   
   ```bash
   sudo python tests/failure_test/run_network_failure_test.py
   ```

3. **测试后网络没有恢复**

   如果测试中断或异常退出导致网络设置没有恢复，可以运行以下命令手动清理：

   ```bash
   # Windows
   taskkill /f /im clumsy.exe
   
   # Linux
   sudo tc qdisc del dev eth0 root  # 替换 eth0 为您的网卡名称
   ```

## 注意事项

- 此测试会临时影响整个系统的网络连接，请不要在生产环境中运行
- 测试时可能会导致其他应用的网络连接出现问题
- 运行测试需要管理员/root权限
- 建议在隔离的测试环境中运行网络故障测试 