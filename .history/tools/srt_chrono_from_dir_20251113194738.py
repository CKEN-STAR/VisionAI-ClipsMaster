#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从“原片字幕目录”按原时间线做去冗快剪并汇总成一个SRT。
- 自动识别每集SRT（按文件名提取集数），集内按原顺序；
- 去口水/低信息量台词，优先保冲突/爆点；
- 重建输出时间轴（从 00:00:00 开始），并保留 #ORIGINAL: episode/index/start/end 元信息；

用法：
  python tools/srt_chrono_from_dir.py <dir_of_original_srts> [--out OUT.srt] [--retain 0.55] [--gap 0.15]
"""
import argparse
import os
import re
from typing import List, Dict, Any, Tuple
import sys
# 确保仓库根目录在 sys.path，便于 import src.*
CUR_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CUR_DIR, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# 依赖核心SRT解析器（支持多编码/健壮性更好）
from src.core.srt_parser import parse_srt

FILLERS = {
    '哈','哈哈','哈哈哈','呵','呵呵','啊','啊啊','哦','喔','嗯','呃','额','哎','哎呀','唉','喂','咦','嗨','嘿',
    '好的','好吧','知道了','行','好','哦哦','嗯嗯','不是吧','不会吧'
}
CONFLICT = [
    '杀','打','骗','告','报警','抓','证据','录音','监控','曝光','道歉','公司','合同','钱','债','借','还',
    '孩子','怀孕','流产','离婚','结婚','出轨','背叛','复仇','死亡','救','医院','法庭','案件','记者','直播',
    '选举','竞选','权力','威胁','勒索','危机','真相','谎言','阴谋'
]

TIME_RE_SIMPLE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")


def sec_to_ts(sec: float) -> str:
    if sec is None:
        sec = 0.0
    if sec < 0:
        sec = 0.0
    ms_total = int(round(sec * 1000))
    ss, ms = divmod(ms_total, 1000)
    mm, ss = divmod(ss, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def ms_to_ts(ms: int) -> str:
    if ms < 0:
        ms = 0
    ss, ms = divmod(ms, 1000)
    mm, ss = divmod(ss, 60)
    hh, mm = divmod(mm, 60)
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


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


def extract_episode_index(name: str) -> int:
    # 优先匹配“第X集”
    m = re.search(r"第\s*(\d+)\s*集", name)
    if m:
        return int(m.group(1))
    # 退化：取文件名中的第一段连续数字
    m = re.search(r"(\d+)", name)
    if m:
        return int(m.group(1))
    return 0


def collect_items_from_dir(dir_path: str) -> List[Dict[str, Any]]:
    srts: List[Tuple[int, str]] = []  # (episode, path)
    for root, _, files in os.walk(dir_path):
        for fn in files:
            if fn.lower().endswith('.srt'):
                ep = extract_episode_index(fn)
                srts.append((ep, os.path.join(root, fn)))
    if not srts:
        raise SystemExit(f"目录下未发现SRT文件: {dir_path}")
    srts.sort(key=lambda x: (x[0], x[1]))

    items: List[Dict[str, Any]] = []
    for ep, fp in srts:
        try:
            segs = parse_srt(fp)  # [{'id','start_time','end_time','duration','text'}]
        except Exception:
            continue
        for seg in segs:
            text = str(seg.get('text', '') or '').strip()
            if not text:
                continue
            idx = seg.get('id') if 'id' in seg else None
            st_s = float(seg.get('start_time') or 0.0)
            en_s = float(seg.get('end_time') or 0.0)
            item = {
                'text': text,
                'original_episode': ep,
                'original_index': int(idx) if isinstance(idx, int) else int(idx or 0),
                'original_start': sec_to_ts(st_s),
                'original_end': sec_to_ts(en_s),
            }
            items.append(item)
    return items


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
            # 解析 original_start 为毫秒
            m = TIME_RE_SIMPLE.match(str(it.get('original_start','')))
            if m:
                hh, mm, ss, ms = map(int, m.groups())
                tms = ((hh*60 + mm)*60 + ss)*1000 + ms
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

        # 保底：至少保留40%
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


def write_srt(items: List[Dict[str, Any]], out_path: str, gap_s: float = 0.15) -> None:
    gap_ms = int(round(gap_s * 1000))
    cur = 0
    with open(out_path, 'w', encoding='utf-8') as f:
        for i, it in enumerate(items, 1):
            dur = 1000  # 1秒保底
            start_ms = cur
            end_ms = cur + max(1, dur)
            cur = end_ms + gap_ms
            f.write(str(i) + "\n")
            f.write(f"{ms_to_ts(start_ms)} --> {ms_to_ts(end_ms)}\n")
            text = (it.get('text') or '').strip()
            if text:
                f.write(text + "\n")
            # 写原始元信息
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
    ap = argparse.ArgumentParser(description="从原片字幕目录按原时间线去冗快剪并汇总SRT")
    ap.add_argument('dir', help='原片字幕所在目录（包含每集SRT）')
    ap.add_argument('--out', help='输出SRT路径（默认：目录下 *_chrono_from_dir.srt）')
    ap.add_argument('--retain', type=float, default=float(os.getenv('CHRONO_RETAIN', '0.55')), help='每集保留比例(0.3-0.9)')
    ap.add_argument('--gap', type=float, default=0.15, help='段间间隔秒，默认0.15')
    args = ap.parse_args()

    dir_path = args.dir
    if not os.path.isdir(dir_path):
        raise SystemExit(f"目录不存在: {dir_path}")

    items = collect_items_from_dir(dir_path)
    if not items:
        raise SystemExit("目录下未收集到有效字幕条目")

    r = max(0.3, min(0.9, float(args.retain)))
    ordered = chrono_prune(items, retain_ratio=r)

    # 默认输出到目录下
    out_path = args.out or os.path.join(dir_path, os.path.basename(dir_path) + '_chrono_from_dir.srt')
    write_srt(ordered, out_path, gap_s=args.gap)

    print(f"wrote: {out_path}")
    print(f"input_count={len(items)} output_count={len(ordered)} retain_ratio~={len(ordered)/max(1,len(items)):.2f}")


if __name__ == '__main__':
    main()

