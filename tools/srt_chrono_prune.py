#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按原片时间线进行“去冗快剪”的SRT重排工具（后处理版）
- 按 original_episode 升序，组内按 original_index 或 original_start 升序
- 评分保留：去掉口水/无用台词，保留更有爆点/冲突的条目
- 重建输出时间轴（从 00:00:00 开始串接），段间可配置间隔
用法：
  python tools/srt_chrono_prune.py <input.srt> [--out OUT.srt] [--retain 0.55] [--gap 0.15]
"""
import argparse
import os
import re
from typing import List, Dict, Any, Tuple

TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
ORIG_RE = re.compile(r"^\s*#ORIGINAL:\s*(.*)$", re.IGNORECASE)


def parse_srt_with_meta(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    items: List[Dict[str, Any]] = []
    i = 0
    n = len(lines)
    while i < n:
        # index line
        if not lines[i].strip().isdigit():
            i += 1
            continue
        sid = int(lines[i].strip())
        i += 1
        if i >= n:
            break
        # time line
        m = TIME_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        i += 1
        sh, sm, ss, sms, eh, em, es, ems = map(int, m.groups())
        start_ms = ((sh*60 + sm)*60 + ss)*1000 + sms
        end_ms = ((eh*60 + em)*60 + es)*1000 + ems
        text_lines = []
        meta_line = None
        while i < n and lines[i].strip() != "":
            ln = lines[i]
            if ORIG_RE.match(ln):
                meta_line = ln.strip()
            else:
                text_lines.append(ln)
            i += 1
        # skip blank line
        while i < n and lines[i].strip() == "":
            i += 1
        text = "\n".join([t for t in text_lines if t.strip()])
        meta = parse_original_meta(meta_line) if meta_line else {}
        items.append({
            'id': sid,
            'start_ms': start_ms,
            'end_ms': end_ms,
            'duration_ms': max(1, end_ms - start_ms),
            'text': text,
            'original_episode': meta.get('episode'),
            'original_index': meta.get('index'),
            'original_start': meta.get('start'),
            'original_end': meta.get('end'),
        })
    return items


def parse_original_meta(line: str) -> Dict[str, Any]:
    # 形如: #ORIGINAL: episode=2, index=58, start=00:08:03,456, end=00:08:05,123
    if not line:
        return {}
    m = ORIG_RE.match(line)
    if not m:
        return {}
    payload = m.group(1)
    parts = [p.strip() for p in payload.split(',')]
    meta: Dict[str, Any] = {}
    for p in parts:
        if '=' not in p:
            continue
        k, v = [x.strip() for x in p.split('=', 1)]
        if k == 'episode':
            try:
                meta['episode'] = int(re.sub(r"[^0-9]", "", v) or 0)
            except Exception:
                meta['episode'] = 0
        elif k == 'index':
            try:
                meta['index'] = int(re.sub(r"[^0-9]", "", v) or 0)
            except Exception:
                meta['index'] = 0
        elif k in ('start', 'end'):
            meta[k] = v
    return meta


# ============ 评分与筛选 ============

def _norm_text(s: str) -> str:
    if not s:
        return ""
    s2 = re.sub(r"(?im)^\s*#ORIGINAL:.*$", "", s)
    s2 = re.sub(r"\s+", "", s2)
    return s2


def _grams(s: str, n: int = 3) -> set:
    s2 = _norm_text(s)
    if not s2:
        return set()
    if len(s2) < n:
        return {s2}
    return {s2[i:i+n] for i in range(len(s2)-n+1)}


def _jacc(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return (inter/uni) if uni else 0.0


FILLERS = {
    '哈','哈哈','哈哈哈','呵','呵呵','啊','啊啊','哦','喔','嗯','呃','额','哎','哎呀','唉','喂','咦','嗨','嘿',
    '好的','好吧','知道了','行','好','哦哦','嗯嗯','不是吧','不会吧'
}
CONFLICT = [
    '杀','打','骗','告','报警','抓','证据','录音','监控','曝光','道歉','公司','合同','钱','债','借','还',
    '孩子','怀孕','流产','离婚','结婚','出轨','背叛','复仇','死亡','救','医院','法庭','案件','记者','直播',
    '选举','竞选','权力','威胁','勒索','危机','真相','谎言','阴谋'
]


def is_filler(t: str) -> bool:
    s = _norm_text(t)
    if not s:
        return True
    if len(s) <= 2:
        return True
    if re.fullmatch(r"[\W_·、，,。.!！?？…~\-：:；;（）()\[\]\s]+", s):
        return True
    if len(set(s)) <= 2 and any(ch in '哈呵啊哦嗯呃额' for ch in set(s)):
        return True
    if s in FILLERS:
        return True
    return False


def score_text(t: str) -> float:
    s = _norm_text(t)
    if is_filler(s):
        return -1.0
    score = 0.0
    bang = t.count('!') + t.count('！')
    q = t.count('?') + t.count('？')
    score += min(0.8, 0.4*bang + 0.4*q)
    kw = sum(1 for w in CONFLICT if w in t)
    if kw >= 2:
        score += 1.0
    elif kw == 1:
        score += 0.5
    L = len(s)
    if 6 <= L <= 36:
        score += 0.3
    elif 37 <= L <= 56:
        score += 0.15
    elif L < 4:
        score -= 0.5
    elif L > 70:
        score -= 0.4
    return score


def parse_ms(ts: str):
    m = re.match(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$", str(ts or '').strip())
    if not m:
        return None
    hh, mm, ss, ms = map(int, m.groups())
    return ((hh*60 + mm)*60 + ss)*1000 + ms


# ============ 主逻辑 ============

def chrono_prune(items: List[Dict[str, Any]], retain_ratio: float = 0.55) -> List[Dict[str, Any]]:
    # 分组 by episode
    groups: Dict[int, List[Dict[str, Any]]] = {}
    for it in items:
        ep = it.get('original_episode') or it.get('episode') or 0
        try:
            ep = int(ep)
        except Exception:
            ep = 0
        groups.setdefault(ep, []).append(it)

    ordered: List[Dict[str, Any]] = []
    for ep in sorted(groups.keys()):
        g = groups[ep]
        def _key(it):
            idx = it.get('original_index')
            if isinstance(idx, int):
                return (0, idx)
            tms = parse_ms(it.get('original_start', ''))
            if tms is not None:
                return (1, tms)
            return (2, 0)
        g_sorted = sorted(g, key=_key)

        scored = [(i, score_text(str(it.get('text','') or '')), it) for i, it in enumerate(g_sorted)]
        base = [(i, sc, it) for (i, sc, it) in scored if sc >= 0]
        total = len(g_sorted)
        target = max(1, min(len(base) if base else total, int(round(retain_ratio * total))))
        top = sorted(base if base else [(i, sc, it) for (i, sc, it) in scored], key=lambda x: x[1], reverse=True)[:target]
        sel_idx = set(i for i, sc, it in top)
        selected = [it for i, it in enumerate(g_sorted) if i in sel_idx]

        # 集内近重复去重
        final_ep: List[Dict[str, Any]] = []
        last_g = None
        for it in selected:
            g3 = _grams(str(it.get('text','') or ''))
            if last_g is not None and _jacc(g3, last_g) > 0.7:
                continue
            final_ep.append(it)
            last_g = g3

        # 保底40%
        min_cnt = max(1, int(0.4 * total))
        if len(final_ep) < min_cnt:
            for it in g_sorted:
                if it in final_ep:
                    continue
                final_ep.append(it)
                if len(final_ep) >= min_cnt:
                    break

        ordered.extend(final_ep)
    return ordered


def ms_to_ts(ms: int) -> str:
    if ms < 0:
        ms = 0
    ss, ms = divmod(ms, 1000)
    mm, ss = divmod(ss, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def write_srt(items: List[Dict[str, Any]], out_path: str, gap_s: float = 0.15) -> None:
    gap_ms = int(round(gap_s * 1000))
    cur = 0
    with open(out_path, 'w', encoding='utf-8') as f:
        for i, it in enumerate(items, 1):
            dur = int(it.get('duration_ms') or 1000)
            start_ms = cur
            end_ms = cur + max(1, dur)
            cur = end_ms + gap_ms
            f.write(str(i) + "\n")
            f.write(f"{ms_to_ts(start_ms)} --> {ms_to_ts(end_ms)}\n")
            text = (it.get('text') or '').strip()
            if text:
                f.write(text + "\n")
            # 保留原始元信息（如有）
            ep = it.get('original_episode')
            idx = it.get('original_index')
            ost = it.get('original_start')
            oen = it.get('original_end')
            meta = []
            if ep is not None:
                meta.append(f"episode={ep}")
            if idx is not None:
                meta.append(f"index={idx}")
            if ost:
                meta.append(f"start={ost}")
            if oen:
                meta.append(f"end={oen}")
            if meta:
                f.write("#ORIGINAL: " + ", ".join(meta) + "\n")
            f.write("\n")


def main():
    ap = argparse.ArgumentParser(description="按原时间线快节奏去冗重排SRT")
    ap.add_argument('input', help='输入SRT（包含#ORIGINAL元信息更佳）')
    ap.add_argument('--out', help='输出SRT路径（默认同目录 *_chrono.srt）')
    ap.add_argument('--retain', type=float, default=float(os.getenv('CHRONO_RETAIN', '0.55')), help='每集保留比例(0.3-0.9), 默认0.55')
    ap.add_argument('--gap', type=float, default=0.15, help='段间间隔秒，默认0.15')
    args = ap.parse_args()

    in_path = args.input
    if not os.path.isfile(in_path):
        raise SystemExit(f"输入文件不存在: {in_path}")
    base, ext = os.path.splitext(in_path)
    out_path = args.out or (base + '_chrono.srt')

    items = parse_srt_with_meta(in_path)
    if not items:
        raise SystemExit("输入SRT无有效条目")

    r = max(0.3, min(0.9, float(args.retain)))
    ordered = chrono_prune(items, retain_ratio=r)

    write_srt(ordered, out_path, gap_s=args.gap)

    print(f"wrote: {out_path}")
    print(f"input_count={len(items)} output_count={len(ordered)} retain_ratio~={len(ordered)/max(1,len(items)):.2f}")


if __name__ == '__main__':
    main()

