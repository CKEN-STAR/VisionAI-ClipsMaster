#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试场景合并逻辑"""

import sys
sys.path.insert(0, '.')

# 模拟场景数据
scenes = [
    {'scene_id': 'scene_1', 'video_path': 'video1.mp4', 'original_episode': 1, 'source_start': 0.0, 'source_end': 2.5, 'duration': 2.5, 'text': '台词1'},
    {'scene_id': 'scene_2', 'video_path': 'video1.mp4', 'original_episode': 1, 'source_start': 2.5, 'source_end': 5.0, 'duration': 2.5, 'text': '台词2'},  # 连续
    {'scene_id': 'scene_3', 'video_path': 'video1.mp4', 'original_episode': 1, 'source_start': 5.2, 'source_end': 7.5, 'duration': 2.3, 'text': '台词3'},  # 间隙0.2秒，可合并
    {'scene_id': 'scene_4', 'video_path': 'video1.mp4', 'original_episode': 1, 'source_start': 10.0, 'source_end': 12.5, 'duration': 2.5, 'text': '台词4'},  # 间隙2.5秒，不合并
    {'scene_id': 'scene_5', 'video_path': 'video2.mp4', 'original_episode': 2, 'source_start': 0.0, 'source_end': 3.0, 'duration': 3.0, 'text': '台词5'},  # 不同视频
    {'scene_id': 'scene_6', 'video_path': 'video2.mp4', 'original_episode': 2, 'source_start': 3.0, 'source_end': 6.0, 'duration': 3.0, 'text': '台词6'},  # 连续
]

# 测试合并逻辑
class TestMerge:
    def _merge_continuous_scenes(self, scenes, gap_threshold=0.5):
        if not scenes or len(scenes) <= 1:
            return scenes
        
        merged_scenes = []
        current_scene = None
        
        for scene in scenes:
            if current_scene is None:
                current_scene = scene.copy()
                current_scene['merged_texts'] = [scene.get('text', '')]
                continue
            
            same_video = current_scene.get('video_path') == scene.get('video_path')
            same_episode = current_scene.get('original_episode') == scene.get('original_episode')
            
            current_source_end = current_scene.get('source_end', 0)
            next_source_start = scene.get('source_start', 0)
            time_gap = next_source_start - current_source_end
            
            is_continuous = same_video and same_episode and (0 <= time_gap <= gap_threshold)
            
            if is_continuous:
                current_scene['source_end'] = scene.get('source_end', 0)
                current_scene['end_time'] = scene.get('end_time', 0)
                current_scene['duration'] = current_scene['source_end'] - current_scene['source_start']
                current_scene['merged_texts'].append(scene.get('text', ''))
                current_scene['scene_id'] = f"merged_{current_scene['scene_id']}"
            else:
                current_scene['text'] = ' '.join(current_scene['merged_texts'])
                del current_scene['merged_texts']
                merged_scenes.append(current_scene)
                
                current_scene = scene.copy()
                current_scene['merged_texts'] = [scene.get('text', '')]
        
        if current_scene is not None:
            current_scene['text'] = ' '.join(current_scene['merged_texts'])
            del current_scene['merged_texts']
            merged_scenes.append(current_scene)
        
        return merged_scenes

if __name__ == '__main__':
    test = TestMerge()
    merged = test._merge_continuous_scenes(scenes)

    print(f'原始场景数: {len(scenes)}')
    print(f'合并后场景数: {len(merged)}')
    print()
    for i, scene in enumerate(merged):
        print(f'场景{i+1}: {scene["scene_id"]}')
        print(f'  视频: {scene["video_path"]}')
        print(f'  时间: {scene["source_start"]:.2f}s - {scene["source_end"]:.2f}s')
        print(f'  时长: {scene["duration"]:.2f}s')
        print(f'  文本: {scene["text"]}')
        print()
