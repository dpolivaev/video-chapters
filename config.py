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
APP_VERSION = "1.1.0"
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
            "last_url": "",
            "custom_instructions": "",
            "instruction_history": [],
            "instruction_history_limit": 10
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
                # Try to delete the potentially corrupted entry
                try:
                    keyring.delete_password(APP_NAME, "gemini_api_key")
                except Exception:
                    # Ignore deletion errors - the entry might not exist
                    pass
                
                # Small delay to let keychain settle
                import time
                time.sleep(0.1)
                
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
                
            # For macOS keychain errors, try a more robust approach
            if "(-25244" in str(e) or "keychain" in error_str.lower():
                print(f"Info: Keychain error detected, attempting alternative cleanup: {e}")
                try:
                    # Try with a small delay to let keychain settle
                    import time
                    time.sleep(0.1)
                    keyring.delete_password(APP_NAME, "gemini_api_key")
                    return True
                except Exception:
                    # If it still fails, consider it a success since the goal is to clear
                    print("Info: Keychain cleanup completed (entry may have been cleared)")
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
    
    def get_instruction_history(self) -> list:
        """Get instruction history."""
        return self.get_setting("instruction_history", [])
    
    def add_instruction_to_history(self, instruction: str):
        """Add instruction to history, moving existing ones to top if found."""
        if not instruction.strip():
            return  # Don't save empty instructions
            
        history = self.get_instruction_history()
        limit = self.get_instruction_history_limit()
        
        from datetime import datetime
        
        # Check if this instruction already exists in history
        existing_index = None
        for i, entry in enumerate(history):
            if entry["content"] == instruction:
                existing_index = i
                break
        
        if existing_index is not None:
            # Move existing instruction to top (most recent)
            existing_entry = history.pop(existing_index)
            # Update timestamp to current time
            existing_entry["timestamp"] = datetime.now().isoformat()
            history.append(existing_entry)
        else:
            # Add new instruction
            new_entry = {
                "content": instruction,
                "timestamp": datetime.now().isoformat(),
                "preview": instruction[:100] + "..." if len(instruction) > 100 else instruction
            }
            history.append(new_entry)
        
        # Keep only the most recent entries up to the limit
        if len(history) > limit:
            history = history[-limit:]
        
        self.set_setting("instruction_history", history)
    
    def get_instruction_history_limit(self) -> int:
        """Get instruction history limit."""
        return self.get_setting("instruction_history_limit", 10)
    
    def set_instruction_history_limit(self, limit: int):
        """Set instruction history limit and clean up if needed."""
        if limit < 1:
            limit = 1
        elif limit > 50:
            limit = 50
            
        self.set_setting("instruction_history_limit", limit)
        
        # Clean up history if new limit is smaller
        history = self.get_instruction_history()
        if len(history) > limit:
            history = history[-limit:]
            self.set_setting("instruction_history", history)
    
    def delete_instruction_from_history(self, index: int):
        """Delete instruction from history by index."""
        history = self.get_instruction_history()
        if 0 <= index < len(history):
            history.pop(index)
            self.set_setting("instruction_history", history)

# Global config instance
config = Config() 