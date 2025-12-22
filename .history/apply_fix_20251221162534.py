#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复_regenerate_timeline方法 - 优先使用原始时间码"""

import re

with open('src/core/real_ai_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 中文引号使用Unicode转义
LEFT_DOUBLE = '\u201c'  # "
RIGHT_DOUBLE = '\u201d'  # "
LEFT_SINGLE = '\u2018'  # '
RIGHT_SINGLE = '\u2019'  # '

# 定义新的_regenerate_timeline方法
new_method = f'''    def _regenerate_timeline(self, all_viral_subtitles: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """重新生成时间轴 - 从00:00:00开始，优先使用原始时间码的时长"""
        try:
            logger.info(f"开始重新生成时间轴，共 {{len(all_viral_subtitles)}} 条字幕")

            # 重新生成时间轴
            current_time = 0  # 毫秒
            regenerated_subtitles = []

            for i, subtitle in enumerate(all_viral_subtitles):
                text = subtitle.get('text', '')
                text_length = len(text)

                # 🔧 优先使用原始时间码的时长（精确到毫秒）
                duration = None
                try:
                    def _parse_ms_local(ts: str):
                        m = re.match(r"^(\\d{{2}}):(\\d{{2}}):(\\d{{2}}),(\\d{{3}})$", str(ts or '').strip())
                        if not m:
                            return None
                        hh, mm, ss, ms = map(int, m.groups())
                        return ((hh*60 + mm)*60 + ss)*1000 + ms
                    o_start = subtitle.get('original_start')
                    o_end = subtitle.get('original_end')
                    ms_s = _parse_ms_local(o_start)
                    ms_e = _parse_ms_local(o_end)
                    if isinstance(ms_s, int) and isinstance(ms_e, int) and ms_e > ms_s:
                        # 使用原始时间码的时长，添加少量缓冲避免紧切
                        duration = ms_e - ms_s + 100  # 添加100ms缓冲
                        logger.debug(f"字幕{{i+1}}：使用原始时长 {{duration}}ms (原始: {{o_start}} -> {{o_end}})")
                except Exception as e:
                    logger.debug(f"字幕{{i+1}}：解析原始时间码失败: {{e}}")

                # 如果没有原始时间码，使用基于文本长度的估算（降级方案）
                if duration is None:
                    if text_length <= 5:
                        duration = 1800
                    elif text_length <= 10:
                        duration = 2200
                    elif text_length <= 15:
                        duration = 2700
                    else:
                        duration = 3200

                    # 语义加权：若非句末，适当延长
                    try:
                        ends_with_punct = False
                        if text:
                            last = text.strip()[-1]
                            ends_with_punct = last in ('。', '！', '？', '.', '!', '?')
                            if (text.count('{LEFT_DOUBLE}') > text.count('{RIGHT_DOUBLE}')) or (text.count('{LEFT_SINGLE}') > text.count('{RIGHT_SINGLE}')):
                                ends_with_punct = False
                            if last in ('…', '，', '、', '—', '—'):
                                ends_with_punct = False
                        if not ends_with_punct:
                            duration += 600
                    except Exception:
                        pass
                    logger.debug(f"字幕{{i+1}}：使用文本长度估算时长 {{duration}}ms")

                # 生成时间轴
                start_time = self._format_time(current_time)
                end_time = self._format_time(current_time + duration)

                # 构建新字幕对象，保留原始时间码信息
                new_subtitle = {{
                    'index': i + 1,
                    'start': start_time,
                    'end': end_time,
                    'text': text
                }}

                # 保留原始字幕的映射信息（如果存在）
                if 'original_episode' in subtitle:
                    new_subtitle['original_episode'] = subtitle['original_episode']
                if 'original_index' in subtitle:
                    new_subtitle['original_index'] = subtitle['original_index']
                if 'original_start' in subtitle:
                    new_subtitle['original_start'] = subtitle['original_start']
                if 'original_end' in subtitle:
                    new_subtitle['original_end'] = subtitle['original_end']

                regenerated_subtitles.append(new_subtitle)

                current_time += duration

            logger.info(f"时间轴重新生成完成，总时长: {{self._format_time(current_time)}}")

            return regenerated_subtitles

        except Exception as e:
            logger.error(f"重新生成时间轴失败: {{str(e)}}")
            import traceback
            logger.error(traceback.format_exc())
            return all_viral_subtitles'''

# 使用正则表达式匹配整个方法
pattern = r'(    def _regenerate_timeline\(self, all_viral_subtitles: List\[Dict\[str, Any\]\], language: str\) -> List\[Dict\[str, Any\]\]:.*?)(    def _format_time\(self, milliseconds: int\))'

match = re.search(pattern, content, re.DOTALL)
if match:
    print(f"找到方法，位置: {match.start()} - {match.end()}")
    # 替换
    new_content = content[:match.start()] + new_method + '\n\n' + match.group(2) + content[match.end():]
    
    with open('src/core/real_ai_engine.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ 替换成功!")
else:
    print("❌ 未找到方法")
