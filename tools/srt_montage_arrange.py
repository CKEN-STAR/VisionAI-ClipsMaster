import os
import re
import sys
import json
from typing import List, Tuple, Dict, Optional

# Simple SRT parser tailored for montage arranging
TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def to_timestamp(t: float) -> str:
    if t < 0:
        t = 0.0
    ms = int(round((t - int(t)) * 1000))
    total = int(t)
    s = total % 60
    m = (total // 60) % 60
    h = total // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def read_text(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk', errors='ignore') as f:
            return f.read()


def parse_blocks(content: str) -> List[List[str]]:
    # Split into blocks by blank line
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    res = []
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln is not None and ln.strip() != ""]
        if lines:
            res.append(lines)
    return res


def parse_items(path: str) -> List[Dict]:
    content = read_text(path)
    items = []
    for lines in parse_blocks(content):
        # find time line
        time_idx = -1
        for i, ln in enumerate(lines):
            if TIME_RE.search(ln):
                time_idx = i
                break
        if time_idx == -1:
            continue
        m = TIME_RE.search(lines[time_idx])
        sh, sm, ss, sms, eh, em, es, ems = m.groups()
        st = to_seconds(sh, sm, ss, sms)
        et = to_seconds(eh, em, es, ems)
        # text lines after time
        text_lines = [ln.strip() for ln in lines[time_idx + 1:]]
        # split text and meta (#ORIGINAL)
        text_main_lines: List[str] = []
        meta_lines: List[str] = []
        for ln in text_lines:
            if ln.strip().startswith('#ORIGINAL:') or ln.strip().startswith('#Original:'):
                meta_lines.append(ln.strip())
            else:
                text_main_lines.append(ln)
        full_text = " ".join(text_lines).strip()
        text_main = " ".join(text_main_lines).strip()
        meta_join = "\n".join(meta_lines) if meta_lines else ""
        # episode from meta if any
        episode: Optional[str] = None
        if meta_lines:
            meta_str = " ".join(meta_lines)
            m1 = re.search(r"episode\s*=\s*(\d+)", meta_str, re.IGNORECASE)
            if m1:
                episode = m1.group(1)
            else:
                m2 = re.search(r"第\s*(\d+)\s*集", meta_str)
                if m2:
                    episode = m2.group(1)
        items.append({
            "start": st,
            "end": et,
            "duration": max(0.0, et - st),
            "text": full_text,
            "text_main": text_main,
            "meta": meta_join,
            "episode": episode or "?"
        })
    return items


def normalize_text(s: str) -> str:
    # remove #ORIGINAL tail, whitespace collapse, lowercase
    s = s.strip()
    s = s.split('#ORIGINAL:')[0].strip()
    s = re.sub(r"\s+", "", s)
    return s.lower()


def char_ngrams(s: str, n: int = 3) -> set:
    if not s:
        return set()
    s = normalize_text(s)
    if len(s) < n:
        return {s}
    return {s[i:i+n] for i in range(len(s)-n+1)}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    if uni == 0:
        return 0.0
    return inter / uni


def impact_score(text_main: str) -> float:
    # higher means stronger; used for seed choice
    t = text_main or ""
    punct = sum(t.count(ch) for ch in ['!', '！', '?', '？', '…'])
    length = len(t)
    return punct * 3 + min(length, 60) / 10.0


def arrange_greedy(items: List[Dict], ngram: int = 3, w_aba: float = 0.8, w_same: float = 0.2) -> List[int]:
    N = len(items)
    grams = [char_ngrams(it.get('text_main') or it.get('text') or '', n=ngram) for it in items]
    episodes = [it.get('episode') for it in items]

    # seed: max impact
    seed_idx = max(range(N), key=lambda i: impact_score(items[i].get('text_main', '')))
    selected = [seed_idx]
    remaining = set(range(N))
    remaining.remove(seed_idx)

    while remaining:
        last = selected[-1]
        prev = selected[-2] if len(selected) >= 2 else None
        best_cost = None
        best_idx = None
        for i in list(remaining):
            sim = jaccard(grams[last], grams[i])
            # penalties
            aba_pen = 0.0
            if prev is not None:
                # A (prev2) -> B (prev1) -> A (candidate) pattern is penalized
                if episodes[prev] != episodes[last] and episodes[i] == episodes[prev]:
                    aba_pen = 1.0
            same_pen = 1.0 if episodes[i] == episodes[last] else 0.0
            cost = sim + w_aba * aba_pen + w_same * same_pen
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_idx = i
        selected.append(best_idx)
        remaining.remove(best_idx)
    return selected


