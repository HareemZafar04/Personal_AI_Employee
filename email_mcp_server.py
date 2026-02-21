"""
Email MCP Server for AI Employee

This MCP server handles email operations for the AI Employee system.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from mcp.server import Server
from mcp.types import CallToolResult, Tool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/email_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("ai-employee-email-mcp")

class EmailMcpServer:
    """MCP server for email operations."""

    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')

        # Validate required environment variables
        if not self.email_address or not self.email_password:
            logger.error("EMAIL_ADDRESS and EMAIL_PASSWORD environment variables must be set")
            raise ValueError("Email credentials not configured")

        # Define tools for the MCP server
        self._register_tools()

    def _register_tools(self):
        """Register available tools with the MCP server."""
        servertools = [
            Tool(
                name="send_email",
                description="Send an email to one or more recipients.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of recipient email addresses"
                        },
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email body content (plain text)"},
                        "html_body": {"type": "string", "description": "HTML version of the email body (optional)"},
                        "cc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of CC email addresses (optional)"
                        },
                        "bcc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of BCC email addresses (optional)"
                        },
                        "attachments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to attach (optional)"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            ),
            Tool(
                name="send_email_with_approval",
                description="Create an approval request file for sending an email. The email will only be sent after human approval.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of recipient email addresses"
                        },
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email body content"},
                        "reason": {"type": "string", "description": "Reason why approval is needed"}
                    },
                    "required": ["to", "subject", "body", "reason"]
                }
            ),
            Tool(
                name="create_draft_email",
                description="Create a draft email and save it to the Pending_Approval folder.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of recipient email addresses"
                        },
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email body content"},
                        "folder": {"type": "string", "description": "Folder to save the draft (default: Pending_Approval)"}
                    },
                    "required": ["to", "subject", "body"]
                }
            )
        ]

        @server.list_tools()
        async def list_tools() -> List[Tool]:
            return servertools

        @server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            try:
                if name == "send_email":
                    return await self.handle_send_email(arguments)
                elif name == "send_email_with_approval":
                    return await self.handle_send_email_with_approval(arguments)
                elif name == "create_draft_email":
                    return await self.handle_create_draft_email(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(error={"message": str(e)})

    async def handle_send_email(self, args: Dict[str, Any]) -> CallToolResult:
        """Handle the send_email tool call."""
        try:
            result = self.send_email(
                to=args.get("to", []),
                subject=args.get("subject", ""),
                body=args.get("body", ""),
                html_body=args.get("html_body"),
                cc=args.get("cc", []),
                bcc=args.get("bcc", []),
                attachments=args.get("attachments", [])
            )

            return CallToolResult(content=json.dumps({"success": True, "message": result}))
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return CallToolResult(error={"message": f"Failed to send email: {str(e)}"})

    async def handle_send_email_with_approval(self, args: Dict[str, Any]) -> CallToolResult:
        """Create an approval request for sending an email."""
        try:
            result = self.create_email_approval_request(
                to=args.get("to", []),
                subject=args.get("subject", ""),
                body=args.get("body", ""),
                reason=args.get("reason", "Standard approval required")
            )

            return CallToolResult(content=json.dumps({"success": True, "message": result}))
        except Exception as e:
            logger.error(f"Error creating email approval request: {e}")
            return CallToolResult(error={"message": f"Failed to create approval request: {str(e)}"})

    async def handle_create_draft_email(self, args: Dict[str, Any]) -> CallToolResult:
        """Create a draft email in the Pending_Approval folder."""
        try:
            folder = args.get("folder", "Pending_Approval")
            result = self.create_draft_email(
                to=args.get("to", []),
                subject=args.get("subject", ""),
                body=args.get("body", ""),
                folder=folder
            )

            return CallToolResult(content=json.dumps({"success": True, "message": result}))
        except Exception as e:
            logger.error(f"Error creating draft email: {e}")
            return CallToolResult(error={"message": f"Failed to create draft email: {str(e)}"})

    def send_email(self, to: List[str], subject: str, body: str, html_body: str = None,
                   cc: List[str] = None, bcc: List[str] = None, attachments: List[str] = None) -> str:
        """Send an email using SMTP."""
        # Validate required parameters
        if not to or not subject or not body:
            raise ValueError("to, subject, and body are required")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = ', '.join(cc)

        # Add body to email
        if html_body:
            msg.attach(MIMEText(body + "\n\n" + html_body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                if Path(file_path).exists():
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())

                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {Path(file_path).name}",
                    )

                    msg.attach(part)
                else:
                    logger.warning(f"Attachment file not found: {file_path}")

        # Create SMTP session
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()  # Enable encryption
        server.login(self.email_address, self.email_password)

        # Get all recipients
        all_recipients = to.copy()
        if cc:
            all_recipients.extend(cc)
        if bcc:
            all_recipients.extend(bcc)

        # Send email
        text = msg.as_string()
        server.sendmail(self.email_address, all_recipients, text)
        server.quit()

        logger.info(f"Email sent successfully to {', '.join(to)}")
        return f"Email sent successfully to {len(to)} recipient(s)"

    def create_email_approval_request(self, to: List[str], subject: str, body: str, reason: str) -> str:
        """Create an email approval request in the Pending_Approval folder."""
        pending_approval_dir = Path("Pending_Approval")
        pending_approval_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        approval_filename = f"EMAIL_APPROVAL_{timestamp}.md"
        approval_filepath = pending_approval_dir / approval_filename

        approval_content = f"""---
