#!/usr/bin/env python3
"""
Comprehensive test script based on the walkthrough
Tests all components step by step
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import sys
import os


def print_section(title):
    """Print a nice section header"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {title}")
    print("=" * 60)


def print_check(description, status, details=""):
    """Print a status check"""
    icon = "✅" if status else "❌"
    print(f"{icon} {description}")
    if details:
        print(f"   {details}")


def test_basic_setup():
    """Test basic project setup"""
    print_section("Basic Project Setup")
    # Check if we're in the right directory
    current_dir = Path.cwd()

    print_check(
        "Working directory",
        current_dir.name == "TelegramObsidianBridge",
        f"Current: {current_dir}",
    )

    # Check required files
    required_files = ["config.json", "main.py", "requirements.txt", "start_bridge.bat"]

    for file in required_files:
        exists = Path(file).exists()
        print_check(f"File {file}", exists)

    # Check required directories
    required_dirs = [
        "telegram_bot",
        "mcp_server",
        "obsidian_integration",
        "transcription",
        "services",
        "content",
        "models",
        "logs",
    ]

    for directory in required_dirs:
        exists = Path(directory).exists()
        print_check(f"Directory {directory}/", exists)


def test_configuration():
    """Test configuration file"""
    print_section("Configuration")

    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        print_check("Config file loads", True)

        # Check required keys
        required_keys = [
            "telegram_bot_token",
            "obsidian_vault_path",
            "whisper_model_path",
            "whisper_exe_path",
        ]

        for key in required_keys:
            exists = key in config
            value = config.get(key, "")
            print_check(f"Config key '{key}'", exists, f"Value: {value[:50]}...")

        # Check if paths exist
        model_exists = Path(config["whisper_model_path"]).exists()
        print_check("Whisper model file", model_exists, config["whisper_model_path"])

        exe_exists = Path(config["whisper_exe_path"]).exists()
        print_check("Whisper executable", exe_exists, config["whisper_exe_path"])

        vault_exists = Path(config["obsidian_vault_path"]).exists()
        print_check("Obsidian vault", vault_exists, config["obsidian_vault_path"])

        return config

    except Exception as e:
        print_check("Config file", False, f"Error: {e}")
        return None


def test_whisper_transcription(config):
    """Test Whisper transcription"""
    print_section("Whisper Transcription")

    if not config:
        print_check("Whisper test", False, "No config available")
        return

    model_path = config["whisper_model_path"]
    exe_path = config["whisper_exe_path"]

    # Test with JFK sample
    jfk_sample = Path("whisper.cpp/samples/jfk.wav")
    if not jfk_sample.exists():
        print_check("JFK sample file", False, f"Not found: {jfk_sample}")
        return

    print_check("JFK sample file", True, str(jfk_sample))
    # Run whisper transcription
    try:
        cmd = [
            str(exe_path),
            "-m",
            str(model_path),
            "-f",
            str(jfk_sample.resolve()),  # Use absolute path
            "--output-txt",
        ]

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=Path(exe_path).parent
        )

        success = result.returncode == 0
        print_check("Whisper transcription", success)

        if success:
            # Look for output
            expected_transcript = "fellow Americans"
            if expected_transcript.lower() in result.stdout.lower():
                print_check("Correct transcription", True, "JFK quote detected")
            else:
                print_check("Correct transcription", False, "JFK quote not found")
        else:
            print(f"Error: {result.stderr}")

    except Exception as e:
        print_check("Whisper transcription", False, f"Error: {e}")


def test_telegram_bot_structure():
    """Test Telegram bot files"""
    print_section("Telegram Bot Structure")

    bot_file = Path("telegram_bot/bot.py")
    print_check("Bot file exists", bot_file.exists())

    if bot_file.exists():
        try:
            # Try to import the bot class
            sys.path.insert(0, str(Path.cwd()))
            from telegram_bot.bot import TelegramCaptureBot

            print_check("Bot class imports", True)
            # Try to create bot instance with dummy config
            test_config = {
                "telegram_bot_token": "dummy_token",
                "obsidian_vault_path": "dummy_path",
                "whisper_model_path": "dummy_model",
                "whisper_exe_path": "dummy_exe",
            }

            try:
                TelegramCaptureBot(test_config)
                print_check("Bot instantiation", True)
            except Exception as e:
                print_check("Bot instantiation", False, f"Error: {e}")

        except Exception as e:
            print_check("Bot class imports", False, f"Error: {e}")


def test_mcp_server():
    """Test MCP server"""
    print_section("MCP Server")

    mcp_file = Path("mcp_server/telegram_mcp.py")
    print_check("MCP server file", mcp_file.exists())
    if mcp_file.exists():
        try:
            sys.path.insert(0, str(Path.cwd()))
            import mcp_server.telegram_mcp

            print_check("MCP server imports", True)
        except Exception as e:
            print_check("MCP server imports", False, f"Error: {e}")


