#!/usr/bin/env python3
"""
Telegram to Claude to Obsidian Bridge
Complete automation system
"""

import json
import logging
import threading
import time
import asyncio

# Import our modules
from telegram_bot.bot import TelegramCaptureBot
from transcription.whisper_transcriber import WhisperTranscriber
from services.voice_processor import VoiceProcessor
from services.text_processor import TextProcessor
from obsidian_integration.file_manager import ObsidianFileManager

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("logs/system.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def run_telegram_bot(config):
    """Run Telegram bot in thread with proper asyncio event loop"""
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        bot = TelegramCaptureBot(config)
        bot.run()
    finally:
        loop.close()


def run_voice_processor(config):
    """Run voice processor in thread"""
    transcriber = WhisperTranscriber(
        config["whisper_model_path"], config["whisper_exe_path"]
    )
    processor = VoiceProcessor(config, transcriber)
    processor.start_monitoring()


def run_text_processor(config):
    """Run text processor in thread"""
    processor = TextProcessor(config)
    processor.start_monitoring()


def run_obsidian_manager(config):
    """Run Obsidian file manager in thread"""
    manager = ObsidianFileManager(config)
    manager.start_monitoring()


def main():
    """Main orchestrator"""
    # Load configuration
    with open("config.json", "r") as f:
        config = json.load(f)

    logger.info(
        "Starting Telegram-Claude-Obsidian Bridg..."
    )  # Start services in threads
    threads = []

    # Telegram bot thread
    bot_thread = threading.Thread(target=run_telegram_bot, args=(config,), daemon=True)
    threads.append(bot_thread)

    # Voice processor thread
    voice_thread = threading.Thread(
        target=run_voice_processor, args=(config,), daemon=True
    )
    threads.append(voice_thread)

    # Text processor thread
    text_thread = threading.Thread(
        target=run_text_processor, args=(config,), daemon=True
    )
    threads.append(text_thread)

    # Obsidian manager thread
    obsidian_thread = threading.Thread(
        target=run_obsidian_manager,
        args=(config,),
    )
    threads.append(obsidian_thread)

    # Start all threads
    for thread in threads:
        thread.start()
        logger.info(f"Started {thread.name}")

    logger.info("All services started. Press Ctrl+C to stop.")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        # Threads are daemon, so they'll stop with main


if __name__ == "__main__":
    main()
