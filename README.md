# Video Chapters Generator

A Python application that downloads YouTube auto-generated subtitles and uses Google Gemini AI to generate chapter timecodes for the video content. Available as both a command-line tool and a modern GUI application.

## 🚀 Quick Start - Ready-to-Use Applications

**For most users, we recommend downloading the ready-to-use GUI applications:**

✅ **Download from [GitHub Releases](../../releases)** - No Python installation required!

- **MacOS (Apple Silicon)**: Download the `.dmg` file - just double-click to run
- **Windows**: Download the `.exe` file - just double-click to run

> **Windows users:** If the app does not start or shows a DLL error, install the [Microsoft Visual C++ 2015-2022 Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe) from Microsoft.

These standalone applications include everything you need and provide a modern, user-friendly interface. Just download, run, and start generating video chapters!

**Note:** You'll still need to get your own [Google Gemini API key](https://aistudio.google.com/apikey) - the GUI will guide you through entering it securely.

---

**The Python installation instructions below are only needed if you want to:**
- Use the command-line interface
- Run the Python scripts directly
- Modify or contribute to the code

## Features

- **GUI Application**: Modern, user-friendly interface with real-time progress tracking
- **Command Line Interface**: Traditional CLI for automation and scripting
- Downloads auto-generated subtitles from YouTube videos in any available language
- Uses Google Gemini AI to analyze subtitle content and create logical video chapters
- Automatically detects subtitle language and generates chapter titles in the same language
- **Secure API Key Storage**: API keys are stored securely using your system's keyring
- **Persistent Settings**: Your preferences are saved between sessions
- Interactive and non-interactive modes
- Configurable Gemini models
- Clean temporary file management

## Prerequisites (For Python Script Usage Only)

- Python 3.7 or higher
- Google Gemini API key

## Installation (For Python Script Usage Only)

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

For development and building executables:
```bash
pip install -r requirements-dev.txt
```

Or install as a package with development dependencies:
```bash
pip install -e .[dev]
```

## Setup

### Get Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. For GUI: Enter the key in the application (it will be stored securely)
4. For CLI: Set it as an environment variable or pass via argument:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Usage

### GUI Application

Launch the GUI application:

```bash
python gui.py
```

The GUI provides:
- **YouTube URL input** with language checking
- **Secure API key storage** (masked input, persistent storage)
- **Language selection** from available options
- **Model selection** (Gemini Pro/Flash)
- **Processing options** via checkboxes
- **Tabbed results** showing progress, subtitles, and chapters
- **Save functionality** for both subtitles and chapters
- **Real-time progress tracking**

#### GUI Features:
- **Check Languages**: Click to see available subtitle languages for any video
- **API Key Management**: Save/Clear buttons for secure key storage
- **Output Directory**: Browse and select where to save files
- **Processing Options**: 
  - Keep files (don't delete temporary files)
  - Show subtitles (display in GUI)
  - Non-interactive mode (minimal interaction)
- **Results Tabs**: 
  - Progress: Real-time processing updates
  - Subtitles: Downloaded subtitle content
  - Chapters: AI-generated chapter timecodes
- **Save Options**: Individual save buttons for subtitles and chapters

### Command Line Interface

#### Basic Usage

```bash
# Auto-selects first available language
python video_chapters.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Check Available Languages

```bash
# Check what languages are available before processing
python video_chapters.py --check-languages "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Specify Language (when multiple are available)

```bash
# For English subtitles
python video_chapters.py --language en "https://www.youtube.com/watch?v=VIDEO_ID"

# For Spanish subtitles  
python video_chapters.py --language es "https://www.youtube.com/watch?v=VIDEO_ID"

# For Russian subtitles
python video_chapters.py --language ru "https://www.youtube.com/watch?v=VIDEO_ID"

# For Ukrainian subtitles
python video_chapters.py --language uk "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Examples with Different Options

```bash
# Non-interactive mode (automatically generate chapters)
python video_chapters.py --non-interactive "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save subtitles and use specific model with language selection
python video_chapters.py --language en --keep-files --model gemini-2.5-flash "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Show subtitle content before generating chapters
python video_chapters.py --show-subtitles "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save to specific directory with Pro model and Russian language
python video_chapters.py --language ru --keep-files --output-dir ./subtitles --model gemini-2.5-pro "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Command Line Options

- `--language`, `-l`: Optional language code for subtitles (e.g., en, es, ru, uk). If not specified, uses first available language.
- `--api-key`: Gemini API key (or set GEMINI_API_KEY env var)
- `--model`: Gemini model to use (gemini-2.5-pro, gemini-2.5-flash)
- `--non-interactive`: Run in non-interactive mode
- `--keep-files`: Keep downloaded subtitle files
- `--output-dir`: Directory to save subtitle files
- `--show-subtitles`: Show subtitle content before processing
- `--check-languages`: Check available languages and exit

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

```
Copyright 2025 Dimitry Polivaev

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
 
