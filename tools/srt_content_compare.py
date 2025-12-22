import os, re, sys, json
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
import unicodedata

TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")
ORIG_LINE_RE = re.compile(r"^\s*#ORIGINAL\s*:(?P<src>.*)$")
ORIG_START_RE = re.compile(r"^\s*#ORIGINAL_START\s*:(?P<ts>[0-9:.]+)")
ORIG_END_RE = re.compile(r"^\s*#ORIGINAL_END\s*:(?P<ts>[0-9:.]+)")


def to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_ts(ts: str) -> Optional[float]:
    # Accept HH:MM:SS,mmm or HH:MM:SS.mmm
    m = re.match(r"^(\d{2}):(\d{2}):(\d{2})[\.,](\d{3})$", ts.strip())
    if not m:
        return None
    h, mi, s, ms = m.groups()
    return to_seconds(h, mi, s, ms)


def parse_srt_with_meta(path: str) -> List[Dict]:
    """Parse SRT and try to extract optional #ORIGINAL metadata lines per block.
    Returns list of dict: {start, end, text, meta: {original, original_start, original_end}}
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk', errors='ignore') as f:
            content = f.read()
    except Exception:
        return []
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    items: List[Dict] = []
    for b in blocks:
        lines = [ln for ln in b.splitlines() if ln.strip()]
        if not lines:
            continue
        start = end = None
        text_lines: List[str] = []
        meta: Dict[str, Optional[str]] = {"original": None, "original_start": None, "original_end": None}
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
            # meta or text
            m1 = ORIG_LINE_RE.match(ln)
            if m1:
                meta["original"] = m1.group("src").strip()
                continue
            m2 = ORIG_START_RE.match(ln)
            if m2:
                meta["original_start"] = m2.group("ts").strip()
                continue
            m3 = ORIG_END_RE.match(ln)
            if m3:
                meta["original_end"] = m3.group("ts").strip()
                continue
            text_lines.append(ln.strip())
        if start is None or end is None:
            continue
        text = " ".join(text_lines).strip()
        items.append({
            "start": start,
            "end": end,
            "text": text,
            "meta": meta
        })
    items.sort(key=lambda x: (x["start"], x["end"]))
    return items


def normalize_text(s: str) -> str:
    s = s.lower().replace("\u3000", " ")
    # keep only letters and numbers (drop punctuation and spaces)
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] in ('L', 'N'))


def derive_episode_id(path: str, source_root: str) -> str:
    rel = os.path.relpath(path, source_root)
    base = os.path.splitext(os.path.basename(path))[0]
    # try to use folder containing '集' or 'ep'
    parts = rel.replace('\\', '/').split('/')
    for p in reversed(parts[:-1]):
        if ('集' in p) or p.lower().startswith('ep') or p.lower().startswith('episode'):
            return p
    return base


def list_source_srts(root_dir: str, exclude_path: str) -> List[str]:
    out = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if not fn.lower().endswith('.srt'):
                continue
            p = os.path.join(dirpath, fn)
            # exclude the mixed srt itself
            if os.path.abspath(p) == os.path.abspath(exclude_path):
                continue
            # avoid picking other mixed srt files if name contains '混剪'
            if '混剪' in fn:
                continue
            out.append(p)
    return out


def build_source_index(srt_paths: List[str], source_root: str):
    sources = []
    total_items = 0
    for p in srt_paths:
        items = parse_srt_with_meta(p)
        epi = derive_episode_id(p, source_root)
        norm_items = []
        for it in items:
            norm_items.append({
                'start': it['start'],
                'end': it['end'],
                'text': it['text'],
                'norm': normalize_text(it['text']),
            })
        sources.append({'path': p, 'episode': epi, 'items': norm_items})
        total_items += len(norm_items)
    return sources, total_items


def best_match(norm_text: str, sources) -> Optional[Tuple[str, str, float, int]]:
    """Return (source_path, episode, match_ratio, index_in_source) or None"""
    best = None
    for src in sources:
        items = src['items']
        for idx, it in enumerate(items):
            if not it['norm']:
                continue
            # quick substring boost
            if norm_text and it['norm'] and (norm_text in it['norm'] or it['norm'] in norm_text):
                ratio = 0.999 if norm_text == it['norm'] else 0.8
            else:
                ratio = SequenceMatcher(None, norm_text, it['norm']).ratio()
            if (best is None) or (ratio > best[2]):
                best = (src['path'], src['episode'], ratio, idx)
    return best


def alternation_top2(seq: List[str]) -> int:
    from collections import Counter
    if not seq:
        return 0
    c = Counter(seq)
    top2 = [k for k,_ in c.most_common(2)]
    if len(top2) < 2:
        return 0
    a, b = top2
    count = 0
    for i in range(len(seq)-2):
        if seq[i] in top2 and seq[i+1] in top2 and seq[i+2] in top2:
            if seq[i] == a and seq[i+1] == b and seq[i+2] == a:
                count += 1
            if seq[i] == b and seq[i+1] == a and seq[i+2] == b:
                count += 1
    return count


def compress_blocks(seq: List[str]) -> List[Tuple[str, int]]:
    if not seq:
        return []
    out = []
    cur = seq[0]
    n = 1
    for s in seq[1:]:
        if s == cur:
            n += 1
        else:
            out.append((cur, n))
            cur, n = s, 1
    out.append((cur, n))
    return out


def find_abab_examples(seq: List[str], k: int = 2) -> List[Tuple[int, str, str]]:
    """Return up to k examples of indices where A->B->A happens, with (i, A, B)."""
    out = []
    for i in range(len(seq)-2):
        a, b, c = seq[i], seq[i+1], seq[i+2]
        if a != b and a == c:
            out.append((i, a, b))
            if len(out) >= k:
                break
    return out


def compare_contents(mixed_srt: str, source_root: str, max_examples: int = 3) -> Dict:
    mixed_items = parse_srt_with_meta(mixed_srt)
    if not mixed_items:
        return {"error": "mixed_srt_empty_or_unparsable", "mixed": mixed_srt}
    source_paths = list_source_srts(source_root, mixed_srt)
    sources, total_items = build_source_index(source_paths, source_root)
    if not sources:
        return {"error": "no_source_srt_found", "source_root": source_root}

    mappings = []  # each: {mix_idx, text, source_path, episode, ratio}
    seq = []       # sequence of episode ids along mixed timeline
    for i, it in enumerate(mixed_items):
        norm = normalize_text(it['text'])
        bm = best_match(norm, sources)
        if bm and bm[2] >= 0.68:
            source_path, episode, ratio, idx_in_src = bm
            mappings.append({
                'mix_index': i,
                'mix_start': it['start'],
                'mix_text': it['text'],
                'source_path': source_path,
                'episode': episode,
                'match_ratio': round(float(ratio), 3),
                'source_index': idx_in_src
            })
            seq.append(episode)
        else:
            mappings.append({
                'mix_index': i,
                'mix_start': it['start'],
                'mix_text': it['text'],
                'source_path': None,
                'episode': None,
                'match_ratio': 0.0,
                'source_index': -1
            })
            seq.append('UNKNOWN')

    # metrics on sequence
    switches = sum(1 for i in range(len(seq)-1) if seq[i] != seq[i+1])
    alt2 = alternation_top2([s for s in seq if s != 'UNKNOWN'])
    blocks = compress_blocks(seq)

    # prepare examples
    examples = []
    for pos, A, B in find_abab_examples(seq, k=max_examples):
        ex = []
        for j in (pos, pos+1, pos+2):
            m = mappings[j]
            ex.append({
                'mix_index': j,
                'episode': m['episode'],
                'text_excerpt': (m['mix_text'] or '')[:36]
            })
        examples.append({'pattern': f'{A}->{B}->{A}', 'positions': [pos, pos+1, pos+2], 'triplet': ex})

    return {
        'mixed_srt': mixed_srt,
        'source_root': source_root,
        'source_srt_count': len(sources),
        'source_total_items': total_items,
        'mapped_count': sum(1 for m in mappings if m['episode'] and m['episode'] != 'UNKNOWN'),
        'sequence_switches': switches,
        'sequence_blocks': blocks[:20],
        'sequence_alt_top2': alt2,
        'abab_examples': examples,
        'samples_head': [{
            'mix_index': m['mix_index'],
            'episode': m['episode'],
            'ratio': m['match_ratio'],
            'text_excerpt': (m['mix_text'] or '')[:36]
        } for m in mappings[:8]],
    }


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage", "usage": "python tools/srt_content_compare.py <混剪SRT> <原片SRT根目录> [max_examples]"}, ensure_ascii=False))
        return
    mixed_srt = sys.argv[1]
    source_root = sys.argv[2]
    max_examples = int(sys.argv[3]) if len(sys.argv) >= 4 else 3
    res = compare_contents(mixed_srt, source_root, max_examples=max_examples)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

