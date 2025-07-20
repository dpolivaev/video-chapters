#!/usr/bin/env python3
#
# Copyright 2025 Dimitry Polivaev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Instruction History Dialog for Chapter Timecode Generator
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from config import config


class InstructionHistoryDialog:
    """Dialog for managing instruction history."""
    
    def __init__(self, parent_gui, instructions_text_widget, tip_label):
        """Initialize the dialog.
        
        Args:
            parent_gui: The main GUI instance
            instructions_text_widget: The text widget to load instructions into
            tip_label: The tip label to hide when instructions are loaded
        """
        self.parent_gui = parent_gui
        self.instructions_text = instructions_text_widget
        self.tip_label = tip_label
        self.dialog = None
        
    def show_dialog(self):
        """Show the Previous Instructions dialog."""
        self.dialog = tk.Toplevel(self.parent_gui.root)
        self.dialog.title("Previous Instructions")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # Center the window
        self.dialog.transient(self.parent_gui.root)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Settings frame
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(settings_frame, text="Keep up to").pack(side=tk.LEFT)
        
        # Limit spinbox
        limit_var = tk.IntVar(value=config.get_instruction_history_limit())
        limit_spinbox = ttk.Spinbox(settings_frame, from_=1, to=50, width=5, 
                                   textvariable=limit_var, command=lambda: self._on_limit_change(limit_var))
        limit_spinbox.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Label(settings_frame, text="versions").pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Instructions frame with scrollbar
        instructions_frame = ttk.Frame(main_frame)
        instructions_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for instructions
        canvas = tk.Canvas(instructions_frame)
        scrollbar = ttk.Scrollbar(instructions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Get instruction history
        history = config.get_instruction_history()
        
        if not history:
            # No history message
            no_history_label = ttk.Label(scrollable_frame, 
                                        text="No previous instructions found.\nInstructions will be saved when you process a video.",
                                        justify=tk.CENTER, foreground="gray")
            no_history_label.pack(pady=20)
        else:
            # Create instruction entries
            for i, entry in enumerate(reversed(history)):  # Show newest first
                self._create_instruction_entry(scrollable_frame, entry, len(history) - 1 - i)
        
        # Close button
        close_btn = ttk.Button(main_frame, text="Close", command=self.dialog.destroy)
        close_btn.pack(pady=(10, 0))
        
        # Center the window on parent
        self.dialog.update_idletasks()
        x = (self.parent_gui.root.winfo_x() + (self.parent_gui.root.winfo_width() // 2) - 
             (self.dialog.winfo_width() // 2))
        y = (self.parent_gui.root.winfo_y() + (self.parent_gui.root.winfo_height() // 2) - 
             (self.dialog.winfo_height() // 2))
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_instruction_entry(self, parent, entry, original_index):
        """Create an instruction entry in the dialog."""
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(entry["timestamp"])
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            timestamp_str = "Unknown time"
        
        # Entry frame
        entry_frame = ttk.Frame(parent)
        entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Timestamp label
        timestamp_label = ttk.Label(entry_frame, text=timestamp_str, 
                                   font=("TkDefaultFont", 9, "bold"))
        timestamp_label.pack(anchor=tk.W)
        
        # Instruction text widget
        text_font = (self.parent_gui.mono_font, int(9 * self.parent_gui.font_scale))
        instruction_text = scrolledtext.ScrolledText(entry_frame, height=4, width=70,
                                                    wrap=tk.WORD, state=tk.DISABLED, font=text_font)
        instruction_text.pack(fill=tk.X, pady=(2, 5))
        instruction_text.configure(selectbackground='#0078d4', selectforeground='white')
        
        # Insert content
        instruction_text.config(state=tk.NORMAL)
        instruction_text.insert(tk.END, entry["content"])
        instruction_text.config(state=tk.DISABLED)
        
        # Buttons frame
        buttons_frame = ttk.Frame(entry_frame)
        buttons_frame.pack(fill=tk.X)
        
        # Select button
        select_btn = ttk.Button(buttons_frame, text="Select", 
                               command=lambda: self._select_instruction(entry["content"]))
        select_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Delete button
        delete_btn = ttk.Button(buttons_frame, text="Delete", 
                               command=lambda: self._delete_instruction(original_index, entry_frame))
        delete_btn.pack(side=tk.LEFT)
    
    def _on_limit_change(self, limit_var):
        """Handle limit change in the dialog."""
        try:
            new_limit = limit_var.get()
            if 1 <= new_limit <= 50:
                config.set_instruction_history_limit(new_limit)
        except tk.TclError:
            # Invalid value, ignore
            pass
    
    def _select_instruction(self, content):
        """Select an instruction and load it into the main text widget."""
        self.instructions_text.delete(1.0, tk.END)
        self.instructions_text.insert(1.0, content)
        self.tip_label.pack_forget()  # Hide tip
        if self.dialog:
            self.dialog.destroy()
    
    def _delete_instruction(self, index, entry_frame):
        """Delete an instruction from history."""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this instruction?"):
            config.delete_instruction_from_history(index)
            entry_frame.destroy() 