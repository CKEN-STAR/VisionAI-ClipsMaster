import sys, json, os
from typing import List, Dict

# add repo root to sys.path so 'src' is importable when invoked from repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.core.screenplay_engineer import ScreenplayEngineer

def monotonic_and_alternation(segments: List[Dict]):
    starts = [float(s.get('start', s.get('start_time', 0.0))) for s in segments]
    ends = [float(s.get('end', s.get('end_time', 0.0))) for s in segments]
    # monotonic check
    back = sum(1 for i in range(len(starts)-1) if starts[i] > starts[i+1])
    # alternation detection (coarse): bucket minutes by int(start//60)
    bins = [int(st//60) for st in starts]
    transitions = sum(1 for i in range(len(bins)-1) if bins[i] != bins[i+1])
    # detect top-2-bin alternation count like A-B-A-B pattern
    from collections import Counter
    cnt = Counter(bins)
    top2 = [b for b, _ in cnt.most_common(2)]
    alt = 0
    if len(top2) == 2:
        a, b = top2
        for i in range(len(bins)-3):
            if bins[i:i+4] == [a,b,a,b] or bins[i:i+4] == [b,a,b,a]:
                alt += 1
    return {
        'count': len(segments),
        'monotonic': back == 0,
        'backward_jumps': back,
        'bin_transitions': transitions,
        'alternation_top2': alt,
        'first5': starts[:5],
        'last5': starts[-5:],
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: python tools/reconstruct_dryrun.py <srt_path>'}, ensure_ascii=False))
        return
    srt_path = sys.argv[1]
    eng = ScreenplayEngineer()
    segs = eng.reconstruct_screenplay(srt_path)
    metrics = monotonic_and_alternation(segs)
    print(json.dumps({'path': srt_path, **metrics}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

