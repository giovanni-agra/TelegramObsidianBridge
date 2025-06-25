import json
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class TextProcessor(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config
        self.incoming_dir = Path("content/incoming")
        self.processed_dir = Path("content/processed")

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(str(event.src_path))

        # Process JSON text files
        if path.suffix == ".json" and path.parent == self.incoming_dir:
            logger.info(f"New text file detected: {path.name}")
            # Wait a moment for file to be fully written
            time.sleep(1)
            self.process_text_file(path)

    def process_text_file(self, text_path):
        """Process a text file by moving it to processed folder"""
        try:
            # Load the text content
            with open(text_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            # Add processing metadata
            content["processed_at"] = datetime.now().isoformat()

            # Save to processed directory
            processed_path = self.processed_dir / text_path.name
            with open(processed_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

            logger.info(f"Moved text file to processed: {text_path.name}")

            # Archive the original file
            self._archive_text_file(text_path, content)

        except Exception as e:
            logger.error(f"Failed to process text file {text_path.name}: {e}")

    def _archive_text_file(self, text_path, content):
        """Archive processed text file"""
        archive_dir = Path("content/archive/texts")
        archive_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create timestamped archive name
            timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_file = (
                archive_dir / f"{text_path.stem}_{timestamp_suffix}{text_path.suffix}"
            )

            # Update content to reflect archive location
            content["archived_to"] = str(archived_file)
            content["archived_at"] = datetime.now().isoformat()

            # Move file to archive
            text_path.rename(archived_file)

            # Write updated metadata to archive
            with open(archived_file, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)

            logger.info(f"Archived text file: {text_path.name} → {archived_file.name}")
        except Exception as e:
            logger.error(f"Failed to archive text file: {e}")

    def process_existing_files(self):
        """Process any existing files in the incoming directory"""
        if not self.incoming_dir.exists():
            return

        for file_path in self.incoming_dir.glob("*.json"):
            logger.info(f"Processing existing file: {file_path.name}")
            self.process_text_file(file_path)

    def start_monitoring(self):
        """Start monitoring for new text files"""
        # Process any existing files first
        self.process_existing_files()

        observer = Observer()
        observer.schedule(self, str(self.incoming_dir), recursive=False)
        observer.start()
        logger.info(f"Monitoring {self.incoming_dir} for text files")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
