# 📚 VisionAI-ClipsMaster API Reference

> **Version**: v1.0.1  
> **Last Updated**: July 25, 2025  
> **Target Audience**: Developers and Integrators

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🧠 Core Modules](#-core-modules)
- [🎬 Script Reconstruction API](#-script-reconstruction-api)
- [🔄 Model Management API](#-model-management-api)
- [📤 Export Functions API](#-export-functions-api)
- [🛠️ Utility Classes API](#-utility-classes-api)
- [⚠️ Error Handling](#-error-handling)
- [📝 Code Examples](#-code-examples)

## 🚀 Quick Start

### Installation and Import

```python
# Install dependencies
pip install -r requirements.txt

# Import core modules
from src.core.model_switcher import ModelSwitcher
from src.core.screenplay_engineer import ScreenplayEngineer
from src.exporters.jianying_pro_exporter import JianyingProExporter
```

### Basic Usage Flow

```python
# 1. Initialize model switcher
switcher = ModelSwitcher()

# 2. Create screenplay engineer
engineer = ScreenplayEngineer(switcher)

# 3. Process subtitle file
result = engineer.reconstruct_screenplay("input.srt")

# 4. Export results
exporter = JianyingProExporter()
exporter.export_project(result, "output.json")
```

## 🧠 Core Modules

### ModelSwitcher Class

Intelligent model switcher for dynamic loading and switching between Chinese and English models.

#### Initialization

```python
class ModelSwitcher:
    def __init__(self, config_path: str = "configs/model_config.yaml"):
        """
        Initialize model switcher
        
        Args:
            config_path (str): Path to model configuration file
        """
```

#### Main Methods

##### detect_language()

```python
def detect_language(self, text: str) -> str:
    """
    Detect text language
    
    Args:
        text (str): Text to detect
        
    Returns:
        str: Language code ('zh' or 'en')
        
    Example:
        >>> switcher = ModelSwitcher()
        >>> lang = switcher.detect_language("This is English text")
        >>> print(lang)  # 'en'
    """
```

##### switch_model()

```python
def switch_model(self, language: str) -> bool:
    """
    Switch to specified language model
    
    Args:
        language (str): Target language ('zh' or 'en')
        
    Returns:
        bool: Whether switch was successful
        
    Raises:
        ModelNotFoundError: Model file not found
        MemoryError: Insufficient memory
    """
```

##### get_model_info()

```python
def get_model_info(self) -> dict:
    """
    Get current model information
    
    Returns:
        dict: Model information dictionary
        {
            'name': str,           # Model name
            'language': str,       # Supported language
            'memory_usage': int,   # Memory usage (MB)
            'quantization': str,   # Quantization level
            'status': str          # Model status
        }
    """
```

### ScreenplayEngineer Class

Screenplay reconstruction engineer for analyzing and restructuring narrative content.

#### Initialization

```python
class ScreenplayEngineer:
    def __init__(self, model_switcher: ModelSwitcher):
        """
        Initialize screenplay engineer
        
        Args:
            model_switcher (ModelSwitcher): Model switcher instance
        """
```

#### Main Methods

##### reconstruct_screenplay()

```python
def reconstruct_screenplay(
    self, 
    input_file: str, 
    style: str = "viral",
    max_duration: int = 300
) -> dict:
    """
    Reconstruct screenplay to viral style
    
    Args:
        input_file (str): Input SRT file path
        style (str): Reconstruction style ('viral', 'dramatic', 'comedy')
        max_duration (int): Maximum duration (seconds)
        
    Returns:
        dict: Reconstruction result
        {
            'segments': List[dict],     # Segment list
            'total_duration': float,    # Total duration
            'style_score': float,       # Style score
            'coherence_score': float    # Coherence score
        }
        
    Raises:
        FileNotFoundError: Input file not found
        InvalidFormatError: Invalid SRT format
    """
```

##### analyze_narrative()

```python
def analyze_narrative(self, subtitles: List[dict]) -> dict:
    """
    Analyze narrative structure
    
    Args:
        subtitles (List[dict]): Subtitle list
        
    Returns:
        dict: Analysis result
        {
            'plot_points': List[dict],   # Plot points
            'emotion_curve': List[float], # Emotion curve
            'character_arcs': dict,      # Character arcs
            'pacing_analysis': dict      # Pacing analysis
        }
    """
```

## 🎬 Script Reconstruction API

### SRTParser Class

SRT subtitle file parser.

```python
class SRTParser:
    @staticmethod
    def parse_file(file_path: str) -> List[dict]:
        """
        Parse SRT file
        
        Args:
            file_path (str): SRT file path
            
        Returns:
            List[dict]: Subtitle entry list
            [
                {
                    'index': int,           # Index number
                    'start_time': float,    # Start time (seconds)
                    'end_time': float,      # End time (seconds)
                    'text': str,           # Subtitle text
                    'duration': float       # Duration (seconds)
                }
            ]
        """
    
    @staticmethod
    def validate_format(file_path: str) -> bool:
        """
        Validate SRT file format
        
        Args:
            file_path (str): File path
            
        Returns:
            bool: Whether format is correct
        """
```

### NarrativeAnalyzer Class

Narrative analyzer for plot structure and emotional flow analysis.

```python
class NarrativeAnalyzer:
    def analyze_plot_structure(self, subtitles: List[dict]) -> dict:
        """
        Analyze plot structure
        
        Args:
            subtitles (List[dict]): Subtitle data
            
        Returns:
            dict: Plot analysis result
            {
                'act_structure': dict,      # Three-act structure
                'turning_points': List[int], # Turning point positions
                'climax_position': int,     # Climax position
                'resolution_quality': float # Resolution quality score
            }
        """
    
    def extract_emotion_curve(self, subtitles: List[dict]) -> List[float]:
        """
        Extract emotion curve
        
        Args:
            subtitles (List[dict]): Subtitle data
            
        Returns:
            List[float]: Emotion intensity sequence (0.0-1.0)
        """
```

## 🔄 Model Management API

### ModelManager Class

Model lifecycle manager.

```python
class ModelManager:
    def load_model(self, model_name: str, quantization: str = "Q4_K_M") -> bool:
        """
        Load specified model
        
        Args:
            model_name (str): Model name
            quantization (str): Quantization level
            
        Returns:
            bool: Whether loading was successful
        """
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload model to free memory
        
        Args:
            model_name (str): Model name
            
        Returns:
            bool: Whether unloading was successful
        """
    
    def get_memory_usage(self) -> dict:
        """
        Get memory usage information
        
        Returns:
            dict: Memory usage info
            {
                'total_memory': int,        # Total memory (MB)
                'used_memory': int,         # Used memory (MB)
                'model_memory': int,        # Model memory (MB)
                'available_memory': int     # Available memory (MB)
            }
        """
```

## 📤 Export Functions API

### JianyingProExporter Class

JianYing Pro project exporter.

```python
class JianyingProExporter:
    def export_project(
        self, 
        segments: List[dict], 
        output_path: str,
        project_name: str = "VisionAI_Project"
    ) -> bool:
        """
        Export JianYing project file
        
        Args:
            segments (List[dict]): Video segment list
            output_path (str): Output file path
            project_name (str): Project name
            
        Returns:
            bool: Whether export was successful
            
        Example:
            >>> exporter = JianyingProExporter()
            >>> segments = [
            ...     {
            ...         'start_time': 0.0,
            ...         'end_time': 5.0,
            ...         'text': 'Opening scene',
            ...         'video_path': 'video.mp4'
            ...     }
            ... ]
            >>> success = exporter.export_project(segments, "project.json")
        """
    
    def validate_segments(self, segments: List[dict]) -> List[str]:
        """
        Validate segment data integrity
        
        Args:
            segments (List[dict]): Segment list
            
        Returns:
            List[str]: Error message list, empty list means no errors
        """
```

## 🛠️ Utility Classes API

### FileChecker Class

File integrity checking utility.

```python
class FileChecker:
    @staticmethod
    def calculate_hash(file_path: str) -> str:
        """
        Calculate file hash
        
        Args:
            file_path (str): File path
            
        Returns:
            str: MD5 hash value
        """
    
    @staticmethod
    def verify_integrity(file_path: str, expected_hash: str) -> bool:
        """
        Verify file integrity
        
        Args:
            file_path (str): File path
            expected_hash (str): Expected hash value
            
        Returns:
            bool: Whether file is intact
        """
```

### MemoryGuard Class

Memory monitoring and management utility.

```python
class MemoryGuard:
    def get_memory_info(self) -> dict:
        """
        Get memory usage information
        
        Returns:
            dict: Memory information
            {
                'total': int,      # Total memory (MB)
                'available': int,  # Available memory (MB)
                'percent': float,  # Usage percentage
                'process': int     # Current process usage (MB)
            }
        """
    
    def check_memory_pressure(self) -> bool:
        """
        Check memory pressure
        
        Returns:
            bool: Whether memory pressure exists
        """
```

## ⚠️ Error Handling

### Exception Types

```python
# Model-related exceptions
class ModelNotFoundError(Exception):
    """Model file not found"""
    pass

class ModelLoadError(Exception):
    """Model loading failed"""
    pass

class InsufficientMemoryError(Exception):
    """Insufficient memory"""
    pass

# File-related exceptions
class InvalidFormatError(Exception):
    """Invalid file format"""
    pass

class FileCorruptedError(Exception):
    """File corrupted"""
    pass

# Processing-related exceptions
class ProcessingError(Exception):
    """Processing error"""
    pass

class TimeoutError(Exception):
    """Processing timeout"""
    pass
```

### Error Handling Example

```python
try:
    switcher = ModelSwitcher()
    result = switcher.switch_model("zh")
except ModelNotFoundError as e:
    print(f"Model file not found: {e}")
except InsufficientMemoryError as e:
    print(f"Insufficient memory: {e}")
except Exception as e:
    print(f"Unknown error: {e}")
```

## 📝 Code Examples

### Complete Workflow Example

```python
import logging
from src.core.model_switcher import ModelSwitcher
from src.core.screenplay_engineer import ScreenplayEngineer
from src.exporters.jianying_pro_exporter import JianyingProExporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_video_script(input_srt: str, output_project: str):
    """
    Complete video script processing workflow
    
    Args:
        input_srt (str): Input SRT file path
        output_project (str): Output project file path
    """
    try:
        # 1. Initialize components
        logger.info("Initializing model switcher...")
        switcher = ModelSwitcher()
        
        logger.info("Creating screenplay engineer...")
        engineer = ScreenplayEngineer(switcher)
        
        # 2. Process screenplay
        logger.info(f"Processing input file: {input_srt}")
        result = engineer.reconstruct_screenplay(
            input_file=input_srt,
            style="viral",
            max_duration=300
        )
        
        # 3. Export project
        logger.info("Exporting JianYing project...")
        exporter = JianyingProExporter()
        success = exporter.export_project(
            segments=result['segments'],
            output_path=output_project,
            project_name="AI_Generated_Project"
        )
        
        if success:
            logger.info(f"Project exported successfully: {output_project}")
            return True
        else:
            logger.error("Project export failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return False

# Usage example
if __name__ == "__main__":
    success = process_video_script(
        input_srt="data/input/original.srt",
        output_project="data/output/project.json"
    )
    
    if success:
        print("✅ Processing completed!")
    else:
        print("❌ Processing failed!")
```

---

## 📞 Get Help

- **GitHub Issues**: [Report issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
- **GitHub Discussions**: [Technical discussions](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions)
- **Email Contact**: [peresbreedanay7156@gmail.com](mailto:peresbreedanay7156@gmail.com)

---

**VisionAI-ClipsMaster API Documentation** | Version v1.0.1 | Updated July 25, 2025
