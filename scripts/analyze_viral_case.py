import os, sys, json, re, subprocess
from pathlib import Path

def locate_ffprobe() -> str:
    repo_ffprobe = Path('tools')/'ffmpeg'/'bin'/'ffprobe.exe'
    if repo_ffprobe.exists():
        return str(repo_ffprobe)
    return 'ffprobe'

VIDEO_EXTS = {'.mp4','.mkv','.mov','.avi','.mpg','.mpeg','.m4v','.wmv'}
SRT_EXTS = {'.srt','.ass'}

TIME_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*--\>\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")

def probe_duration(ffprobe: str, p: Path):
    try:
        cmd = [ffprobe, '-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1', str(p)]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=False)
        s = out.decode('utf-8','ignore').strip()
        return float(s)
    except Exception:
        return None

def parse_srt_times(p: Path):
    encodings = ['utf-8-sig','utf-8','gbk','cp936','ansi','latin-1']
    txt = None
    for enc in encodings:
        try:
            with open(p, 'r', encoding=enc, errors='strict') as fh:
                txt = fh.read()
                break
        except Exception:
            continue
    if txt is None:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
            txt = fh.read()
    matches = TIME_RE.findall(txt)
    items = []
    for m in matches:
        h1,m1,s1,ms1,h2,m2,s2,ms2 = map(int, m)
        st = h1*3600 + m1*60 + s1 + ms1/1000.0
        et = h2*3600 + m2*60 + s2 + ms2/1000.0
        if et > st:
            items.append((st, et))
    items.sort()
    return items

def merge_coverage(items):
    if not items: return []
    items = sorted(items)
    merged = [list(items[0])]
    for st,et in items[1:]:
        if st <= merged[-1][1] + 1e-3:
            merged[-1][1] = max(merged[-1][1], et)
        else:
            merged.append([st,et])
    return [(a,b) for a,b in merged]

def analyze(dir_path: str):
    ffprobe = locate_ffprobe()
    root = Path(dir_path)
    videos, subtitles = [], []
    for base, dirs, files in os.walk(dir_path):
        for f in files:
            p = Path(base)/f
            ext = p.suffix.lower()
            if ext in VIDEO_EXTS:
                videos.append(p)
            if ext in SRT_EXTS and ext == '.srt':
                subtitles.append(p)
    video_infos = []
    for v in videos:
        video_infos.append({'path': str(v), 'duration_sec': probe_duration(ffprobe, v)})
    srt_infos = []
    for s in subtitles:
        items = parse_srt_times(s)
        merged = merge_coverage(items)
        n = len(items)
        sum_durations = sum(et-st for st,et in items)
        coverage_dur = sum(et-st for st,et in merged)
        first_ts = items[0][0] if items else None
        last_ts = items[-1][1] if items else None
        span = (last_ts-first_ts) if (first_ts is not None and last_ts is not None) else None
        avg_dur = (sum_durations/n) if n else None
        q = [0.0,0.0,0.0,0.0]
        cum = 0.0
        for st,et in items:
            d = et-st
            if sum_durations <= 0: break
            mid = (cum + d/2.0)/sum_durations
            idx = min(3, max(0, int(mid*4)))
            q[idx] += d
            cum += d
        srt_infos.append({
            'path': str(s),
            'num_lines': n,
            'sum_durations_sec': round(sum_durations,3),
            'coverage_duration_sec': round(coverage_dur,3),
            'avg_line_duration_sec': round(avg_dur,3) if avg_dur is not None else None,
            'span_sec': round(span,3) if span is not None else None,
            'first_ts_sec': round(first_ts,3) if first_ts is not None else None,
            'last_ts_sec': round(last_ts,3) if last_ts is not None else None,
            'quartiles': [round(x,3) for x in q],
        })
    video_infos_sorted = sorted([vi for vi in video_infos if vi['duration_sec']], key=lambda x: x['duration_sec'] or 0, reverse=True)
    ref_video = video_infos_sorted[0] if video_infos_sorted else None
    summary = {'video_files': video_infos, 'srt_files': srt_infos, 'ref_video': ref_video}
    if ref_video and srt_infos:
        srt_sorted = sorted(srt_infos, key=lambda x: x['coverage_duration_sec'] or 0, reverse=True)
        srt_ref = srt_sorted[0]
        ov = ref_video['duration_sec'] or 0
        vv = srt_ref['coverage_duration_sec'] or 0
        cuts = srt_ref['num_lines'] or 0
        total_sum = srt_ref['sum_durations_sec'] or 0
        cuts_per_min = (cuts / (total_sum/60.0)) if total_sum>0 else None
        retention_ratio = (vv/ov) if ov>0 else None
        summary['derived'] = {
            'viral_estimated_length_sec': round(total_sum,3),
            'viral_span_sec': srt_ref['span_sec'],
            'viral_switches_count': cuts,
            'viral_switches_per_minute': round(cuts_per_min,3) if cuts_per_min else None,
            'retention_ratio_vs_original': round(retention_ratio,4) if retention_ratio else None,
            'quartiles_sec': srt_ref['quartiles'],
            'ref_srt_path': srt_ref['path'],
            'ref_video_path': ref_video['path'],
        }
    return summary

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else r"D:\\Material\\"
    if target == r"D:\\Material\\":
        target = r"D:\\Material\\"
    # Allow explicit path via env if needed
    target = os.environ.get('VACL_ANALYZE_DIR', target)
    try:
        result = analyze(target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({'error': str(e), 'dir': target}, ensure_ascii=False))

