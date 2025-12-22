#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, json, argparse

def analyze(path: str):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    eps = []
    for ln in lines:
        m = re.match(r'^#ORIGINAL:\s*.*episode=([0-9]+)', ln)
        if m:
            eps.append(m.group(1).zfill(2))
    blocks = []
    for e in eps:
        if not blocks or blocks[-1][0] != e:
            blocks.append([e, 1])
        else:
            blocks[-1][1] += 1
    return {
        'n': len(eps),
        'switches': max(0, len(blocks)-1),
        'blocks': blocks[:50],  # show head 50 blocks
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('srt')
    args = ap.parse_args()
    res = analyze(args.srt)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

