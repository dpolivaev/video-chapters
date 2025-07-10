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
GUI for Video Subtitles to Chapter Timecodes
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
import re

from core import VideoProcessor, ProcessingOptions, AVAILABLE_MODELS
from config import config

# Windows DPI awareness
if sys.platform == "win32":
    try:
        import ctypes
        # Make the application DPI aware
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (ImportError, AttributeError, OSError):
        try:
            # Fallback for older Windows versions
            ctypes.windll.user32.SetProcessDPIAware()
        except (ImportError, AttributeError, OSError):
            pass

class ChapterTimecodeGUI:
    """Main GUI application for Chapter Timecodes."""
    
    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("Chapter Timecodes - Video Subtitle to Chapter Converter")
        
        # Configure for better DPI handling
        self.setup_dpi_scaling()
        
        # Set window size and constraints
        self.root.geometry(config.get_window_geometry())
        self.root.minsize(900, 700)
        
        # Configure style
        self.setup_style()
        
        # Setup variables
        self.setup_variables()
        
        # macOS-specific setup
        if sys.platform == "darwin":
            self.setup_macos_integration()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main widgets
        self.create_widgets()
        
        # Setup bindings
        self.setup_bindings()
        
        # Load saved settings
        self.load_settings()
        
    def setup_dpi_scaling(self):
        """Configure DPI scaling for better appearance on high-DPI displays."""
        if sys.platform == "win32":
            # Windows DPI scaling
            try:
                import ctypes
                user32 = ctypes.windll.user32
                dpi = user32.GetDpiForSystem()
                scaling_factor = dpi / 96.0  # 96 DPI is standard
                
                # Configure tkinter scaling
                self.root.tk.call('tk', 'scaling', scaling_factor)
                
                # Set font scaling
                self.font_scale = max(1.0, scaling_factor * 0.9)  # Slightly smaller than full scale
                
            except (ImportError, AttributeError, OSError):
                self.font_scale = 1.0
        elif sys.platform == "darwin":
            # macOS handles DPI automatically, but we can detect retina displays
            try:
                # Check if we're on a retina display
                import tkinter as tk
                scaling = self.root.tk.call('tk', 'scaling')
                if scaling > 1.4:  # Likely a retina display
                    self.font_scale = 1.1  # Slightly larger fonts for retina
                else:
                    self.font_scale = 1.0
            except:
                self.font_scale = 1.0
        else:
            # Linux and other platforms
            self.font_scale = 1.0
        
    def setup_style(self):
        """Setup the GUI style."""
        style = ttk.Style()
        
        # Calculate scaled font sizes
        title_size = int(16 * self.font_scale)
        section_size = int(12 * self.font_scale)
        info_size = int(9 * self.font_scale)
        default_size = int(10 * self.font_scale)
        
        # Platform-specific font choices
        if sys.platform == "win32":
            ui_font = "Segoe UI"
            mono_font = "Consolas"
        elif sys.platform == "darwin":
            ui_font = "SF Pro Text"
            mono_font = "SF Mono"
            # Fallback fonts for older macOS
            try:
                import tkinter.font as tkFont
                available_fonts = tkFont.families()
                if "SF Pro Text" not in available_fonts:
                    ui_font = "Helvetica Neue"
                if "SF Mono" not in available_fonts:
                    mono_font = "Monaco"
            except:
                ui_font = "Helvetica Neue"
                mono_font = "Monaco"
        else:
            # Linux and other platforms
            ui_font = "Liberation Sans"
            mono_font = "Liberation Mono"
            # Fallback fonts
            try:
                import tkinter.font as tkFont
                available_fonts = tkFont.families()
                if "Liberation Sans" not in available_fonts:
                    ui_font = "DejaVu Sans"
                if "Liberation Mono" not in available_fonts:
                    mono_font = "DejaVu Sans Mono"
            except:
                ui_font = "DejaVu Sans"
                mono_font = "DejaVu Sans Mono"
        
        # Store fonts for later use
        self.ui_font = ui_font
        self.mono_font = mono_font
        
        # Configure styles for better appearance with DPI scaling
        style.configure('Title.TLabel', font=(ui_font, title_size, 'bold'))
        style.configure('Section.TLabel', font=(ui_font, section_size, 'bold'))
        style.configure('Info.TLabel', font=(ui_font, info_size), foreground='gray')
        
        # Configure notebook style with scaled padding
        padding = [int(20 * self.font_scale), int(10 * self.font_scale)]
        style.configure('Custom.TNotebook', tabposition='n')
        style.configure('Custom.TNotebook.Tab', padding=padding)
        
        # Configure default font for all widgets
        default_font = (ui_font, default_size)
        self.root.option_add('*Font', default_font)
        
    def setup_variables(self):
        """Setup GUI variables."""
        self.url_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.language_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.keep_files_var = tk.BooleanVar()
        self.output_dir_var = tk.StringVar()
        self.progress_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        
        self.processor = None
        self.processing_thread = None
        self.available_languages = {}
        
    def setup_macos_integration(self):
        """Setup macOS-specific menu integration."""
        try:
            # Register About command for macOS application menu
            self.root.createcommand('tkAboutDialog', self.show_about)
            
            # Set up the application to use the system menu bar
            self.root.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.root._w, 'document')
        except Exception as e:
            # If macOS integration fails, just continue without it
            print(f"macOS integration failed: {e}")
        
    def create_menu_bar(self):
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Create Help menu (on macOS, About will also appear in app menu via createcommand)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_widgets(self):
        """Create main GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text=config.get_app_title(), 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL input
        ttk.Label(main_frame, text="YouTube video URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # Check languages button
        self.check_langs_btn = ttk.Button(main_frame, text="Check Languages", 
                                         command=self.check_languages)
        self.check_langs_btn.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # API Key input
        ttk.Label(main_frame, text="Gemini API Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # API Key buttons
        api_key_frame = ttk.Frame(main_frame)
        api_key_frame.grid(row=2, column=2, pady=5, padx=(5, 0))
        
        ttk.Button(api_key_frame, text="Delete API Key", 
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
        
        # Configure text widget with scaled font
        text_font = (self.mono_font, int(10 * self.font_scale))
        self.progress_text = scrolledtext.ScrolledText(self.progress_frame, height=15, width=80, font=text_font)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Subtitles tab
        self.subtitles_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.subtitles_frame, text="Subtitles")
        
        # Chapters tab
        self.chapters_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chapters_frame, text="Chapters")
        
        # Create text widgets for each tab
        self.create_progress_tab(self.progress_frame)
        self.create_subtitles_tab(self.subtitles_frame)
        self.create_chapters_tab(self.chapters_frame)
        
        # Configure text widgets for scrolling
        self.setup_scrolling_widgets()
        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=8, column=0, columnspan=3, pady=(10, 0))
        
        self.process_btn = ttk.Button(control_frame, text="Process Video", 
                                     command=self.process_video)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Copy and Save buttons
        self.copy_btn = ttk.Button(control_frame, text="Copy to Clipboard", 
                                  command=self.copy_current_tab)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_btn = ttk.Button(control_frame, text="Save to File", 
                                  command=self.save_current_tab)
        self.save_btn.pack(side=tk.LEFT)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     style='Info.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
    def create_progress_tab(self, parent_frame):
        """Create and configure the progress tab."""

        self.progress_text.configure(selectbackground='#0078d4', selectforeground='white')
        self.progress_text.bind('<Key>', self._on_text_key)
        self.progress_text.bind('<Control-Key>', self._on_text_key)
        self.progress_text.bind('<Button-2>', self._on_text_paste)
        self.progress_text.bind('<Button-3>', self._on_text_paste)
        self.progress_text.bind('<MouseWheel>', self._on_mousewheel)
        self.progress_text.bind('<Button-4>', self._on_mousewheel)
        self.progress_text.bind('<Button-5>', self._on_mousewheel)
        
    def create_subtitles_tab(self, parent_frame):
        """Create and configure the subtitles tab."""
        text_font = (self.mono_font, int(10 * self.font_scale))
        self.subtitles_text = scrolledtext.ScrolledText(parent_frame, height=12, width=80,
                                                        wrap=tk.WORD, state=tk.NORMAL, font=text_font)
        self.subtitles_text.pack(fill=tk.BOTH, expand=True)
        self.subtitles_text.configure(selectbackground='#0078d4', selectforeground='white')
        self.subtitles_text.bind('<Key>', self._on_text_key)
        self.subtitles_text.bind('<Control-Key>', self._on_text_key)
        self.subtitles_text.bind('<Button-2>', self._on_text_paste)
        self.subtitles_text.bind('<Button-3>', self._on_text_paste)
        self.subtitles_text.bind('<MouseWheel>', self._on_mousewheel)
        self.subtitles_text.bind('<Button-4>', self._on_mousewheel)
        self.subtitles_text.bind('<Button-5>', self._on_mousewheel)
        
        self.subtitles_text.bind('<B1-Motion>', self._on_drag_motion)
        self.subtitles_text.bind('<ButtonRelease-1>', self._on_drag_end)
        
    def create_chapters_tab(self, parent_frame):
        """Create and configure the chapters tab."""
        text_font = (self.mono_font, int(10 * self.font_scale))
        self.chapters_text = scrolledtext.ScrolledText(parent_frame, height=12, width=80,
                                                       wrap=tk.WORD, state=tk.NORMAL, font=text_font)
        self.chapters_text.pack(fill=tk.BOTH, expand=True)
        self.chapters_text.configure(selectbackground='#0078d4', selectforeground='white')
        self.chapters_text.bind('<Key>', self._on_text_key)
        self.chapters_text.bind('<Control-Key>', self._on_text_key)
        self.chapters_text.bind('<Button-2>', self._on_text_paste)
        self.chapters_text.bind('<Button-3>', self._on_text_paste)
        self.chapters_text.bind('<MouseWheel>', self._on_mousewheel)
        self.chapters_text.bind('<Button-4>', self._on_mousewheel)
        self.chapters_text.bind('<Button-5>', self._on_mousewheel)
        
        self.chapters_text.bind('<B1-Motion>', self._on_drag_motion)
        self.chapters_text.bind('<ButtonRelease-1>', self._on_drag_end)
        
    def setup_scrolling_widgets(self):
        """Configure text widgets for auto-scrolling."""
        self.subtitles_text.bind('<B1-Motion>', self._on_drag_motion)
        self.chapters_text.bind('<B1-Motion>', self._on_drag_motion)
        
        self.subtitles_text.bind('<ButtonRelease-1>', self._on_drag_end)
        self.chapters_text.bind('<ButtonRelease-1>', self._on_drag_end)
        
    def setup_bindings(self):
        """Setup event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.url_var.trace_add("write", self.save_settings)
        self.model_var.trace_add("write", self.save_settings)
        self.language_var.trace_add("write", self.save_settings)
        self.keep_files_var.trace_add("write", self.save_settings)
        self.output_dir_var.trace_add("write", self.save_settings)
        
        self.api_key_var.trace_add("write", self.save_api_key_auto)
        
    def load_settings(self):
        """Load settings from config."""
        self.url_var.set(config.get_last_url())
        self.model_var.set(config.get_model())
        self.language_var.set(config.get_language() or "Auto-detect")
        self.keep_files_var.set(config.get_keep_files())
        
        self.output_dir_var.set(config.get_output_dir())
        
        api_key = config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)
        
    def save_settings(self, *args):
        """Save settings to config."""
        config.set_last_url(self.url_var.get())
        config.set_model(self.model_var.get())
        config.set_language(self.language_var.get() if self.language_var.get() != "Auto-detect" else "")
        config.set_keep_files(self.keep_files_var.get())
        
        config.set_output_dir(self.output_dir_var.get())
        
    def save_api_key_auto(self, *args):
        """Auto-save API key to secure storage."""
        api_key = self.api_key_var.get().strip()
        if api_key:
            config.set_api_key(api_key)
            
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
            messagebox.showwarning("Warning", "Please enter a YouTube video URL.")
            return
            
        def check_langs_thread():
            try:
                self.update_status("Checking available languages...")
                self.check_langs_btn.config(state=tk.DISABLED)
                
                processor = VideoProcessor(self.log_progress)
                langs = processor.get_available_languages(url)
                
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
            messagebox.showwarning("Warning", "Please enter a YouTube video URL.")
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
            self.processor = VideoProcessor(self.log_progress)
            
            # Create options
            options = ProcessingOptions(
                language=self.language_var.get() if self.language_var.get() != "Auto-detect" else None,
                api_key=api_key,
                model=self.model_var.get(),
                keep_files=self.keep_files_var.get(),
                output_dir=self.output_dir_var.get() if self.output_dir_var.get() else None,
                show_subtitles=False
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
            self.subtitles_text.delete(1.0, tk.END)
            self.subtitles_text.insert(tk.END, subtitle_info.content)
            self.notebook.select(1)  # Switch to subtitles tab
            
        # Show chapters
        if gemini_response:
            self.chapters_text.delete(1.0, tk.END)
            self.chapters_text.insert(tk.END, gemini_response)
            self.notebook.select(2)  # Switch to chapters tab
            
        self.update_status("Processing completed successfully!")
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for text widgets."""
        # Determine scroll direction and amount
        if event.delta:
            # Windows/Mac
            delta = -1 * (event.delta / 120)
        else:
            # Linux
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = 0
        
        # Scroll the text widget
        event.widget.yview_scroll(int(delta), "units")
        return "break"
        
    def _on_text_key(self, event):
        """Handle key events for read-only text widgets (allow selection, prevent editing)."""
        # Allow selection keys
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next',
                           'Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R'):
            return
        
        # Allow copy operations
        if event.state & 0x4:  # Control key pressed
            if event.keysym in ('c', 'C', 'a', 'A'):  # Ctrl+C (copy) or Ctrl+A (select all)
                return
        
        # Block all other keys
        return "break"
        
    def _on_text_paste(self, event):
        """Block paste operations in read-only text widgets."""
        return "break"
        
    def _on_drag_motion(self, event):
        """Handle drag motion for auto-scrolling during text selection."""
        widget = event.widget
        
        # Get widget dimensions
        widget_height = widget.winfo_height()
        
        # Get mouse position relative to widget
        mouse_y = event.y
        
        # Define scroll zones (top and bottom 20 pixels)
        scroll_zone = 20
        
        # Auto-scroll when dragging near edges
        if mouse_y < scroll_zone:
            # Scroll up
            widget.yview_scroll(-1, "units")
        elif mouse_y > widget_height - scroll_zone:
            # Scroll down
            widget.yview_scroll(1, "units")
        
        # Schedule the next auto-scroll if still dragging
        if hasattr(self, '_auto_scroll_after_id'):
            self.root.after_cancel(self._auto_scroll_after_id)
        
        # Continue auto-scrolling while in scroll zone
        if mouse_y < scroll_zone or mouse_y > widget_height - scroll_zone:
            self._auto_scroll_after_id = self.root.after(50, lambda: self._continue_auto_scroll(widget, mouse_y, widget_height))
        
        return None  # Don't break the event chain
        
    def _continue_auto_scroll(self, widget, mouse_y, widget_height):
        """Continue auto-scrolling during drag selection."""
        scroll_zone = 20
        
        if mouse_y < scroll_zone:
            widget.yview_scroll(-1, "units")
        elif mouse_y > widget_height - scroll_zone:
            widget.yview_scroll(1, "units")
        
    def _on_drag_end(self, event):
        """Stop auto-scrolling when the mouse button is released."""
        if hasattr(self, '_auto_scroll_after_id'):
            self.root.after_cancel(self._auto_scroll_after_id)
        
    def show_error(self, error_message: str):
        """Show error message."""
        messagebox.showerror("Error", error_message)
        self.log_progress(f"ERROR: {error_message}")
        
    def clear_results(self):
        """Clear all result text areas."""
        self.progress_text.delete(1.0, tk.END)
        self.subtitles_text.delete(1.0, tk.END)
        self.chapters_text.delete(1.0, tk.END)
        
    def copy_current_tab(self):
        """Copy content from the currently selected tab to clipboard."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0: # Progress tab
            content = self.progress_text.get(1.0, tk.END).strip()
            tab_name = "Progress"
        elif selected_tab == 1: # Subtitles tab
            content = self.subtitles_text.get(1.0, tk.END).strip()
            tab_name = "Subtitles"
        elif selected_tab == 2: # Chapters tab
            content = self.chapters_text.get(1.0, tk.END).strip()
            tab_name = "Chapters"
        else:
            messagebox.showwarning("Warning", "No content to copy from this tab.")
            return
            
        if not content:
            messagebox.showwarning("Warning", f"No {tab_name} content to copy.")
            return
            
        self.copy_to_clipboard(content, tab_name)
        
    def save_current_tab(self):
        """Save content from the currently selected tab to a file."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0: # Progress tab
            content = self.progress_text.get(1.0, tk.END).strip()
            default_name = "progress"
            tab_name = "Progress"
        elif selected_tab == 1: # Subtitles tab
            content = self.subtitles_text.get(1.0, tk.END).strip()
            default_name = "subtitles"
            tab_name = "Subtitles"
        elif selected_tab == 2: # Chapters tab
            content = self.chapters_text.get(1.0, tk.END).strip()
            default_name = "chapters"
            tab_name = "Chapters"
        else:
            messagebox.showwarning("Warning", "No content to save from this tab.")
            return
            
        if not content:
            messagebox.showwarning("Warning", f"No {tab_name} content to save.")
            return
            
        self.save_content(content, default_name, f"Save {tab_name}")
        
    def copy_to_clipboard(self, content: str, content_type: str):
        """Copy content to system clipboard."""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()  # Make sure the clipboard is updated
            messagebox.showinfo("Success", f"{content_type} copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy to clipboard: {e}")
        
    def save_content(self, content: str, default_name: str, title: str):
        """Save content to file."""
        filename = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{default_name}.txt"
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

    def show_about(self):
        """Show the About dialog."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Chapter Timecode Generator")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        
        # Center the window
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(about_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # App info
        title_label = ttk.Label(main_frame, text=config.get_app_title(), 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 5))
        
        version_label = ttk.Label(main_frame, text=f"Version: {config.get_app_version()}")
        version_label.pack()
        
        copyright_label = ttk.Label(main_frame, text=config.get_app_copyright())
        copyright_label.pack(pady=(10, 0))
        
        license_label = ttk.Label(main_frame, text=f"License: {config.get_app_license()}")
        license_label.pack(pady=(5, 0))
        
        # Description
        desc_text = ("A tool for generating chapter timecodes from video subtitles "
                    "using Google's Gemini AI to create meaningful chapter markers.")
        desc_label = ttk.Label(main_frame, text=desc_text, wraplength=450, justify=tk.CENTER)
        desc_label.pack(pady=(15, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        # View License button
        license_btn = ttk.Button(button_frame, text="View License", 
                                command=lambda: self.show_license())
        license_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Close button
        close_btn = ttk.Button(button_frame, text="Close", 
                              command=about_window.destroy)
        close_btn.pack(side=tk.LEFT)
        
        # Center the window on parent
        about_window.update_idletasks()
        x = (self.root.winfo_x() + (self.root.winfo_width() // 2) - 
             (about_window.winfo_width() // 2))
        y = (self.root.winfo_y() + (self.root.winfo_height() // 2) - 
             (about_window.winfo_height() // 2))
        about_window.geometry(f"+{x}+{y}")
        
    def show_license(self):
        """Show the full license text."""
        license_window = tk.Toplevel(self.root)
        license_window.title("License - Apache License 2.0")
        license_window.geometry("700x500")
        
        # Center the window
        license_window.transient(self.root)
        license_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(license_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # License text
        license_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, 
                                                font=("Courier", 10))
        license_text.pack(fill=tk.BOTH, expand=True)
        
        # Try to read license file
        try:
            # Handle both development and packaged environments
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller packaged environment
                license_path = Path(sys._MEIPASS) / "LICENSE"
            else:
                # Development environment
                license_path = Path("LICENSE")
            
            if license_path.exists():
                with open(license_path, 'r', encoding='utf-8') as f:
                    license_content = f.read()
            else:
                license_content = """License file not found.

This software is licensed under the Apache License 2.0.
You can view the full license text at:
http://www.apache.org/licenses/LICENSE-2.0

Copyright 2025 Dimitry Polivaev"""
        except Exception as e:
            license_content = f"""Error reading license file: {e}

This software is licensed under the Apache License 2.0.
You can view the full license text at:
http://www.apache.org/licenses/LICENSE-2.0

Copyright 2025 Dimitry Polivaev"""
        
        license_text.insert(tk.END, license_content)
        license_text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = ttk.Button(main_frame, text="Close", 
                              command=license_window.destroy)
        close_btn.pack(pady=(10, 0))
        
        # Center the window on parent
        license_window.update_idletasks()
        x = (self.root.winfo_x() + (self.root.winfo_width() // 2) - 
             (license_window.winfo_width() // 2))
        y = (self.root.winfo_y() + (self.root.winfo_height() // 2) - 
             (license_window.winfo_height() // 2))
        license_window.geometry(f"+{x}+{y}")

def main():
    """Main function for GUI application."""
    try:
        app = ChapterTimecodeGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 