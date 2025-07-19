import json
import os
import logging
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KnowledgeBase")

class MemoryIssuePattern:
    """Represents a memory issue pattern for detection and resolution."""
    
    def __init__(self, 
                 pattern_id: str,
                 name: str,
                 description: str,
                 symptoms: List[str],
                 causes: List[str],
                 solutions: List[str],
                 severity: int = 3,  # 1-5 scale
                 detection_regex: Optional[str] = None,
                 code_snippet: Optional[str] = None):
        """
        Initialize a memory issue pattern.
        
        Args:
            pattern_id: Unique identifier for the pattern
            name: Short name of the pattern
            description: Detailed description
            symptoms: List of symptom descriptions
            causes: List of potential causes
            solutions: List of potential solutions
            severity: Severity level (1-5)
            detection_regex: Regex pattern to detect this issue in logs
            code_snippet: Example code demonstrating the issue
        """
        self.pattern_id = pattern_id
        self.name = name
        self.description = description
        self.symptoms = symptoms
        self.causes = causes
        self.solutions = solutions
        self.severity = severity
        self.detection_regex = detection_regex
        self.code_snippet = code_snippet
        
        # Compile regex if provided
        self.regex = re.compile(detection_regex) if detection_regex else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary for serialization."""
        return {
            "id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "symptoms": self.symptoms,
            "causes": self.causes,
            "solutions": self.solutions,
            "severity": self.severity,
            "detection_regex": self.detection_regex,
            "code_snippet": self.code_snippet
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryIssuePattern':
        """Create pattern from dictionary."""
        return cls(
            pattern_id=data["id"],
            name=data["name"],
            description=data["description"],
            symptoms=data["symptoms"],
            causes=data["causes"],
            solutions=data["solutions"],
            severity=data.get("severity", 3),
            detection_regex=data.get("detection_regex"),
            code_snippet=data.get("code_snippet")
        )
    
    def matches_log(self, log_entry: str) -> bool:
        """
        Check if a log entry matches this pattern.
        
        Args:
            log_entry: Log entry string to check
            
        Returns:
            True if pattern matches, False otherwise
        """
        if not self.regex:
            return False
        return bool(self.regex.search(log_entry))


class KnowledgeBase:
    """
    Knowledge base for memory issue patterns and cases.
    Provides pattern matching and solution recommendations.
    """
    
    def __init__(self, default_patterns_file: Optional[str] = None, custom_cases_file: Optional[str] = None):
        """
        Initialize the knowledge base.
        
        Args:
            default_patterns_file: Path to default patterns JSON file
            custom_cases_file: Path to custom cases JSON file
        """
        self.patterns: Dict[str, MemoryIssuePattern] = {}
        self.custom_cases: List[Dict[str, Any]] = []
        
        # Load default patterns if provided
        if default_patterns_file and os.path.exists(default_patterns_file):
            self.load_patterns(default_patterns_file)
        else:
            self._load_builtin_patterns()
        
        # Load custom cases if provided
        if custom_cases_file and os.path.exists(custom_cases_file):
            self.load_custom_cases(custom_cases_file)
        
        logger.info(f"KnowledgeBase initialized with {len(self.patterns)} patterns and {len(self.custom_cases)} custom cases")
    
    def _load_builtin_patterns(self) -> None:
        """Load built-in memory issue patterns."""
        patterns = [
            MemoryIssuePattern(
                pattern_id="LEAK_LARGE_NUMPY_ARRAY",
                name="Large NumPy Array Memory Leak",
                description="Memory leak caused by large NumPy arrays not being properly garbage collected",
                symptoms=[
                    "Steadily increasing memory usage",
                    "Memory usage grows with each video processing iteration",
                    "Application crashes with OOM error after processing multiple videos"
                ],
                causes=[
                    "References to large arrays are maintained in global variables",
                    "Circular references preventing garbage collection",
                    "Not explicitly deleting large arrays when no longer needed"
                ],
                solutions=[
                    "Use 'del array_variable' after processing is complete",
                    "Set array_variable = None when done with processing",
                    "Use context managers or explicit scope to manage array lifecycle",
                    "Consider using memory-mapped arrays for very large data"
                ],
                severity=4,
                detection_regex=r"(memory|RAM) (usage|consumption) (increase|growing|high)",
                code_snippet="""
