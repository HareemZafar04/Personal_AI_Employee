"""
Human-in-the-Loop Approval System for AI Employee

Monitors for approval requests and processes them when approved.
"""
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import shutil
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/approval_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ApprovalSystem:
    """Manages the human-in-the-loop approval workflow."""

    def __init__(self):
        self.pending_approval_dir = Path("Pending_Approval")
        self.approved_dir = Path("Approved")
        self.rejected_dir = Path("Rejected")
        self.done_dir = Path("Done")
        self.needs_action_dir = Path("Needs_Action")

        # Create necessary directories
        for dir_path in [self.pending_approval_dir, self.approved_dir, self.rejected_dir, self.done_dir, self.needs_action_dir]:
            dir_path.mkdir(exist_ok=True)

        # Email MCP server will be initialized when needed
        self.email_server = None

    def check_for_approvals(self) -> int:
        """Check for approval requests and process approved ones."""
        approval_files = list(self.pending_approval_dir.glob("*.md"))
        processed = 0

        for file_path in approval_files:
            try:
                # Read the approval request
                content = file_path.read_text()

                # Check if this file has been approved (exists in Approved folder)
                approved_file = self.approved_dir / file_path.name
                if approved_file.exists():
                    # Process the approved request
                    success = self.process_approved_request(file_path, content)
                    if success:
                        # Move both original and approved files to Done
                        done_file = self.done_dir / file_path.name
                        shutil.move(file_path, done_file)
                        shutil.move(approved_file, self.done_dir / approved_file.name)
                        logger.info(f"Processed and moved approved request: {file_path.name}")
                        processed += 1
                    else:
                        logger.error(f"Failed to process approved request: {file_path.name}")
                else:
                    # Check if this file has been rejected (exists in Rejected folder)
                    rejected_file = self.rejected_dir / file_path.name
                    if rejected_file.exists():
                        # Move both original and rejected files to Done
                        done_file = self.done_dir / file_path.name
                        shutil.move(file_path, done_file)
                        shutil.move(rejected_file, self.done_dir / rejected_file.name)
                        logger.info(f"Rejected and moved request: {file_path.name}")
                        processed += 1

            except Exception as e:
                logger.error(f"Error processing approval file {file_path}: {e}")

        return processed

    def process_approved_request(self, file_path: Path, content: str) -> bool:
        """Process an approved request based on its type."""
        try:
            # Determine the type of request from the file content
            if "---" in content:
                # Parse front matter
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    front_matter = parts[1]
                    # Parse YAML-like front matter
                    front_matter_dict = self._parse_front_matter(front_matter)
                    request_type = front_matter_dict.get('type', 'unknown')
                else:
                    request_type = 'unknown'
            else:
                request_type = 'unknown'

            logger.info(f"Processing {request_type} request: {file_path.name}")

            if request_type == 'email_approval_request':
                return self._process_email_approval(file_path, content)
            elif request_type == 'payment_approval_request':
                return self._process_payment_approval(file_path, content)
            elif request_type == 'action_approval_request':
                return self._process_action_approval(file_path, content)
            else:
                logger.warning(f"Unknown request type: {request_type}")
                return False

        except Exception as e:
            logger.error(f"Error processing approved request {file_path}: {e}")
            return False

    def _parse_front_matter(self, front_matter: str) -> Dict[str, Any]:
        """Parse front matter from markdown file."""
        result = {}
        for line in front_matter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                result[key] = value
        return result

    def _process_email_approval(self, file_path: Path, content: str) -> bool:
        """Process an approved email request."""
        # Extract email details from the content
        lines = content.split('\n')
        to_addresses = []
        subject = ""
        body = ""
        extracting_body = False
        body_lines = []

        for line in lines:
            if line.strip().startswith('- **To:**'):
                to_match = re.search(r'- \*\*To:\*\* (.+)', line)
                if to_match:
                    to_text = to_match.group(1)
                    # Split multiple addresses if comma-separated
                    to_addresses = [addr.strip().strip('\'"') for addr in to_text.split(',')]
            elif line.strip().startswith('- **Subject:**'):
                subject_match = re.search(r'- \*\*Subject:\*\* (.+)', line)
                if subject_match:
                    subject = subject_match.group(1)
            elif line.strip() == '**Body:**':
                extracting_body = True
                continue
            elif extracting_body:
                if line.startswith('## ') or line.startswith('# '):
                    # End of body reached
                    extracting_body = False
                    break
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        if not to_addresses or not subject or not body:
            logger.error(f"Could not extract email details from {file_path.name}")
            return False

        # Initialize the email server when needed
        if not self.email_server:
            try:
                from email_mcp_server import EmailMcpServer
                self.email_server = EmailMcpServer()
            except Exception as e:
                logger.error(f"Could not initialize email server: {e}")
                return False

        if self.email_server:
            try:
                result = self.email_server.send_email(
                    to=to_addresses,
                    subject=subject,
                    body=body
                )
                logger.info(f"Email sent successfully: {result}")
                return True
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                return False
        else:
            logger.error("Email server not available")
            return False

    def _process_payment_approval(self, file_path: Path, content: str) -> bool:
        """Process an approved payment request."""
        # This is a placeholder - in a real implementation, you would connect to
        # payment APIs to execute the payment
        logger.info(f"Processing payment approval for {file_path.name}")

        # Extract payment details and process them
        # In a real implementation, you would use actual payment processing APIs
        logger.info("Payment processed successfully")
        return True

    def _process_action_approval(self, file_path: Path, content: str) -> bool:
        """Process an approved general action request."""
        logger.info(f"Processing action approval for {file_path.name}")

        # In a real implementation, you would determine what action to take
        # based on the content of the approval request

        # For now, just log that the action was processed
        logger.info("Action processed successfully")
        return True

    def create_approval_request(self, request_type: str, details: Dict[str, Any], reason: str = "") -> Path:
        """Create a new approval request."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        request_id = abs(hash(str(details)[:10])) % 10000  # Simple ID generation
        approval_filename = f"APPROVAL_REQUEST_{request_type.upper()}_{timestamp}_{request_id:04d}.md"
        approval_filepath = self.pending_approval_dir / approval_filename

        approval_content = f"""---
