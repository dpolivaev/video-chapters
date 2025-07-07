# Video Chapters Generator

A Python script that downloads YouTube auto-generated subtitles and uses Google Gemini AI to generate chapter timecodes for the video content.

## Features

- Downloads auto-generated subtitles from YouTube videos in any available language
- Uses Google Gemini AI to analyze subtitle content and create logical video chapters
- Automatically detects subtitle language and generates chapter titles in the same language
- Interactive and quiet modes
- Configurable Gemini models
- Clean temporary file management

## Prerequisites

- Python 3.7 or higher
- Google Gemini API key

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Setup

### Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set it as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or pass it directly via the `--api-key` argument.

## Usage

### Basic Usage

```bash
# Auto-selects first available language
python video_chapters.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Specify Language (when multiple are available)

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

### Examples with Different Options

```bash
# Quiet mode (automatically generate chapters)
python video_chapters.py --quiet "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save subtitles and use specific model with language selection
python video_chapters.py --language en --keep-files --model gemini-2.5-flash "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Show subtitle content before generating chapters
python video_chapters.py --show-subtitles "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Save to specific directory with Pro model and Russian language
python video_chapters.py --language ru --keep-files --output-dir ./subtitles --model gemini-2.5-pro "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Command Line Options

- `--language`, `-l`: Optional language code for subtitles (e.g., en, es, ru, uk). If not specified, uses first available language.
- `--api-key`: Gemini API key (or set GEMINI_API_KEY env var)
- `--model`: Gemini model to use (gemini-2.5-pro, gemini-2.5-flash)
- `--quiet`: Run in non-interactive mode
- `--keep-files`: Keep downloaded subtitle files
- `--output-dir`: Directory to save subtitle files
- `--show-subtitles`: Show subtitle content before processing

## How It Works

1. **Download**: Uses yt-dlp to download auto-generated subtitles from YouTube
2. **Language Selection**: 
   - If `--language` specified: finds that specific language or shows available options
   - If no language specified: automatically uses first available language and shows other options
3. **Language Detection**: Gemini automatically detects the subtitle language
4. **AI Analysis**: Sends subtitle content to Google Gemini with instructions to break content into logical chapters
5. **Chapter Generation**: Returns AI-generated chapter timecodes with descriptive titles in the same language as the subtitles

## Output Format

The script generates chapter timecodes in mm:ss format with descriptive titles in the original language:

**English example:**
```
00:19 - Introduction and host welcome
02:45 - Main topic discussion
05:30 - Examples and demonstrations
08:15 - Conclusion and next steps
```

**Spanish example:**
```
00:19 - Introducción y bienvenida del anfitrión
02:45 - Discusión del tema principal
05:30 - Ejemplos y demostraciones
08:15 - Conclusión y próximos pasos
```

**Russian example:**
```
00:19 - Вступление и приветствие ведущего
02:45 - Обсуждение основной темы
05:30 - Примеры и демонстрации
08:15 - Заключение и следующие шаги
```

**Ukrainian example:**
```
00:19 - Вступ та привітання ведучого
02:45 - Обговорення основної теми
05:30 - Приклади та демонстрації
08:15 - Висновки та наступні кроки
```

These timecodes can be used for:
- YouTube video chapters
- Video navigation
- Content organization
- Study notes
- Video editing reference

## Error Handling

- Script stops if no auto-generated subtitles are available
- Validates YouTube URLs and API keys
- Handles temporary file cleanup automatically

## Model Configuration

You can easily change the default model by editing the top of the script:

```python
DEFAULT_MODEL = 'gemini-2.5-pro'  # or 'gemini-2.5-flash'
```

## Dependencies

- `yt-dlp`: YouTube video downloading
- `google-generativeai`: Google Gemini AI integration

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
 