def test_content_processing():
    """Test content processing with existing files"""
    print_section("Content Processing")

    content_dir = Path("content")

    # Check directories
    subdirs = ["incoming", "processed", "voices", "ready_for_obsidian"]
    for subdir in subdirs:
        path = content_dir / subdir
        path.mkdir(exist_ok=True)
        print_check(f"Directory {subdir}/", path.exists())

    # Check for existing files
    incoming_files = list((content_dir / "incoming").glob("*.json"))
    print_check(
        "Incoming files", len(incoming_files) > 0, f"Found {len(incoming_files)} files"
    )

    for file_path in incoming_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print_check(
                f"File {file_path.name}", True, f"Type: {data.get('type', 'unknown')}"
            )
        except Exception as e:
            print_check(f"File {file_path.name}", False, f"Error: {e}")


def test_obsidian_integration(config):
    """Test Obsidian integration"""
    print_section("Obsidian Integration")

    if not config:
        print_check("Obsidian test", False, "No config available")
        return

    vault_path = Path(config["obsidian_vault_path"])
    print_check("Vault path exists", vault_path.exists(), str(vault_path))

    if vault_path.exists():
        # Check if Telegram Captures folder structure exists
        telegram_folder = vault_path / "Telegram Captures"
        subfolders = ["TODOs", "Ideas", "Voice Notes", "Quick Notes", "Links"]

        for subfolder in subfolders:
            folder_path = telegram_folder / subfolder
            folder_path.mkdir(parents=True, exist_ok=True)
            print_check(f"Obsidian folder {subfolder}", folder_path.exists())


def create_test_content():
    """Create some test content for processing"""
    print_section("Creating Test Content")

    content_dir = Path("content")
    incoming_dir = content_dir / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    # Create test TODO
    test_todo = {
        "type": "todo",
        "content": "TODO: Test the Telegram to Obsidian bridge system",
        "timestamp": datetime.now().isoformat(),
        "user_id": 12345,
        "username": "test_user",
    }

    todo_file = (
        incoming_dir / f"todo_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(todo_file, "w", encoding="utf-8") as f:
        json.dump(test_todo, f, indent=2, ensure_ascii=False)

    print_check("Test TODO created", todo_file.exists(), str(todo_file))

    # Create test idea
    test_idea = {
        "type": "idea",
        "content": "IDEA: Create an automated personal assistant using Telegram and Claude",
        "timestamp": datetime.now().isoformat(),
        "user_id": 12345,
        "username": "test_user",
    }

    idea_file = (
        incoming_dir / f"idea_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(idea_file, "w", encoding="utf-8") as f:
        json.dump(test_idea, f, indent=2, ensure_ascii=False)

    print_check("Test IDEA created", idea_file.exists(), str(idea_file))


def test_startup_script():
    """Test the startup script"""
    print_section("Startup Script")

    startup_script = Path("start_bridge.bat")
    print_check("Startup script exists", startup_script.exists())

    if startup_script.exists():
        with open(startup_script, "r") as f:
            content = f.read()

        # Check if script has correct path
        has_correct_path = "TelegramObsidianBridge" in content
        print_check("Script has correct path", has_correct_path)

        has_venv_activation = "venv\\Scripts\\activate" in content
        print_check("Script activates venv", has_venv_activation)

        has_main_py = "main.py" in content
        print_check("Script runs main.py", has_main_py)


def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE TELEGRAM-OBSIDIAN BRIDGE TEST")
    print("Based on the implementation walkthrough")
    print(f"Started at: {datetime.now()}")

    # Ensure we're in the right directory
    project_dir = Path(
        "c:/Users/giova/OneDrive/Documents/AIU/VSC_Projects/TelegramObsidianBridge"
    )
    if Path.cwd() != project_dir:
        print(f"Changing directory to: {project_dir}")
        os.chdir(project_dir)

    # Run all tests
    test_basic_setup()
    config = test_configuration()
    test_whisper_transcription(config)
    test_telegram_bot_structure()
    test_mcp_server()
    test_content_processing()
    test_obsidian_integration(config)
    create_test_content()
    test_startup_script()

    print_section("Test Summary")
    print("✅ If all items above show ✅, your system is ready!")
    print("❌ If you see ❌ items, please address them before running.")
    print("\n🚀 Next steps:")
    print("1. Start the bridge: Double-click 'start_bridge.bat'")
    print("2. Test with Telegram messages")
    print("3. Process content through Claude Desktop")
    print("4. Check results in Obsidian")


if __name__ == "__main__":
    main()
