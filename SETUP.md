# Telegram-Claude-Obsidian Bridge Setup

## Installation Steps

### 1. Clone and Setup Project

```bash
git clone <your-repo-url>
cd TelegramObsidianBridge

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings

#### A. Copy and edit config.json

```bash
cp config.example.json config.json
```

Edit `config.json` with your settings:

```json
{
  "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
  "obsidian_vault_path": "/path/to/your/obsidian/vault",
  "whisper_model_path": "./models/ggml-base.en.bin",
  "whisper_exe_path": "./whisper.cpp/build/bin/Release/whisper-cli.exe"
}
```

#### B. Setup Claude Desktop MCP Connection

1. **Find your Claude Desktop config location:**

   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Add the telegram-bridge server to your config:**

   Copy from `claude_desktop_config.example.json` and update paths:

   ```json
   {
     "mcpServers": {
       "telegram-bridge": {
         "command": "python",
         "args": ["mcp_server/telegram_mcp.py"],
         "cwd": "/FULL/PATH/TO/YOUR/TelegramObsidianBridge",
         "env": {
           "PYTHONPATH": "/FULL/PATH/TO/YOUR/TelegramObsidianBridge"
         }
       }
     }
   }
   ```

   **Replace `/FULL/PATH/TO/YOUR/TelegramObsidianBridge` with your actual project path:**

   - **Windows example:** `"C:\\Users\\YourName\\Documents\\TelegramObsidianBridge"`
   - **macOS example:** `"/Users/YourName/Documents/TelegramObsidianBridge"`
   - **Linux example:** `"/home/yourname/Documents/TelegramObsidianBridge"`

### 3. Download Required Models

```bash
# Create models directory
mkdir models

# Download Whisper model (or use your preferred model)
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin -O models/ggml-base.en.bin
```

### 4. Install FFmpeg

- **Windows:** `winget install ffmpeg` or download from https://ffmpeg.org
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` (Ubuntu/Debian)

### 5. Build Whisper.cpp (if needed)

```bash
git submodule update --init --recursive
cd whisper.cpp
mkdir build && cd build
cmake ..
cmake --build . --config Release
```

### 6. Start the Bridge

```bash
# Windows:
start_bridge.bat

# macOS/Linux:
python main.py
```

### 7. Test the Setup

1. **Restart Claude Desktop** completely
2. Send a message to your Telegram bot: `TODO: Test the system`
3. In Claude Desktop: "Please check my pending Telegram content"
4. You should see Claude find and process your TODO!

## Path Configuration Guide

The project uses relative paths internally, but you need to provide absolute paths in two places:

1. **config.json** - Use relative paths for whisper components:

   ```json
   "whisper_model_path": "./models/ggml-base.en.bin",
   "whisper_exe_path": "./whisper.cpp/build/bin/Release/whisper-cli.exe"
   ```

2. **Claude Desktop config** - Use absolute paths for the project root:
   ```json
   "cwd": "/absolute/path/to/TelegramObsidianBridge"
   ```

The `cwd` setting ensures the MCP server runs from the project directory, making all relative paths work correctly.

## Troubleshooting

### MCP Server Not Found

- Restart Claude Desktop completely
- Check that the `cwd` path in Claude config is correct
- Verify Python can run from that directory

### Files Not Being Processed

- Check that the content directories exist: `content/incoming/`, `content/processed/`
- Verify file permissions
- Look for MCP connection icon in Claude Desktop

### Whisper Transcription Issues

- Test Whisper directly: `./whisper.cpp/build/bin/Release/whisper-cli.exe --help`
- Check model file exists: `ls -la models/`
- Verify FFmpeg is installed: `ffmpeg -version`
