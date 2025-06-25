# Telegram-Obsidian Bridge

A complete automation system that bridges Telegram messages to Obsidian through voice transcription and intelligent processing using Claude AI via MCP (Model Context Protocol).

## 🌟 Features

- 🤖 **Telegram Bot Integration**: Capture messages, voice notes, TODOs, and ideas directly from Telegram
- 🎤 **Voice Transcription**: Automatic voice-to-text using Whisper.cpp for offline processing
- 🧠 **AI Processing**: Smart content categorization and formatting through Claude AI
- 📋 **MCP Server**: Model Context Protocol server for seamless Claude Desktop integration
- 🗂 **Auto Organization**: Intelligent file organization and archiving system
- 📚 **Obsidian Integration**: Direct integration with your Obsidian vault for knowledge management
- 🔄 **Real-time Monitoring**: File system monitoring for instant processing
- 📊 **Content Categories**: Support for todos, notes, ideas, links, and voice messages

## 🏗 Architecture

The system consists of several interconnected components:

```
Telegram Bot → Content Capture → Voice Transcription → AI Processing → Obsidian Vault
     ↓              ↓                    ↓               ↓              ↓
  [bot.py]    [File System]      [Whisper.cpp]    [Claude via MCP]  [File Manager]
```

### Core Components:

1. **Telegram Bot** (`telegram_bot/bot.py`): Captures all incoming messages and media
2. **Voice Processor** (`services/voice_processor.py`): Monitors and transcribes voice files
3. **Text Processor** (`services/text_processor.py`): Handles text content processing
4. **MCP Server** (`mcp_server/telegram_mcp.py`): Provides Claude AI integration
5. **Obsidian Integration** (`obsidian_integration/file_manager.py`): Manages vault files
6. **Whisper Transcriber** (`transcription/whisper_transcriber.py`): Converts speech to text

## 📋 Prerequisites

- **Python 3.9+**
- **FFmpeg** (for audio processing)
- **Telegram Bot Token** (from @BotFather)
- **Obsidian Vault** (target knowledge base)
- **Claude Desktop** (for AI processing)
- **Whisper.cpp Model** (for voice transcription)

## 🚀 Installation

### 1. Quick Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd TelegramObsidianBridge

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install System Dependencies

**FFmpeg Installation:**

- **Windows**: `winget install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 3. Download Whisper Model

```bash
# Create models directory
mkdir models

# Download base English model (or your preferred model)
# Place ggml-base.en.bin in the models/ directory
```

### 4. Build Whisper.cpp (Optional)

```bash
git submodule update --init --recursive
cd whisper.cpp
mkdir build && cd build
cmake ..
cmake --build . --config Release
```

## ⚙️ Configuration

### 1. Basic Configuration

Copy and edit the main configuration file:

```bash
cp config.example.json config.json
```

Update `config.json` with your settings:

```json
{
  "telegram_bot_token": "YOUR_BOT_TOKEN_FROM_BOTFATHER",
  "obsidian_vault_path": "C:\\path\\to\\your\\obsidian\\vault",
  "whisper_model_path": "./models/ggml-base.en.bin",
  "whisper_exe_path": "./whisper.cpp/build/bin/Release/whisper-cli.exe"
}
```

### 2. Claude Desktop MCP Setup

**Find your Claude Desktop config:**

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Add the telegram-bridge server:**

```json
{
  "mcpServers": {
    "telegram-bridge": {
      "command": "python",
      "args": ["mcp_server/telegram_mcp.py"],
      "cwd": "C:\\full\\path\\to\\TelegramObsidianBridge",
      "env": {
        "PYTHONPATH": "C:\\full\\path\\to\\TelegramObsidianBridge"
      }
    }
  }
}
```

### 3. Telegram Bot Setup

1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token to your `config.json`
4. Start chatting with your bot!

## 🎯 Usage

### Starting the System

```bash
# Option 1: Use the provided batch file (Windows)
start_bridge.bat

