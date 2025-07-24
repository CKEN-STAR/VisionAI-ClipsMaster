# 多平台适配层

## 简介

多平台适配层是VisionAI-ClipsMaster压力测试套件的重要组成部分，提供了统一的内存和系统资源监控接口，使应用能够在Windows、macOS和Linux平台上无缝运行。

该模块位于`src/monitor/platform_adapter.py`，旨在解决跨平台内存监控的一致性问题，特别是在不同操作系统提供不同内存管理和监控机制的情况下。

## 功能特点

1. **统一接口**：提供统一的函数接口，隐藏底层平台差异
2. **优雅降级**：首选使用跨平台的psutil库，在不可用时自动降级到平台特定方法
3. **全面监控**：不仅提供内存监控，还支持CPU、磁盘和平台信息获取
4. **错误处理**：提供稳健的错误处理机制，避免监控失败导致整个应用崩溃

## 主要API

### 内存使用信息

```python
from src.monitor.platform_adapter import get_memory_usage

# 获取内存使用信息
mem_info = get_memory_usage()
print(f"总内存: {mem_info['total']:.2f}MB")
print(f"可用内存: {mem_info['available']:.2f}MB")
print(f"已用内存: {mem_info['used']:.2f}MB")
print(f"使用率: {mem_info['percent']:.1f}%")
print(f"进程内存: {mem_info['process']:.2f}MB")
```

### 平台信息

```python
from src.monitor.platform_adapter import get_platform_info

# 获取平台信息
platform_info = get_platform_info()
print(f"系统类型: {platform_info['system']}")
print(f"系统版本: {platform_info['release']}")
print(f"机器类型: {platform_info['machine']}")
print(f"处理器: {platform_info['processor']}")
```

### CPU使用率

```python
from src.monitor.platform_adapter import get_cpu_usage

# 获取CPU使用率
cpu_percent = get_cpu_usage()
print(f"CPU使用率: {cpu_percent:.1f}%")
```

### 磁盘使用信息

```python
from src.monitor.platform_adapter import get_disk_usage

# 获取磁盘使用信息
disk_info = get_disk_usage('.')  # 当前目录
print(f"总空间: {disk_info['total']:.2f}GB")
print(f"已用空间: {disk_info['used']:.2f}GB")
print(f"可用空间: {disk_info['free']:.2f}GB")
print(f"使用率: {disk_info['percent']:.1f}%")
```

## 平台特定实现

### Windows实现

在Windows上，适配层首先尝试使用psutil库。如果不可用，则使用WMI（Windows Management Instrumentation）来获取系统信息：

```python
# Windows示例实现（当psutil不可用时）
def _get_windows_memory_fallback():
    result = subprocess.run(['wmic', 'OS', 'get', 'FreePhysicalMemory,TotalVisibleMemorySize'], 
                          stdout=subprocess.PIPE, text=True)
    output = result.stdout.strip()
    lines = output.split('\n')
    if len(lines) >= 2:
        values = lines[1].split()
        if len(values) >= 2:
            total = float(values[1]) / 1024  # MB
            free = float(values[0]) / 1024   # MB
            # 计算其他值...
```

### macOS实现

在macOS上，适配层首先尝试使用psutil库。如果不可用，则使用vm_stat命令：

```python
# macOS示例实现（当psutil不可用时）
def _get_mac_memory_fallback():
    result = subprocess.run(['vm_stat'], stdout=subprocess.PIPE, text=True)
    output = result.stdout.strip()
    lines = output.split('\n')
    stats = {}
    
    for line in lines[1:]:
        if ':' in line:
            parts = line.split(':')
            key = parts[0].strip()
            value = parts[1].strip().replace('.', '')
            stats[key] = int(value)
    
    # 处理vm_stat输出...
```

### Linux实现

在Linux上，适配层首先尝试使用psutil库。如果不可用，则解析/proc/meminfo文件：

```python
# Linux示例实现（当psutil不可用时）
def _get_linux_memory_fallback():
    with open('/proc/meminfo', 'r') as f:
        meminfo = f.read()
    
    # 解析内存信息
    mem_total = 0
    mem_available = 0
    
    for line in meminfo.split('\n'):
        if 'MemTotal:' in line:
            mem_total = int(line.split()[1]) / 1024  # MB
        elif 'MemAvailable:' in line:
            mem_available = int(line.split()[1]) / 1024  # MB
    
    # 计算其他值...
```

## 集成到MemoryMonitor

多平台适配层已集成到MemoryMonitor类中，通过替换原来依赖psutil的代码：

```python
def _monitor_thread(self):
    """内存监控线程"""
    try:
        while not self._stop_event.is_set():
            try:
                # 获取当前时间
                current_time = time.time()
                elapsed = current_time - self.start_time
                
                # 使用平台适配层获取内存信息
                mem_info = get_memory_usage()
                
                # 获取进程内存和系统内存百分比
                process_mem = mem_info['process']  # MB
                system_percent = mem_info['percent']  # %
                
                # 记录数据
                self.memory_history.append((elapsed, process_mem, system_percent))
                
                logger.debug(f"内存监控: 进程={process_mem:.2f}MB, 系统={system_percent:.1f}%")
                
            except Exception as e:
                logger.error(f"监控数据采集异常: {e}")
            
            # 等待下一个采样点
            time.sleep(self.sample_interval)
            
    except Exception as e:
        logger.exception(f"内存监控线程异常: {e}")
```

## 测试

可以使用以下命令运行平台适配层测试：

```bash
python tests/monitor_test/platform_test.py
```

## 最佳实践

1. **首选使用高级接口**：直接使用MemoryMonitor类，而不是直接调用适配层函数
2. **异常处理**：始终处理可能的异常，特别是在平台特定功能可能不可用的情况下
3. **预先测试**：在部署前在目标平台上运行测试，确认适配层工作正常
4. **降级策略**：考虑当监控功能不可用时的应用行为

## 常见问题

1. **导入错误**：确保已安装psutil库（`pip install psutil`）
2. **权限问题**：在Linux上，确保应用有读取/proc文件系统的权限
3. **数据不一致**：不同平台计算内存使用的方式可能略有不同，关注趋势而不是绝对值
4. **性能开销**：高频率采样可能导致额外的系统负载，根据需要调整采样间隔 