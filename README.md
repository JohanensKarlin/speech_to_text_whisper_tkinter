# Speech to Text - Voice Recognition and Transcription

## Project Overview
A Python-based speech recognition application with a minimalist, floating user interface for transcribing audio in German and English using OpenAI's Whisper API.

## Core Functionality
- Record audio through your microphone
- Transcribe audio using OpenAI's Whisper API
- Automatically insert transcriptions at cursor position
- Support for multiple languages (German and English)
- Floating UI with minimal and normal modes

## Technical Stack
- Python 3.12
- Libraries:
  - sounddevice (audio recording)
  - numpy (audio data processing)
  - customtkinter (enhanced GUI)
  - keyboard (global hotkeys)
  - pyautogui (text insertion)
  - pyperclip (clipboard management)
  - OpenAI (transcription service)

## Project Files
- `speech_to_text.py` - Main application with all functionality
- `config_example.json` - Example configuration file (rename to config.json and add your API key)
- `hallucination.json` - Contains phrases to filter out from transcriptions in various languages
- `start_app.bat` - Batch file to install dependencies and launch the application
- `Verbesserung_ideen.md` - Future improvement ideas for the project
- `requirements.txt` - Lists all required Python packages and versions
- `pyproject.toml` - Project configuration file for dependency management and build settings
- `uv.lock` - Lock file for uv package manager that tracks exact versions of dependencies for aligned collaboration
- `.python-version` - Specifies the Python version (3.10+) required for the project

## User Interface
- Compact, frameless window with rounded corners
- Dark gray color scheme (#424242)
- Draggable interface
- Always-on-top behavior
- Rounded buttons with subtle hover effects
- Wave animation during recording (left to right)
- Reverse wave animation during transcription (right to left)
- Minimal mode for reduced screen space usage

## Hotkeys
- Ctrl+Y: Start/Stop recording
- Alt+L: Toggle language
- Alt+M: Enable/disable keyboard shortcuts
- Alt+Q: Quit application

## Language Management
- Switch between German and English
- Language selection via button
- OpenAI Whisper API processes transcription language

## Getting Started

### Prerequisites
- Python 3.12 or newer
- OpenAI API key

### Installation
1. Clone or download this repository
2. Rename `config_example.json` to `config.json` and add your OpenAI API key
3. Install dependencies using one of the startup methods below

### Starting the Application

#### Method 1: Batch File (with console window)
Double-click `start_app.bat` to launch the application. This file:
- Automatically installs all required dependencies
- Starts the application with a visible console window

#### Method 2: VBS Script (without console window)
Double-click `start_app_hidden.vbs` to start the application without a console window.

#### Method 3: Executable File (.exe)
A standalone executable can be created using PyInstaller:

```bash
# Install the latest hooks
pip install -U pyinstaller-hooks-contrib

# Create the executable
pyinstaller --onefile --windowed --recursive-copy-metadata openai --recursive-copy-metadata tqdm --hidden-import=openai --hidden-import=tqdm --name="SpeechToText" speech_to_text.py
```

The executable will be created in the `dist` folder and can be copied and run on any Windows computer without Python installed.

## Setting Up Autostart
1. Press `Win+R`, type `shell:startup` and press Enter
2. Copy `start_app_hidden.vbs` or a shortcut to the .exe file into this folder

## Known Issues and Solutions
- **OpenAI module error with .exe**: Use the PyInstaller options mentioned above to include metadata and hidden dependencies
- **Window jumps when clicking**: Fixed with improved drag functionality
- **Multiple mute button activations**: Fixed with delay between clicks

## Security Notes
- Store your OpenAI API key in the config.json file
- For production environments, the API key should be stored in environment variables or a secure configuration file

## Future Improvements
See the `Verbesserung_ideen.md` file for a detailed list of planned improvements, including:
1. Enhanced user interface with themes and customization
2. Improved audio processing with noise reduction
3. Advanced transcription features
4. Custom hotkeys
5. Transcript history and management
6. Integration with other tools and services
7. Performance optimizations
