#!/usr/bin/env python3
"""
Simple test script to verify all components are working
"""

import json
import sys
from pathlib import Path


def test_content_directory():
    """Test if content directories exist and are accessible"""
    content_dir = Path("content")
    dirs_to_check = ["incoming", "processed", "voices", "texts", "todos"]

    print("🔍 Testing content directories...")
    for dir_name in dirs_to_check:
        dir_path = content_dir / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/ exists")
        else:
            print(f"  ❌ {dir_name}/ missing")

    # Check for pending content
    incoming_files = list((content_dir / "incoming").glob("*.json"))
    if incoming_files:
        print(f"  📄 Found {len(incoming_files)} pending file(s)")
        for file_path in incoming_files:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(
                f"    - {file_path.name}: {data.get('type', 'unknown')} ({data.get('timestamp', 'no timestamp')})"
            )
    else:
        print("  📄 No pending files found")


def test_config():
    """Test if configuration is valid"""
    print("\n🔍 Testing configuration...")
    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        required_keys = ["telegram_bot_token", "whisper_model_path", "whisper_exe_path"]
        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            print(f"  ❌ Missing config keys: {missing_keys}")
        else:
            print("  ✅ All required config keys present")

        # Check if model and executable exist
        model_path = Path(config.get("whisper_model_path", ""))
        if model_path.exists():
            print(f"  ✅ Whisper model found: {model_path}")
        else:
            print(f"  ⚠️  Whisper model not found: {model_path}")

        exe_path = Path(config.get("whisper_exe_path", ""))
        if exe_path.exists():
            print(f"  ✅ Whisper executable found: {exe_path}")
        else:
            print(f"  ⚠️  Whisper executable not found: {exe_path}")

    except FileNotFoundError:
        print("  ❌ config.json not found")
    except json.JSONDecodeError:
        print("  ❌ config.json is not valid JSON")


def test_imports():
    """Test if all required modules can be imported"""
    print("\n🔍 Testing Python imports...")

    modules_to_test = [
        ("telegram", "Python Telegram Bot"),
        ("mcp", "Model Context Protocol"),
        ("httpx", "HTTP client"),
        ("pathlib", "Path handling"),
        ("json", "JSON handling"),
    ]

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {description} ({module_name})")
        except ImportError:
            print(f"  ❌ {description} ({module_name}) - not installed")


def main():
    print("🧪 TelegramObsidianBridge System Test")
    print("=" * 50)

    test_imports()
    test_config()
    test_content_directory()

    print("\n📝 Summary:")
    print("If all items show ✅, the system is ready to run!")
    print("If you see ❌ items, please fix them before running the bridge.")
    print("⚠️  items are warnings but won't prevent basic functionality.")


if __name__ == "__main__":
    main()
