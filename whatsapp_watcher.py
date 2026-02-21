"""
WhatsApp Watcher for AI Employee

Monitors WhatsApp Web for new messages using Playwright and creates action items.
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import json
from playwright.sync_api import sync_playwright
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/whatsapp_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhatsAppWatcher:
    """Watches WhatsApp Web for new messages and creates action items."""

    def __init__(self, session_path="whatsapp_session", needs_action_path="Needs_Action"):
        self.session_path = Path(session_path)
        self.needs_action_path = Path(needs_action_path)
        self.processed_messages = set()
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency', 'as soon as possible']

        # Create necessary directories
        self.needs_action_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)

    def authenticate_whatsapp(self):
        """Authenticate with WhatsApp Web and maintain session."""
        logger.info("Opening WhatsApp Web. Please scan QR code if prompted...")

        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=False,  # Set to True for headless operation
                viewport={'width': 1280, 'height': 800}
            )

            # Navigate to WhatsApp Web
            page = self.browser.new_page()
            page.goto('https://web.whatsapp.com')

            # Wait for user to scan QR code (or for session to load)
            page.wait_for_selector('div[data-testid="chat-list"]', timeout=30000)
            logger.info("WhatsApp Web authenticated successfully")

            self.page = page
            return True

        except Exception as e:
            logger.error(f"Failed to authenticate WhatsApp: {e}")
            return False

    def check_for_new_messages(self):
        """Check for new unread messages in WhatsApp."""
        try:
            # Get all unread chats
            unread_chats = self.page.query_selector_all('div[data-testid="default-chat"] div[aria-label^="Unread"]')

            new_messages = []

            for chat in unread_chats:
                try:
                    # Click on the chat to open it
                    chat.click()

                    # Wait a bit for messages to load
                    time.sleep(1)

                    # Get the chat title (contact name)
                    chat_title_element = self.page.query_selector('header span[dir="auto"]')
                    contact_name = chat_title_element.text_content() if chat_title_element else "Unknown Contact"

                    # Get the last few messages (unseen ones)
                    message_bubbles = self.page.query_selector_all('div.message-in, div.message-out')

                    for bubble in message_bubbles:
                        # Check if message is from contact (incoming message)
                        if 'message-in' in bubble.get_attribute('class', ''):
                            # Get message content
                            message_element = bubble.query_selector('span[data-testid="vcard-body"], span[dir="auto"], div[dir="auto"]')
                            if message_element:
                                message_text = message_element.text_content().strip()

                                # Create message data
                                message_data = {
                                    'contact': contact_name,
                                    'message': message_text,
                                    'timestamp': datetime.now().isoformat(),
                                    'priority': self._determine_priority(message_text, contact_name)
                                }

                                # Avoid processing duplicate messages
                                message_id = f"{contact_name}:{message_text[:50]}"
                                if message_id not in self.processed_messages:
                                    new_messages.append(message_data)
                                    self.processed_messages.add(message_id)

                except Exception as e:
                    logger.error(f"Error processing chat: {e}")
                    continue

            return new_messages

        except Exception as e:
            logger.error(f"Error checking for new messages: {e}")
            return []

    def _determine_priority(self, message_text, contact_name):
        """Determine priority based on keywords and context."""
        text_lower = message_text.lower()

        # Check for urgent keywords
        if any(keyword in text_lower for keyword in ['urgent', 'asap', 'emergency', 'as soon as possible']):
            return 'high'

        # Check for business-related keywords
        if any(keyword in text_lower for keyword in ['invoice', 'payment', 'money', 'bill', 'due']):
            return 'high'

        # Check for help-related keywords
        if any(keyword in text_lower for keyword in ['help', 'issue', 'problem', 'trouble']):
            return 'medium'

        # Default priority
        return 'medium'

    def create_action_file(self, message_data):
        """Create an action file in the Needs_Action folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        contact_safe = re.sub(r'[^a-zA-Z0-9]', '_', message_data['contact'][:20])  # Sanitize contact name
        action_filename = f"WHATSAPP_{timestamp}_{contact_safe}.md"
        action_filepath = self.needs_action_path / action_filename

        action_content = f"""---
type: whatsapp_message
contact: {message_data['contact']}
priority: {message_data['priority']}
status: pending
received: {message_data['timestamp']}
---

# New WhatsApp Message

## Message Details
- **Contact:** {message_data['contact']}
- **Priority:** {message_data['priority']}
- **Received:** {message_data['timestamp']}

## Message Content
{message_data['message']}

## Actions Required
- [ ] Review message content
- [ ] Determine appropriate response based on Company_Handbook.md
- [ ] Respond if necessary (respect approval requirements for sensitive actions)
- [ ] Flag for follow-up if needed
- [ ] Move to Done when processed

## Processing Notes
Based on the Company Handbook:
- High priority messages should be responded to quickly
- Payment/invoice requests require special handling
- All responses should be professional and polite
- Follow approval requirements for financial matters
"""

        try:
            action_filepath.write_text(action_content)
            logger.info(f"Created WhatsApp action file: {action_filepath.name}")
            return action_filepath
        except Exception as e:
            logger.error(f"Failed to create action file: {e}")
            return None

    def run(self):
        """Main loop to continuously monitor WhatsApp."""
        # Authenticate first
        if not self.authenticate_whatsapp():
            logger.error("Failed to authenticate with WhatsApp. Exiting.")
            return

        logger.info("Starting WhatsApp Watcher...")

        while True:
            try:
                # Check for new messages
                new_messages = self.check_for_new_messages()

                # Process each new message
                for message in new_messages:
                    self.create_action_file(message)

                if new_messages:
                    logger.info(f"Processed {len(new_messages)} new WhatsApp messages")

                # Wait before checking again (check every 30 seconds)
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("WhatsApp Watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in WhatsApp Watcher: {e}")
                # Wait before retrying to avoid rapid error loops
                time.sleep(60)

        # Clean up
        try:
            self.browser.close()
            self.playwright.stop()
        except:
            pass

def main():
    """Main function to run the WhatsApp Watcher."""
    try:
        watcher = WhatsAppWatcher()
        watcher.run()
    except Exception as e:
        logger.error(f"Failed to start WhatsApp Watcher: {e}")

if __name__ == "__main__":
    main()