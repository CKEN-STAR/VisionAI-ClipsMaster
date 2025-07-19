# 内存压力测试工具

本工具用于测试VisionAI-ClipsMaster在低配设备(4GB内存/无GPU)上的内存性能和模型加载行为。

## 功能特点

- **多种压力模式**：支持阶梯式、突发式和锯齿波动三种内存压力测试模式
- **模型加载测试**：测试不同内存压力下模型加载性能
- **量化级别测试**：比较不同量化级别对性能的影响
- **长时间稳定性测试**：验证系统在长时间运行下的稳定性
- **自动报告生成**：生成详细的JSON和CSV格式测试报告
- **测试环境模拟**：通过Docker或cgroups模拟不同内存限制的设备环境

## 安装依赖

确保安装以下依赖：

```bash
pip install psutil numpy pyyaml
```

## 基本使用

### 简单内存压力测试

不涉及模型加载，纯测试系统内存行为：

```bash
# 阶梯式压力测试 (每1秒增加100MB，最多20步)
python src/utils/memory_test_cli.py simple --mode staircase --step-size 100 --interval 1.0 --steps 20

# 突发式压力测试 (占用70%内存5秒)
python src/utils/memory_test_cli.py simple --mode burst --target 70 --duration 5.0

# 锯齿波动测试 (在30%-70%之间波动，3个周期)
python src/utils/memory_test_cli.py simple --mode sawtooth --min 30 --max 70 --cycles 3

# 分配到满测试 (持续分配直到接近系统极限)
python src/utils/memory_test_cli.py simple --mode allocate_full
```

### 模型加载测试

测试在内存压力下模型的加载性能：

```bash
# 在突发式压力下加载模型
python src/utils/memory_test_cli.py model --model-id qwen2.5-7b-zh --mode burst --save-report

# 在阶梯式压力下加载模型，自定义测试持续时间
python src/utils/memory_test_cli.py model --model-id qwen2.5-7b-zh --mode staircase --test-duration 120 --save-report
```

### 量化级别测试

比较不同量化级别的性能表现：

```bash
# 测试三种量化级别
python src/utils/memory_test_cli.py quantization --model-id qwen2.5-7b-zh --quant-levels Q2_K,Q4_K_M,Q6_K --save-report
```

### 长时间稳定性测试

测试系统在长时间运行下的稳定性：

```bash
# 运行1小时稳定性测试，不加载模型
python src/utils/memory_test_cli.py stability --hours 1.0 --save-report

# 运行8小时稳定性测试，加载模型
python src/utils/memory_test_cli.py stability --hours 8.0 --use-model --model-id qwen2.5-7b-zh --save-report
```

### 测试环境模拟

使用配置好的环境配置来模拟不同内存条件：

```bash
# 列出所有可用的环境配置
python scripts/test_low_memory_env.py --list

# 创建所有环境的测试脚本
python scripts/test_low_memory_env.py --create-scripts

# 显示各环境的Docker命令
python scripts/test_low_memory_env.py --show-docker

# 运行指定环境的测试
python scripts/test_low_memory_env.py --run "4GB连线"

# 使用脚本直接运行环境测试 (Linux/macOS)
scripts/run_memory_env_test.sh --environment "极限2GB模式" --mode staircase --duration 60

# Windows版本
scripts\run_memory_env_test.bat --environment "极限2GB模式" --mode burst --target 70
```

## 测试报告

测试报告默认保存在`logs/memory_tests`目录下，包含：

- **JSON报告**：完整详细的测试数据
- **CSV报告**：关键指标摘要，方便导入到Excel分析

可以通过`--output-dir`参数自定义输出目录：

```bash
python src/utils/memory_test_cli.py model --model-id qwen2.5-7b-zh --save-report --output-dir custom/report/path
```

## 压力模式详解

### 阶梯式增长(Staircase)

每隔固定时间增加固定大小的内存，呈现阶梯状上升，用于测试系统在内存逐渐增长时的响应。

