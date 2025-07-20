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
from instruction_history import InstructionHistoryDialog

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
        
        # Set window icon
        self.setup_icon()
        
        # Windows-specific taskbar icon setup
        if sys.platform == "win32":
            self.setup_windows_taskbar_icon()
        
        # Configure for better DPI handling
        self.setup_dpi_scaling()
        
        # Set window size and constraints
        self.root.geometry(config.get_window_geometry())
        self.root.minsize(900, 700)
        
        # Configure style
        self.setup_style()
        
        # Setup variables
        self.setup_variables()
        
        # Load saved settings before setting up bindings
        self.load_settings()
        
        # macOS-specific setup
        if sys.platform == "darwin":
            self.setup_macos_integration()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main widgets
        self.create_widgets()
        
        # Setup bindings (after loading settings)
        self.setup_bindings()
        
    def setup_icon(self):
        """Set up the application icon for different platforms."""
        try:
            # Handle both development and packaged environments
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller packaged environment
                base_path = Path(sys._MEIPASS)
            else:
                # Development environment
                base_path = Path(".")
            
            # Platform-specific icon handling
            if sys.platform == "win32":
                # Windows - use .ico file
                # In PyInstaller, the icon should already be embedded in the executable
                # But we can still try to set it for the window
                icon_path = base_path / "icon.ico"
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
                else:
                    # Try alternative locations
                    alt_paths = [
                        base_path / "assets" / "icon.ico",
                        base_path / "icons" / "icon.ico",
                        Path("icon.ico"),
                        Path("build/icon.ico")  # Add build directory path
                    ]
                    for alt_path in alt_paths:
                        if alt_path.exists():
                            self.root.iconbitmap(str(alt_path))
                            break
                    else:
                        # If no .ico file found, try using PNG as fallback
                        png_path = base_path / "icon.png"
                        if png_path.exists():
                            try:
                                icon_image = tk.PhotoImage(file=str(png_path))
                                self.root.iconphoto(True, icon_image)
                            except Exception as png_error:
                                print(f"Warning: Could not load PNG icon: {png_error}")
                        else:
                            # Try build directory for PNG
                            build_png = Path("build/icon.png")
                            if build_png.exists():
                                try:
                                    icon_image = tk.PhotoImage(file=str(build_png))
                                    self.root.iconphoto(True, icon_image)
                                except Exception as png_error:
                                    print(f"Warning: Could not load PNG icon from build: {png_error}")
                            
            elif sys.platform == "darwin":
                # macOS - use .icns file via iconphoto (iconbitmap doesn't work well on macOS)
                icon_path = base_path / "icon.icns"
                if icon_path.exists():
                    # For macOS, we need to convert to PhotoImage
                    # Note: tkinter doesn't directly support .icns, so we'll use .png as fallback
                    png_path = base_path / "icon.png"
                    if png_path.exists():
                        icon_image = tk.PhotoImage(file=str(png_path))
                        self.root.iconphoto(True, icon_image)
                else:
                    # Try PNG fallback
                    png_path = base_path / "icon.png"
                    if png_path.exists():
                        icon_image = tk.PhotoImage(file=str(png_path))
                        self.root.iconphoto(True, icon_image)
                        
            else:
                # Linux and other platforms - use .png file
                icon_path = base_path / "icon.png"
                if icon_path.exists():
                    icon_image = tk.PhotoImage(file=str(icon_path))
                    self.root.iconphoto(True, icon_image)
                else:
                    # Try alternative locations
                    alt_paths = [
                        base_path / "assets" / "icon.png",
                        base_path / "icons" / "icon.png",
                        Path("icon.png")
                    ]
                    for alt_path in alt_paths:
                        if alt_path.exists():
                            icon_image = tk.PhotoImage(file=str(alt_path))
                            self.root.iconphoto(True, icon_image)
                            break
                            
        except Exception as e:
            # If icon loading fails, just continue without icon
            print(f"Warning: Could not load application icon: {e}")
        
    def setup_windows_taskbar_icon(self):
        """Set up Windows taskbar icon using Windows API."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get the window handle
            hwnd = self.root.winfo_id()
            
            # Load the icon from the executable (should be embedded by PyInstaller)
            # Try to load from the current executable first
            try:
                # Get the executable path
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller environment - icon should be embedded
                    exe_path = sys.executable
                else:
                    # Development environment
                    exe_path = sys.executable
                
                # Load the icon from the executable
                icon_handle = ctypes.windll.shell32.ExtractIconW(
                    ctypes.windll.kernel32.GetModuleHandleW(None),
                    exe_path,
                    0
                )
                
                if icon_handle:
                    # Set the window icon
                    ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, icon_handle)  # WM_SETICON, ICON_SMALL
                    ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, icon_handle)  # WM_SETICON, ICON_BIG
                    
            except Exception as exe_error:
                print(f"Warning: Could not load icon from executable: {exe_error}")
                
                # Fallback: try to load from icon file
                try:
                    if hasattr(sys, '_MEIPASS'):
                        base_path = Path(sys._MEIPASS)
                    else:
                        base_path = Path(".")
                    
                    icon_path = base_path / "icon.ico"
                    if not icon_path.exists():
                        icon_path = Path("build/icon.ico")
                    
                    if icon_path.exists():
                        # Load icon from file
                        icon_handle = ctypes.windll.shell32.ExtractIconW(
                            ctypes.windll.kernel32.GetModuleHandleW(None),
                            str(icon_path),
                            0
                        )
                        
                        if icon_handle:
                            # Set the window icon
                            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, icon_handle)  # WM_SETICON, ICON_SMALL
                            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, icon_handle)  # WM_SETICON, ICON_BIG
                            
                except Exception as file_error:
                    print(f"Warning: Could not load icon from file: {file_error}")
                    
        except Exception as e:
            print(f"Warning: Could not set Windows taskbar icon: {e}")
        
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
        
        # Configure notebook style with reduced padding scaling
        # Use a smaller scaling factor for padding to avoid excessive gaps
        padding_scale = min(self.font_scale, 1.1)  # Cap padding scaling at 1.1
        padding = [int(20 * padding_scale), int(10 * padding_scale)]
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
        
        # Store initial API key value to avoid keyring access on exit
        self.initial_api_key = None
        
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

        # Create Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Platform-specific accelerator text
        if sys.platform == "darwin":
            cut_accel = "Cmd+X"
            copy_accel = "Cmd+C"
            paste_accel = "Cmd+V"
            select_all_accel = "Cmd+A"
        else:
            cut_accel = "Ctrl+X"
            copy_accel = "Ctrl+C"
            paste_accel = "Ctrl+V"
            select_all_accel = "Ctrl+A"
        
        edit_menu.add_command(label="Cut", command=self.menu_cut, accelerator=cut_accel)
        edit_menu.add_command(label="Copy", command=self.menu_copy, accelerator=copy_accel)
        edit_menu.add_command(label="Paste", command=self.menu_paste, accelerator=paste_accel)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.menu_select_all, accelerator=select_all_accel)

        # Create Help menu (on macOS, About will also appear in app menu via createcommand)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_widgets(self):
        """Create main GUI widgets."""
        # Main container - reduced padding for more compact layout
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text=config.get_app_title(), 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # URL input
        ttk.Label(main_frame, text="YouTube video URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Check languages button
        self.check_langs_btn = ttk.Button(main_frame, text="Check Languages", 
                                         command=self.check_languages, width=15)
        self.check_langs_btn.grid(row=1, column=2, pady=2, padx=(5, 0))
        
        # API Key input
        ttk.Label(main_frame, text="Gemini API Key:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # API Key buttons
        api_key_frame = ttk.Frame(main_frame)
        api_key_frame.grid(row=2, column=2, pady=2, padx=(5, 0))
        
        ttk.Button(api_key_frame, text="Delete API Key", 
                   command=self.clear_api_key, width=15).pack(side=tk.LEFT)
        
        # Language selection
        ttk.Label(main_frame, text="Language:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.language_combo = ttk.Combobox(main_frame, textvariable=self.language_var, 
                                          values=["Auto-detect"], state="readonly")
        self.language_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Model selection
        ttk.Label(main_frame, text="Model:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, 
                                       values=AVAILABLE_MODELS, state="readonly")
        self.model_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Options frame
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        options_frame.columnconfigure(2, weight=1)  # Make column 2 (entry field) expand
        
        # Keep files in a separate frame to not affect main alignment
        keep_files_frame = ttk.Frame(options_frame)
        keep_files_frame.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Label(keep_files_frame, text="Keep files").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Checkbutton(keep_files_frame, variable=self.keep_files_var).pack(side=tk.LEFT)
        
        # Output directory aligned with main form fields
        ttk.Label(options_frame, text="Output Dir:").grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.output_dir_entry = ttk.Entry(options_frame, textvariable=self.output_dir_var, width=35)
        self.output_dir_entry.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(options_frame, text="Browse", 
                  command=self.browse_output_dir, width=15).grid(row=0, column=3, padx=(0, 0))
        
        # Create notebook for results
        self.notebook = ttk.Notebook(main_frame, style='Custom.TNotebook')
        self.notebook.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Bind tab selection to focus the appropriate text widget
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # Your Instructions tab
        self.instructions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.instructions_frame, text="Your Instructions")
        
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
        self.create_instructions_tab(self.instructions_frame)
        self.create_progress_tab(self.progress_frame)
        self.create_subtitles_tab(self.subtitles_frame)
        self.create_chapters_tab(self.chapters_frame)
        
        # Configure text widgets for scrolling
        self.setup_scrolling_widgets()
        

        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=8, column=0, columnspan=3, pady=(5, 0))
        
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

        self.progress_text.configure(selectbackground='#0078d4', selectforeground='white', state=tk.DISABLED)
        self.progress_text.bind('<Button-2>', self._on_text_paste)
        self.progress_text.bind('<Button-3>', self._on_text_paste)
        self.progress_text.bind('<MouseWheel>', self._on_mousewheel)
        self.progress_text.bind('<Button-4>', self._on_mousewheel)
        self.progress_text.bind('<Button-5>', self._on_mousewheel)
        
    def create_instructions_tab(self, parent_frame):
        """Create and configure the instructions tab."""
        # Add tip label above the text widget
        self.instructions_tip_label = ttk.Label(parent_frame, text="You can enter custom instructions here...", 
                                               foreground="gray", font=("TkDefaultFont", 9))
        self.instructions_tip_label.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        text_font = (self.mono_font, int(10 * self.font_scale))
        self.instructions_text = scrolledtext.ScrolledText(parent_frame, height=12, width=80,
                                                          wrap=tk.WORD, state=tk.NORMAL, font=text_font)
        self.instructions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.instructions_text.configure(selectbackground='#0078d4', selectforeground='white')
        
        # Bind the text widget to handle tip visibility
        self.instructions_text.bind('<KeyRelease>', self._on_instructions_change)
        
        # Load saved instructions
        custom_instructions = config.get_setting("custom_instructions", "")
        if custom_instructions:
            self.instructions_text.insert(tk.END, custom_instructions)
            self.instructions_tip_label.pack_forget()  # Hide tip if there's content
        
        # Initialize instruction history dialog
        self.history_dialog = InstructionHistoryDialog(self, self.instructions_text, self.instructions_tip_label)
        
        # Add Previous Instructions button
        instructions_header_frame = ttk.Frame(parent_frame)
        instructions_header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        ttk.Button(instructions_header_frame, text="Previous Instructions", 
                   command=self.history_dialog.show_dialog).pack(side=tk.RIGHT)
            
    def _on_instructions_change(self, event=None):
        """Handle changes to the instructions text widget."""
        content = self.instructions_text.get(1.0, tk.END).strip()
        
        # Show/hide tip label based on content
        if content:
            self.instructions_tip_label.pack_forget()  # Hide tip when there's content
        else:
            self.instructions_tip_label.pack(anchor=tk.W, padx=5, pady=(5, 0))  # Show tip when empty
            
    def create_subtitles_tab(self, parent_frame):
        """Create and configure the subtitles tab."""
        text_font = (self.mono_font, int(10 * self.font_scale))
        self.subtitles_text = scrolledtext.ScrolledText(parent_frame, height=12, width=80,
                                                        wrap=tk.WORD, state=tk.DISABLED, font=text_font)
        self.subtitles_text.pack(fill=tk.BOTH, expand=True)
        self.subtitles_text.configure(selectbackground='#0078d4', selectforeground='white')
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
                                                       wrap=tk.WORD, state=tk.DISABLED, font=text_font)
        self.chapters_text.pack(fill=tk.BOTH, expand=True)
        self.chapters_text.configure(selectbackground='#0078d4', selectforeground='white')
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
        
    def load_settings(self):
        """Load saved settings."""
        self.url_var.set(config.get_last_url())
        self.model_var.set(config.get_model())
        self.language_var.set(config.get_language() if config.get_language() else "Auto-detect")
        self.keep_files_var.set(config.get_keep_files())
        self.output_dir_var.set(config.get_output_dir())
        
        # Load API key
        api_key = config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)
            self.initial_api_key = api_key
        else:
            # Ensure initial_api_key is set even when no key is loaded
            self.initial_api_key = ""
        
    def save_settings(self, *args):
        """Save current settings."""
        config.set_last_url(self.url_var.get())
        config.set_model(self.model_var.get())
        config.set_language(self.language_var.get() if self.language_var.get() != "Auto-detect" else "")
        config.set_keep_files(self.keep_files_var.get())
        config.set_output_dir(self.output_dir_var.get())
        
        # Get custom instructions directly from the widget
        custom_instructions = self.instructions_text.get(1.0, tk.END).strip()
        config.set_setting("custom_instructions", custom_instructions)
        
        # Save API key if changed
        current_api_key = self.api_key_var.get()
        if current_api_key != self.initial_api_key:
            config.set_api_key(current_api_key)
            self.initial_api_key = current_api_key
        
    def clear_api_key(self):
        """Clear API key from secure storage."""
        success = config.clear_api_key()
        self.api_key_var.set("")
        if success:
            messagebox.showinfo("Success", "API key cleared!")
        else:
            messagebox.showerror("Error", "Failed to clear API key from keychain. The field has been cleared, but the key may still exist in your keychain.")
        
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
        
        # Switch to progress tab to show processing status
        self.notebook.select(1)  # Progress tab is at index 1
        
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
            self.stopping = False
            
            # Create processor
            self.processor = VideoProcessor(self.log_progress)
            
            # Get current instructions
            custom_instructions = self.instructions_text.get(1.0, tk.END).strip()
            
            # Save instructions to history if they exist
            if custom_instructions:
                config.add_instruction_to_history(custom_instructions)
            
            # Create options
            options = ProcessingOptions(
                language=self.language_var.get() if self.language_var.get() != "Auto-detect" else None,
                api_key=api_key,
                model=self.model_var.get(),
                keep_files=self.keep_files_var.get(),
                output_dir=self.output_dir_var.get() if self.output_dir_var.get() else None,
                show_subtitles=False,
                custom_instructions=custom_instructions
            )
            
            # Check if stopping was requested
            if self.stopping:
                return
            
            # Download subtitles first
            subtitle_info = self.processor.download_subtitles(
                url, 
                options.language, 
                options.output_dir
            )
            
            # Check if stopping was requested
            if self.stopping:
                return
            
            # Show subtitles immediately after download
            if subtitle_info:
                self.root.after(0, self.show_subtitles, subtitle_info)
            
            # Process with Gemini if API key provided
            gemini_response = None
            if options.api_key:
                # Mark that Gemini processing has started
                self.gemini_started = True
                
                # Disable stop button - can't abort API calls
                self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
                
                gemini_response = self.processor.process_with_gemini(
                    subtitle_info.content,
                    options.api_key,
                    options.model,
                    options.custom_instructions
                )
                
                # Show chapters when generated
                if gemini_response:
                    self.root.after(0, self.show_chapters, gemini_response)
            
            # Update UI with final results
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
        
        # Clean up temporary files only if processing completed (not stopped)
        if hasattr(self, 'processor') and self.processor and not self.stopping:
            self.processor.cleanup()
        
        self.update_status("Ready")
        
        # Reset processing flags
        self.stopping = False
        self.gemini_started = False
        
    def stop_processing(self):
        """Stop the current processing."""
        if self.processing_thread and self.processing_thread.is_alive():
            # Check if we can actually stop (before Gemini processing starts)
            if hasattr(self, 'gemini_started') and self.gemini_started:
                messagebox.showinfo("Info", "Cannot stop processing after Gemini API request has been sent. The operation will complete.")
                return
            
            # Mark that we're stopping to prevent further operations
            self.stopping = True
            self.update_status("Stopping...")
        
    def log_progress(self, message: str):
        """Log progress message."""
        self.root.after(0, self.append_progress, message)
        
    def append_progress(self, message: str):
        """Append message to progress text."""
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state=tk.DISABLED)
        
    def show_subtitles(self, subtitle_info):
        """Show subtitles and switch to subtitles tab."""
        self.subtitles_text.config(state=tk.NORMAL)
        self.subtitles_text.delete(1.0, tk.END)
        self.subtitles_text.insert(tk.END, subtitle_info.content)
        self.subtitles_text.config(state=tk.DISABLED)
        self.notebook.select(2)  # Switch to subtitles tab (index 2)
        
    def show_chapters(self, gemini_response):
        """Show chapters and switch to chapters tab."""
        self.chapters_text.config(state=tk.NORMAL)
        self.chapters_text.delete(1.0, tk.END)
        self.chapters_text.insert(tk.END, gemini_response)
        self.chapters_text.config(state=tk.DISABLED)
        self.notebook.select(3)  # Switch to chapters tab (index 3)
        
    def show_results(self, subtitle_info, gemini_response):
        """Show processing results."""
        # Show subtitles
        if subtitle_info:
            self.subtitles_text.config(state=tk.NORMAL)
            self.subtitles_text.delete(1.0, tk.END)
            self.subtitles_text.insert(tk.END, subtitle_info.content)
            self.subtitles_text.config(state=tk.DISABLED)
            
        # Show chapters
        if gemini_response:
            self.chapters_text.config(state=tk.NORMAL)
            self.chapters_text.delete(1.0, tk.END)
            self.chapters_text.insert(tk.END, gemini_response)
            self.chapters_text.config(state=tk.DISABLED)
            
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
        

        
    def _on_text_paste(self, event):
        """Block paste operations in read-only text widgets."""
        return "break"
        
    def _on_tab_changed(self, event):
        """Focus the appropriate text widget when tab changes."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0:  # Instructions tab
            self.instructions_text.focus_set()
        elif selected_tab == 1:  # Progress tab
            self.progress_text.focus_set()
        elif selected_tab == 2:  # Subtitles tab
            self.subtitles_text.focus_set()
        elif selected_tab == 3:  # Chapters tab
            self.chapters_text.focus_set()
        
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
        self.progress_text.config(state=tk.NORMAL)
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.config(state=tk.DISABLED)
        
        self.subtitles_text.config(state=tk.NORMAL)
        self.subtitles_text.delete(1.0, tk.END)
        self.subtitles_text.config(state=tk.DISABLED)
        
        self.chapters_text.config(state=tk.NORMAL)
        self.chapters_text.delete(1.0, tk.END)
        self.chapters_text.config(state=tk.DISABLED)
        
    def copy_current_tab(self):
        """Copy content from the currently selected tab to clipboard."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0: # Instructions tab
            content = self.instructions_text.get(1.0, tk.END).strip()
            tab_name = "Instructions"
        elif selected_tab == 1: # Progress tab
            content = self.progress_text.get(1.0, tk.END).strip()
            tab_name = "Progress"
        elif selected_tab == 2: # Subtitles tab
            content = self.subtitles_text.get(1.0, tk.END).strip()
            tab_name = "Subtitles"
        elif selected_tab == 3: # Chapters tab
            content = self.chapters_text.get(1.0, tk.END).strip()
            tab_name = "Chapters"
        else:
            return
        
        if content:
            self.copy_to_clipboard(content, tab_name)
        else:
            messagebox.showinfo("Info", f"No content to copy from {tab_name} tab.")
        
    def save_current_tab(self):
        """Save content from the currently selected tab to file."""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0: # Instructions tab
            content = self.instructions_text.get(1.0, tk.END).strip()
            tab_name = "Instructions"
            default_name = "instructions"
        elif selected_tab == 1: # Progress tab
            content = self.progress_text.get(1.0, tk.END).strip()
            tab_name = "Progress"
            default_name = "progress"
        elif selected_tab == 2: # Subtitles tab
            content = self.subtitles_text.get(1.0, tk.END).strip()
            tab_name = "Subtitles"
            default_name = "subtitles"
        elif selected_tab == 3: # Chapters tab
            content = self.chapters_text.get(1.0, tk.END).strip()
            tab_name = "Chapters"
            default_name = "chapters"
        else:
            return
        
        if content:
            self.save_content(content, default_name, f"Save {tab_name}")
        else:
            messagebox.showinfo("Info", f"No content to save from {tab_name} tab.")
        
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
        """Handle application closing."""
        # Save window geometry
        geometry = self.root.geometry()
        config.set_window_geometry(geometry)
        
        # Save all settings
        self.save_settings()
        
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



    def menu_copy(self):
        """Handle Copy from Edit menu."""
        focused_widget = self.root.focus_get()
        
        if focused_widget == self.url_entry:
            self.copy_entry_field(self.url_entry)
        elif focused_widget == self.api_key_entry:
            # Don't allow copying from API key field
            messagebox.showwarning("Security", "Cannot copy from API key field for security reasons.")
        elif focused_widget == self.output_dir_entry:
            self.copy_entry_field(self.output_dir_entry)
        elif focused_widget in [self.progress_text, self.subtitles_text, self.chapters_text]:
            self.copy_text_selection()
        else:
            # Try to copy from currently active text widget
            self.copy_current_tab()

    def menu_paste(self):
        """Handle Paste from Edit menu."""
        focused_widget = self.root.focus_get()
        
        if focused_widget == self.url_entry:
            self.paste_entry_field(self.url_entry)
        elif focused_widget == self.api_key_entry:
            self.paste_entry_field(self.api_key_entry)
        elif focused_widget == self.output_dir_entry:
            self.paste_entry_field(self.output_dir_entry)
        # Text widgets are read-only, so no paste

    def menu_select_all(self):
        """Handle Select All from Edit menu."""
        focused_widget = self.root.focus_get()
        
        if focused_widget in [self.url_entry, self.api_key_entry, self.output_dir_entry]:
            self.select_all_entry_field(focused_widget)
        elif focused_widget in [self.progress_text, self.subtitles_text, self.chapters_text]:
            self.select_all_text_widget()

    def menu_cut(self):
        """Handle Cut from Edit menu."""
        focused_widget = self.root.focus_get()
        
        if focused_widget == self.url_entry:
            self.cut_entry_field(self.url_entry)
        elif focused_widget == self.api_key_entry:
            # Don't allow cutting from API key field
            messagebox.showwarning("Security", "Cannot cut from API key field for security reasons.")
        elif focused_widget == self.output_dir_entry:
            self.cut_entry_field(self.output_dir_entry)
        elif focused_widget in [self.progress_text, self.subtitles_text, self.chapters_text]:
            # Text widgets are read-only, so no cutting allowed
            messagebox.showwarning("Read-only", "Cannot cut from read-only text areas.")
        # No fallback action needed

    def copy_entry_field(self, entry_widget):
        """Copy selected text from entry field to clipboard."""
        try:
            if entry_widget.selection_present():
                text = entry_widget.selection_get()
            else:
                text = entry_widget.get()
            
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()
        except tk.TclError:
            # No selection or other error
            pass

    def paste_entry_field(self, entry_widget):
        """Paste text from clipboard to entry field."""
        try:
            clipboard_text = self.root.clipboard_get()
            
            if entry_widget.selection_present():
                # Replace selection
                entry_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                entry_widget.insert(tk.INSERT, clipboard_text)
            else:
                # Insert at cursor position
                entry_widget.insert(tk.INSERT, clipboard_text)
                
        except tk.TclError:
            # No clipboard content or other error
            pass

    def cut_entry_field(self, entry_widget):
        """Cut selected text from entry field to clipboard."""
        try:
            if entry_widget.selection_present():
                text = entry_widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()
                entry_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                # If no selection, copy all and delete
                text = entry_widget.get()
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.root.update()
                entry_widget.delete(0, tk.END)
        except tk.TclError:
            # No selection or other error
            pass

    def select_all_entry_field(self, entry_widget):
        """Select all text in entry field."""
        entry_widget.select_range(0, tk.END)
        entry_widget.icursor(tk.END)

    def copy_text_selection(self):
        """Copy selected text from text widget to clipboard."""
        try:
            # Determine which text widget has focus or selection
            focused_widget = self.root.focus_get()
            
            if focused_widget == self.progress_text:
                widget = self.progress_text
            elif focused_widget == self.subtitles_text:
                widget = self.subtitles_text
            elif focused_widget == self.chapters_text:
                widget = self.chapters_text
            else:
                # Default to current tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 0:
                    widget = self.progress_text
                elif selected_tab == 1:
                    widget = self.subtitles_text
                elif selected_tab == 2:
                    widget = self.chapters_text
                else:
                    return
            
            # Copy selection if any, otherwise copy all
            try:
                if widget.tag_ranges(tk.SEL):
                    text = widget.selection_get()
                else:
                    text = widget.get(1.0, tk.END).strip()
                
                if text:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)
                    self.root.update()
                    
            except tk.TclError:
                # No selection, copy all content
                text = widget.get(1.0, tk.END).strip()
                if text:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)
                    self.root.update()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy text: {e}")



    def select_all_text_widget(self):
        """Select all text in the focused text widget."""
        try:
            focused_widget = self.root.focus_get()
            
            if focused_widget == self.progress_text:
                widget = self.progress_text
            elif focused_widget == self.subtitles_text:
                widget = self.subtitles_text
            elif focused_widget == self.chapters_text:
                widget = self.chapters_text
            else:
                # Default to current tab
                selected_tab = self.notebook.index(self.notebook.select())
                if selected_tab == 0:
                    widget = self.progress_text
                elif selected_tab == 1:
                    widget = self.subtitles_text
                elif selected_tab == 2:
                    widget = self.chapters_text
                else:
                    return
            
            widget.tag_add(tk.SEL, "1.0", tk.END)
            widget.mark_set(tk.INSERT, "1.0")
            widget.see(tk.INSERT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not select text: {e}")
    


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