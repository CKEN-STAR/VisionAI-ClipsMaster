import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

from event_tracer import EventTracer, CircuitEvent

class EventList:
    """
    Displays circuit breaking events in a list format with details.
    """
    
    def __init__(self, parent_frame, event_tracer: EventTracer):
        """
        Initialize the event list.
        
        Args:
            parent_frame: The parent tkinter frame
            event_tracer: The EventTracer instance to get events from
        """
        self.parent = parent_frame
        self.event_tracer = event_tracer
        self.current_event = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the event list UI components."""
        # Create the main frame
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add filter controls at the top
        self.filter_frame = ttk.Frame(self.frame)
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Event type filter
        ttk.Label(self.filter_frame, text="Event Type:").pack(side=tk.LEFT, padx=5)
        self.type_var = tk.StringVar(value="All")
        event_types = ["All", "MEMORY_WARNING", "CIRCUIT_BREAK", "RESOURCE_RELEASE", 
                      "RECOVERY_ATTEMPT", "RECOVERY_SUCCESS", "RECOVERY_FAILURE"]
        type_combo = ttk.Combobox(self.filter_frame, textvariable=self.type_var, 
                                values=event_types, width=15)
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Source filter
        ttk.Label(self.filter_frame, text="Source:").pack(side=tk.LEFT, padx=5)
        self.source_var = tk.StringVar(value="All")
        self.source_combo = ttk.Combobox(self.filter_frame, textvariable=self.source_var, 
                                       width=15)
        self.source_combo.pack(side=tk.LEFT, padx=5)
        self.source_combo.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Time range filter
        ttk.Label(self.filter_frame, text="Time Range:").pack(side=tk.LEFT, padx=5)
        self.time_var = tk.StringVar(value="1h")
        time_options = ttk.Combobox(self.filter_frame, textvariable=self.time_var, 
                                   values=["15m", "30m", "1h", "3h", "6h", "12h", "24h"],
                                   width=5)
        time_options.pack(side=tk.LEFT, padx=5)
        time_options.bind("<<ComboboxSelected>>", self.on_filter_changed)
        
        # Add refresh button
        ttk.Button(self.filter_frame, text="Refresh", 
                  command=self.refresh_events).pack(side=tk.RIGHT, padx=5)
        
        # Create a paned window for the list and details
        self.paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left side - Event list
        self.list_frame = ttk.Frame(self.paned)
        self.paned.add(self.list_frame, weight=1)
        
        # Create event Treeview
        columns = ("time", "type", "source")
        self.event_tree = ttk.Treeview(self.list_frame, columns=columns, show="headings")
        
        # Define headings
        self.event_tree.heading("time", text="Time")
        self.event_tree.heading("type", text="Type")
        self.event_tree.heading("source", text="Source")
        
        # Define columns
        self.event_tree.column("time", width=150)
        self.event_tree.column("type", width=150)
        self.event_tree.column("source", width=150)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, 
                                command=self.event_tree.yview)
        self.event_tree.configure(yscrollcommand=y_scroll.set)
        
        # Pack everything
        self.event_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.event_tree.bind("<<TreeviewSelect>>", self.on_event_selected)
        
        # Right side - Event details
        self.details_frame = ttk.LabelFrame(self.paned, text="Event Details")
        self.paned.add(self.details_frame, weight=1)
        
        # Add details text
        self.details_text = tk.Text(self.details_frame, wrap=tk.WORD, height=20, width=50)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar for details
        details_scroll = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL,
                                     command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Set the initial state
        self.details_text.insert(tk.END, "Select an event to view details")
        self.details_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_var = tk.StringVar(value="No events loaded")
        self.status_bar = ttk.Label(self.frame, textvariable=self.status_var, 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load initial events
        self.refresh_events()
        
    def refresh_events(self):
        """Refresh the events list from the event tracer."""
        # Get events from tracer
        self._populate_events()
        self._update_source_filter_options()
        
    def _populate_events(self):
        """Populate the events treeview based on current filters."""
        # Clear existing items
        for item in self.event_tree.get_children():
            self.event_tree.delete(item)
            
        # Get filter values
        event_type = self.type_var.get()
        if event_type == "All":
            event_type = None
            
        source = self.source_var.get()
        if source == "All":
            source = None
            
        time_filter = self.time_var.get()
        time_start = None
        
        # Convert time filter to timestamp
        if time_filter:
            now = datetime.now()
            
            # Parse time filter
            if time_filter.endswith("m"):
                minutes = int(time_filter[:-1])
                time_start = now.timestamp() - (minutes * 60)
            elif time_filter.endswith("h"):
                hours = int(time_filter[:-1])
                time_start = now.timestamp() - (hours * 3600)
        
        # Find matching events
        events = self.event_tracer.find_events(
            event_type=event_type,
            source=source,
            time_start=time_start
        )
        
        # Sort events by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Add to treeview
        for event in events:
            time_str = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            # Get event type name from constant value
            event_type_name = event.event_type
            for name, value in CircuitEvent.EVENT_TYPES.items():
                if str(value) == event.event_type:
                    event_type_name = name
                    break
            
            self.event_tree.insert("", tk.END, 
                                  values=(time_str, event_type_name, event.source),
                                  tags=(event.event_type,), iid=event.event_id)
            
        # Configure tag colors
        self.event_tree.tag_configure("10", background="lightyellow")  # MEMORY_WARNING
        self.event_tree.tag_configure("20", background="lightcoral")   # CIRCUIT_BREAK
        self.event_tree.tag_configure("30", background="lightgreen")   # RESOURCE_RELEASE
        self.event_tree.tag_configure("40", background="lightblue")    # RECOVERY_ATTEMPT
        self.event_tree.tag_configure("50", background="lightgreen")   # RECOVERY_SUCCESS
        self.event_tree.tag_configure("60", background="lightcoral")   # RECOVERY_FAILURE
        
        # Update status
        self.status_var.set(f"{len(events)} events loaded")
        
        # Select first event if available
        if events:
            self.event_tree.selection_set(events[0].event_id)
            self.on_event_selected(None)
            
    def _update_source_filter_options(self):
        """Update the source filter dropdown with available sources."""
        # Get all unique sources
        sources = set()
        for event in self.event_tracer.events:
            sources.add(event.source)
            
        # Sort and add "All" option
        sorted_sources = sorted(list(sources))
        sorted_sources.insert(0, "All")
        
        # Update combobox values, keeping current selection if possible
        current = self.source_var.get()
        self.source_combo["values"] = sorted_sources
        
        if current not in sorted_sources:
            self.source_var.set("All")
            
    def on_filter_changed(self, event):
        """Handle filter selection change."""
        self._populate_events()
        
    def on_event_selected(self, event):
        """Handle event selection in the tree."""
        selected_items = self.event_tree.selection()
        if not selected_items:
            return
            
        # Get the event ID
        event_id = selected_items[0]
        self.current_event = self.event_tracer.get_event_by_id(event_id)
        
        if not self.current_event:
            return
            
        # Update details text
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        # Format the event details
        time_str = datetime.fromtimestamp(self.current_event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get event type name from constant value
        event_type_name = self.current_event.event_type
        for name, value in CircuitEvent.EVENT_TYPES.items():
            if str(value) == self.current_event.event_type:
                event_type_name = name
                break
                
        self.details_text.insert(tk.END, f"Event ID: {self.current_event.event_id}\n")
        self.details_text.insert(tk.END, f"Time: {time_str}\n")
        self.details_text.insert(tk.END, f"Type: {event_type_name}\n")
        self.details_text.insert(tk.END, f"Source: {self.current_event.source}\n\n")
        
        # Add details section
        self.details_text.insert(tk.END, "Details:\n")
        if self.current_event.details:
            # Format details as pretty JSON
            details_str = json.dumps(self.current_event.details, indent=2)
            self.details_text.insert(tk.END, details_str)
        else:
            self.details_text.insert(tk.END, "No details available")
            
        # Add related events section
        self.details_text.insert(tk.END, "\n\nRelated Events:\n")
        
        related_events = self.event_tracer.find_related_events(self.current_event)
        if related_events:
            for i, rel in enumerate(related_events):
                time_str = datetime.fromtimestamp(rel.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                # Get event type name
                rel_type_name = rel.event_type
                for name, value in CircuitEvent.EVENT_TYPES.items():
                    if str(value) == rel.event_type:
                        rel_type_name = name
                        break
                        
                self.details_text.insert(tk.END, f"{i+1}. [{time_str}] {rel_type_name} from {rel.source}\n")
        else:
            self.details_text.insert(tk.END, "No related events")
            
        self.details_text.config(state=tk.DISABLED)
        
    def select_event(self, event_id: str):
        """
        Select a specific event in the list.
        
        Args:
            event_id: ID of the event to select
        """
        # Check if the event is in the current view
        items = self.event_tree.get_children()
        if event_id in items:
            self.event_tree.selection_set(event_id)
            self.event_tree.see(event_id)
            self.on_event_selected(None)
        else:
            # Try to reset filters to find the event
            event = self.event_tracer.get_event_by_id(event_id)
            if event:
                self.type_var.set("All")
                self.source_var.set("All")
                
                # Set time filter to include this event
                now = datetime.now().timestamp()
                event_time = event.timestamp
                time_diff_hours = (now - event_time) / 3600
                
                if time_diff_hours < 0.25:
                    self.time_var.set("15m")
                elif time_diff_hours < 0.5:
                    self.time_var.set("30m")
                elif time_diff_hours < 1:
                    self.time_var.set("1h")
                elif time_diff_hours < 3:
                    self.time_var.set("3h")
                elif time_diff_hours < 6:
                    self.time_var.set("6h")
                elif time_diff_hours < 12:
                    self.time_var.set("12h")
                else:
                    self.time_var.set("24h")
                    
                # Refresh with new filters
                self._populate_events()
                
                # Try to select again
                if event_id in self.event_tree.get_children():
                    self.event_tree.selection_set(event_id)
                    self.event_tree.see(event_id)
                    self.on_event_selected(None)
        
    def update(self):
        """Update the event list with the latest events."""
        # Keep track of current selection
        selected_items = self.event_tree.selection()
        selected_id = selected_items[0] if selected_items else None
        
        # Refresh the events
        self._populate_events()
        
        # Restore selection if possible
        if selected_id and selected_id in self.event_tree.get_children():
            self.event_tree.selection_set(selected_id)
            self.event_tree.see(selected_id)


# For testing the component independently
if __name__ == "__main__":
    import time
    import random

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

    
    # Create a sample EventTracer
    tracer = EventTracer()
    
    # Generate sample events
    event_types = list(CircuitEvent.EVENT_TYPES.items())
    sources = ["VideoProcessor", "TranscriptGenerator", "SubtitleExtractor", "LLMService"]
    
    # Add some events
    now = time.time()
    
    # Create a sequence of related events
    # 1. Memory warning
    warning_event = tracer.record_event(
        event_type=str(CircuitEvent.EVENT_TYPES["MEMORY_WARNING"]),
        source="VideoProcessor",
        details={"memory_percent": 85.2, "memory_mb": 3584.7}
    )
    
    # 2. Circuit break
    break_event = tracer.record_event(
        event_type=str(CircuitEvent.EVENT_TYPES["CIRCUIT_BREAK"]),
        source="VideoProcessor",
        details={"memory_percent": 92.1, "memory_mb": 3867.3, "trigger": "threshold"},
        related_to=warning_event
    )
    
    # 3. Resource release
    release_event = tracer.record_event(
        event_type=str(CircuitEvent.EVENT_TYPES["RESOURCE_RELEASE"]),
        source="VideoProcessor",
        details={"resources": ["video_buffer", "frame_cache"], "memory_released_mb": 1200.5},
        related_to=break_event
    )
    
    # 4. Recovery attempt
    recovery_event = tracer.record_event(
        event_type=str(CircuitEvent.EVENT_TYPES["RECOVERY_ATTEMPT"]),
        source="RecoveryManager",
        details={"point_id": "auto_recovery_1", "resources": ["video_processor"]},
        related_to=break_event
    )
    
    # 5. Recovery success
    success_event = tracer.record_event(
        event_type=str(CircuitEvent.EVENT_TYPES["RECOVERY_SUCCESS"]),
        source="RecoveryManager",
        details={"point_id": "auto_recovery_1", "success_rate": 100},
        related_to=recovery_event
    )
    
    # Add some random events
    for i in range(20):
        event_time = now - random.uniform(0, 86400)  # Random time in the last 24 hours
        event_type = random.choice(event_types)
        source = random.choice(sources)
        
        tracer.record_event(
            event_type=str(event_type[1]),
            source=source,
            details={"message": f"Sample event {i}"}
        )
    
    # Create the Tkinter app
    root = tk.Tk()
    root.title("Circuit Event List Test")
    root.geometry("1000x600")
    
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    
    event_list = EventList(frame, tracer)
    
    root.mainloop() 