type: email_approval_request
status: pending
created: {datetime.now().isoformat()}
expires: {datetime.now().replace(day=datetime.now().day+7).isoformat()}  # Expires in 7 days
---

# Email Approval Required

## Email Details
- **To:** {', '.join(to)}
- **Subject:** {subject}
- **Reason for Approval:** {reason}

## Email Content
**Subject:** {subject}

**Body:**
{body}

## Approval Instructions
To approve this email:
1. Review the content above
2. If content is acceptable, move this file to the `Approved` folder
3. The email will be sent automatically

To reject this email:
- Move this file to the `Rejected` folder

## Created By
AI Employee Email System
"""

        approval_filepath.write_text(approval_content)
        logger.info(f"Created email approval request: {approval_filepath.name}")
        return f"Approval request created: {approval_filepath.name}"

    def create_draft_email(self, to: List[str], subject: str, body: str, folder: str = "Pending_Approval") -> str:
        """Create a draft email in the specified folder."""
        draft_dir = Path(folder)
        draft_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_filename = f"DRAFT_EMAIL_{timestamp}.md"
        draft_filepath = draft_dir / draft_filename

        draft_content = f"""---
type: email_draft
status: draft
created: {datetime.now().isoformat()}
---

# Draft Email

## Email Details
- **To:** {', '.join(to)}
- **Subject:** {subject}

## Email Content
{body}

## Instructions
- Review and edit as needed
- When ready to send, move to `Approved` folder
- Or delete to cancel

## Created By
AI Employee Email System
"""

        draft_filepath.write_text(draft_content)
        logger.info(f"Created draft email: {draft_filepath.name}")
        return f"Draft email created: {draft_filepath.name}"

def main():
    """Run the MCP server."""
    import sys

    # Initialize the server
    try:
        email_server = EmailMcpServer()
        print("Email MCP Server initialized successfully")

        if email_server.email_address and email_server.email_password:
            print("✓ Email credentials configured")
        else:
            print("! Email credentials not configured (set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables)")
    except Exception as e:
        print(f"! Email MCP Server initialization error: {e}")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - just validate configuration
        print("Testing Email MCP Server configuration...")
        print("✓ Email MCP Server configuration validated")
    else:
        # In a real implementation, this would start the MCP server
        # For this demo, we'll just show that it's configured
        print("Email MCP Server is configured and ready to handle requests")
        print("Run with MCP framework to enable actual tool calls")

if __name__ == "__main__":
    main()