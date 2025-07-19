@echo off
REM VisionAI-ClipsMaster Windows测试环境设置脚本

echo === VisionAI-ClipsMaster 测试环境设置 ===
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请安装Python 3.8或更高版本
    goto :EOF
)

REM 创建测试虚拟环境
echo [步骤1] 正在创建测试虚拟环境...
if exist test_venv (
    echo 测试环境已存在，跳过创建
) else (
    python -m venv test_venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        goto :EOF
    )
    echo [成功] 虚拟环境创建成功
)

REM 激活虚拟环境
echo [步骤2] 正在激活虚拟环境...
call test_venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败
    goto :EOF
)
echo [成功] 虚拟环境激活成功

REM 创建目录结构
echo [步骤3] 正在创建目录结构...
if not exist tests mkdir tests
if not exist configs\models\available_models mkdir configs\models\available_models
if not exist src\core mkdir src\core
if not exist data\input\subtitles mkdir data\input\subtitles
if not exist data\output\generated_srt mkdir data\output\generated_srt
if not exist data\output\final_videos mkdir data\output\final_videos
echo [成功] 目录结构创建完成

REM 安装测试依赖
echo [步骤4] 正在安装测试依赖...
python scripts\setup_test_env.py
if %errorlevel% neq 0 (
    echo [错误] 测试依赖安装失败
    goto :EOF
)
echo [成功] 测试依赖安装完成

REM 创建测试数据
echo [步骤5] 正在创建测试数据...
if not exist data\input\subtitles\test_zh.srt (
    echo 1 > data\input\subtitles\test_zh.srt
    echo 00:00:01,000 --^> 00:00:05,000 >> data\input\subtitles\test_zh.srt
    echo 大家好，这是一个测试字幕 >> data\input\subtitles\test_zh.srt
    echo. >> data\input\subtitles\test_zh.srt
    echo 2 >> data\input\subtitles\test_zh.srt
    echo 00:00:06,000 --^> 00:00:10,000 >> data\input\subtitles\test_zh.srt
    echo 我们正在测试VisionAI-ClipsMaster >> data\input\subtitles\test_zh.srt
)

if not exist data\input\subtitles\test_en.srt (
    echo 1 > data\input\subtitles\test_en.srt
    echo 00:00:01,000 --^> 00:00:05,000 >> data\input\subtitles\test_en.srt
    echo Hello, this is a test subtitle >> data\input\subtitles\test_en.srt
    echo. >> data\input\subtitles\test_en.srt
    echo 2 >> data\input\subtitles\test_en.srt
    echo 00:00:06,000 --^> 00:00:10,000 >> data\input\subtitles\test_en.srt
    echo We are testing VisionAI-ClipsMaster >> data\input\subtitles\test_en.srt
)
echo [成功] 测试数据创建完成

REM 运行语言检测测试
echo [步骤6] 正在运行语言检测测试...
python -m pytest tests\test_language_detector.py -v
if %errorlevel% neq 0 (
    echo [警告] 语言检测测试未完全通过，但继续执行
) else (
    echo [成功] 语言检测测试通过
)

REM 运行内存测试
echo [步骤7] 正在运行内存测试...
python tests\memory_test.py
if %errorlevel% neq 0 (
    echo [警告] 内存测试未完全通过，但继续执行
) else (
    echo [成功] 内存测试通过
)

REM 验证模型配置
echo [步骤8] 正在验证模型配置...
if exist configs\models\active_model.yaml (
    echo [成功] 激活模型配置文件存在
) else (
    echo [错误] 激活模型配置文件不存在
    goto :EOF
)

if exist configs\models\available_models\qwen2.5-7b-zh.yaml (
    echo [成功] 中文模型配置文件存在
) else (
    echo [错误] 中文模型配置文件不存在
    goto :EOF
)

if exist configs\models\available_models\mistral-7b-en.yaml (
    echo [成功] 英文模型配置文件存在
) else (
    echo [错误] 英文模型配置文件不存在
    goto :EOF
)

REM 验证语言检测器
python src\core\language_detector.py data\input\subtitles\test_zh.srt
if %errorlevel% neq 0 (
    echo [警告] 语言检测器验证未完全通过
) else (
    echo [成功] 语言检测器验证通过
)

echo.
echo === VisionAI-ClipsMaster 测试环境设置完成 ===
echo.
echo 可通过以下命令激活测试环境:
echo    test_venv\Scripts\activate
echo.
echo 运行内存测试: python tests\memory_test.py 