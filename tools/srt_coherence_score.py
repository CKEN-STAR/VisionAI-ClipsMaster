import re, os, sys, json
from typing import List, Dict, Tuple

TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def parse_srt_texts(path: str) -> List[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    out: List[str] = []
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln.strip()]
        if not lines:
            continue
        seen_time = False
        text_lines: List[str] = []
        for ln in lines:
            if not seen_time:
                if TIME_RE.search(ln):
                    seen_time = True
                continue
            # ignore metadata lines like '#ORIGINAL: ...'
            if re.match(r'^\s*#ORIGINAL:', ln, flags=re.IGNORECASE):
                continue
            text_lines.append(ln.strip())
        if not text_lines:
            continue
        out.append(" ".join(text_lines))
    return out


def clean_text(s: str) -> str:
    # keep CJK, letters and digits; remove punctuation/spaces
    return ''.join(ch for ch in s if _is_cjk(ch) or ch.isalnum())


def _is_cjk(ch: str) -> bool:
    cp = ord(ch)
    # CJK Unified Ideographs ranges (basic + extensions A/B partially sufficient for subtitles)
    return (0x4E00 <= cp <= 0x9FFF) or (0x3400 <= cp <= 0x4DBF)


def char_ngrams(s: str, n: int = 3) -> List[str]:
    if len(s) < n:
        if not s:
            return []
        # fallback to single chars if too short
        return [s[i:i+1] for i in range(len(s))]
    return [s[i:i+n] for i in range(0, len(s)-n+1)]


def jaccard(a: List[str], b: List[str]) -> float:
    if not a and not b:
        return 0.0
    sa, sb = set(a), set(b)
    u = len(sa | sb)
    if u == 0:
        return 0.0
    return len(sa & sb) / u


def adjacency_coherence(texts: List[str], n: int = 3) -> Dict:
    sims: List[float] = []
    pairs: List[Tuple[int, float]] = []
    tokens = [char_ngrams(clean_text(t), n=n) for t in texts]
    for i in range(len(tokens)-1):
        sim = jaccard(tokens[i], tokens[i+1])
        sims.append(sim)
        pairs.append((i, sim))
    if not sims:
        return {
            'count': len(texts), 'pairs': 0,
            'mean': 0.0, 'median': 0.0,
            'p25': 0.0, 'p75': 0.0,
            'ratio_lt_0_05': 0.0, 'ratio_lt_0_10': 0.0, 'ratio_gt_0_20': 0.0,
            'low_runs': []
        }
    ssorted = sorted(sims)
    def q(p: float) -> float:
        idx = max(0, min(int(p*len(ssorted)), len(ssorted)-1))
        return round(ssorted[idx], 4)
    def mean(xs: List[float]) -> float:
        return round(sum(xs)/len(xs), 4)
    # low-sim runs
    LOW = 0.08
    runs: List[int] = []
    cur = 0
    for v in sims:
        if v < LOW:
            cur += 1
        else:
            if cur > 0:
                runs.append(cur)
                cur = 0
    if cur > 0:
        runs.append(cur)
    # pick worst K examples indices
    worst = sorted(pairs, key=lambda x: x[1])[:8]
    return {
        'count': len(texts),
        'pairs': len(sims),
        'mean': mean(sims),
        'median': q(0.5),
        'p25': q(0.25),
        'p75': q(0.75),
        'ratio_lt_0_05': round(sum(1 for x in sims if x < 0.05)/len(sims), 4),
        'ratio_lt_0_10': round(sum(1 for x in sims if x < 0.10)/len(sims), 4),
        'ratio_gt_0_20': round(sum(1 for x in sims if x > 0.20)/len(sims), 4),
        'low_runs': runs[:10],
        'worst_examples': [
            {
                'pos': i,
                'sim': round(sim, 4),
                't0': texts[i][:24],
                't1': texts[i+1][:24]
            } for (i, sim) in worst
        ]
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Compute adjacency coherence of SRT: char-gram Jaccard between adjacent lines')
    ap.add_argument('srt_path')
    ap.add_argument('--ngram', type=int, default=3)
    args = ap.parse_args()

    texts = parse_srt_texts(args.srt_path)
    res = adjacency_coherence(texts, n=args.ngram)
    res.update({'path': args.srt_path})
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

