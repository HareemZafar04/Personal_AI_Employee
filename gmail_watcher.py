"""
Gmail Watcher for AI Employee

Monitors Gmail for new emails and creates action items in Needs_Action.
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import os
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/gmail_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcher:
    """Watches Gmail for new messages and creates action items."""

    def __init__(self, credentials_path='client_secret_754978810874-nii4jlgmal5i8aoq39e068i9mtjt7u8o.apps.googleusercontent.com.json'):
        self.credentials_path = Path(credentials_path)
        self.needs_action_path = Path("Needs_Action")
        self.processed_ids = set()
        self.service = None

        # Create necessary directories
        self.needs_action_path.mkdir(exist_ok=True)

        # Initialize Gmail service
        self.authenticate_gmail()

    def authenticate_gmail(self):
        """Authenticate with Gmail API."""
        creds = None

        # The file token.json stores the user's access and refresh tokens.
        token_path = Path('token.json')
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    # If refresh fails, delete token and re-authenticate
                    if token_path.exists():
                        token_path.unlink()
                    creds = None

            if not creds:
                if not self.credentials_path.exists():
                    logger.error(f"Credentials file not found at {self.credentials_path}")
                    logger.info("Please follow the Google API setup instructions to create credentials.json")
                    return

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail authentication successful")

    def check_for_new_emails(self, query='is:unread'):
        """Check for new emails matching the query."""
        if not self.service:
            logger.error("Gmail service not initialized")
            return []

        try:
            # Get list of unread messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10  # Limit to 10 messages to avoid overwhelming the system
            ).execute()

            messages = results.get('messages', [])
            new_messages = []

            for message in messages:
                msg_id = message['id']
                if msg_id not in self.processed_ids:
                    try:
                        # Get the full message
                        msg = self.service.users().messages().get(
                            userId='me',
                            id=msg_id,
                            format='full'
                        ).execute()

                        new_messages.append(msg)
                        self.processed_ids.add(msg_id)
                    except HttpError as e:
                        logger.error(f"Error retrieving message {msg_id}: {e}")

            return new_messages

        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            return []

    def extract_email_data(self, message):
        """Extract relevant data from an email message."""
        headers = {header['name']: header['value']
                  for header in message['payload'].get('headers', [])}

        # Extract body
        body = ""
        payload = message.get('payload', {})
        parts = payload.get('parts', [])

        # If no parts, try to get body from payload directly
        if not parts:
            body_data = payload.get('body', {}).get('data', '')
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
        else:
            # Look for the text/plain part
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    body_data = part.get('body', {}).get('data', '')
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    break
            # If no text/plain part, look for text/html part
            if not body:
                for part in parts:
                    if part.get('mimeType') == 'text/html':
                        body_data = part.get('body', {}).get('data', '')
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break

        # Create email data dictionary
        email_data = {
            'id': message['id'],
            'thread_id': message.get('threadId', ''),
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', 'Unknown'),
            'subject': headers.get('Subject', 'No Subject'),
            'date': headers.get('Date', ''),
            'body': body[:1000],  # Limit body to first 1000 characters to avoid huge files
            'size': message.get('sizeEstimate', 0),
            'labels': message.get('labelIds', []),
            'snippet': message.get('snippet', '')
        }

        return email_data

    def create_action_file(self, email_data):
        """Create an action file in the Needs_Action folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_id_short = email_data['id'][:8]  # Use first 8 chars of email ID
        action_filename = f"EMAIL_{timestamp}_{email_id_short}.md"
        action_filepath = self.needs_action_path / action_filename

        # Determine priority based on labels
        priority = "medium"
        if "IMPORTANT" in email_data['labels'] or "CATEGORY_UPDATES" in email_data['labels']:
            priority = "high"
        elif "CATEGORY_SOCIAL" in email_data['labels'] or "CATEGORY_PROMOTIONS" in email_data['labels']:
            priority = "low"

        # Check for urgent keywords
        urgent_keywords = ["urgent", "asap", "emergency", "payment", "invoice", "immediate"]
        email_content = f"{email_data['subject']} {email_data['body']}".lower()
        if any(keyword in email_content for keyword in urgent_keywords):
            priority = "high"

        action_content = f"""---
type: email
priority: {priority}
status: pending
email_id: {email_data['id']}
thread_id: {email_data['thread_id']}
received: {datetime.now().isoformat()}
---

# New Email Received

## Email Details
- **From:** {email_data['from']}
- **To:** {email_data['to']}
- **Subject:** {email_data['subject']}
- **Date:** {email_data['date']}
- **Size:** {email_data['size']} bytes

## Email Content
{email_data['body']}

## Actions Required
- [ ] Review email content
- [ ] Determine appropriate response based on Company_Handbook.md
- [ ] Respond if necessary (follow approval requirements for sensitive actions)
- [ ] Flag for follow-up if needed
- [ ] Move to Done when processed

## Processing Notes
Based on the Company Handbook:
- High priority emails should be responded to within 2 hours
- Payment/invoice emails require special handling
- All responses should be professional and polite
"""

        try:
            action_filepath.write_text(action_content)
            logger.info(f"Created email action file: {action_filepath.name}")
            return action_filepath
        except Exception as e:
            logger.error(f"Failed to create action file: {e}")
            return None

    def run(self):
        """Main loop to continuously monitor Gmail."""
        logger.info("Starting Gmail Watcher...")

        while True:
            try:
                # Check for new emails
                new_emails = self.check_for_new_emails()

                # Process each new email
                for email in new_emails:
                    email_data = self.extract_email_data(email)
                    self.create_action_file(email_data)

                if new_emails:
                    logger.info(f"Processed {len(new_emails)} new emails")

                # Wait before checking again (check every 2 minutes)
                time.sleep(120)

            except KeyboardInterrupt:
                logger.info("Gmail Watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Gmail Watcher: {e}")
                # Wait before retrying to avoid rapid error loops
                time.sleep(60)

def main():
    """Main function to run the Gmail Watcher."""
    try:
        watcher = GmailWatcher()
        watcher.run()
    except Exception as e:
        logger.error(f"Failed to start Gmail Watcher: {e}")

if __name__ == "__main__":
    main()