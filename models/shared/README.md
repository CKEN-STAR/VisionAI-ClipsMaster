# Shared Resources

This directory contains resources shared between different models and languages.

## Directory Structure

### training_data/
Contains raw training data before language-specific processing:
- Original video subtitles
- Viral short video subtitles
- Parallel corpus for cross-language learning

### vocabularies/
Shared vocabulary files:
- Base vocabulary for tokenization
- Special tokens for video editing
- Cross-lingual vocabulary mapping

## Usage Guidelines

1. All training data should be properly labeled with language tags
2. Maintain clear separation between different data sources
3. Update vocabulary files only during scheduled model updates
4. Keep track of data sources and licenses

## Data Format Specifications

### Subtitle Format
```json
{
    "id": "unique_id",
    "source": "original/viral",
    "language": "en/zh",
    "content": {
        "text": "subtitle text",
        "start_time": "00:00:00,000",
        "end_time": "00:00:00,000"
    }
}
```

### Vocabulary Format
```json
{
    "token": "string",
    "id": "integer",
    "frequency": "float",
    "languages": ["en", "zh"]
}
``` 