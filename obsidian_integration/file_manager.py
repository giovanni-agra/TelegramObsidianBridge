import shutil
import logging
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class ObsidianFileManager(FileSystemEventHandler):
    def __init__(self, config):
        self.vault_path = Path(config["obsidian_vault_path"])
        self.ready_dir = Path("content/ready_for_obsidian")
        self.telegram_folder = self.vault_path / "Telegram Captures"

        # Create Obsidian folders
        self.setup_vault_structure()

    def setup_vault_structure(self):
        """Create folder structure in Obsidian vault"""
        folders = [
            "Telegram Captures",
            "Telegram Captures/TODOs",
            "Telegram Captures/Ideas",
            "Telegram Captures/Voice Notes",
            "Telegram Captures/Links",
            "Telegram Captures/Archive",
        ]
        for folder in folders:
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

        logger.info(f"Vault structure ready at {self.vault_path}")

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(str(event.src_path))

        # Process markdown files ready for Obsidian
        if path.suffix == ".md" and path.parent == self.ready_dir:
            logger.info(f"New Obsidian file ready: {path.name}")
            self.move_to_obsidian(path)

    def move_to_obsidian(self, file_path):
        """Move processed file to appropriate Obsidian folder"""
        # Determine target folder based on filename
        filename = file_path.name

        if filename.startswith("todo_"):
            target_folder = self.telegram_folder / "TODOs"
        elif filename.startswith("idea_"):
            target_folder = self.telegram_folder / "Ideas"
        elif filename.startswith("voice_"):
            target_folder = self.telegram_folder / "Voice Notes"
        elif filename.startswith("link_"):
            target_folder = self.telegram_folder / "Quick Notes"
        else:
            # Default folder for other types
            target_folder = self.telegram_folder / "Archive"

        # Copy file to Obsidian
        target_path = target_folder / filename
        try:
            shutil.copy2(file_path, target_path)
            logger.info(f"Moved {filename} to Obsidian vault")

            # Archive the original
            archive_dir = Path("content/archived")
            archive_dir.mkdir(exist_ok=True)
            file_path.rename(archive_dir / filename)

        except Exception as e:
            logger.error(f"Failed to move file: {e}")

    def create_daily_note(self):
        """Create or update daily note with Telegram captures"""
        today = datetime.now()
        daily_note_path = self.vault_path / f"{today.strftime('%Y-%m-%d')}.md"

        # Count today's captures
        stats = {
            "todos": len(
                list(
                    (self.telegram_folder / "TODOs").glob(
                        f"*{today.strftime('%Y%m%d')}*.md"
                    )
                )
            ),
            "ideas": len(
                list(
                    (self.telegram_folder / "Ideas").glob(
                        f"*{today.strftime('%Y%m%d')}*.md"
                    )
                )
            ),
            "voice": len(
                list(
                    (self.telegram_folder / "Voice Notes").glob(
                        f"*{today.strftime('%Y%m%d')}*.md"
                    )
                )
            ),
            "notes": len(
                list(
                    (self.telegram_folder / "Quick Notes").glob(
                        f"*{today.strftime('%Y%m%d')}*.md"
                    )
                )
            ),
        }

        telegram_section = f"""
## 📱 Telegram Captures

- TODOs: {stats["todos"]}
- Ideas: {stats["ideas"]}
- Voice Notes: {stats["voice"]}
- Quick Notes: {stats["notes"]}

### Recent Captures
![[Telegram Cpatures/TODOs]]
![[Telegram Captures/Ideas]]
"""

        # Append to daily note if it exists
        if daily_note_path.exists():
            with open(daily_note_path, "a", encoding="utf-8") as f:
                f.write(telegram_section)
        else:
            # Create new daily note
            with open(daily_note_path, "w", encoding="utf-8") as f:
                f.write(f"#{today.strftime('%Y-%m-%d')}\n\n")
                f.write(telegram_section)

    def start_monitoring(self):
        """Start monitoring for Obsidian-ready files"""
        observer = Observer()
        observer.schedule(self, str(self.ready_dir), recursive=False)
        observer.start()
        logger.info(f"Monitoring {self.ready_dir} for Obsidian files")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
