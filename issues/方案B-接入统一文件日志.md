# 方案B：接入统一文件日志（simple_ui_fixed.py）

## 背景
- UI 仅使用 logging.basicConfig(StreamHandler) 输出到控制台，未落盘至 logs/visionai.log。
- 需要最小改动、可回退地让 UI 与核心模块共用统一的日志配置（写入日志文件 + 控制台）。

## 方案
- 使用已有模块 src/utils/log_handler.py（其在导入时通过 basicConfig 注册了 FileHandler 到 logs/visionai.log 与控制台）。
- 在 simple_ui_fixed.py 中移除本地 basicConfig，改为导入 get_logger，并获取模块级 logger。

## 代码改动
- 文件：simple_ui_fixed.py（约 9 行 → 3 行）
- 替换内容（原 41–49 行）：
  - 删除：logging.basicConfig(...StreamHandler()) + logging.getLogger(__name__)
  - 新增：from src.utils.log_handler import get_logger; logger = get_logger(__name__)

## 验证与影响
- 影响面：仅日志初始化方式；功能逻辑不变；可随时回退。
- 预期效果：
  1) 所有使用 logging 的模块日志会写入 logs/visionai.log；
  2) 控制台输出仍保留（便于开发/调试）。
- 打印(print) 仍为控制台输出，不强行重定向至文件（保持“最小改动”原则）。如后续需要，可新增可选开关重定向 stdout/stderr。

## 下一步（需要用户执行）
1. 正常启动 UI（无需 Tee）：`python -u simple_ui_fixed.py`
2. 在 UI 内按“工作流程模式”执行一次完整流程（原片+SRT）。
3. 我将解析 logs/visionai.log，完成端到端核验报告（九步流程、FFmpeg/NVENC、AI推理GPU配置、耗时与告警）。

## 状态
- 已完成改动，等待用户复跑 UI 并生成日志。

