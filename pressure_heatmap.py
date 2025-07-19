import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

class PressureHeatmap:
    """
    Visualizes memory pressure over time using a heatmap.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the pressure heatmap.
        
        Args:
            parent_frame: The parent tkinter frame
        """
        self.parent = parent_frame
        
        # Store pressure readings (time, value)
        self.pressure_readings = []
        self.max_readings = 100
        
        # Time buckets for the heatmap (in minutes)
        self.time_buckets = 10
        self.rows = 5  # Number of pressure level rows
        
        # Create the heatmap matrix
        self.heatmap_data = np.zeros((self.rows, self.time_buckets))
        
        # Counters for each cell
        self.hit_counts = np.zeros((self.rows, self.time_buckets))
        
        # Pressure thresholds for rows
        self.pressure_thresholds = [20, 40, 60, 80, 100]
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the heatmap UI components."""
        # Create a frame for the heatmap
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add time range selector
        self.toolbar_frame = ttk.Frame(self.frame)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.toolbar_frame, text="Time Window:").pack(side=tk.LEFT, padx=5)
        self.time_window_var = tk.StringVar(value="15m")
        time_options = ttk.Combobox(self.toolbar_frame, textvariable=self.time_window_var, 
                                   values=["5m", "15m", "30m", "1h", "3h"],
                                   width=5)
        time_options.pack(side=tk.LEFT, padx=5)
        time_options.bind("<<ComboboxSelected>>", self.on_time_window_changed)
        
        # Add resolution selector
        ttk.Label(self.toolbar_frame, text="Buckets:").pack(side=tk.LEFT, padx=5)
        self.buckets_var = tk.StringVar(value="10")
        bucket_options = ttk.Combobox(self.toolbar_frame, textvariable=self.buckets_var, 
                                     values=["5", "10", "15", "20", "30"],
                                     width=5)
        bucket_options.pack(side=tk.LEFT, padx=5)
        bucket_options.bind("<<ComboboxSelected>>", self.on_buckets_changed)
        
        # Create a matplotlib figure for the heatmap
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Create the canvas to display the figure
        self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status label below the heatmap
        self.status_label = ttk.Label(self.frame, text="No data")
        self.status_label.pack(padx=5, pady=5)
        
        # Initialize the heatmap
        self._draw_heatmap()
        
    def _get_time_window_minutes(self) -> int:
        """Convert time window setting to minutes."""
        window = self.time_window_var.get()
        if window.endswith('m'):
            return int(window[:-1])
        elif window.endswith('h'):
            return int(window[:-1]) * 60
        return 15  # Default to 15 minutes
        
    def _get_bucket_count(self) -> int:
        """Get the number of time buckets."""
        try:
            return int(self.buckets_var.get())
        except:
            return 10
        
    def _update_heatmap_data(self):
        """Update the heatmap data matrix from pressure readings."""
        # Get current settings
        window_minutes = self._get_time_window_minutes()
        bucket_count = self._get_bucket_count()
        
        # If settings have changed, resize the matrices
        if bucket_count != self.time_buckets:
            self.time_buckets = bucket_count
            self.heatmap_data = np.zeros((self.rows, self.time_buckets))
            self.hit_counts = np.zeros((self.rows, self.time_buckets))
        
        # Filter readings within the time window
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=window_minutes)
        cutoff_timestamp = cutoff_time.timestamp()
        
        recent_readings = [(t, v) for t, v in self.pressure_readings 
                           if t >= cutoff_timestamp]
        
        # Clear the existing data
        self.heatmap_data.fill(0)
        self.hit_counts.fill(0)
        
        # No data to display
        if not recent_readings:
            return
            
        # Calculate bucket width in seconds
        bucket_width = (window_minutes * 60) / self.time_buckets
        
        # Process each reading
        for timestamp, value in recent_readings:
            # Determine which bucket this reading belongs to
            time_offset = now.timestamp() - timestamp
            if time_offset <= 0:
                time_offset = 0
                
            bucket_index = min(int(time_offset / bucket_width), self.time_buckets - 1)
            
            # Determine which row (pressure level) this reading belongs to
            row_index = 0
            for i, threshold in enumerate(self.pressure_thresholds):
                if value <= threshold:
                    row_index = i
                    break
            
            # Update the heatmap data
            self.heatmap_data[row_index, bucket_index] += value
            self.hit_counts[row_index, bucket_index] += 1
            
        # Calculate averages
        with np.errstate(divide='ignore', invalid='ignore'):
            avg_data = np.divide(self.heatmap_data, self.hit_counts)
            avg_data = np.nan_to_num(avg_data)  # Replace NaN with 0
            
        self.heatmap_data = avg_data
        
    def _draw_heatmap(self):
        """Draw the heatmap visualization."""
        # Clear previous content
        self.ax.clear()
        
        # Update the heatmap data
        self._update_heatmap_data()
        
        # Create the heatmap
        cmap = matplotlib.cm.get_cmap('RdYlGn_r')  # Red-Yellow-Green (reversed)
        im = self.ax.imshow(self.heatmap_data, cmap=cmap, aspect='auto',
                          vmin=0, vmax=100)
                          
        # Add colorbar
        cbar = self.figure.colorbar(im, ax=self.ax)
        cbar.set_label('Memory Pressure (%)')
        
        # Set labels
        window_minutes = self._get_time_window_minutes()
        now = datetime.now()
        start_time = now - timedelta(minutes=window_minutes)
        
        # Create time labels
        time_labels = []
        for i in range(self.time_buckets):
            # Calculate the time for this bucket
            fraction = i / self.time_buckets
            offset_minutes = window_minutes * (1 - fraction)
            bucket_time = now - timedelta(minutes=offset_minutes)
            time_labels.append(bucket_time.strftime('%H:%M'))
            
        # Only show a subset of time labels to prevent crowding
        show_indices = np.linspace(0, self.time_buckets-1, min(5, self.time_buckets), dtype=int)
        visible_time_labels = [time_labels[i] if i in show_indices else '' for i in range(self.time_buckets)]
        
        # Set x-axis labels (time)
        self.ax.set_xticks(np.arange(self.time_buckets))
        self.ax.set_xticklabels(visible_time_labels)
        
        # Set y-axis labels (pressure levels)
        pressure_labels = [f"0-{self.pressure_thresholds[0]}%"]
        for i in range(1, len(self.pressure_thresholds)):
            prev = self.pressure_thresholds[i-1]
            curr = self.pressure_thresholds[i]
            pressure_labels.append(f"{prev}-{curr}%")
            
        self.ax.set_yticks(np.arange(self.rows))
        self.ax.set_yticklabels(pressure_labels)
        
        # Add title and labels
        self.ax.set_title(f"Memory Pressure Heatmap (Last {window_minutes} minutes)")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Pressure Level")
        
        # Add grid
        self.ax.grid(False)
        
        # Update status label
        if not any(self.hit_counts.flatten()):
            self.status_label.config(text="No data in the selected time range")
        else:
            total_readings = int(np.sum(self.hit_counts))
            self.status_label.config(text=f"Displaying {total_readings} readings")
            
        # Refresh the canvas
        self.figure.tight_layout()
        self.canvas.draw()
        
    def on_time_window_changed(self, event):
        """Handle time window selection change."""
        self._draw_heatmap()
        
    def on_buckets_changed(self, event):
        """Handle bucket count selection change."""
        self._draw_heatmap()
        
    def update(self, stats: Dict[str, Any]):
        """
        Update the heatmap with new pressure data.
        
        Args:
            stats: Dictionary with pressure statistics including readings
        """
        # Extract pressure readings from stats
        if "readings" in stats:
            readings = stats["readings"]
            
            # Add new readings to our collection
            for reading in readings:
                # Each reading is expected to be (timestamp, percentage, mb)
                if len(reading) >= 2:
                    timestamp, percentage = reading[0], reading[1]
                    self.pressure_readings.append((timestamp, percentage))
            
            # Limit the number of stored readings
            if len(self.pressure_readings) > self.max_readings:
                self.pressure_readings = self.pressure_readings[-self.max_readings:]
        
        # Update the heatmap
        self._draw_heatmap()


# For testing the component independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Memory Pressure Heatmap Test")
    root.geometry("800x600")
    
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    heatmap = PressureHeatmap(frame)
    
    # Test with sample data
    import random
    import time
    
    def update_test():
        now = time.time()
        
        # Generate several minutes of sample data
        sample_readings = []
        
        # Create a pattern of pressure over time
        for i in range(60):  # Last 60 minutes
            timestamp = now - (60 - i) * 60  # Every minute
            
            # Create a pattern - starts low, rises, peaks, falls
            if i < 15:
                base_pressure = 20 + i * 1.5  # Rising slowly
            elif i < 30:
                base_pressure = 40 + (i - 15) * 2  # Rising faster
            elif i < 45:
                base_pressure = 70 - (i - 30) * 1.5  # Falling
            else:
                base_pressure = 30 - (i - 45) * 0.5  # Falling slowly
                
            # Add some randomness
            pressure = min(100, max(0, base_pressure + random.uniform(-10, 10)))
            
            # 10 seconds of readings per minute
            for j in range(10):
                sample_timestamp = timestamp + j * 6
                sample_pressure = pressure + random.uniform(-5, 5)
                sample_readings.append((sample_timestamp, sample_pressure, 0))
        
        # Update the heatmap
        heatmap.update({"readings": sample_readings})
        
        # No need to update again for testing
    
    # Run the update once with sample data
    update_test()
    
    root.mainloop() 