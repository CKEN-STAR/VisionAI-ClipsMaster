# AR Guidance Assets

This directory contains assets used for AR (Augmented Reality) guidance in the VisionAI-ClipsMaster application.

## Asset Types

- **Overlays**: Visual elements that are placed over UI components to highlight them
- **Animations**: Animated guides that demonstrate interactions
- **Markers**: Reference points for positioning AR elements
- **Instructions**: Text and visual instructions for users

## File Structure

```
ar_guides/
├── upload_video.asset    # Guide for uploading videos
├── slider_control.asset  # Guide for parameter slider controls
├── button_highlight.asset # Guide for button interactions
└── interface_tour.asset  # Complete interface tour guide
```

## Asset Format

AR guide assets are stored in a custom format that includes:
- Visual elements (SVG or PNG)
- Positioning information
- Animation data
- Interaction hints

## Usage

These assets are used by the `ar_guidance.py` module to provide interactive AR guidance to users. 