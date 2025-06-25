import json
import logging
import time
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import NetworkError, TimedOut, RetryAfter, Conflict
import httpx

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TelegramCaptureBot:
    def __init__(self, config):
        self.config = config
        self.content_dir = Path("content")
        self.setup_directories()

    def setup_directories(self):
        """Create necessary directories"""
        dirs = ["incoming", "processed", "voices", "texts", "todos"]
        for dir_name in dirs:
            (self.content_dir / dir_name).mkdir(parents=True, exist_ok=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if update.message:
            await update.message.reply_text(
                "🤖 Personal Assistant Bot Active!\n\n"
                "Send me:\n"
                "- Voice messages 🎤\n"
                "- TODOs (start with 'TODO:')\n"
                "- Ideas (start with 'IDEA:')\n"
                "- Links 🔗\n"
                "- Any text notes 📝"
            )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        try:
            if not update.message or not update.message.text:
                return

            text = update.message.text
            timestamp = datetime.now()

            # Determine message type
            if text.startswith("TODO:") or text.startswith("Task:"):
                message_type = "todo"
            elif text.startswith("IDEA:") or "💡" in text:
                message_type = "idea"
            elif text.startswith("http") or "www." in text:
                message_type = "link"
            else:
                message_type = "note"

            filename = f"{message_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.content_dir / "incoming" / filename

            content = {
                "type": message_type,
                "content": text,
                "timestamp": timestamp.isoformat(),
                "user_id": update.effective_user.id if update.effective_user else None,
                "username": update.effective_user.username
                if update.effective_user
                else None,
                "processed": False,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {message_type}: {filename}")
            if update.message:
                await update.message.reply_text(f"✅ {message_type.title()} captured!")

        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            if update.message:
                try:
                    await update.message.reply_text(
                        "❌ Sorry, there was an error processing your message."
                    )
                except Exception:
                    pass  # Don't let reply errors crash the handler

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages"""
        try:
            if not update.message or not update.message.voice:
                return

            voice = update.message.voice
            timestamp = datetime.now()

            # Download voice file
            file = await context.bot.get_file(voice.file_id)
            filename = f"voice_{timestamp.strftime('%Y%m%d_%H%M%S')}.ogg"
            filepath = self.content_dir / "voices" / filename
            await file.download_to_drive(str(filepath))

            # Save metadata
            metadata = {
                "type": "voice",
                "filename": filename,
                "duration": voice.duration,
                "timestamp": timestamp.isoformat(),
                "user_id": update.effective_user.id if update.effective_user else None,
                "processed": False,
            }

            meta_path = filepath.with_suffix(".json")
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved voice message: {filename}")
            if update.message:
                await update.message.reply_text(
                    f"🎤 Voice message received ({voice.duration}s)\n"
                    "Processing will begin shortly..."
                )

        except Exception as e:
            logger.error(f"Error handling voice message: {e}")
            if update.message:
                try:
                    await update.message.reply_text(
                        "❌ Sorry, there was an error processing your voice message."
                    )
                except Exception:
                    pass  # Don't let reply errors crash the handler

    def run(self):
        """Start the bot with enhanced error handling and retry logic"""
        max_retries = 10
        retry_delay = 5  # Initial delay in seconds
        max_delay = 300  # Maximum delay (5 minutes)

        for attempt in range(max_retries):
            try:
                logger.info(f"Bot starting (attempt {attempt + 1}/{max_retries})...")

                # Create application with longer timeout settings
                application = (
                    Application.builder()
                    .token(self.config["telegram_bot_token"])
                    .read_timeout(30)
                    .write_timeout(30)
                    .connect_timeout(30)
                    .pool_timeout(30)
                    .build()
                )

                # Add handlers
                application.add_handler(CommandHandler("start", self.start))
                application.add_handler(
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
                )
                application.add_handler(
                    MessageHandler(filters.VOICE, self.handle_voice)
                )

                # Use run_polling with enhanced error handling
                application.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                    poll_interval=2.0,
                    timeout=20,
                )

                # If we reach here, the bot ran successfully without major errors
                logger.info("Bot shut down normally.")
                break

            except (NetworkError, TimedOut, RetryAfter, Conflict) as e:
                logger.warning(f"Telegram API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff
                else:
                    logger.error(f"Max retries ({max_retries}) reached. Bot stopping.")
                    raise

            except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning(f"HTTP connection error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff
                else:
                    logger.error(f"Max retries ({max_retries}) reached. Bot stopping.")
                    raise

            except KeyboardInterrupt:
                logger.info("Bot stopped by user.")
                break

            except Exception as e:
                logger.error(
                    f"Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {e}"
                )
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff
                else:
                    logger.error(f"Max retries ({max_retries}) reached. Bot stopping.")
                    raise

        logger.info("Bot run method completed.")


if __name__ == "__main__":
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        bot = TelegramCaptureBot(config)
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
