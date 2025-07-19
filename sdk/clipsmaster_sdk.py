import requests
from typing import Optional

API_URL = "http://localhost:8000/api/v1/generate"

class ClipsMasterClient:
    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        if api_key:
            self.session.headers = {"Authorization": f"Bearer {api_key}"}

    def generate_clip(self, video_path: str, srt_path: str, quant_level: str = "Q4_K_M", lang: str = "zh"):
        """
        Python SDK调用示例：生成视频剪辑
        """
        payload = {
            "video_path": video_path,
            "srt_path": srt_path,
            "quant_level": quant_level,
            "lang": lang
        }
        resp = self.session.post(API_URL, json=payload)
        resp.raise_for_status()
        return resp.json() 