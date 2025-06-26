from fastmcp import FastMCP
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

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


def move_processed_file(source_path):
    """Move a processed file to the archive directory"""
    try:
        source = Path(source_path)
        if not source.exists():
            logger.warning(f"Source file not found: {source}")
            return

        archive_dir = CONTENT_DIR / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        dest = archive_dir / source.name
        counter = 1
        while dest.exists():
            stem = source.stem
            suffix = source.suffix
            dest = archive_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        source.rename(dest)
        logger.info(f"Moved {source} to {dest}")
    except Exception as e:
        logger.error(f"Failed to move file {source_path}: {e}")


def format_content_for_obsidian(
    content: str, content_type: str, additional_context: str = ""
) -> str:
    """Format content for Obsidian - shared function used by both individual and batch processing"""
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
"""

    return formatted


def save_formatted_content(formatted_content: str, content_type: str) -> str:
    """Save formatted content to ready-for-obsidian directory and return the file path"""
    timestamp = datetime.now()
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
        raise Exception(f"Failed to create directory: {e}")

    filename = f"{content_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
    output_path = ready_dir / filename

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)
        logger.info(f"File written successfully: {output_path.resolve()}")
        return str(output_path)
    except Exception as e:
        logger.error(f"Failed to write file: {e}")
        raise Exception(f"Failed to write file: {e}")


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


@mcp.tool()
async def process_for_obsidian(
    content: str,
    content_type: str,
    additional_context: str = "",
    source_file_path: str = "",
) -> str:
    """Process SINGLE item of content and format it for Obsidian

    Use this for processing individual items or when you have specific content to process.
    For multiple pending files, prefer using process_all_pending() for better efficiency.

    Args:
        content: The content to process
        content_type: Type of content (todo, voice_transcription, idea, note, link)
        additional_context: Any additional context or Claude's analysis
        source_file_path: Path to the original file (will be moved to archive if provided)
    """
    # Create the formatted content using the shared function
    formatted = format_content_for_obsidian(content, content_type, additional_context)

    # Save the formatted content to the ready-for-obsidian directory
    output_path = save_formatted_content(formatted, content_type)

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


@mcp.tool()
async def process_all_pending(auto_archive: bool = True) -> str:
    """BATCH PROCESSING: Process ALL pending content at once for maximum efficiency

    This is the PREFERRED method for processing multiple files. Use this instead of
    calling process_for_obsidian multiple times. Benefits:
    - Processes all files in one operation
    - Consistent formatting and timestamps
    - Automatic error handling and reporting
    - Bulk archiving of processed files
    - Comprehensive summary of results

    Args:
        auto_archive: Whether to automatically move processed files to archive (default: True)
    """
    try:
        processed_items = []
        error_items = []

        # Get all pending content
        for directory in [INCOMING_DIR, PROCESSED_DIR]:
            if not directory.exists():
                continue

            for file_path in directory.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                        content_type = data.get("type", "note")
                        content = data.get("content", "")
                        if content_type == "voice_transcription":
                            content = data.get("transcription", "")

                        # Generate smart context based on content type
                        if content_type == "todo":
                            context = "This is a task that needs to be organized and prioritized."
                        elif content_type == "idea":
                            context = "This is a creative idea that should be evaluated and potentially developed."
                        elif content_type == "voice_transcription":
                            context = "This was captured as a voice message and has been transcribed."
                        else:
                            context = "This is a quick capture that may need further categorization."

                        # Use the shared formatting functions
                        try:
                            formatted_content = format_content_for_obsidian(
                                content, content_type, context
                            )
                            output_file = save_formatted_content(
                                formatted_content, content_type
                            )

                            # Move the processed file to archive if requested
                            if auto_archive and file_path.exists():
                                move_processed_file(str(file_path))

                            processed_items.append(
                                {
                                    "file": file_path.name,
                                    "type": content_type,
                                    "status": "success",
                                    "output_file": output_file,
                                }
                            )

                        except Exception as e:
                            logger.error(f"Failed to process {file_path.name}: {e}")
                            processed_items.append(
                                {
                                    "file": file_path.name,
                                    "type": content_type,
                                    "status": "error",
                                    "error": str(e),
                                }
                            )

                except Exception as e:
                    error_items.append({"file": file_path.name, "error": str(e)})
                    logger.error(f"Failed to process {file_path.name}: {e}")

        return json.dumps(
            {
                "operation": "batch_processing",
                "processed": len(processed_items),
                "errors": len(error_items),
                "total_files_found": len(processed_items) + len(error_items),
                "summary": f"Batch processed {len(processed_items)} files successfully"
                + (f" with {len(error_items)} errors" if error_items else ""),
                "items": processed_items,
                "error_details": error_items if error_items else None,
                "batch_advantages": [
                    "All files processed in single operation",
                    "Consistent formatting across all items",
                    "Automatic archiving if enabled",
                    "Comprehensive error reporting",
                ],
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def analyze_content_patterns() -> str:
    """Analyze patterns in captured content for insights"""
    try:
        analysis = {
            "total_files": 0,
            "by_type": {},
            "by_hour": {},
            "recent_trends": {},
            "suggestions": [],
        }

        # Analyze all content from last 7 days
        cutoff = datetime.now() - timedelta(days=7)

        for directory in [INCOMING_DIR, PROCESSED_DIR, CONTENT_DIR / "archive"]:
            if not directory.exists():
                continue

            for file_path in directory.rglob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    timestamp_str = data.get("timestamp", "")
                    if timestamp_str:
                        time_stamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                        if time_stamp < cutoff:
                            continue

                        # Count by hour (moved inside the timestamp_str check)
                        hour = time_stamp.hour
                        analysis["by_hour"][hour] = analysis["by_hour"].get(hour, 0) + 1

                    analysis["total_files"] += 1

                    # Count by type
                    content_type = data.get("type", "unknown")
                    analysis["by_type"][content_type] = (
                        analysis["by_type"].get(content_type, 0) + 1
                    )

                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")

        # Generate suggestions
        if analysis["by_type"].get("todo", 0) > 10:
            analysis["suggestions"].append(
                "Consider setting up automated TODO prioritization"
            )

        if analysis["by_type"].get("voice_transcription", 0) > 5:
            analysis["suggestions"].append(
                "You're using voice capture frequently - great for quick thoughts!"
            )

        # Finde peak hours
        if analysis["by_hour"]:
            peak_hour = max(analysis["by_hour"], key=analysis["by_hour"].get)
            analysis["suggestions"].append(
                f"Your most active capture time is {peak_hour:02d}:00"
            )

        return json.dumps(analysis, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
