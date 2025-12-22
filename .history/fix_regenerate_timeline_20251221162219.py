#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复_regenerate_timeline方法"""

import re

with open('src/core/real_ai_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义旧代码模式（使用正则表达式匹配）
old_pattern = r'''            # 重新生成时间轴
            current_time = 0  # 毫秒
            regenerated_subtitles = \[\]

            for i, subtitle in enumerate\(all_viral_subtitles\):
                # 计算字幕时长（根据文本长度）
                text = subtitle\.get\('text', ''\)
                text_length = len\(text\)

                # 自适应时长（毫秒）：考虑文本长度 \+ 语义（句末/省略号/引号）\+ 原始时长提示
                # 基线：略高于原映射，避免"话未完即切"
                if text_length <= 5:
                    duration = 1800
                elif text_length <= 10:
                    duration = 2200
                elif text_length <= 15:
                    duration = 2700
                else:
                    duration = 3200

                # 语义加权：若非句末或省略、逗号收尾，适当延长
                try:
                    ends_with_punct = False
                    if text:
                        last = text\.strip\(\)\[-1\]
                        # 仅将真正句末标点视为完句（不含省略号与右引号）
                        ends_with_punct = last in \('。', '！', '？', '\.', '!', '\?'\)
                        # 未闭合引号 -> 视为未完句，延长
                        if \(text\.count\('"'\) > text\.count\('"'\)\) or \(text\.count\('''\) > text\.count\('''\)\):
                            ends_with_punct = False
                        # 省略号或逗号/顿号/破折号收尾 -> 延长
                        if last in \('…', '，', '、', '—', '—'\):
                            ends_with_punct = False
                    if not ends_with_punct:
                        duration \+= 600  # 语义尾音缓冲（增强）
                except Exception:
                    pass

                # 若带有原始时间码提示，则与基线取较大值，但不超过软上限
                try:
                    import re
                    def _parse_ms_local\(ts: str\):
                        m = re\.match\(r"\^\(\\d\{2\}\):\(\\d\{2\}\):\(\\d\{2\}\),\(\\d\{3\}\)\$", str\(ts or ''\)\.strip\(\)\)
                        if not m:
                            return None
                        hh, mm, ss, ms = map\(int, m\.groups\(\)\)
                        return \(\(hh\*60 \+ mm\)\*60 \+ ss\)\*1000 \+ ms
                    o_start = subtitle\.get\('original_start'\)
                    o_end = subtitle\.get\('original_end'\)
                    ms_s = _parse_ms_local\(o_start\)
                    ms_e = _parse_ms_local\(o_end\)
                    if isinstance\(ms_s, int\) and isinstance\(ms_e, int\) and ms_e > ms_s:
                        orig = ms_e - ms_s
                        # 给予软性冗余，避免紧切（增强上限/冗余）
                        duration = max\(duration, min\(7000, orig \+ 600\)\)
                except Exception:
                    pass

                # 生成时间轴
                start_time = self\._format_time\(current_time\)
                end_time = self\._format_time\(current_time \+ duration\)'''

# 定义新代码
new_code = '''            # 重新生成时间轴
            current_time = 0  # 毫秒
            regenerated_subtitles = []

            for i, subtitle in enumerate(all_viral_subtitles):
                text = subtitle.get('text', '')
                text_length = len(text)

                # 🔧 优先使用原始时间码的时长
                duration = None
                try:
                    import re
                    def _parse_ms_local(ts: str):
                        m = re.match(r"^(\\d{2}):(\\d{2}):(\\d{2}),(\\d{3})$", str(ts or '').strip())
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
                except Exception:
                    pass

                # 如果没有原始时间码，使用基于文本长度的估算
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
                            if (text.count('"') > text.count('"')) or (text.count(''') > text.count(''')):
                                ends_with_punct = False
                            if last in ('…', '，', '、', '—', '—'):
                                ends_with_punct = False
                        if not ends_with_punct:
                            duration += 600
                    except Exception:
                        pass

                # 生成时间轴
                start_time = self._format_time(current_time)
                end_time = self._format_time(current_time + duration)'''

# 简单的字符串替换方法
# 先找到关键标记
marker_start = "            # 重新生成时间轴\n            current_time = 0  # 毫秒"
marker_end = "end_time = self._format_time(current_time + duration)"

# 规范化换行符
content = content.replace('\r\n', '\n')

# 找到开始和结束位置
start_idx = content.find(marker_start)
if start_idx == -1:
    # 尝试CRLF
    marker_start_crlf = marker_start.replace('\n', '\r\n')
    start_idx = content.find(marker_start_crlf)

end_idx = content.find(marker_end, start_idx)
if end_idx != -1:
    end_idx = end_idx + len(marker_end)

if start_idx != -1 and end_idx != -1:
    print(f"找到代码块: {start_idx} - {end_idx}")
    # 替换
    new_content = content[:start_idx] + new_code + content[end_idx:]
    
    with open('src/core/real_ai_engine.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("替换成功!")
else:
    print(f"未找到代码块: start_idx={start_idx}, end_idx={end_idx}")
