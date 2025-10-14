#!/usr/bin/env python3
"""检查生成的草稿文件"""
import json
from pathlib import Path

draft_path = Path(r"C:\Users\CKEN\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft\JianyingTest_Workflow")

# 读取draft_content.json
draft_content_file = draft_path / "draft_content.json"
if draft_content_file.exists():
    with open(draft_content_file, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    print("=== draft_content.json 结构 ===")
    print(f"ID: {content.get('id')}")
    print(f"Duration: {content.get('duration')}")
    print(f"Materials数量: {len(content.get('materials', {}).get('videos', []))}")
    print(f"Tracks数量: {len(content.get('tracks', []))}")
    
    # 检查tracks
    for i, track in enumerate(content.get('tracks', [])):
        print(f"\nTrack {i}:")
        print(f"  Type: {track.get('type')}")
        print(f"  Segments数量: {len(track.get('segments', []))}")
        for j, seg in enumerate(track.get('segments', [])):
            print(f"  Segment {j}:")
            print(f"    Material ID: {seg.get('material_id')}")
            print(f"    Target timerange: {seg.get('target_timerange')}")
            print(f"    Source timerange: {seg.get('source_timerange')}")
            print(f"    Clip: {seg.get('clip')}")
    
    # 保存格式化的JSON以便查看
    with open("draft_content_formatted.json", 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print("\n✅ 已保存格式化的JSON到 draft_content_formatted.json")
else:
    print("❌ draft_content.json 不存在")

# 读取draft_meta_info.json
meta_file = draft_path / "draft_meta_info.json"
if meta_file.exists():
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    print("\n=== draft_meta_info.json ===")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
else:
    print("❌ draft_meta_info.json 不存在")

