# VisionAI-ClipsMaster User Guide (English)

## Introduction
VisionAI-ClipsMaster is an AI-powered smart short drama editing tool, supporting both Chinese and English models, optimized for low-end devices, and capable of automated script reconstruction and viral-style editing.

## Installation & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the service:
   ```bash
   python -m src.main
   ```
3. Access API documentation:
   - [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

## Main Features
- Input original video and SRT subtitles to automatically generate viral-style edited videos
- Export Jianying project files for further editing
- Support hot switching between Chinese and English models, friendly to low-end devices
- Built-in API performance monitoring and reporting

## FAQ
- If the English model is not downloaded, the API will return a "model not available" error. After downloading the model, it will take effect immediately without restart.
- Logs and performance reports are stored in the logs/ directory
- For detailed parameters and extensions, refer to API_REFERENCE.md

## Model Configuration
- Chinese model is integrated by default, no download required
- English model is only reserved in config, download and place it in the models/ path to use
- Switch between Chinese and English via the lang field

## Performance Monitoring
- The system automatically records API response times and exceptions, and supports /api/v1/report for statistical reports
- Monitoring frequency is optimized for low-end devices 