import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List

class CircuitEventTimeline:
    """
    Displays circuit breaking events on a timeline.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the circuit event timeline.
        
        Args:
            parent_frame: The parent tkinter frame
        """
        self.parent = parent_frame
        self.event_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the timeline UI components."""
        # Create a frame for the timeline
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create toolbar frame above the chart
        self.toolbar_frame = ttk.Frame(self.frame)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add timeline range selector
        ttk.Label(self.toolbar_frame, text="Time Range:").pack(side=tk.LEFT, padx=5)
        self.range_var = tk.StringVar(value="1h")
        range_options = ttk.Combobox(self.toolbar_frame, textvariable=self.range_var, 
                                    values=["15m", "30m", "1h", "3h", "6h", "12h", "24h"],
                                    width=5)
        range_options.pack(side=tk.LEFT, padx=5)
        range_options.bind("<<ComboboxSelected>>", self.on_range_changed)
        
        # Add filter checkboxes
        self.filter_frame = ttk.LabelFrame(self.toolbar_frame, text="Event Types")
        self.filter_frame.pack(side=tk.RIGHT, padx=5)
        
        # Event type filters
        self.filter_vars = {}
        self.filter_colors = {
            "MEMORY_WARNING": "gold",
            "CIRCUIT_BREAK": "red",
            "RESOURCE_RELEASE": "green",
            "RECOVERY_ATTEMPT": "blue",
            "RECOVERY_SUCCESS": "green",
            "RECOVERY_FAILURE": "red"
        }
        
        for event_type, color in self.filter_colors.items():
            self.filter_vars[event_type] = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(self.filter_frame, text=event_type.replace('_', ' ').title(),
                                variable=self.filter_vars[event_type],
                                command=self.on_filter_changed)
            cb.pack(side=tk.LEFT, padx=2)
        
        # Create a matplotlib figure for the timeline
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Create the canvas to display the figure
        self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status label below the chart
        self.status_label = ttk.Label(self.frame, text="No events to display")
        self.status_label.pack(padx=5, pady=5, anchor=tk.W)
        
        # Initialize the timeline
        self._draw_timeline()
        
    def _draw_timeline(self):
        """Draw the timeline visualization."""
        # Clear previous content
        self.ax.clear()
        
        # Calculate time range
        time_range = self.range_var.get()
        end_time = datetime.now()
        
        # Parse time range
        if time_range.endswith('m'):
            minutes = int(time_range[:-1])
            start_time = end_time - timedelta(minutes=minutes)
        elif time_range.endswith('h'):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        else:
            # Default to 1 hour
            start_time = end_time - timedelta(hours=1)
            
        # Filter events by time and selected types
        filtered_events = []
        for event in self.event_data:
            # Check if this event type is enabled
            event_type = event.get('event_type')
            if not event_type or not self.filter_vars.get(event_type, tk.BooleanVar(value=True)).get():
                continue
                
            # Check if within time range
            timestamp = event.get('timestamp', 0)
            event_time = datetime.fromtimestamp(timestamp)
            if event_time >= start_time and event_time <= end_time:
                filtered_events.append(event)
        
        # Update status label
        if not filtered_events:
            self.status_label.config(text="No events to display in the selected time range")
            self.ax.text(0.5, 0.5, "No events to display",
                       ha='center', va='center', transform=self.ax.transAxes)
            self.ax.set_xlabel("Time")
            self.canvas.draw()
            return
            
        self.status_label.config(text=f"Displaying {len(filtered_events)} events")
        
        # Plot events on the timeline
        event_times = [datetime.fromtimestamp(e.get('timestamp', 0)) for e in filtered_events]
        event_types = [e.get('event_type', 'UNKNOWN') for e in filtered_events]
        event_sources = [e.get('source', 'unknown') for e in filtered_events]
        
        # Create y-positions for each event (staggered by type)
        y_positions = []
        y_labels = []
        y_map = {}  # Maps source to y-position
        
        for source in event_sources:
            if source not in y_map:
                y_map[source] = len(y_map) + 1
                y_labels.append(source)
            y_positions.append(y_map[source])
        
        # Create colormap for event types
        colors = []
        for event_type in event_types:
            color = self.filter_colors.get(event_type, 'gray')
            colors.append(color)
        
        # Plot events as markers on the timeline
        self.ax.scatter(event_times, y_positions, c=colors, s=100, alpha=0.7, 
                      marker='o', edgecolors='black')
        
        # Add connecting lines between events from the same source
        sources = list(y_map.keys())
        for source in sources:
            source_indices = [i for i, s in enumerate(event_sources) if s == source]
            if len(source_indices) > 1:
                source_times = [event_times[i] for i in source_indices]
                source_y = [y_positions[i] for i in source_indices]
                self.ax.plot(source_times, source_y, 'k-', alpha=0.3)
        
        # Format the x-axis as a time axis
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Set the y-axis to show source names
        self.ax.set_yticks(list(range(1, len(sources) + 1)))
        self.ax.set_yticklabels(sources)
        
        # Add grid and labels
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Source")
        
        # Add a title
        time_range_str = f"{start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')}"
        self.ax.set_title(f"Circuit Events - {time_range_str}")
        
        # Add a legend for event types
        legend_elements = []
        for event_type, color in self.filter_colors.items():
            if self.filter_vars.get(event_type, tk.BooleanVar(value=True)).get():
                legend_elements.append(matplotlib.patches.Patch(
                    facecolor=color, edgecolor='black',
                    label=event_type.replace('_', ' ').title()))
        
        if legend_elements:
            self.ax.legend(handles=legend_elements, loc='upper left', 
                         bbox_to_anchor=(1.02, 1), fontsize='small')
        
        # Rotate x-axis labels for better readability
        plt = self.figure.gca()
        for label in plt.get_xticklabels():
            label.set_rotation(45)
            label.set_horizontalalignment('right')
        
        # Adjust layout to make room for the legend
        self.figure.tight_layout()
        
        # Refresh the canvas
        self.canvas.draw()
        
    def on_range_changed(self, event):
        """Handle time range selection change."""
        self._draw_timeline()
        
    def on_filter_changed(self):
        """Handle event type filter change."""
        self._draw_timeline()
        
    def update(self, event_data: List[Dict[str, Any]]):
        """
        Update the timeline with new event data.
        
        Args:
            event_data: List of event dictionaries
        """
        self.event_data = event_data
        self._draw_timeline()


# For testing the component independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Circuit Event Timeline Test")
    root.geometry("800x600")
    
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    timeline = CircuitEventTimeline(frame)
    
    # Test with sample data
    import time
    
    # Generate sample events over the past hour
    now = time.time()
    sample_events = []
    
    # Event types for testing
    event_types = [
        "MEMORY_WARNING", 
        "CIRCUIT_BREAK", 
        "RESOURCE_RELEASE", 
        "RECOVERY_ATTEMPT",
        "RECOVERY_SUCCESS", 
        "RECOVERY_FAILURE"
    ]
    
    # Sources for testing
    sources = ["VideoProcessor", "TranscriptGenerator", "SubtitleExtractor", "LLMService"]
    
    # Generate random events
    import random
    for i in range(30):
        event_time = now - random.uniform(0, 3600)  # Random time in the last hour
        event_type = random.choice(event_types)
        source = random.choice(sources)
        
        sample_events.append({
            "event_id": f"event_{i}",
            "event_type": event_type,
            "source": source,
            "timestamp": event_time,
            "details": {"message": f"Sample event {i}"}
        })
    
    # Sort by timestamp
    sample_events.sort(key=lambda x: x["timestamp"])
    
    # Update the timeline
    timeline.update(sample_events)
    
    root.mainloop() 