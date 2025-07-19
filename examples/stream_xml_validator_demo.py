#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stream-based XML Validator Demo

Demonstrates the memory-efficient XML validation capabilities for large XML files.
Compares performance of traditional vs. stream-based validation approaches.
"""

import os
import sys
import time
import argparse
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import random
import resource

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.export.xml_validator import validate_export_xml
from src.export.stream_xml_validator import memory_efficient_validation


def get_memory_usage():
    """Get current memory usage in MB"""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def create_large_xml_sample(file_path: str, num_clips: int = 1000, include_disclaimer: bool = True):
    """
    Create a large sample XML file with specified number of clips
    
    Args:
        file_path: Output file path
        num_clips: Number of video clips to include
        include_disclaimer: Whether to include AI disclaimer
    """
    print(f"Creating sample XML with {num_clips} clips...")
    
    # Root element
    root = ET.Element("project", {"version": "1.0"})
    
    # Add metadata
    meta = ET.SubElement(root, "meta")
    ET.SubElement(meta, "generator").text = "ClipsMaster Demo Generator"
    ET.SubElement(meta, "copyright").text = "ClipsMaster 2023"
    
    if include_disclaimer:
        ET.SubElement(meta, "disclaimer").text = "本视频由AI生成，仅用于技术演示。AI Generated Content by ClipsMaster."
    
    # Add resources section with many video clips
    resources = ET.SubElement(root, "resources")
    
    # Add many resource entries
    for i in range(num_clips):
        video = ET.SubElement(resources, "video", {
            "id": f"video{i}",
            "path": f"assets/clip_{i}.mp4",
            "name": f"Clip {i}",
            "duration": f"{random.randint(5, 60)}",
            "resolution": "1920x1080"
        })
        
        # Add metadata to each video clip to increase file size
        metadata = ET.SubElement(video, "metadata")
        ET.SubElement(metadata, "fps").text = "30"
        ET.SubElement(metadata, "codec").text = "h264"
        ET.SubElement(metadata, "bitrate").text = f"{random.randint(10000, 50000)}"
        ET.SubElement(metadata, "created").text = "2023-09-15T12:00:00Z"
        
        # Add more nested elements to increase depth
        settings = ET.SubElement(metadata, "settings")
        for j in range(5):
            ET.SubElement(settings, f"param{j}").text = f"value{j}"
    
    # Add timeline section with many clips
    timeline = ET.SubElement(root, "timeline")
    
    # Add video track
    video_track = ET.SubElement(timeline, "track", {"type": "video"})
    
    # Add many clips to the timeline
    current_time = 0
    for i in range(num_clips):
        duration = random.randint(2, 10)
        clip = ET.SubElement(video_track, "clip", {
            "resourceId": f"video{i}",
            "start": f"{current_time}",
            "duration": f"{duration}",
            "offset": "0"
        })
        
        # Add effects to each clip
        effects = ET.SubElement(clip, "effects")
        for j in range(random.randint(1, 3)):
            effect = ET.SubElement(effects, "effect", {
                "type": random.choice(["color", "transform", "blur", "sharpen"]),
                "intensity": f"{random.random()}"
            })
            
            # Add parameters to effect
            params = ET.SubElement(effect, "parameters")
            for k in range(3):
                ET.SubElement(params, f"param{k}").text = f"{random.random()}"
        
        current_time += duration
    
    # Add audio track
    audio_track = ET.SubElement(timeline, "track", {"type": "audio"})
    
    # Add audio clips
    current_time = 0
    for i in range(num_clips // 2):  # Fewer audio clips than video
        duration = random.randint(5, 15)
        ET.SubElement(audio_track, "clip", {
            "resourceId": f"video{i}",  # Reuse video resources for audio
            "start": f"{current_time}",
            "duration": f"{duration}",
            "volume": f"{random.random() + 0.5}"
        })
        current_time += duration
    
    # Create XML tree and save to file
    tree = ET.ElementTree(root)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Created sample XML file: {file_path}")
    print(f"File size: {file_size_mb:.2f} MB")
    
    return file_path


def benchmark_validation(xml_path: str):
    """
    Benchmark traditional vs. stream-based validation
    
    Args:
        xml_path: Path to XML file to validate
    """
    print("\n" + "=" * 50)
    print("Validation Performance Benchmark")
    print("=" * 50)
    
    file_size_mb = os.path.getsize(xml_path) / (1024 * 1024)
    print(f"XML File: {xml_path} ({file_size_mb:.2f} MB)")
    
    # Measure memory before traditional validation
    before_mem = get_memory_usage()
    print(f"\nTraditional validation approach:")
    print(f"Starting memory usage: {before_mem:.2f} MB")
    
    # Time traditional validation
    start_time = time.time()
    traditional_result = validate_export_xml(xml_path)
    trad_time = time.time() - start_time
    
    # Memory after traditional validation
    after_trad_mem = get_memory_usage()
    print(f"Completed in {trad_time:.2f} seconds")
    print(f"Peak memory usage: {after_trad_mem:.2f} MB")
    print(f"Memory increase: {after_trad_mem - before_mem:.2f} MB")
    
    # Give system a moment to recover
    time.sleep(1)
    
    # Measure memory before stream validation
    before_stream_mem = get_memory_usage()
    print(f"\nStream-based validation approach:")
    print(f"Starting memory usage: {before_stream_mem:.2f} MB")
    
    # Time stream validation
    start_time = time.time()
    stream_result = memory_efficient_validation(xml_path)
    stream_time = time.time() - start_time
    
    # Memory after stream validation
    after_stream_mem = get_memory_usage()
    print(f"Completed in {stream_time:.2f} seconds")
    print(f"Peak memory usage: {after_stream_mem:.2f} MB")
    print(f"Memory increase: {after_stream_mem - before_stream_mem:.2f} MB")
    
    # Compare results
    print("\nResults Comparison:")
    print(f"Traditional: {sum(1 for v in traditional_result.values() if v)}/{len(traditional_result)} checks passed")
    print(f"Stream-based: {sum(1 for v in stream_result.values() if v)}/{len(stream_result)} checks passed")
    
    # Calculate and show performance difference
    time_diff = trad_time - stream_time
    time_percent = (time_diff / trad_time) * 100 if trad_time > 0 else 0
    
    mem_diff = (after_trad_mem - before_mem) - (after_stream_mem - before_stream_mem)
    mem_percent = (mem_diff / (after_trad_mem - before_mem)) * 100 if (after_trad_mem - before_mem) > 0 else 0
    
    print(f"\nPerformance improvement:")
    print(f"Time: {time_percent:.1f}% ({time_diff:.2f} seconds)")
    print(f"Memory: {mem_percent:.1f}% ({mem_diff:.2f} MB)")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Stream XML Validator Demo")
    parser.add_argument("--xml", help="Path to existing XML file to validate")
    parser.add_argument("--generate", action="store_true", help="Generate a sample XML file")
    parser.add_argument("--clips", type=int, default=1000, help="Number of clips for generated XML")
    parser.add_argument("--no-disclaimer", action="store_true", help="Omit disclaimer in generated XML")
    
    args = parser.parse_args()
    
    xml_path = args.xml
    
    # Generate sample XML if requested or if no XML path provided
    if args.generate or not xml_path:
        # Create temporary directory if using generated XML
        if not xml_path:
            temp_dir = tempfile.TemporaryDirectory()
            xml_path = os.path.join(temp_dir.name, "large_sample.xml")
            
        # Generate large sample XML
        xml_path = create_large_xml_sample(
            xml_path, 
            args.clips, 
            not args.no_disclaimer
        )
    
    # Run benchmark
    benchmark_validation(xml_path)
    
    
if __name__ == "__main__":
    main() 