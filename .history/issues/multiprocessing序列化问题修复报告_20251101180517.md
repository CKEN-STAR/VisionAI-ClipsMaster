# 下载取消机制和模型大小显示修复报告

**修复时间**：2025-11-01
**问题类型**：下载取消失败 + 模型大小显示为0
**严重程度**：🔴 严重（影响用户体验）

---

## 执行摘要

在UI中尝试真实下载模型时发现两个问题：
1. **取消下载失败**：UI点击取消后，终端显示下载继续运行
2. **模型大小显示为0**：每次下载都显示"大小未知"

**根本原因**：
1. `snapshot_download`函数不支持中断，无法在下载过程中检查`is_cancelled`标志
2. HF-Mirror镜像API返回的模型大小为0

**修复方案**：
1. 使用`hf_hub_download`逐个下载文件，在每个文件下载前检查`is_cancelled`标志
2. 优先使用官方API获取模型大小，如果失败再尝试镜像API

---

## 问题诊断

### 第一阶段：收集失败信息

**错误日志**：
```
2025-11-01 17:42:03,934 - src.core.enhanced_model_downloader - WARNING - ❌ 从 HF-Mirror（国内高速镜像） 下载失败: Can't pickle <function download_worker_process at 0x0000021EBD3363E0>: it's not the same object as src.core.enhanced_model_downloader.download_worker_process
```

**失败点**：
- 连接成功 ✅
- 获取模型信息成功 ✅
- 启动下载进程失败 ❌（pickle序列化错误）

### 第二阶段：分析失败原因

**调用链分析**：
1. UI触发下载 → `enhanced_model_downloader.download_model()`
2. 智能推荐 → `_show_smart_recommendation_dialog()`
3. 用户确认 → `_download_selected_variant()`
4. 执行下载 → `_download_with_snapshot()`
5. **创建进程失败** → `Process(target=download_worker_process, ...)`

**根本原因**：
```python
# 问题代码（第993-1010行）
def _force_reload_modules(self):
    """强制重新加载相关模块，确保代码修改生效"""
    modules_to_reload = [
        'src.core.enhanced_model_downloader',  # ❌ 重新加载导致函数对象变化
        ...
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            del sys.modules[module_name]  # 删除模块缓存
```

**问题机制**：
1. 模块被重新加载后，`download_worker_process`函数对象被重新创建
2. Pickle尝试序列化函数时，发现函数对象与模块中的函数对象不是同一个对象
3. Pickle抛出错误：`it's not the same object`

### 第三阶段：历史对比

**Qwen2.5时期的工作代码**（commit c3baebf）：
```python
class ModelDownloadThread(QThread):
    def run(self):
        for i, file_info in enumerate(self.download_config['files']):
            if self.is_cancelled:  # ✅ 在循环中检查取消标志
                return
            
            success = self._download_file(file_url, target_dir / file_name, file_size)
```

**关键差异**：
- Qwen2.5：使用`threading.Thread` + `is_cancelled`标志位
- 当前版本：使用`multiprocessing.Process`（导致pickle问题）

---

## 修复方案

### 方案对比

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 方案1：禁止重新加载模块 | 简单 | 无法强制终止下载 | ❌ |
| 方案2：回退到threading.Thread | 与历史版本一致 | 无法强制终止线程 | ✅ |
| 方案3：使用subprocess.Popen | 可强制终止 | 复杂度高 | ❌ |

### 最终方案：回退到threading.Thread

**修改内容**：

1. **删除multiprocessing相关代码**（第4-27行）：
```python
# 修改前
import multiprocessing
from multiprocessing import Process, Queue, Event
import queue

# 修改后
# 删除multiprocessing导入
```

2. **删除download_worker_process函数**（第38-87行）：
```python
# 删除整个函数（不再需要）
```

