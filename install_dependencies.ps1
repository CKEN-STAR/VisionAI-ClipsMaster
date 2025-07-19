# 确保在虚拟环境中
if (-not $env:VIRTUAL_ENV) {
    Write-Host "请先激活虚拟环境！"
    exit 1
}

# 创建必要的目录
New-Item -ItemType Directory -Force -Path "logs"
Write-Host "创建日志目录..."

# 升级pip
python -m pip install --upgrade pip

# 安装基础依赖
pip install -r requirements.txt

# 安装预提交钩子
pre-commit install

# 下载必要的模型和数据
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
python -c "import spacy; spacy.cli.download('en_core_web_sm'); spacy.cli.download('zh_core_web_sm')"

Write-Host "依赖安装完成！" 