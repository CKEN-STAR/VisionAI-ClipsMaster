from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import time
from threading import Lock
from typing import Dict, Any

router = APIRouter(tags=["language"])

# 当前语言状态
current_lang = 'zh'
# 切换频率限制（每分钟最多3次）
switch_log = []
switch_lock = Lock()

@router.post("/switch_lang")
def force_switch(lang: str) -> Dict[str, str]:
    """强制切换处理语言，安全防护：每分钟最多切换3次"""
    global current_lang, switch_log
    if lang not in ['zh', 'en']:
        raise HTTPException(400, detail="Invalid language")
    now = time.time()
    with switch_lock:
        # 清理过期记录
        switch_log = [t for t in switch_log if now - t < 60]
        if len(switch_log) >= 3:
            raise HTTPException(429, detail="切换过于频繁，请稍后再试")
        switch_log.append(now)
        current_lang = lang
    return {"status": f"已强制切换至{lang.upper()}模式"}

@router.get("/current_lang")
def get_current_lang() -> Dict[str, Any]:
    """获取当前使用的语言"""
    now = time.time()
    with switch_lock:
        # 清理过期记录
        switch_log = [t for t in switch_log if now - t < 60]
        remaining = 3 - len(switch_log)
    
    return {
        "current_language": current_lang,
        "language_name": "中文" if current_lang == "zh" else "English",
        "remaining_switches": remaining,
        "cooldown": 60 - int(now - switch_log[0]) if switch_log else 0
    } 