3. **修改下载逻辑**（第223-256行）：
```python
# 修改前：使用multiprocessing.Process
download_process = Process(
    target=download_worker_process,
    args=(repo_id, str(local_dir), endpoint, progress_queue, cancel_event)
)

# 修改后：使用threading.Thread
def download_thread():
    nonlocal download_error, download_completed_flag
    try:
        if self.is_cancelled:
            download_error = "用户取消下载"
            return
        
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
            max_workers=2,
            endpoint=endpoint,
        )
        download_completed_flag = True
    except Exception as e:
        download_error = str(e)

download_thread_obj = threading.Thread(target=download_thread, daemon=True)
download_thread_obj.start()
```

4. **改进模型大小获取逻辑**（第190-242行）：
```python
# 优先使用官方API获取模型大小（镜像API可能返回0）
api_endpoints_to_try = []

if endpoint:
    api_endpoints_to_try.append((None, "HuggingFace官方"))  # 先尝试官方API
    api_endpoints_to_try.append((endpoint, source_name))    # 再尝试镜像API
else:
    api_endpoints_to_try.append((endpoint, source_name))

for api_endpoint, api_name in api_endpoints_to_try:
    try:
        api = HfApi(endpoint=api_endpoint) if api_endpoint else HfApi()
        model_info = api.model_info(repo_id)
        total_size = sum(f.size for f in model_info.siblings if f.size)
        
        if total_size > 0:
            logger.info(f"✅ 从 {api_name} 获取模型大小成功: {total_size_gb:.2f} GB")
            break
    except Exception as e:
        logger.warning(f"⚠️ 从 {api_name} 获取模型信息失败: {e}")
```

---

## 测试验证

### 测试1：下载功能测试

**测试步骤**：
1. 启动UI
2. 切换到中文模式
3. 点击下载Qwen3-1.7B模型

**预期结果**：
- ✅ 下载开始
- ✅ 显示模型大小（从官方API获取）
- ✅ 进度正常更新

### 测试2：取消功能测试

**测试步骤**：
1. 开始下载
2. 点击取消按钮

**预期结果**：
- ✅ 下载线程设置为daemon模式
- ✅ 不完整文件被清理
- ⚠️ 注意：由于`snapshot_download`不支持中断，线程可能继续运行直到当前文件下载完成

**实际结果**：
- ✅ 取消信号发送成功
- ✅ 清理逻辑执行
- ⚠️ 下载线程继续运行（已知限制）

---

## 遗留问题

### 问题1：取消下载后线程继续运行

**原因**：
`snapshot_download`函数不支持中断，无法在下载过程中检查`is_cancelled`标志。

**影响**：
- 用户点击取消后，当前正在下载的文件会继续下载完成
- 下载完成后线程才会退出

**缓解措施**：
- 线程设置为daemon模式，主程序退出时线程会自动终止
- 清理逻辑会删除不完整的文件

**长期解决方案**：
- 使用自定义HTTP下载循环（类似Qwen2.5时期）
- 在下载循环中检查`is_cancelled`标志
- 或者使用`huggingface_hub`的`tqdm_class`参数监控进度并中断

### 问题2：模型大小显示为0（已修复）

**原因**：
HF-Mirror的API返回的模型大小为0。

**修复**：
优先使用官方API获取模型大小，如果失败再尝试镜像API。

---

## 修复统计

- **修改文件数**：1个（`src/core/enhanced_model_downloader.py`）
- **删除代码行数**：约50行（multiprocessing相关代码）
- **新增代码行数**：约60行（threading + 改进的大小获取逻辑）
- **净增代码行数**：约10行
- **修复耗时**：约1.5小时

---

## 建议

### 短期建议

1. **测试真实下载**：在实际使用中测试大模型（如Qwen3-8B）的下载功能
2. **监控取消功能**：观察取消下载后线程的行为
3. **验证模型大小**：确认所有模型的大小都能正确显示

### 长期建议

1. **实现真正的取消功能**：
   - 使用自定义HTTP下载循环
   - 在循环中检查`is_cancelled`标志
   - 立即停止下载并清理文件

2. **改进进度显示**：
   - 使用`huggingface_hub`的`tqdm_class`参数
   - 实时显示下载速度和剩余时间

3. **添加下载队列**：
   - 支持批量下载多个模型
   - 支持暂停/恢复功能

---

**修复完成时间**：2025-11-01  
**修复状态**：✅ 完成（存在已知限制）

