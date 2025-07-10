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
GUI for YouTube Subtitles to Chapter Timecodes
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List
import re

from core import YouTubeProcessor, ProcessingOptions, AVAILABLE_MODELS
from config import config

class YouTubeChaptersGUI:
    """Main GUI application for YouTube Chapters."""
    
    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("YouTube Chapters - Subtitle to Timecode Generator")
        self.root.geometry(config.get_window_geometry())
        self.root.minsize(800, 600)
        
        # Configure style
        self.setup_style()
        
        # Initialize processor
        self.processor = None
        self.processing_thread = None
        self.available_languages = {}
        
        # Variables
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        
        # Load saved settings
        self.load_settings()
        
        # Bind events
        self.setup_bindings()
        
    def setup_style(self):
        """Setup the GUI style."""
        style = ttk.Style()
        
        # Configure styles for better appearance
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Section.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Info.TLabel', font=('Helvetica', 9), foreground='gray')
        
        # Configure notebook style
        style.configure('Custom.TNotebook', tabposition='n')
        style.configure('Custom.TNotebook.Tab', padding=[20, 10])
        
    def setup_variables(self):
        """Setup tkinter variables."""
        self.url_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.language_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.keep_files_var = tk.BooleanVar()
        self.show_subtitles_var = tk.BooleanVar()
        self.quiet_var = tk.BooleanVar()
        self.output_dir_var = tk.StringVar()
        self.progress_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Chapters Generator", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL input
        ttk.Label(main_frame, text="YouTube URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # Check languages button
        self.check_langs_btn = ttk.Button(main_frame, text="Check Languages", 
                                         command=self.check_languages)
        self.check_langs_btn.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # API Key input
        ttk.Label(main_frame, text="Gemini API Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, 
                                      show="*", width=50)
        self.api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # API Key buttons
        api_key_frame = ttk.Frame(main_frame)
        api_key_frame.grid(row=2, column=2, pady=5, padx=(5, 0))
        
        ttk.Button(api_key_frame, text="Save", 
                  command=self.save_api_key).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(api_key_frame, text="Clear", 
                  command=self.clear_api_key).pack(side=tk.LEFT)
        
        # Language selection
        ttk.Label(main_frame, text="Language:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.language_combo = ttk.Combobox(main_frame, textvariable=self.language_var, 
                                          values=["Auto-detect"], state="readonly")
        self.language_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # Model selection
        ttk.Label(main_frame, text="Model:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, 
                                       values=AVAILABLE_MODELS, state="readonly")
        self.model_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(3, weight=1)
        
        # Checkboxes
        ttk.Checkbutton(options_frame, text="Keep files", 
                       variable=self.keep_files_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Show subtitles", 
                       variable=self.show_subtitles_var).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Quiet mode", 
                       variable=self.quiet_var).grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        
        # Output directory
        ttk.Label(options_frame, text="Output Dir:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.output_dir_entry = ttk.Entry(options_frame, textvariable=self.output_dir_var, width=40)
        self.output_dir_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0), padx=(5, 0))
        ttk.Button(options_frame, text="Browse", 
                  command=self.browse_output_dir).grid(row=1, column=3, pady=(10, 0), padx=(5, 0))
        
        # Create notebook for results
        self.notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
        self.notebook.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Progress tab
        self.progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_frame, text="Progress")
        
        self.progress_text = scrolledtext.ScrolledText(self.progress_frame, height=15, width=80)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Subtitles tab
        self.subtitles_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.subtitles_frame, text="Subtitles")
        
        self.subtitles_text = scrolledtext.ScrolledText(self.subtitles_frame, height=15, width=80)
        self.subtitles_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chapters tab
        self.chapters_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chapters_frame, text="Chapters")
        
        self.chapters_text = scrolledtext.ScrolledText(self.chapters_frame, height=15, width=80)
        self.chapters_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add save buttons to tabs
        self.create_save_buttons()
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        
        self.process_btn = ttk.Button(control_frame, text="Process Video", 
                                     command=self.process_video)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(control_frame, text="Clear All", 
                                   command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     style='Info.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        
    def create_save_buttons(self):
        """Create save buttons for each tab."""
        # Subtitles save button
        subtitles_btn_frame = ttk.Frame(self.subtitles_frame)
        subtitles_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(subtitles_btn_frame, text="Save Subtitles", 
                  command=self.save_subtitles).pack(side=tk.RIGHT)
        
        # Chapters save button
        chapters_btn_frame = ttk.Frame(self.chapters_frame)
        chapters_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(chapters_btn_frame, text="Save Chapters", 
                  command=self.save_chapters).pack(side=tk.RIGHT)
        
    def setup_bindings(self):
        """Setup event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-save settings on change
        self.url_var.trace_add("write", self.save_settings)
        self.model_var.trace_add("write", self.save_settings)
        self.language_var.trace_add("write", self.save_settings)
        self.keep_files_var.trace_add("write", self.save_settings)
        self.show_subtitles_var.trace_add("write", self.save_settings)
        self.quiet_var.trace_add("write", self.save_settings)
        self.output_dir_var.trace_add("write", self.save_settings)
        
    def load_settings(self):
        """Load settings from config."""
        self.url_var.set(config.get_last_url())
        self.model_var.set(config.get_model())
        self.language_var.set(config.get_language() or "Auto-detect")
        self.keep_files_var.set(config.get_keep_files())
        self.show_subtitles_var.set(config.get_show_subtitles())
        self.quiet_var.set(config.get_quiet())
        self.output_dir_var.set(config.get_output_dir())
        
        # Load API key
        api_key = config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)
        
    def save_settings(self, *args):
        """Save settings to config."""
        config.set_last_url(self.url_var.get())
        config.set_model(self.model_var.get())
        config.set_language(self.language_var.get() if self.language_var.get() != "Auto-detect" else "")
        config.set_keep_files(self.keep_files_var.get())
        config.set_show_subtitles(self.show_subtitles_var.get())
        config.set_quiet(self.quiet_var.get())
        config.set_output_dir(self.output_dir_var.get())
        
    def save_api_key(self):
        """Save API key to secure storage."""
        api_key = self.api_key_var.get().strip()
        if api_key:
            config.set_api_key(api_key)
            messagebox.showinfo("Success", "API key saved securely!")
        else:
            messagebox.showwarning("Warning", "Please enter an API key first.")
            
    def clear_api_key(self):
        """Clear API key from secure storage."""
        config.clear_api_key()
        self.api_key_var.set("")
        messagebox.showinfo("Success", "API key cleared!")
        
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            
    def check_languages(self):
        """Check available languages for the video."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL first.")
            return
            
        def check_langs_thread():
            try:
                self.update_status("Checking available languages...")
                self.check_langs_btn.config(state=tk.DISABLED)
                
                processor = YouTubeProcessor(self.log_progress)
                langs = processor.get_available_languages(url)
                
                # Update language combo
                self.root.after(0, self.update_language_combo, langs)
                
            except Exception as e:
                self.root.after(0, self.show_error, f"Error checking languages: {e}")
            finally:
                self.root.after(0, lambda: self.check_langs_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.update_status("Ready"))
                
        threading.Thread(target=check_langs_thread, daemon=True).start()
        
    def update_language_combo(self, langs: Dict[str, List[str]]):
        """Update language combo with available languages."""
        self.available_languages = langs
        
        if not langs:
            messagebox.showwarning("Warning", "No subtitles available for this video.")
            return
            
        # Create language options
        lang_options = ["Auto-detect"]
        
        for category, languages in langs.items():
            if languages:
                lang_options.append(f"--- {category.title()} ---")
                lang_options.extend(languages)
                
        self.language_combo.config(values=lang_options)
        
        # Show info about available languages
        info_msg = "Available languages:\n"
        for category, languages in langs.items():
            if languages:
                info_msg += f"{category.title()}: {', '.join(languages)}\n"
                
        messagebox.showinfo("Languages Available", info_msg)
        
    def process_video(self):
        """Process the video in a separate thread."""
        url = self.url_var.get().strip()
        api_key = self.api_key_var.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL.")
            return
            
        if not api_key:
            messagebox.showwarning("Warning", "Please enter your Gemini API key.")
            return
            
        # Clear previous results
        self.clear_results()
        
        # Start processing
        self.processing_thread = threading.Thread(target=self.process_video_thread, args=(url, api_key))
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Update UI
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar.start()
        
    def process_video_thread(self, url: str, api_key: str):
        """Process video in background thread."""
        try:
            self.update_status("Processing video...")
            
            # Create processor
            self.processor = YouTubeProcessor(self.log_progress)
            
            # Create options
            options = ProcessingOptions(
                language=self.language_var.get() if self.language_var.get() != "Auto-detect" else None,
                api_key=api_key,
                model=self.model_var.get(),
                keep_files=self.keep_files_var.get(),
                output_dir=self.output_dir_var.get() if self.output_dir_var.get() else None,
                show_subtitles=self.show_subtitles_var.get(),
                quiet=self.quiet_var.get()
            )
            
            # Process video
            subtitle_info, gemini_response = self.processor.process_video(url, options)
            
            # Update UI with results
            self.root.after(0, self.show_results, subtitle_info, gemini_response)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Error processing video: {e}")
        finally:
            self.root.after(0, self.processing_finished)
            
    def processing_finished(self):
        """Called when processing is finished."""
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.update_status("Ready")
        
    def stop_processing(self):
        """Stop the current processing."""
        if self.processing_thread and self.processing_thread.is_alive():
            # Note: This is a graceful stop - we can't forcefully kill threads
            if self.processor:
                self.processor.cleanup()
            self.update_status("Stopping...")
            
    def log_progress(self, message: str):
        """Log progress message."""
        self.root.after(0, self.append_progress, message)
        
    def append_progress(self, message: str):
        """Append message to progress text."""
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        
    def show_results(self, subtitle_info, gemini_response):
        """Show processing results."""
        # Show subtitles
        if subtitle_info:
            self.subtitles_text.insert(tk.END, subtitle_info.content)
            self.notebook.select(1)  # Switch to subtitles tab
            
        # Show chapters
        if gemini_response:
            self.chapters_text.insert(tk.END, gemini_response)
            self.notebook.select(2)  # Switch to chapters tab
            
        self.update_status("Processing completed successfully!")
        
    def show_error(self, error_message: str):
        """Show error message."""
        messagebox.showerror("Error", error_message)
        self.log_progress(f"ERROR: {error_message}")
        
    def clear_results(self):
        """Clear all result text areas."""
        self.progress_text.delete(1.0, tk.END)
        self.subtitles_text.delete(1.0, tk.END)
        self.chapters_text.delete(1.0, tk.END)
        
    def clear_all(self):
        """Clear all fields and results."""
        self.clear_results()
        self.url_var.set("")
        self.language_var.set("Auto-detect")
        self.output_dir_var.set("")
        
    def save_subtitles(self):
        """Save subtitles to file."""
        content = self.subtitles_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "No subtitles to save.")
            return
            
        self.save_content(content, "subtitles", "Save Subtitles")
        
    def save_chapters(self):
        """Save chapters to file."""
        content = self.chapters_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "No chapters to save.")
            return
            
        self.save_content(content, "chapters", "Save Chapters")
        
    def save_content(self, content: str, default_name: str, title: str):
        """Save content to file."""
        filename = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialname=f"{default_name}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Content saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")
                
    def update_status(self, message: str):
        """Update status message."""
        self.status_var.set(message)
        
    def on_closing(self):
        """Handle window closing."""
        # Save window geometry
        config.set_window_geometry(self.root.geometry())
        
        # Stop any processing
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_processing()
            
        # Cleanup
        if self.processor:
            self.processor.cleanup()
            
        self.root.destroy()
        
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()

def main():
    """Main function for GUI application."""
    try:
        app = YouTubeChaptersGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 