import json
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class VoiceProcessor(FileSystemEventHandler):
    def __init__(self, config, transcriber):
        self.config = config
        self.transcriber = transcriber
        self.voice_dir = Path("content/voices")
        self.processed_dir = Path("content/processed")

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Process OGG voice files
        if path.suffix == ".ogg" and path.parent == self.voice_dir:
            logger.info(f"New voice file detected: {path.name}")
            # Wait a moment for file to be fully written
            time.sleep(1)
            self.process_voice_file(path)

    def process_voice_file(self, voice_path):
        """Process a voice file"""
        meta_path = voice_path.with_suffix(".json")

        # Load metadata
        if meta_path.exists():
            with open(meta_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"timestamp": datetime.now().isoformat()}

        # Transcribe
        logger.info(f"Transcribing {voice_path.name}")
        transcription = self.transcriber.transcribe(voice_path)

        if transcription:
            # Save processed content
            processed_data = {
                "type": "voice_transcription",
                "original_file": voice_path.name,
                "transcription": transcription,
                "timestamp": metadata.get("timestamp"),
                "processed_at": datetime.now().isoformat(),
                "duration": metadata.get("duration", 0),
            }

            output_path = self.processed_dir / f"voice_{voice_path.stem}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved transcription to {output_path.name}")

            # Move voice files to archive after successful processing
            self._archive_voice_files(voice_path, meta_path, metadata, transcription)
        else:
            logger.error(f"Failed to transcribe {voice_path.name}")

    def _archive_voice_files(self, voice_path, meta_path, metadata, transcription):
        """Archive processed voice files"""
        archive_dir = Path("content/archive/voices")
        archive_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create timestamped archive names
            timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_voice = (
                archive_dir / f"{voice_path.stem}_{timestamp_suffix}{voice_path.suffix}"
            )
            archived_meta = archive_dir / f"{voice_path.stem}_{timestamp_suffix}.json"

            # Update metadata to reflect processing and archive location
            metadata["processed"] = True
            metadata["transcription_preview"] = (
                transcription[:100] + "..."
                if len(transcription) > 100
                else transcription
            )
            metadata["archived_to"] = str(archived_voice)
            metadata["archived_at"] = datetime.now().isoformat()

            # Move files
            voice_path.rename(archived_voice)
            if meta_path.exists():
                meta_path.rename(archived_meta)
                # Write updated metadata to archive
                with open(archived_meta, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
            else:
                # Create metadata file in archive if it didn't exist
                with open(archived_meta, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Archived voice files: {voice_path.name} → {archived_voice.name}"
            )
        except Exception as e:
            logger.error(f"Failed to archive voice files: {e}")
            # If archiving fails, at least log the error but don't crash

    def start_monitoring(self):
        """Start monitoring for new voice files"""
        observer = Observer()
        observer.schedule(self, str(self.voice_dir), recursive=False)
        observer.start()
        logger.info(f"Monitoring {self.voice_dir} for voice files")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
