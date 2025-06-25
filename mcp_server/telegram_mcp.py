from fastmcp import FastMCP
import json
import logging
from pathlib import Path
from datetime import datetime

# Initialize MCP server
mcp = FastMCP("telegram-obsidian-bridge")
logger = logging.getLogger(__name__)

# Use absolute paths instead of relative paths
script_dir = Path(
    __file__
).parent.parent  # Go up one level from mcp_server to project root
CONTENT_DIR = script_dir / "content"
PROCESSED_DIR = CONTENT_DIR / "processed"
INCOMING_DIR = CONTENT_DIR / "incoming"

# Log the resolved absolute paths for debugging
logger.info(f"Current working directory: {Path.cwd()}")
logger.info(f"Content directory: {CONTENT_DIR.resolve()}")
logger.info(f"Incoming directory: {INCOMING_DIR.resolve()}")
logger.info(f"Processed directory: {PROCESSED_DIR.resolve()}")


@mcp.tool()
async def get_pending_content(content_type: str = "all") -> str:
    """Get pending content form Telegram for processing

    Args:
        content_type: Type of content to retrieve (all, todo, voice, idea, note, link)
    """
    try:
        pending_files = []

        # Check both incoming and processed directories
        for directory in [INCOMING_DIR, PROCESSED_DIR]:
            if not directory.exists():
                continue

            for file_path in directory.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if content_type == "all" or data.get("type") == content_type:
                    data["file_path"] = str(file_path)
                    pending_files.append(data)

        # Sort by timestamp
        pending_files.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return json.dumps(
            {
                "count": len(pending_files),
                "items": pending_files[:10],  # Limit to recent 10
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Error getting pending content: {e}")
        return json.dumps({"error": str(e)})


def move_processed_file(source_file_path: str):
    """Move a processed file to the archive directory"""
    try:
        source_path = Path(source_file_path)
        if not source_path.exists():
            logger.warning(f"Source file not found: {source_path}")
            return False

        # Create archive directory
        archive_dir = CONTENT_DIR / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Move file to archive with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        archive_path = archive_dir / archive_filename

        # Move the file
        source_path.rename(archive_path)
        logger.info(f"Moved processed file: {source_path.name} → {archive_path.name}")
        return True

    except Exception as e:
        logger.error(f"Failed to move file {source_file_path}: {e}")
        return False


@mcp.tool()
async def process_for_obsidian(
    content: str,
    content_type: str,
    additional_context: str = "",
    source_file_path: str = "",
) -> str:
    """Process content and format it for Obsidian

    Args:
        content: The content to process
        content_type: Type of content (todo, voice_transcription, idea, note, link)
        additional_context: Any additional context or Claude's analysis
        source_file_path: Path to the original file (will be moved to archive)
    """
    timestamp = datetime.now()

    # Create appropriate formatting based on type
    if content_type == "todo":
        formatted = f"""---
type: todo
created: {timestamp.isoformat()}
status: open
tags: [telegram, todo]
---

# TODO: {content[:50]}...

## Task Description
{content}

## Context & Analysis
{additional_context}

## Action Steps
- [ ] Review and break down task
- [ ] Set priority and deadline
- [ ] Add to appropriate project

---
*Captured from Telegram at {timestamp.strftime("%Y-%m-%d %H:%M")}*
"""

    elif content_type == "voice_transcription":
        formatted = f"""---
type: voice-note
created: {timestamp.isoformat()}
tags: [telegram, voice, transcription]
---

# Voice Note - {timestamp.strftime("%Y-%m-%d %H:%M")}

## Transcription
{content}

## Key Points
{additional_context}

## Follow-up Actions
- [ ] Review and extract action items
- [ ] Link to relevant projects
- [ ] Archive or process further

---
*Voice message transcribed from Telegram*
"""

    elif content_type == "idea":
        formatted = f"""---
type: idea
created: {timestamp.isoformat()}
tags: [telegram, idea]
---

# 💡 Idea: {content[:50]}...

## Description
{content}

## Initial Thoughts
{additional_context}

## Next Steps
- [ ] Evaluate feasibility
- [ ] Research similar concepts
- [ ] Create action plan if viable

---
*Captured from Telegram at {timestamp.strftime("%Y-%m-%d %H:%M")}*
"""

    else:  # General note
        formatted = f"""---
type: note
created: {timestamp.isoformat()}
tags: [telegram, quick-capture]
---

# Quick Note - {timestamp.strftime("%Y-%m-%d %H:%M")}

{content}

## Additional Context
{additional_context}

---
*Captured from Telegram*
"""  # Save to ready-for-obsidian directory
    ready_dir = CONTENT_DIR / "ready_for_obsidian"

    logger.info(f"About to create directory: {ready_dir}")
    logger.info(f"CONTENT_DIR exists: {CONTENT_DIR.exists()}")
    logger.info(f"Ready dir exists: {ready_dir.exists()}")

    try:
        # Ensure parent directories exist first
        CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        ready_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ready directory ensured: {ready_dir.resolve()}")
    except Exception as e:
        logger.error(f"Failed to create ready directory: {e}")
        return json.dumps({"error": f"Failed to create directory: {e}"})

    filename = f"{content_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
    output_path = ready_dir / filename

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        logger.info(f"File written successfully: {output_path.resolve()}")
    except Exception as e:
        logger.error(f"Failed to write file: {e}")
        return json.dumps({"error": f"Failed to write file: {e}"})

    # Move the processed file to archive if a source path is provided
    if source_file_path:
        move_processed_file(source_file_path)

    return json.dumps(
        {
            "status": "success",
            "file": str(output_path),
            "preview": formatted[:200] + "...",
        }
    )


@mcp.tool()
async def get_daily_summary() -> str:
    """Get a summary of today's captures from Telegram"""
    today = datetime.now().date()
    summary = {
        "date": str(today),
        "todos": 0,
        "ideas": 0,
        "voice_notes": 0,
        "notes": 0,
        "links": 0,
    }

    # Count items from today
    for directory in [INCOMING_DIR, PROCESSED_DIR]:
        if not directory.exists():
            continue

        for file_path in directory.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            timestamp = datetime.fromisoformat(data.get("timestamp", ""))
            if timestamp.date() == today:
                content_type = data.get("type", "note")
                if content_type == "todo":
                    summary["todos"] += 1
                elif content_type == "idea":
                    summary["ideas"] += 1
                elif content_type == "voice_transcription":
                    summary["voice_notes"] += 1
                elif content_type == "link":
                    summary["links"] += 1
                else:
                    summary["notes"] += 1

    summary["total"] = sum(
        [summary[k] for k in ["todos", "ideas", "voice_notes", "notes", "links"]]
    )

    return json.dumps(summary, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
