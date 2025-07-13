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

"""Configuration management for Chapter Timecode Generator."""

import os
import sys
import keyring
from pathlib import Path
from typing import Optional, Dict, Any
import json
from core import DEFAULT_MODEL, AVAILABLE_MODELS

# Application information
APP_NAME = "timecode-generator"
APP_VERSION = "1.0.1"
APP_TITLE = "Chapter Timecode Generator"
APP_AUTHOR = "Dimitry Polivaev"
APP_COPYRIGHT = "Copyright 2025 Dimitry Polivaev"
APP_LICENSE = "Apache License 2.0"
APP_URL = "https://github.com/dimitrypolivaev/timecodes"

# Application name for keyring
CONFIG_DIR = Path.home() / ".timecode-generator"
CONFIG_FILE = CONFIG_DIR / "config.json"

class Config:
    """Configuration manager for the application."""
    
    def __init__(self):
        """Initialize configuration."""
        self.settings = self._load_settings()
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        CONFIG_DIR.mkdir(exist_ok=True)
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file."""
        default_settings = {
            "model": DEFAULT_MODEL,
            "language": "",
            "keep_files": False,
            "show_subtitles": False,
            "non_interactive": False,
            "output_dir": "",
            "window_geometry": "800x600",
            "last_url": ""
        }
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_settings.update(loaded_settings)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_settings
    
    def _save_settings(self):
        """Save settings to config file."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from secure storage."""
        try:
            return keyring.get_password(APP_NAME, "gemini_api_key")
        except Exception as e:
            print(f"Warning: Could not retrieve API key: {e}")
            return None
    
    def set_api_key(self, api_key: str) -> bool:
        """Store API key in secure storage with universal auto-recovery.
        
        Returns:
            bool: True if successful, False if failed even after auto-recovery
        """
        try:
            keyring.set_password(APP_NAME, "gemini_api_key", api_key)
            return True
        except Exception as e:
            # Universal auto-recovery: try to delete corrupted entry and retry
            # This works safely across all platforms (Windows, macOS, Linux)
            try:
                print(f"Info: Attempting auto-recovery for keyring error: {e}")
                keyring.delete_password(APP_NAME, "gemini_api_key")
                # Retry after deleting potentially corrupted entry
                keyring.set_password(APP_NAME, "gemini_api_key", api_key)
                print("Info: Auto-recovery successful")
                return True
            except Exception as recovery_error:
                print(f"Warning: Auto-recovery failed: {recovery_error}")
                return False
    
    def clear_api_key(self) -> bool:
        """Clear API key from secure storage with universal error handling.
        
        Returns:
            bool: True if successful, False if failed
        """
        try:
            keyring.delete_password(APP_NAME, "gemini_api_key")
            return True
        except Exception as e:
            error_str = str(e).lower()
            
            # For deletion, "not found" errors are actually success across all platforms
            if ("not found" in error_str or 
                "does not exist" in error_str or
                "no such" in error_str):
                return True
                
            # Other keyring errors - log but consider it a failure
            print(f"Warning: Could not clear API key: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value."""
        self.settings[key] = value
        self._save_settings()
    
    def get_model(self) -> str:
        """Get the selected model."""
        model = self.get_setting("model", DEFAULT_MODEL)
        # Validate model is still available
        if model not in AVAILABLE_MODELS:
            model = DEFAULT_MODEL
            self.set_setting("model", model)
        return model
    
    def set_model(self, model: str):
        """Set the selected model."""
        if model in AVAILABLE_MODELS:
            self.set_setting("model", model)
    
    def get_language(self) -> str:
        """Get the selected language."""
        return self.get_setting("language", "")
    
    def set_language(self, language: str):
        """Set the selected language."""
        self.set_setting("language", language)
    
    def get_keep_files(self) -> bool:
        """Get keep files setting."""
        return self.get_setting("keep_files", False)
    
    def set_keep_files(self, keep_files: bool):
        """Set keep files setting."""
        self.set_setting("keep_files", keep_files)
    
    def get_show_subtitles(self) -> bool:
        """Get show subtitles setting."""
        return self.get_setting("show_subtitles", False)
    
    def set_show_subtitles(self, show_subtitles: bool):
        """Set show subtitles setting."""
        self.set_setting("show_subtitles", show_subtitles)
    
    def get_non_interactive(self) -> bool:
        """Get non-interactive setting."""
        return self.get_setting("non_interactive", False)
    
    def set_non_interactive(self, non_interactive: bool):
        """Set non-interactive setting."""
        self.set_setting("non_interactive", non_interactive)
    
    def get_output_dir(self) -> str:
        """Get output directory setting."""
        return self.get_setting("output_dir", "")
    
    def set_output_dir(self, output_dir: str):
        """Set output directory setting."""
        self.set_setting("output_dir", output_dir)
    
    def get_window_geometry(self) -> str:
        """Get window geometry."""
        return self.get_setting("window_geometry", "1000x700")
    
    def set_window_geometry(self, geometry: str):
        """Set window geometry."""
        self.set_setting("window_geometry", geometry)
    
    # App information methods
    def get_app_version(self) -> str:
        """Get app version."""
        return APP_VERSION
    
    def get_app_title(self) -> str:
        """Get app title."""
        return APP_TITLE
    
    def get_app_author(self) -> str:
        """Get app author."""
        return APP_AUTHOR
    
    def get_app_copyright(self) -> str:
        """Get app copyright."""
        return APP_COPYRIGHT
    
    def get_app_license(self) -> str:
        """Get app license."""
        return APP_LICENSE
    
    def get_app_url(self) -> str:
        """Get app URL."""
        return APP_URL
    
    def get_last_url(self) -> str:
        """Get last used URL."""
        return self.get_setting("last_url", "")
    
    def set_last_url(self, url: str):
        """Set last used URL."""
        self.set_setting("last_url", url)
    
    def export_settings(self, filepath: str):
        """Export settings to a file (excluding sensitive data)."""
        try:
            export_data = {k: v for k, v in self.settings.items() if k != "api_key"}
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Could not export settings: {e}")
    
    def import_settings(self, filepath: str):
        """Import settings from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Validate and merge settings
            for key, value in imported_settings.items():
                if key in self.settings:
                    self.settings[key] = value
            
            self._save_settings()
        except Exception as e:
            raise ValueError(f"Could not import settings: {e}")

# Global config instance
config = Config() 