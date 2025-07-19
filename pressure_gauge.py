import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import Dict, Any

class MemoryPressureGauge:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """
    Displays a gauge visualization for memory pressure.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the memory pressure gauge.
        
        Args:
            parent_frame: The parent tkinter frame
        """
        self.parent = parent_frame
        self.setup_ui()
        
        # Initialize data
        self.current_memory_pct = 0
        self.trend = "stable"
        self.warning_threshold = 80.0
        self.critical_threshold = 90.0
        
    def setup_ui(self):
        """Set up the gauge UI components."""
        # Create a frame for the gauge
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a matplotlib figure for the gauge
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111, polar=True)
        
        # Create the canvas to display the figure
        self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add labels below the gauge
        self.label_frame = ttk.Frame(self.frame)
        self.label_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.value_label = ttk.Label(self.label_frame, text="0.0%", font=("Arial", 24))
        self.value_label.pack(side=tk.LEFT, padx=10)
        
        self.trend_label = ttk.Label(self.label_frame, text="Stable", font=("Arial", 12))
        self.trend_label.pack(side=tk.RIGHT, padx=10)
        
        # Initialize the gauge
        self._draw_gauge()
        
    def _draw_gauge(self):
        """Draw the gauge visualization."""
        # Clear previous content
        self.ax.clear()
        
        # Define gauge properties
        gauge_min = 0
        gauge_max = 100
        
        # Define color zones
        green_max = self.warning_threshold
        yellow_max = self.critical_threshold
        
        # Set gauge limits
        self.ax.set_theta_direction(-1)  # Clockwise
        self.ax.set_theta_offset(np.pi/2)  # Start at top
        
        # Set gauge range (in radians)
        start_angle = np.radians(180)   # Start at -90 degrees
        end_angle = np.radians(0)       # End at 90 degrees
        
        # Hide unnecessary parts
        self.ax.set_rticks([])  # Hide radial ticks
        self.ax.set_xticks(np.linspace(start_angle, end_angle, 6))
        self.ax.set_xticklabels(['0', '20', '40', '60', '80', '100'])
        self.ax.grid(False)
        
        # Draw gauge background
        # Green zone
        green_end = start_angle + (end_angle - start_angle) * green_max / gauge_max
        self.ax.barh(0, 1, height=0.8, left=0, 
                   color='lightgreen', alpha=0.6,
                   theta1=start_angle, theta2=green_end)
                   
        # Yellow zone
        yellow_end = start_angle + (end_angle - start_angle) * yellow_max / gauge_max
        self.ax.barh(0, 1, height=0.8, left=0, 
                   color='yellow', alpha=0.6,
                   theta1=green_end, theta2=yellow_end)
                   
        # Red zone
        self.ax.barh(0, 1, height=0.8, left=0, 
                   color='lightcoral', alpha=0.6,
                   theta1=yellow_end, theta2=end_angle)
        
        # Draw the needle based on current value
        needle_angle = start_angle + (end_angle - start_angle) * self.current_memory_pct / gauge_max
        self.ax.plot([0, needle_angle], [0, 0.75], 'k-', linewidth=3)
        self.ax.plot([0], [0], 'ko', markersize=8)
        
        # Add title
        self.ax.set_title('Memory Pressure', pad=15)
        
        # Refresh the canvas
        self.canvas.draw()
        
    def update(self, memory_pct: float, stats: Dict[str, Any] = None):
        """
        Update the gauge with new memory pressure data.
        
        Args:
            memory_pct: Current memory percentage (0-100)
            stats: Optional additional statistics
        """
        self.current_memory_pct = memory_pct
        
        # Update trend if stats provided
        if stats and "trend" in stats:
            self.trend = stats["trend"]
        
        # Update gauge visualization
        self._draw_gauge()
        
        # Update text labels
        self.value_label.config(text=f"{memory_pct:.1f}%")
        
        # Format trend label
        trend_text = self.trend.capitalize()
        trend_color = "black"
        
        if self.trend == "rising":
            trend_text = "⬆ Rising"
            trend_color = "red"
        elif self.trend == "falling":
            trend_text = "⬇ Falling"
            trend_color = "green"
        else:
            trend_text = "➡ Stable"
        
        self.trend_label.config(text=trend_text, foreground=trend_color)


# For testing the component independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Memory Pressure Gauge Test")
    root.geometry("400x400")
    
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    gauge = MemoryPressureGauge(frame)
    
    # Test updating the gauge
    def update_test():
        import random
        # Generate a random memory percentage
        memory_pct = random.uniform(0, 100)
        # Randomly select a trend
        trend = random.choice(["rising", "falling", "stable"])
        # Update the gauge
        gauge.update(memory_pct, {"trend": trend})
        # Schedule the next update
        root.after(2000, update_test)
    
    # Start the update loop
    update_test()
    
    root.mainloop() 