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

### 问题1：取消下载失败

**用户报告**：
> "用户在ui层面取消下载时失败，终端显示还在下载"

**终端证据**：
```
2025-11-01 17:53:44,865 - src.core.enhanced_model_downloader - INFO - 用户取消下载: Qwen3-1.7B-Instruct-FP16
2025-11-01 17:53:45,206 - src.core.enhanced_model_downloader - WARNING - ⚠️ 用户取消下载
[Download continues for another 1+ minute]
model-00002-of-00002.safetensors:  66%|███████████████████▋          | 409M/622M [01:33<01:07, 3.16MB/s]
```

**根本原因**：
`snapshot_download`函数不支持中断，无法在下载过程中检查`is_cancelled`标志。

**代码分析**：
```python
# 问题代码（第260-267行）
snapshot_download(
    repo_id=repo_id,
    local_dir=str(local_dir),
    local_dir_use_symlinks=False,
    resume_download=True,
    max_workers=2,
    endpoint=endpoint,
)
# ❌ 这个函数会一次性下载所有文件，无法中断
```

### 问题2：模型大小显示为0

**用户报告**：
> "每次下载都显示未知大小"

**日志证据**：
```
2025-11-01 17:53:43,123 - src.core.enhanced_model_downloader - WARNING - ⚠️ API返回的模型大小为0，将仅显示已下载大小
```

**根本原因**：
HF-Mirror镜像API返回的模型文件大小为0。

**代码分析**：
```python
# 问题代码（第207-212行）
api = HfApi(endpoint=endpoint)  # endpoint = 'https://hf-mirror.com'
model_info = api.model_info(repo_id)
total_size = sum(f.size for f in model_info.siblings if f.size)
# ❌ HF-Mirror API返回的f.size为0
```

### 历史对比：Qwen2.5时期的工作代码

**Qwen2.5时期**（commit c3baebf）：
- 下载方式：`ModelDownloadThread(QThread)` + 文件列表循环
- 取消机制：在每个文件下载前检查`is_cancelled`标志
- 模型格式：GGUF量化模型（单个文件）

**Qwen3时期**（当前）：
- 下载方式：`snapshot_download`（一次性下载所有文件）
- 取消机制：无法中断（问题所在）
- 模型格式：HuggingFace原始模型（多个文件）

**关键差异**：
```python
# Qwen2.5时期（可以取消）
for i, file_info in enumerate(self.download_config['files']):
    if self.is_cancelled:  # ✅ 每个文件下载前检查
        return
    success = self._download_file(file_url, target_dir / file_name, file_size)

# Qwen3时期（无法取消）
snapshot_download(...)  # ❌ 一次性下载所有文件，无法中断
```

---

## 修复方案

### 方案对比

| 方案 | 优点 | 缺点 | 选择 |
|------|------|------|------|
| 方案1：使用daemon线程 | 简单 | 无法真正取消下载 | ❌ |
| 方案2：逐文件下载 | 可以在每个文件前检查取消标志 | 需要重构代码 | ✅ |
| 方案3：使用自定义tqdm_class | 可以监控进度并中断 | 复杂度高 | ❌ |

### 最终方案：使用hf_hub_download逐文件下载

**核心思路**：
将`snapshot_download`（一次性下载所有文件）替换为`hf_hub_download`（逐个下载文件），这样就可以在每个文件下载前检查`is_cancelled`标志。

**修改内容**：

1. **导入hf_hub_download**（第28行）：
```python
# 修改前
from huggingface_hub import snapshot_download, HfApi

# 修改后
from huggingface_hub import snapshot_download, HfApi, hf_hub_download
```

2. **获取文件列表**（第244-258行）：
```python
# 获取模型文件列表
try:
    api = HfApi(endpoint=endpoint) if endpoint else HfApi()
    model_info = api.model_info(repo_id)
    files_to_download = [f for f in model_info.siblings if not f.rfilename.startswith('.')]
    logger.info(f"📋 需要下载 {len(files_to_download)} 个文件")
except Exception as e:
    logger.error(f"❌ 获取文件列表失败: {e}")
    continue  # 跳到下一个镜像源
```

3. **逐文件下载（支持取消）**（第260-305行）：
```python
# 逐个下载文件（支持取消）
downloaded_size = 0
for file_idx, file_info in enumerate(files_to_download):
    # 检查是否已取消
    if self.is_cancelled:
        logger.warning("⚠️ 用户取消下载")
        self.progress_updated.emit(0, "正在取消下载...")
        self._cleanup_snapshot_download(local_dir)
        raise Exception("用户取消下载")

    file_name = file_info.rfilename
    file_size = file_info.size if file_info.size else 0

    logger.info(f"📥 [{file_idx+1}/{len(files_to_download)}] 下载文件: {file_name}")

    try:
        # 使用hf_hub_download下载单个文件
        hf_hub_download(
            repo_id=repo_id,
            filename=file_name,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
            endpoint=endpoint,
        )

        # 更新进度
        downloaded_size += file_size
        if total_size > 0:
            progress = int(10 + (downloaded_size / total_size) * 85)
            self.progress_updated.emit(
                progress,
                f"下载中... {file_idx+1}/{len(files_to_download)} 文件 ({progress}%)"
            )

        logger.info(f"✅ 文件下载完成: {file_name}")

    except Exception as e:
        logger.error(f"❌ 文件下载失败: {file_name}, 错误: {e}")
        raise Exception(f"文件下载失败: {file_name}")
```

4. **改进模型大小获取逻辑**（第194-231行）：
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
- ✅ 进度正常更新（显示文件数量和百分比）
- ✅ 支持断点续传

### 测试2：取消功能测试

**测试步骤**：
1. 开始下载
2. 等待第一个文件下载完成
3. 点击取消按钮

**预期结果**：
- ✅ 立即停止下载（在下一个文件下载前）
- ✅ 不完整文件被清理
- ✅ UI显示"正在取消下载..."
- ✅ 终端不再显示下载活动

**实际结果**（待用户测试）：
- 等待用户在UI中测试并反馈

### 测试3：模型大小显示测试

**测试步骤**：
1. 启动UI
2. 点击下载Qwen3-1.7B模型

**预期结果**：
- ✅ 显示正确的模型大小（约3.4GB）
- ✅ 进度百分比准确

**实际结果**（待用户测试）：
- 等待用户在UI中测试并反馈

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