# Option 2: Run directly
python main.py

# Option 3: Test the system first
python test_system.py
```

### Telegram Commands

- **Text Messages**: Automatically categorized as notes
- **Voice Messages**: Transcribed and processed
- **`/todo`**: Mark message as a TODO item
- **`/idea`**: Mark message as an idea
- **`/note`**: Mark message as a note
- **URLs**: Automatically detected and categorized as links

### Claude Integration

Once the MCP server is running, you can use Claude Desktop to:

1. **Get pending content**: `@telegram-bridge get_pending_content`
2. **Process for Obsidian**: `@telegram-bridge process_for_obsidian`
3. **Get daily summary**: `@telegram-bridge get_daily_summary`

### Content Flow

1. **Send message** to Telegram bot
2. **Content captured** in `content/incoming/`
3. **Voice transcribed** (if applicable)
4. **Moved to** `content/processed/`
5. **AI processes** via Claude MCP
6. **Final output** ready for Obsidian in `content/ready_for_obsidian/`

## 📁 Project Structure

```
TelegramObsidianBridge/
├── 📁 content/                    # Content processing pipeline
│   ├── 📁 incoming/              # Raw captured content
│   ├── 📁 processed/             # Transcribed content
│   ├── 📁 ready_for_obsidian/    # AI-processed, ready for vault
│   ├── 📁 archive/               # Archived content
│   ├── 📁 voices/                # Voice message files
│   ├── 📁 texts/                 # Text message files
│   └── 📁 todos/                 # TODO items
├── 📁 mcp_server/                # Claude integration
│   └── telegram_mcp.py           # MCP server implementation
├── 📁 telegram_bot/              # Telegram bot logic
│   └── bot.py                    # Main bot implementation
├── 📁 services/                  # Processing services
│   ├── voice_processor.py        # Voice file monitoring
│   └── text_processor.py         # Text processing
├── 📁 transcription/             # Speech-to-text
│   └── whisper_transcriber.py    # Whisper.cpp integration
├── 📁 obsidian_integration/      # Vault management
│   └── file_manager.py           # File operations
├── 📁 models/                    # AI models
│   └── ggml-base.en.bin          # Whisper model
├── 📁 logs/                      # System logs
├── 📁 whisper.cpp/               # Whisper.cpp submodule
├── main.py                       # Main application entry
├── config.json                   # Configuration file
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🛠 Development

### Testing

```bash
# Run basic system tests
python test_system.py

# Run comprehensive tests
python comprehensive_test.py
```

### Adding New Content Types

1. Modify `telegram_bot/bot.py` to capture new content
2. Update `services/text_processor.py` for processing logic
3. Add MCP functions in `mcp_server/telegram_mcp.py`
4. Update Obsidian integration in `obsidian_integration/file_manager.py`

### Logging

Logs are stored in the `logs/` directory:

- `system.log`: Main application logs
- `bot.log`: Telegram bot specific logs

## 🔧 Troubleshooting

### Common Issues

**Bot not receiving messages:**

- Check your bot token in `config.json`
- Ensure the bot is started and not blocked

**Voice transcription failing:**

- Verify FFmpeg installation
- Check Whisper model path
- Ensure whisper.cpp is built correctly

**MCP connection issues:**

- Verify Claude Desktop config paths
- Check that the MCP server starts without errors
- Ensure Python environment is activated

**File permission errors:**

- Check Obsidian vault path permissions
- Ensure content directories are writable

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

### Code Style

- Use Python type hints
- Follow PEP 8 guidelines
- Add docstrings for new functions
- Include appropriate logging

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) for efficient speech recognition
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integration
- [FastMCP](https://github.com/jlowin/fastmcp) for Model Context Protocol implementation
- [Anthropic](https://anthropic.com) for Claude AI integration

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review the logs in the `logs/` directory
3. Run `python test_system.py` to diagnose issues
4. Open an issue on GitHub with detailed information

---

**Happy note-taking! 📝✨**
