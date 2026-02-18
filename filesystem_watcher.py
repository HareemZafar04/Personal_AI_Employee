"""
File System Watcher for AI Employee

Monitors the Inbox folder for new files and creates action items in Needs_Action.
"""
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/file_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InboxHandler(FileSystemEventHandler):
    """Handles file creation events in the Inbox folder."""

    def __init__(self, needs_action_path: Path):
        self.needs_action_path = needs_action_path
        self.processed_files = set()

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Skip temporary files and files we've already processed
        if file_path.name.startswith('.') or file_path.suffix == '.tmp':
            return

        if file_path in self.processed_files:
            return

        logger.info(f"New file detected: {file_path.name}")
        self.processed_files.add(file_path)

        # Create an action file in Needs_Action
        self.create_action_file(file_path)

    def on_moved(self, event):
        """Handle file move events."""
        if event.is_directory:
            return

        file_path = Path(event.dest_path)
        logger.info(f"File moved to inbox: {file_path.name}")

        # Skip temporary files
        if file_path.name.startswith('.') or file_path.suffix == '.tmp':
            return

        if file_path in self.processed_files:
            return

        self.processed_files.add(file_path)
        self.create_action_file(file_path)

    def create_action_file(self, source_file: Path):
        """Create an action file in the Needs_Action folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        action_filename = f"FILE_ACTION_{timestamp}_{source_file.stem}.md"
        action_filepath = self.needs_action_path / action_filename

        # Create metadata for the action file
        file_size = source_file.stat().st_size
        file_ext = source_file.suffix.lower()

        # Determine file type based on extension
        if file_ext in ['.pdf', '.doc', '.docx']:
            file_type = "document"
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            file_type = "image"
        elif file_ext in ['.csv', '.xlsx']:
            file_type = "spreadsheet"
        else:
            file_type = "general"

        action_content = f"""---
type: file_drop
file_type: {file_type}
original_name: {source_file.name}
size_bytes: {file_size}
priority: medium
status: pending
created: {datetime.now().isoformat()}
---

# New File Received

## File Details
- **Original Name:** {source_file.name}
- **Size:** {file_size} bytes
- **Type:** {file_type}

## Source
- **Path:** {source_file.parent}

## Action Required
- [ ] Review file content
- [ ] Determine appropriate response
- [ ] Take necessary action
- [ ] Move to Done when complete

## File Content Preview
```
{self.get_file_preview(source_file)}
```

## Next Steps
Please review this file and determine the appropriate course of action based on company handbook guidelines.
"""

        try:
            action_filepath.write_text(action_content)
            logger.info(f"Created action file: {action_filepath.name}")
        except Exception as e:
            logger.error(f"Failed to create action file: {e}")

    def get_file_preview(self, file_path: Path, max_lines=10):
        """Get a preview of the file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        if i == max_lines:  # Only add this once
                            lines.append("... (truncated)")
                        break
                    lines.append(line.rstrip())
                return "\\n".join(lines)
        except UnicodeDecodeError:
            return f"[Binary file - {file_path.suffix} - {file_path.stat().st_size} bytes]"
        except Exception as e:
            return f"[Could not read file: {str(e)}]"

def main():
    """Main function to run the file system watcher."""
    inbox_path = Path("Inbox")
    needs_action_path = Path("Needs_Action")

    # Create directories if they don't exist
    inbox_path.mkdir(exist_ok=True)
    needs_action_path.mkdir(exist_ok=True)

    event_handler = InboxHandler(needs_action_path)
    observer = Observer()
    observer.schedule(event_handler, str(inbox_path), recursive=False)

    logger.info("Starting File System Watcher...")
    logger.info(f"Monitoring: {inbox_path.absolute()}")
    logger.info(f"Action files will be created in: {needs_action_path.absolute()}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping File System Watcher...")
        observer.stop()

    observer.join()
    logger.info("File System Watcher stopped.")

if __name__ == "__main__":
    main()