def write_srt(path: str, items: List[Dict], order: List[int], gap: float = 0.15):
    lines: List[str] = []
    t = 0.5  # start from 0.5s to avoid 00:00:00,000 edge
    for i, idx in enumerate(order):
        it = items[idx]
        dur = it.get('duration', 2.0) or 2.0
        start_ts = to_timestamp(t)
        end_ts = to_timestamp(t + dur)
        lines.append(str(i + 1))
        lines.append(f"{start_ts} --> {end_ts}")
        text_main = (it.get('text_main') or it.get('text') or '').split('#ORIGINAL:')[0].strip()
        if not text_main:
            text_main = it.get('text') or ''
        lines.append(text_main)
        meta = it.get('meta')
        if meta:
            # ensure meta lines preserved and each on its own line
            for ln in meta.splitlines():
                ln = ln.strip()
                if ln:
                    lines.append(ln)
        lines.append("")
        t += dur + gap
    out = "\n".join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(out)


def adjacency_coherence_metrics(items: List[Dict], order: List[int], ngram: int = 3) -> Dict:
    sims: List[float] = []
    grams = [char_ngrams(items[i].get('text_main') or items[i].get('text') or '', n=ngram) for i in order]
    for i in range(len(order) - 1):
        s = jaccard(grams[i], grams[i + 1])
        sims.append(s)
    if not sims:
        return {"pairs": 0}
    sims_sorted = sorted(sims)
    def pct_lt(th: float) -> float:
        return sum(1 for v in sims if v < th) / len(sims)
    return {
        "pairs": len(sims),
        "mean": sum(sims) / len(sims),
        "p25": sims_sorted[int(0.25 * (len(sims_sorted) - 1))],
        "p75": sims_sorted[int(0.75 * (len(sims_sorted) - 1))],
        "ratio_lt_0_05": pct_lt(0.05),
        "ratio_lt_0_10": pct_lt(0.10),
        "ratio_gt_0_20": sum(1 for v in sims if v > 0.20) / len(sims),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Reorder a mixed SRT into montage style: minimize adjacency similarity, avoid A-B-A.")
    ap.add_argument("input", help="Path to mixed SRT")
    ap.add_argument("--out", help="Output SRT path (default: <input>_montage.srt)")
    ap.add_argument("--ngram", type=int, default=3, help="Character n for n-gram (default 3)")
    ap.add_argument("--w-aba", type=float, default=0.8, help="Penalty weight for A-B-A pattern")
    ap.add_argument("--w-same", type=float, default=0.2, help="Penalty weight for same-episode adjacency")
    ap.add_argument("--gap", type=float, default=0.15, help="Gap seconds between clips in new timeline")
    args = ap.parse_args()

    in_path = args.input
    if not os.path.exists(in_path):
        print(json.dumps({"error": "not_found", "input": in_path}, ensure_ascii=False))
        return 1

    out_path = args.out
    if not out_path:
        base, ext = os.path.splitext(in_path)
        out_path = f"{base}_montage.srt"

    items = parse_items(in_path)
    if not items:
        print(json.dumps({"error": "empty_or_unparsable", "input": in_path}, ensure_ascii=False))
        return 2

    order = arrange_greedy(items, ngram=args.ngram, w_aba=args.w_aba, w_same=args.w_same)
    write_srt(out_path, items, order, gap=args.gap)

    # quick metrics to STDOUT
    metrics = adjacency_coherence_metrics(items, order, ngram=args.ngram)
    episodes_seq = [items[i].get('episode') for i in order]
    # simple A-B-A count on top2 episodes
    from collections import Counter
    c = Counter(episodes_seq)
    top2 = [ep for ep, _ in c.most_common(2)]
    aba_count = 0
    if len(top2) == 2:
        for i in range(len(episodes_seq) - 2):
            a, b, c2 = episodes_seq[i], episodes_seq[i + 1], episodes_seq[i + 2]
            if a in top2 and b in top2 and c2 in top2 and a != b and a == c2:
                aba_count += 1

    print(json.dumps({
        "input": in_path,
        "output": out_path,
        "count": len(items),
        "weights": {"w_aba": args.w_aba, "w_same": args.w_same},
        "adjacency": metrics,
        "aba_top2": aba_count
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

