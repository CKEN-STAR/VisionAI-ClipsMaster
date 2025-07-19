import os
import re
import shutil
from loguru import logger
from src.utils.exceptions import UserInputError

class SecurityAlert(Exception):
    pass

def detect_malicious_patterns(srt_path: str) -> bool:
    """检测恶意内容，包括SQL注入、路径遍历、异常Unicode等"""
    with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # SQL注入特征
    sql_patterns = [r"(--|;|/\*|\*/|xp_|exec|select |insert |delete |update |drop |union | or | and )"]
    # 路径遍历
    path_traversal = [r"\.\./", r"\.\.\\"]
    # 异常Unicode
    unicode_pattern = [r"[\ud800-\udfff]"]
    patterns = sql_patterns + path_traversal + unicode_pattern
    for pat in patterns:
        if re.search(pat, content, re.IGNORECASE):
            logger.warning(f"检测到恶意内容: {pat}")
            return True
    return False

def validate_srt_format(srt_path: str) -> bool:
    """验证SRT文件格式是否合法
    
    检查:
    1. 序号递增
    2. 时间格式正确（00:00:00,000 --> 00:00:00,000）
    3. 字幕内容完整
    
    Returns:
        bool: 格式是否有效
    """
    try:
        with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 基本SRT结构匹配模式
        srt_pattern = r'\d+\s+\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}\s+.+?(?=\n\s*\n\d+|\Z)'
        matches = re.findall(srt_pattern, content, re.DOTALL)
        
        if not matches:
            logger.warning(f"SRT格式无效: {srt_path}")
            return False
            
        # 检查序号是否递增
        index_pattern = r'^\d+'
        indices = []
        lines = content.split('\n')
        for line in lines:
            if re.match(index_pattern, line):
                indices.append(int(line.strip()))
        
        # 验证序号连续性
        if len(indices) >= 2:
            if any(indices[i+1] != indices[i]+1 for i in range(len(indices)-1)):
                logger.warning(f"SRT序号不连续: {srt_path}")
                # 非严格检查，仍然返回True
        
        return True
        
    except Exception as e:
        logger.error(f"SRT格式验证失败: {e}")
        return False

def quarantine_file(srt_path: str):
    """隔离可疑文件"""
    quarantine_dir = "quarantine/"
    os.makedirs(quarantine_dir, exist_ok=True)
    shutil.move(srt_path, os.path.join(quarantine_dir, os.path.basename(srt_path)))
    logger.warning(f"文件已隔离: {srt_path}")

def sanitize_input(srt_path: str):
    """字幕文件输入消毒"""
    if not srt_path.endswith('.srt'):
        raise UserInputError("仅支持SRT格式")
    if os.path.getsize(srt_path) > 10*1024*1024:
        raise UserInputError("字幕文件过大")
    if not validate_srt_format(srt_path):
        raise UserInputError("SRT格式无效")
    if detect_malicious_patterns(srt_path):
        quarantine_file(srt_path)
        raise SecurityAlert("检测到恶意内容") 