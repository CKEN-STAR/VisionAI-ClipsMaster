import os, re, sys, json, statistics
from typing import List, Dict, Tuple

TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path: str) -> List[Tuple[float, float, str]]:
    items = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()
    except Exception:
        return []
    # Split into blocks by blank lines
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln.strip()]
        if not lines:
            continue
        # Find the first timecode line
        for ln in lines:
            m = TIME_RE.search(ln)
            if m:
                sh, sm, ss, sms, eh, em, es, ems = m.groups()
                st = to_seconds(sh, sm, ss, sms)
                et = to_seconds(eh, em, es, ems)
                # Remaining text
                text_lines = []
                seen_time = False
                for ln2 in lines:
                    if not seen_time and TIME_RE.search(ln2):
                        seen_time = True
                        continue
                    if seen_time:
                        text_lines.append(ln2.strip())
                text = " ".join(text_lines).strip()
                items.append((st, et, text))
                break
    # sort just in case
    items.sort(key=lambda x: (x[0], x[1]))
    return items


def stats_for(path: str) -> Dict:
    if not os.path.exists(path):
        return {"path": path, "error": "not_found"}
    items = parse_srt(path)
    if not items:
        return {"path": path, "count": 0, "error": "empty_or_unparsable"}
    durs = [max(0.0, et - st) for st, et, _ in items]
    starts = [st for st, _, _ in items]
    monotonic = all(starts[i] <= starts[i+1] + 1e-6 for i in range(len(starts)-1))
    # forward jumps (gaps), and backward jumps (violations)
    gaps = [max(0.0, starts[i+1] - starts[i]) for i in range(len(starts)-1)]
    backward = [starts[i] - starts[i+1] for i in range(len(starts)-1) if starts[i] > starts[i+1]]
    # Minute-bin alternation score
    bins = [int(st // 60) for st in starts]
    bin_transitions = sum(1 for i in range(len(bins)-1) if bins[i] != bins[i+1])
    # Alternation heuristic: transitions between two dominant bins back-and-forth
    from collections import Counter
    c = Counter(bins)
    top2 = [b for b,_ in c.most_common(2)]
    alt_count = 0
    if len(top2) == 2:
        b1, b2 = top2
        for i in range(len(bins)-2):
            if bins[i] in top2 and bins[i+1] in top2 and bins[i+2] in top2:
                if bins[i] == b1 and bins[i+1] == b2 and bins[i+2] == b1:
                    alt_count += 1
                if bins[i] == b2 and bins[i+1] == b1 and bins[i+2] == b2:
                    alt_count += 1
    def pct(x, th):
        return sum(1 for v in x if v < th) / len(x)
    res = {
        "path": path,
        "count": len(items),
        "duration_stats": {
            "mean": statistics.mean(durs),
            "median": statistics.median(durs),
            "p25": statistics.quantiles(durs, n=4)[0] if len(durs) >= 4 else durs[0],
            "p75": statistics.quantiles(durs, n=4)[-1] if len(durs) >= 4 else durs[-1],
            "min": min(durs),
            "max": max(durs),
            "lt2s": pct(durs, 2.0),
            "lt3s": pct(durs, 3.0),
            "lt5s": pct(durs, 5.0)
        },
        "time_order": {
            "monotonic": monotonic,
            "backward_jumps": len(backward),
            "max_backward_jump": max(backward) if backward else 0.0,
            "avg_gap": statistics.mean(gaps) if gaps else 0.0,
            "p90_gap": (sorted(gaps)[int(0.9*len(gaps))] if gaps else 0.0),
            "bin_transitions": bin_transitions,
            "alternation_top2": alt_count
        }
    }
    return res


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no_paths"}, ensure_ascii=False))
        return
    out = {}
    for p in sys.argv[1:]:
        out[p] = stats_for(p)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

