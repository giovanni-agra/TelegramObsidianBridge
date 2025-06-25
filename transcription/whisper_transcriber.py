import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    def __init__(self, model_path, whisper_exe_path):
        self.model_path = Path(model_path)
        self.whisper_exe = Path(whisper_exe_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        if not self.whisper_exe.exists():
            raise FileNotFoundError(f"Whisper exe not found: {self.whisper_exe}")

    def convert_ogg_to_wav(self, ogg_path):
        """Convert Telegram's OGG format to WAV using FFmpeg"""
        ogg_path = Path(ogg_path)
        wav_path = ogg_path.with_suffix(
            ".wav"
        )  # FFmpeg command to convert OGG to WAV with Whisper-optimized settings
        cmd = [
            "ffmpeg",
            "-i",
            str(ogg_path),  # Input file
            "-ar",
            "16000",  # Sample rate 16kHz (optimal for Whisper)
            "-ac",
            "1",  # Mono channel
            "-y",  # Overwrite output file
            str(wav_path),  # Output file
        ]

        try:
            logger.info(f"Converting {ogg_path.name} to WAV using FFmpeg")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully converted {ogg_path.name} to WAV")
            return wav_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error(
                "FFmpeg not found. Please install FFmpeg and add it to your PATH"
            )
            raise

    def transcribe(self, audio_path):
        """Transcribe audio file"""
        audio_path = Path(audio_path)

        # Convert if OGG
        if audio_path.suffix.lower() == ".ogg":
            wav_path = self.convert_ogg_to_wav(audio_path)
        else:
            wav_path = audio_path

        # Prepare output path
        txt_path = wav_path.with_suffix(
            ".txt"
        )  # Run Whisper - Use absolute paths for cross-directory execution
        cmd = [
            str(self.whisper_exe),
            "-m",
            str(self.model_path.resolve()),
            "-f",
            str(wav_path.resolve()),  # Use absolute path
            "-otxt",
            "-of",
            str(txt_path.with_suffix("").resolve()),  # Use absolute path
        ]

        try:
            logger.info(f"Running Whisper on {wav_path.name}")
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.whisper_exe.parent,
            )  # Set working directory

            # Read transcription
            if txt_path.exists():
                with open(txt_path, "r", encoding="utf-8") as f:
                    transcription = f.read().strip()

                # Cleanup
                txt_path.unlink()
                if audio_path.suffix.lower() == ".ogg":
                    wav_path.unlink()

                logger.info(f"Transcription complete: {len(transcription)} chars")
                return transcription
            else:
                logger.error("Transcription file not created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Whisper failed: {e.stderr}")
            return None
