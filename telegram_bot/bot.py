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

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get daily summary of captured content"""
        try:
            if not update.message:
                return

            today_stats = {"todos": 0, "ideas": 0, "voice": 0, "notes": 0, "links": 0}

            # Count files from today
            today_str = datetime.now().strftime("%Y%m%d")

            # Check both incoming and processed directories
            for directory in ["incoming", "processed"]:
                dir_path = self.content_dir / directory
                if not dir_path.exists():
                    continue

                for file_path in dir_path.glob(f"*{today_str}*.json"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        content_type = data.get("type", "note")
                        if content_type == "todo":
                            today_stats["todos"] += 1
                        elif content_type == "idea":
                            today_stats["ideas"] += 1
                        elif content_type in ["voice", "voice_transcription"]:
                            today_stats["voice"] += 1
                        elif content_type == "link":
                            today_stats["links"] += 1
                        else:
                            today_stats["notes"] += 1

                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {e}")

            total_items = sum(today_stats.values())

            summary_text = f"""📊 **Today's Captures** ({datetime.now().strftime("%Y-%m-%d")}):

• **TODOs**: {today_stats["todos"]}
• **Ideas**: {today_stats["ideas"]} 💡
• **Voice Notes**: {today_stats["voice"]} 🎤
• **Quick Notes**: {today_stats["notes"]} 📝
• **Links**: {today_stats["links"]} 🔗

**Total**: {total_items} items captured

Use Claude Desktop to process pending items!"""

            await update.message.reply_text(summary_text, parse_mode="Markdown")
            user_id = update.effective_user.id if update.effective_user else "unknown"
            logger.info(f"Summary requested by user {user_id}: {total_items} items")

        except Exception as e:
            logger.error(f"Error in summary command: {e}")
            if update.message:
                await update.message.reply_text(
                    "❌ Error generating summary. Check logs for details."
                )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        help_text = """🤖 **Personal Assistant Bot Commands**

**Basic Commands:**
/start - Show welcome message
/help - Show this help
/summary - Today's capture statistics
/status - System status check

**Content Types:**
• **Voice messages** 🎤 - Auto-transcribed
• **TODO:** - Task management
• **IDEA:** or 💡 - Idea capture  
• **Links** 🔗 - URL bookmarking
• **Text notes** 📝 - General notes

**Tips:**
• Use Claude Desktop to process captures
• Check your Obsidian vault under "Telegram Captures"
• Voice messages are transcribed automatically

**Support:**
Send /status if something isn't working"""

        if update.message:
            await update.message.reply_text(help_text, parse_mode="Markdown")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check system status"""
        try:
            from datetime import timedelta

            status_info = []

            # Check directories
            dirs_ok = all(
                [
                    (self.content_dir / "incoming").exists(),
                    (self.content_dir / "processed").exists(),
                    (self.content_dir / "voices").exists(),
                ]
            )
            status_info.append(f"📁 Directories: {'✅' if dirs_ok else '❌'}")

            # Check pending files
            incoming_count = len(list((self.content_dir / "incoming").glob("*.json")))
            processed_count = len(list((self.content_dir / "processed").glob("*.json")))
            status_info.append(
                f"📄 Pending: {incoming_count} | Processed: {processed_count}"
            )

            # Check recent activity
            recent_files = 0
            cutoff = datetime.now() - timedelta(hours=1)
            for dir_name in ["incoming", "processed"]:
                dir_path = self.content_dir / dir_name
                if dir_path.exists():
                    for file_path in dir_path.glob("*.json"):
                        if file_path.stat().st_mtime > cutoff.timestamp():
                            recent_files += 1

            status_info.append(f"🕐 Last hour: {recent_files} files")
            status_info.append("🤖 Bot status: ✅ Running")
            status_info.append(
                f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}"
            )

            status_text = "📊 **System Status**\n\n" + "\n".join(status_info)

            if update.message:
                await update.message.reply_text(status_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in status command: {e}")
            if update.message:
                await update.message.reply_text("❌ Error checking status. Check logs.")

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
                application.add_handler(CommandHandler("summary", self.summary))
                application.add_handler(CommandHandler("help", self.help_command))
                application.add_handler(CommandHandler("status", self.status))
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
