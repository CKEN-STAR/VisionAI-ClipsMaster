#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create valid test video files for VisionAI-ClipsMaster precision testing
"""

import sys
import subprocess
from pathlib import Path

def create_test_video_files():
    """Create test video files using FFmpeg"""
    print("Creating test video files for precision testing...")
    
    project_root = Path(__file__).parent
    test_data_dir = project_root / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # FFmpeg path
    ffmpeg_paths = [
        project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
        "ffmpeg"  # System PATH
    ]
    
    ffmpeg_path = None
    for path in ffmpeg_paths:
        try:
            result = subprocess.run([str(path), "-version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                ffmpeg_path = str(path)
                print(f"✅ Found FFmpeg: {ffmpeg_path}")
                break
        except:
            continue
    
    if not ffmpeg_path:
        print("❌ FFmpeg not found. Cannot create test video files.")
        return False
    
    # Create test videos with different durations and properties
    test_videos = [
        {
            "name": "test_precision_30s.mp4",
            "duration": 30,
            "resolution": "640x480",
            "fps": 25
        },
        {
            "name": "test_precision_60s.mp4", 
            "duration": 60,
            "resolution": "1280x720",
            "fps": 30
        },
        {
            "name": "test_precision_10s.mp4",
            "duration": 10,
            "resolution": "320x240", 
            "fps": 24
        }
    ]
    
    success_count = 0
    
    for video_config in test_videos:
        output_file = test_data_dir / video_config["name"]
        
        # Skip if file already exists and is valid
        if output_file.exists() and output_file.stat().st_size > 1000:
            print(f"⚠️ {video_config['name']} already exists, skipping...")
            success_count += 1
            continue
        
        print(f"Creating {video_config['name']}...")
        
        # Create test video with color bars and timecode
        cmd = [
            ffmpeg_path,
            "-f", "lavfi",
            "-i", f"testsrc2=duration={video_config['duration']}:size={video_config['resolution']}:rate={video_config['fps']}",
            "-f", "lavfi", 
            "-i", f"sine=frequency=1000:duration={video_config['duration']}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_file),
            "-y"  # Overwrite
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_file.exists():
                file_size = output_file.stat().st_size
                print(f"✅ Created {video_config['name']} ({file_size/1024:.1f} KB)")
                success_count += 1
            else:
                print(f"❌ Failed to create {video_config['name']}")
                print(f"   Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout creating {video_config['name']}")
        except Exception as e:
            print(f"❌ Error creating {video_config['name']}: {str(e)}")
    
    print(f"\nTest video creation completed: {success_count}/{len(test_videos)} files created")
    
    # Create corresponding SRT files
    create_test_srt_files(test_data_dir)
    
    return success_count > 0

def create_test_srt_files(test_data_dir):
    """Create corresponding SRT subtitle files"""
    print("\nCreating test SRT files...")
    
    srt_files = [
        {
            "name": "test_precision_30s.srt",
            "content": """1
00:00:01,000 --> 00:00:05,000
Test subtitle 1 - Beginning

2
00:00:10,000 --> 00:00:15,000
Test subtitle 2 - Middle section

3
00:00:20,000 --> 00:00:25,000
Test subtitle 3 - Near end

4
00:00:26,000 --> 00:00:29,000
Test subtitle 4 - Final"""
        },
        {
            "name": "test_precision_60s.srt",
            "content": """1
00:00:01,000 --> 00:00:05,000
Long video test - Start

2
00:00:15,000 --> 00:00:20,000
Long video test - Quarter

3
00:00:30,000 --> 00:00:35,000
Long video test - Half

4
00:00:45,000 --> 00:00:50,000
Long video test - Three quarters

5
00:00:55,000 --> 00:00:59,000
Long video test - End"""
        },
        {
            "name": "test_precision_10s.srt",
            "content": """1
00:00:01,000 --> 00:00:03,000
Short test - Start

2
00:00:05,000 --> 00:00:08,000
Short test - End"""
        }
    ]
    
    for srt_config in srt_files:
        srt_file = test_data_dir / srt_config["name"]
        
        try:
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(srt_config["content"])
            print(f"✅ Created {srt_config['name']}")
        except Exception as e:
            print(f"❌ Failed to create {srt_config['name']}: {str(e)}")

if __name__ == "__main__":
    success = create_test_video_files()
    sys.exit(0 if success else 1)
