import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import Dict, Any, List

class MemoryReleaseChart:
    """
    Visualizes memory release effectiveness with bar charts.
    """
    
    def __init__(self, parent_frame):
        """
        Initialize the memory release chart.
        
        Args:
            parent_frame: The parent tkinter frame
        """
        self.parent = parent_frame
        self.release_stats = {
            "total_releases": 0,
            "successful_releases": 0,
            "success_rate": 0,
            "total_memory_released_mb": 0,
            "average_release_mb": 0,
            "largest_release_mb": 0,
        }
        self.history = {
            "total_memory_released": [],
            "success_rates": []
        }
        self.max_history_points = 20
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the chart UI components."""
        # Create a frame for the chart
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add view selector
        self.view_frame = ttk.Frame(self.frame)
        self.view_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.view_frame, text="View:").pack(side=tk.LEFT, padx=5)
        self.view_var = tk.StringVar(value="current")
        view_options = ttk.Combobox(self.view_frame, textvariable=self.view_var, 
                                   values=["current", "history"],
                                   width=10)
        view_options.pack(side=tk.LEFT, padx=5)
        view_options.bind("<<ComboboxSelected>>", self.on_view_changed)
        
        # Create frames for different views
        self.current_view_frame = ttk.Frame(self.frame)
        self.current_view_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_view_frame = ttk.Frame(self.frame)
        
        # Set up current view (bar chart)
        self.current_figure = Figure(figsize=(5, 4), dpi=100)
        self.current_ax = self.current_figure.add_subplot(111)
        
        self.current_canvas = FigureCanvasTkAgg(self.current_figure, self.current_view_frame)
        self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Set up history view (line chart)
        self.history_figure = Figure(figsize=(5, 4), dpi=100)
        self.history_ax = self.history_figure.add_subplot(111)
        
        self.history_canvas = FigureCanvasTkAgg(self.history_figure, self.history_view_frame)
        self.history_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add stats labels
        self.stats_frame = ttk.LabelFrame(self.frame, text="Release Statistics")
        self.stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_labels = {}
        stats_layout = [
            ("total_releases", "Total Releases:", 0, 0),
            ("successful_releases", "Successful:", 0, 1),
            ("success_rate", "Success Rate:", 0, 2),
            ("total_memory_released_mb", "Total Released:", 1, 0),
            ("average_release_mb", "Avg Release Size:", 1, 1),
            ("largest_release_mb", "Largest Release:", 1, 2)
        ]
        
        for key, label_text, row, col in stats_layout:
            label = ttk.Label(self.stats_frame, text=label_text)
            label.grid(row=row, column=col*2, padx=5, pady=2, sticky="e")
            
            value_label = ttk.Label(self.stats_frame, text="0")
            value_label.grid(row=row, column=col*2+1, padx=5, pady=2, sticky="w")
            
            self.stats_labels[key] = value_label
        
        # Configure grid
        for i in range(6):
            self.stats_frame.columnconfigure(i, weight=1)
            
        # Initialize the charts
        self._draw_current_chart()
        self._draw_history_chart()
        
    def _draw_current_chart(self):
        """Draw the current release stats bar chart."""
        # Clear previous content
        self.current_ax.clear()
        
        # Get the data
        categories = ["Successful", "Failed", "Total Released (MB)"]
        values = [
            self.release_stats["successful_releases"],
            self.release_stats["total_releases"] - self.release_stats["successful_releases"],
            self.release_stats["total_memory_released_mb"]
        ]
        
        # Set colors based on values
        colors = ['green', 'red', 'blue']
        
        # Create the bar chart
        bars = self.current_ax.bar(categories, values, color=colors, alpha=0.7)
        
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            self.current_ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                              f'{height:.1f}', ha='center', va='bottom')
        
        # Customize the chart
        self.current_ax.set_ylabel('Count / Size (MB)')
        self.current_ax.set_title('Memory Release Effectiveness')
        self.current_ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Refresh the canvas
        self.current_figure.tight_layout()
        self.current_canvas.draw()
        
    def _draw_history_chart(self):
        """Draw the release history line chart."""
        # Clear previous content
        self.history_ax.clear()
        
        # Plot total memory released history
        x = list(range(len(self.history["total_memory_released"])))
        if x:  # Only plot if we have data
            self.history_ax.plot(x, self.history["total_memory_released"], 
                               'b-', label='Memory Released (MB)', marker='o')
                               
            # Plot success rate on secondary y-axis
            ax2 = self.history_ax.twinx()
            ax2.plot(x, self.history["success_rates"], 
                   'g-', label='Success Rate (%)', marker='s')
            ax2.set_ylabel('Success Rate (%)', color='g')
            ax2.tick_params(axis='y', labelcolor='g')
            ax2.set_ylim(0, 100)  # Success rate is percentage
            
            # Labels and title
            self.history_ax.set_xlabel('Time')
            self.history_ax.set_ylabel('Memory Released (MB)', color='b')
            self.history_ax.tick_params(axis='y', labelcolor='b')
            self.history_ax.set_title('Memory Release History')
            
            # Add grid
            self.history_ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add legend
            lines1, labels1 = self.history_ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            self.history_ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            # Use integers for x-axis if we have many points
            if len(x) > 10:
                self.history_ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        else:
            self.history_ax.text(0.5, 0.5, "No history data available",
                              ha='center', va='center', transform=self.history_ax.transAxes)
        
        # Refresh the canvas
        self.history_figure.tight_layout()
        self.history_canvas.draw()
        
    def on_view_changed(self, event):
        """Handle view selection change."""
        view = self.view_var.get()
        
        if view == "current":
            self.history_view_frame.pack_forget()
            self.current_view_frame.pack(fill=tk.BOTH, expand=True)
        else:  # history
            self.current_view_frame.pack_forget()
            self.history_view_frame.pack(fill=tk.BOTH, expand=True)
        
    def update(self, stats: Dict[str, Any]):
        """
        Update the chart with new release statistics.
        
        Args:
            stats: Dictionary with release statistics
        """
        # Save the stats
        old_stats = self.release_stats.copy()
        self.release_stats = stats
        
        # Update history if values have changed
        if (old_stats["total_memory_released_mb"] != stats["total_memory_released_mb"] or
            old_stats["success_rate"] != stats["success_rate"]):
            
            # Add to history
            self.history["total_memory_released"].append(stats["total_memory_released_mb"])
            self.history["success_rates"].append(stats["success_rate"])
            
            # Limit history size
            if len(self.history["total_memory_released"]) > self.max_history_points:
                self.history["total_memory_released"] = self.history["total_memory_released"][-self.max_history_points:]
                self.history["success_rates"] = self.history["success_rates"][-self.max_history_points:]
        
        # Update the charts
        self._draw_current_chart()
        self._draw_history_chart()
        
        # Update stats labels
        self._update_stats_labels()
        
    def _update_stats_labels(self):
        """Update the statistics labels with current values."""
        formats = {
            "total_releases": "{:d}",
            "successful_releases": "{:d}",
            "success_rate": "{:.1f}%",
            "total_memory_released_mb": "{:.1f} MB",
            "average_release_mb": "{:.1f} MB",
            "largest_release_mb": "{:.1f} MB"
        }
        
        for key, label in self.stats_labels.items():
            value = self.release_stats.get(key, 0)
            format_str = formats.get(key, "{}")
            label.config(text=format_str.format(value))


# For testing the component independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Memory Release Chart Test")
    root.geometry("700x600")
    
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    chart = MemoryReleaseChart(frame)
    
    # Test with sample data
    import random
    
    def update_test():
        # Generate sample stats
        successful = random.randint(5, 20)
        total = successful + random.randint(0, 5)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        total_released = random.uniform(100, 500)
        avg_release = total_released / total if total > 0 else 0
        largest = avg_release * random.uniform(1.5, 3.0)
        
        stats = {
            "total_releases": total,
            "successful_releases": successful,
            "success_rate": success_rate,
            "total_memory_released_mb": total_released,
            "average_release_mb": avg_release,
            "largest_release_mb": largest
        }
        
        # Update the chart
        chart.update(stats)
        
        # Schedule the next update
        root.after(3000, update_test)
    
    # Start the update loop
    update_test()
    
    root.mainloop() 