参数:
- `--step-size`: 每步增加的内存(MB)
- `--interval`: 每步间隔时间(秒)
- `--steps`: 最大步数

### 突发式分配(Burst)

快速分配达到系统总内存的指定百分比，并维持一段时间，用于测试系统对突发内存需求的处理能力。

参数:
- `--target`: 目标内存占用百分比(0-100)
- `--duration`: 维持高内存状态的时间(秒)

### 锯齿波动(Sawtooth)

在最小和最大内存占用比例之间循环波动，模拟真实工作负载下的内存变化模式。

参数:
- `--min`: 最小内存占用百分比(0-100)
- `--max`: 最大内存占用百分比(0-100)
- `--cycles`: 波动周期数
- `--duration`: 每个周期持续时间(秒)

## 测试环境配置

在`configs/low_mem_env.yaml`文件中定义了多种测试环境配置：

- **4GB连线**：模拟标准4GB RAM设备，带交换空间
- **极限2GB模式**：模拟仅有2GB RAM且无交换空间的极限环境
- **手机模拟**：模拟3GB RAM的移动设备
- **老旧设备**：模拟2.5GB RAM的老旧设备

可以通过Docker容器精确模拟这些环境：

```bash
# 使用Docker模拟4GB内存环境
docker run --memory="3800m" --memory-swap="3800m" visionai-clipsmaster:latest python src/utils/memory_test_cli.py simple

# 或使用环境模拟工具
python -c "from src.utils.env_simulator import EnvironmentSimulator; simulator = EnvironmentSimulator(); simulator.run_docker_container('4GB连线')"
```

## 集成开发

内存压力测试模块设计为可集成到其他部分，主要包含三个组件：

1. **MemoryPressurer**：内存压力生成器，提供各种压力模式
2. **MemoryGuard**：内存防护器，监控并优化内存使用
3. **MemoryManager**：统一管理接口，集成前两者功能
4. **EnvironmentSimulator**：环境模拟器，加载和应用环境配置

### 代码集成示例

```python
from src.utils.memory_integration import get_memory_manager

# 获取内存管理器单例（可指定环境配置）
mm = get_memory_manager(env_profile_name="4GB连线")

# 启动内存监控
mm.start_monitoring()

# 运行受控内存压力测试
report = mm.run_controlled_pressure_test(
    test_mode="burst",
    model_id="your_model_id",
    target_percent=0.7,
    burst_duration_sec=10
)

# 生成内存报告
mem_report = mm.generate_memory_report()
print(f"内存趋势: {mem_report['trend']}")
print(f"建议量化级别: {mem_report['quantization']['current_optimal']}")
print(f"环境配置: {mem_report['environment']['profile_name']}")

# 停止监控
mm.stop_monitoring()
```

### 环境模拟器使用示例

```python
from src.utils.env_simulator import EnvironmentSimulator

# 创建环境模拟器
simulator = EnvironmentSimulator()

# 列出所有可用配置
simulator.print_profiles()

# 生成Docker命令
cmd = simulator.generate_docker_command(
    profile_name="极限2GB模式",
    command="python src/utils/memory_test_cli.py simple --mode=burst"
)
print(cmd)

# 创建测试脚本
simulator.create_test_script("4GB连线", "scripts/test_4gb.sh")
```

## 故障排除

- **内存分配失败**：检查系统可用内存，降低测试参数
- **测试卡住**：可能是系统接近内存耗尽，使用Ctrl+C中断，降低测试强度
- **模型加载失败**：确保模型ID正确，检查模型文件完整性
- **Docker命令执行失败**：确保已安装Docker并具有足够权限
- **环境配置加载失败**：检查configs/low_mem_env.yaml文件是否存在且格式正确

## 注意事项

- 在生产环境使用前，建议先在测试环境验证
- 极端压力测试可能导致系统不稳定，请谨慎使用
- 长时间测试建议使用`nohup`或screen会话运行
- 报告中的内存使用率包括系统其他进程占用的内存
- Docker容器内的内存限制是精确的，适合重现特定内存条件 