# Problem:
results = []
for video in videos:
    frame_data = process_video(video)  # Returns large numpy array
    results.append(frame_data)  # Keeps all arrays in memory
    
# Solution:
results = []
for video in videos:
    frame_data = process_video(video)
    result = compute_result(frame_data)
    results.append(result)  # Only store the result, not the full array
    del frame_data  # Explicitly release memory
                """
            ),
            
            MemoryIssuePattern(
                pattern_id="FFMPEG_RESOURCE_LEAK",
                name="FFmpeg Resource Leak",
                description="Resources not properly released when using FFmpeg for video processing",
                symptoms=[
                    "Memory usage increases with each video processed",
                    "File handles remain open",
                    "Temporary files accumulate on disk"
                ],
                causes=[
                    "FFmpeg processes not properly terminated",
                    "File handles not explicitly closed",
                    "Temporary files not cleaned up"
                ],
                solutions=[
                    "Use context managers (with statements) for FFmpeg operations",
                    "Explicitly close file handles after use",
                    "Implement cleanup routines for temporary files",
                    "Use the '-y' flag to automatically overwrite output files"
                ],
                severity=3,
                detection_regex=r"(resource|file|handle) (leak|not closed|remains open)",
                code_snippet="""
# Problem:
def process_videos(video_paths):
    for path in video_paths:
        stream = ffmpeg.input(path)
        # Process video
        output = ffmpeg.output(stream, 'output.mp4')
        ffmpeg.run(output)  # No cleanup
        
# Solution:
def process_videos(video_paths):
    for path in video_paths:
        try:
            stream = ffmpeg.input(path)
            # Process video
            output = ffmpeg.output(stream, f'output_{os.path.basename(path)}')
            ffmpeg.run(output, overwrite_output=True)
        finally:
            # Ensure cleanup of any temporary files
            for temp_file in glob.glob('*.tmp'):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
                """
            ),
            
            MemoryIssuePattern(
                pattern_id="CASCADE_MEMORY_FRAGMENTATION",
                name="Memory Fragmentation in Video Processing Pipeline",
                description="Memory fragmentation due to varied allocation/deallocation patterns in pipeline processing",
                symptoms=[
                    "Memory usage higher than expected",
                    "Performance degradation over time",
                    "Memory allocations start failing despite sufficient total memory"
                ],
                causes=[
                    "Frequent allocation and deallocation of different-sized objects",
                    "Long-running processes with varied memory usage patterns",
                    "Mixing small and large allocations"
                ],
                solutions=[
                    "Use object pooling for frequently created objects",
                    "Batch similar-sized allocations together",
                    "Implement processing in stages with clear memory boundaries",
                    "Periodically restart worker processes for long-running tasks"
                ],
                severity=3,
                detection_regex=r"(fragmentation|allocation failed|memory layout)",
                code_snippet="""
# Problem:
def process_video_frames(video):
    frames = []
    for i in range(video.frame_count):
        frame = video.get_frame(i)  # Creates new frame object
        processed = apply_effects(frame)  # Creates more objects of different sizes
        frames.append(processed)  # Keeps all in memory
    return frames
    
# Solution:
def process_video_frames(video):
    results = []
    # Process in batches to reduce fragmentation
    batch_size = 100
    for i in range(0, video.frame_count, batch_size):
        batch_frames = []
        for j in range(i, min(i + batch_size, video.frame_count)):
            frame = video.get_frame(j)
            batch_frames.append(frame)
        
        # Process batch
        processed_batch = apply_effects_to_batch(batch_frames)
        results.extend(process_results(processed_batch))
        
        # Explicitly clear batch
        batch_frames.clear()
        
    return results
                """
            ),
            
            MemoryIssuePattern(
                pattern_id="SUBTITLE_PARSING_OVERFLOW",
                name="Subtitle Parsing Memory Overflow",
                description="Memory overflow when parsing large subtitle files or corrupted subtitle formats",
                symptoms=[
                    "Sudden memory spikes during subtitle processing",
                    "Application crashes when processing specific subtitle files",
                    "Memory usage grows proportionally to subtitle file size"
                ],
                causes=[
                    "Loading entire subtitle file into memory at once",
                    "Recursive parsing of nested subtitle elements",
                    "Not handling malformed subtitle files properly"
                ],
                solutions=[
                    "Process subtitles in a streaming fashion",
                    "Implement size limits for subtitle loading",
                    "Add validation and error handling for malformed files",
                    "Use iterative instead of recursive parsing approaches"
                ],
                severity=4,
                detection_regex=r"(subtitle|srt|vtt) (parsing|processing) (error|failed|crash)",
                code_snippet="""