type: {request_type}_approval_request
status: pending
created: {datetime.now().isoformat()}
expires: {datetime.now().replace(day=datetime.now().day+7).isoformat()}
request_id: {request_id:04d}
---

# Approval Request

## Request Type
{request_type.replace('_', ' ').title()}

## Request Details
"""
        for key, value in details.items():
            approval_content += f"- **{key.replace('_', ' ').title()}:** {value}\n"

        if reason:
            approval_content += f"\n## Reason for Approval\n{reason}\n"

        approval_content += f"""
## Actions Required
- [ ] Review the above details
- [ ] Verify this action is appropriate
- [ ] Move this file to `Approved` folder to proceed
- [ ] Or move to `Rejected` folder to cancel

## Created By
AI Employee Approval System
"""

        approval_filepath.write_text(approval_content)
        logger.info(f"Created approval request: {approval_filepath.name}")
        return approval_filepath

    def monitor_approval_folders(self):
        """Monitor the Approved and Rejected folders for changes."""
        # This method would typically use file system monitoring
        # For now, we'll just call check_for_approvals which handles this logic
        pass

    def run(self):
        """Main loop to continuously monitor for approvals."""
        logger.info("Starting Approval System...")

        while True:
            try:
                # Check for and process any approved or rejected requests
                processed = self.check_for_approvals()

                if processed > 0:
                    logger.info(f"Processed {processed} approval requests")

                # Wait before checking again (check every 30 seconds)
                time.sleep(30)

            except KeyboardInterrupt:
                logger.info("Approval System stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Approval System: {e}")
                # Wait before retrying to avoid rapid error loops
                time.sleep(60)

def main():
    """Main function to demonstrate approval system functionality."""
    try:
        approval_system = ApprovalSystem()

        # Example: Create a sample approval request
        sample_details = {
            "recipient": "client@example.com",
            "amount": "$1,500",
            "description": "Payment for completed project",
            "deadline": "2026-02-20"
        }

        approval_file = approval_system.create_approval_request(
            "payment",
            sample_details,
            "Large payment request requiring approval per Company Handbook policy"
        )

        print(f"Created sample approval request: {approval_file.name}")

        # Example: Create an email approval request
        email_details = {
            "to": "client@example.com",
            "subject": "Project Update and Next Steps",
            "body_length": "250 characters"
        }

        email_approval_file = approval_system.create_approval_request(
            "email",
            email_details,
            "Client communication requiring approval"
        )

        print(f"Created sample email approval request: {email_approval_file.name}")

        print("Approval system is ready to monitor for approvals.")

        # Uncomment the following line to run the monitoring loop continuously
        # approval_system.run()

    except Exception as e:
        logger.error(f"Error in approval system demo: {e}")

if __name__ == "__main__":
    main()