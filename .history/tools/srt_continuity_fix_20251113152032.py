import os, re, sys, json
from typing import List, Dict, Tuple

# Parse SRT (compatible with tools/srt_content_compare.py)
TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def seconds_to_ts(sec: float) -> str:
    if sec < 0: sec = 0
    ms = int(round((sec - int(sec)) * 1000))
    s = int(sec) % 60
    m = (int(sec) // 60) % 60
    h = int(sec) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt_blocks(path: str) -> List[Dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()
    except Exception:
        return []
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    out = []
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln.strip()]
        if not lines:
            continue
        start = end = None
        text_lines: List[str] = []
        seen_time = False
        for ln in lines:
            m = TIME_RE.search(ln)
            if m and not seen_time:
                sh, sm, ss, sms, eh, em, es, ems = m.groups()
                start = to_seconds(sh, sm, ss, sms)
                end = to_seconds(eh, em, es, ems)
                seen_time = True
                continue
            if not seen_time:
                continue
            text_lines.append(ln.strip())
        if start is None or end is None:
            continue
        text = " ".join(text_lines).strip()
        out.append({
            'start': start,
            'end': end,
            'dur': max(0.0, end - start),
            'text': text
        })
    return out


def write_srt(path: str, items: List[Dict]):
    lines = []
    for i, it in enumerate(items, start=1):
        st = seconds_to_ts(it['start'])
        et = seconds_to_ts(it['end'])
        lines.append(str(i))
        lines.append(f"{st} --> {et}")
        # text can contain internal newlines if needed (we keep single line)
        lines.append(it['text'] or '')
        lines.append('')
    data = "\n".join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)


# Simple continuity smoother: remove short singleton blocks A-B-A where len(B) < min_block

def compress_blocks(labels: List[str]) -> List[Tuple[str, int, int, int]]:
    """Return list of (label, start_idx, end_idx, length) where indices refer to original sequence."""
    if not labels:
        return []
    res = []
    cur = labels[0]
    start = 0
    for i in range(1, len(labels)):
        if labels[i] != cur:
            res.append((cur, start, i-1, i-start))
            cur = labels[i]
            start = i
    res.append((cur, start, len(labels)-1, len(labels)-start))
    return res


def build_labels_from_filenames(mixed_path: str, source_root: str, items: List[Dict]) -> List[str]:
    # Heuristic: if text contains markers like "#E{num}" use that; else derive from previous export patterns in filename
    # For now, we can't robustly recover episode; fallback to filename bucket by keywords in text is unreliable.
    # We keep UNKNOWN labels and let GUI-integrated fix handle exact episode with metadata.
    return ['UNKNOWN'] * len(items)


def fix_ab_singletons(labels: List[str], items: List[Dict], min_block: int = 2) -> List[int]:
    """Return a new order of indices where patterns A B A with len(B) < min_block are smoothed by moving B near its neighbors if possible.
    Conservative: only move blocks with length < min_block and both neighbors equal.
    """
    if len(items) <= 2:
        return list(range(len(items)))
    blocks = compress_blocks(labels)
    order = list(range(len(items)))
    # find patterns A B A
    i = 0
    while i < len(blocks)-2:
        A1, s1, e1, n1 = blocks[i]
        B, s2, e2, n2 = blocks[i+1]
        A2, s3, e3, n3 = blocks[i+2]
        if A1 == A2 and B != A1 and n2 < min_block:
            # Move the small middle block B after the second A block (merge with future same B if any)
            # Compute indices of B
            idxs_B = order[s2:e2+1]
            # Remove B from current position in order
            del order[s2:e2+1]
            # After removal, blocks indices change; recompute new insertion point as end of (updated) A block
            insert_pos = e3 - (e2 - s2 + 1) + 1  # end of second A block + 1
            if insert_pos < 0: insert_pos = 0
            if insert_pos > len(order): insert_pos = len(order)
            for k, idx in enumerate(idxs_B):
                order.insert(insert_pos + k, idx)
            # Rebuild blocks based on new order and continue scanning from previous block
            new_labels = [labels[j] for j in order]
            blocks = compress_blocks(new_labels)
            i = max(0, i-1)
            labels = new_labels
            continue
        i += 1
    return order


def reassign_times_by_order(items: List[Dict], order: List[int], gap: float = 0.06) -> List[Dict]:
    out = []
    t = 0.0
    for idx in order:
        it = items[idx]
        dur = max(0.0, it.get('dur', it['end'] - it['start']))
        out.append({'start': t, 'end': t + dur, 'text': it['text']})
        t += dur + gap
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Continuity fixer for mixed SRT: smooth out A-B-A singletons conservatively.')
    ap.add_argument('mixed_srt', help='path to mixed SRT')
    ap.add_argument('--source-root', default=None, help='root dir of original SRTs (optional)')
    ap.add_argument('--min-block', type=int, default=2, help='min middle-block length to keep (default=2 meaning singletons will be moved)')
    ap.add_argument('--out', default=None, help='output path (default: <mixed>_fixed.srt)')
    args = ap.parse_args()

    mixed = args.mixed_srt
    items = parse_srt_blocks(mixed)
    if not items:
        print(json.dumps({'error': 'mixed_srt_empty_or_unparsable', 'mixed_srt': mixed}, ensure_ascii=False))
        return

    labels = build_labels_from_filenames(mixed, args.source_root or '', items)
    order = fix_ab_singletons(labels, items, min_block=args.min_block)
    fixed_items = reassign_times_by_order(items, order)

    out_path = args.out or (os.path.splitext(mixed)[0] + '_fixed.srt')
    write_srt(out_path, fixed_items)
    print(json.dumps({'status': 'ok', 'out': out_path, 'count': len(fixed_items)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