# Problem:
def parse_subtitles(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()  # Loads entire file into memory
    
    subtitles = []
    # Parse all at once
    for block in content.split('\\n\\n'):
        if block.strip():
            subtitles.append(parse_subtitle_block(block))
    return subtitles
    
# Solution:
def parse_subtitles(file_path, max_size_mb=10):
    # Check file size before processing
    if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
        raise ValueError(f"Subtitle file too large: {file_path}")
    
    subtitles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        current_block = []
        for line in f:  # Process line by line
            if line.strip():
                current_block.append(line)
            elif current_block:
                try:
                    subtitle = parse_subtitle_block(''.join(current_block))
                    subtitles.append(subtitle)
                except Exception as e:
                    logger.warning(f"Error parsing subtitle block: {e}")
                current_block = []
                
    return subtitles
                """
            ),
            
            MemoryIssuePattern(
                pattern_id="VIDEO_FRAME_CACHE_OVERFLOW",
                name="Video Frame Cache Overflow",
                description="Memory overflow due to excessive caching of video frames",
                symptoms=[
                    "Memory usage spikes during video playback or processing",
                    "Performance degrades after processing multiple videos",
                    "Out of memory errors during frame-by-frame operations"
                ],
                causes=[
                    "Unlimited caching of video frames",
                    "Not evicting frames from cache when no longer needed",
                    "Caching full-resolution frames unnecessarily"
                ],
                solutions=[
                    "Implement LRU caching with size limits",
                    "Use weak references for non-critical frame caching",
                    "Adjust cache size based on available system memory",
                    "Store downsampled frames for preview purposes"
                ],
                severity=3,
                detection_regex=r"(cache|buffer) (full|overflow|exceeded|too large)",
                code_snippet="""
# Problem:
class VideoProcessor:
    def __init__(self):
        self.frame_cache = {}  # Unlimited cache
        
    def get_frame(self, video_id, frame_num):
        cache_key = f"{video_id}_{frame_num}"
        if cache_key not in self.frame_cache:
            frame = self._load_frame(video_id, frame_num)
            self.frame_cache[cache_key] = frame
        return self.frame_cache[cache_key]
    
# Solution:
import collections

class VideoProcessor:
    def __init__(self, max_cache_size=1000):
        self.frame_cache = collections.OrderedDict()  # LRU cache
        self.max_cache_size = max_cache_size
        
    def get_frame(self, video_id, frame_num):
        cache_key = f"{video_id}_{frame_num}"
        if cache_key in self.frame_cache:
            # Move to end (most recently used)
            frame = self.frame_cache.pop(cache_key)
            self.frame_cache[cache_key] = frame
            return frame
            
        frame = self._load_frame(video_id, frame_num)
        
        # Add to cache and evict oldest if necessary
        if len(self.frame_cache) >= self.max_cache_size:
            self.frame_cache.popitem(last=False)  # Remove oldest item
            
        self.frame_cache[cache_key] = frame
        return frame
                """
            )
        ]
        
        # Add patterns to dictionary
        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern
    
    def load_patterns(self, file_path: str) -> None:
        """
        Load patterns from a JSON file.
        
        Args:
            file_path: Path to patterns JSON file
        """
        try:
            with open(file_path, 'r') as f:
                patterns_data = json.load(f)
            
            for pattern_data in patterns_data:
                pattern = MemoryIssuePattern.from_dict(pattern_data)
                self.patterns[pattern.pattern_id] = pattern
            
            logger.info(f"Loaded {len(patterns_data)} patterns from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load patterns from {file_path}: {e}")
    
    def load_custom_cases(self, file_path: str) -> None:
        """
        Load custom cases from a JSON file.
        
        Args:
            file_path: Path to custom cases JSON file
        """
        try:
            with open(file_path, 'r') as f:
                self.custom_cases = json.load(f)
            
            logger.info(f"Loaded {len(self.custom_cases)} custom cases from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load custom cases from {file_path}: {e}")
    
    def save_patterns(self, file_path: str) -> None:
        """
        Save patterns to a JSON file.
        
        Args:
            file_path: Path to patterns JSON file
        """
        patterns_data = [pattern.to_dict() for pattern in self.patterns.values()]
        try:
            with open(file_path, 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            logger.info(f"Saved {len(patterns_data)} patterns to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save patterns to {file_path}: {e}")
    
    def save_custom_cases(self, file_path: str) -> None:
        """
        Save custom cases to a JSON file.
        
        Args:
            file_path: Path to custom cases JSON file
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.custom_cases, f, indent=2)
            
            logger.info(f"Saved {len(self.custom_cases)} custom cases to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save custom cases to {file_path}: {e}")
    
    def add_pattern(self, pattern: MemoryIssuePattern) -> None:
        """
        Add a pattern to the knowledge base.
        
        Args:
            pattern: MemoryIssuePattern to add
        """
        self.patterns[pattern.pattern_id] = pattern
        logger.info(f"Added pattern: {pattern.name} (ID: {pattern.pattern_id})")
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """
        Remove a pattern from the knowledge base.
        
        Args:
            pattern_id: ID of pattern to remove
            
        Returns:
            True if pattern was removed, False if not found
        """
        if pattern_id in self.patterns:
            del self.patterns[pattern_id]
            logger.info(f"Removed pattern with ID: {pattern_id}")
            return True
        return False
    
    def add_custom_case(self, case: Dict[str, Any]) -> None:
        """
        Add a custom case to the knowledge base.
        
        Args:
            case: Custom case data
        """
        # Add timestamp if not present
        if "timestamp" not in case:
            case["timestamp"] = datetime.now().isoformat()
        
        self.custom_cases.append(case)
        logger.info(f"Added custom case: {case.get('title', 'Untitled')}")
    
    def remove_custom_case(self, case_id: str) -> bool:
        """
        Remove a custom case from the knowledge base.
        
        Args:
            case_id: ID of case to remove
            
        Returns:
            True if case was removed, False if not found
        """
        for i, case in enumerate(self.custom_cases):
            if case.get("id") == case_id:
                self.custom_cases.pop(i)
                logger.info(f"Removed custom case with ID: {case_id}")
                return True
        return False
    
    def match_log_patterns(self, log_entries: List[str]) -> Dict[str, List[str]]:
        """
        Find patterns that match log entries.
        
        Args:
            log_entries: List of log entry strings to match
            
        Returns:
            Dictionary of pattern IDs to lists of matching log entries
        """
        matches: Dict[str, List[str]] = {}
        
        for entry in log_entries:
            for pattern_id, pattern in self.patterns.items():
                if pattern.matches_log(entry):
                    if pattern_id not in matches:
                        matches[pattern_id] = []
                    matches[pattern_id].append(entry)
        
        return matches
    
    def get_solutions_for_issue(self, issue_description: str) -> List[Dict[str, Any]]:
        """
        Find potential solutions for an issue based on its description.
        
        Args:
            issue_description: Description of the issue
            
        Returns:
            List of potential solutions with pattern information
        """
        solutions = []
        issue_lower = issue_description.lower()
        
        # Check each pattern for keyword matches in the issue description
        for pattern in self.patterns.values():
            score = 0
            
            # Check name and description
            if pattern.name.lower() in issue_lower:
                score += 3
            
            if any(keyword in issue_lower for keyword in pattern.description.lower().split()):
                score += 1
            
            # Check symptoms
            for symptom in pattern.symptoms:
                if any(keyword in issue_lower for keyword in symptom.lower().split()):
                    score += 2
            
            # Check causes
            for cause in pattern.causes:
                if any(keyword in issue_lower for keyword in cause.lower().split()):
                    score += 2
            
            if score > 0:
                solutions.append({
                    "pattern_id": pattern.pattern_id,
                    "name": pattern.name,
                    "solutions": pattern.solutions,
                    "relevance_score": score,
                    "severity": pattern.severity
                })
        
        # Sort by relevance score (descending)
        solutions.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return solutions
    
    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """
        Get all patterns in the knowledge base.
        
        Returns:
            List of all patterns as dictionaries
        """
        return [pattern.to_dict() for pattern in self.patterns.values()]
    
    def get_pattern(self, pattern_id: str) -> Optional[MemoryIssuePattern]:
        """
        Get a specific pattern by ID.
        
        Args:
            pattern_id: ID of the pattern to get
            
        Returns:
            MemoryIssuePattern if found, None otherwise
        """
        return self.patterns.get(pattern_id) 