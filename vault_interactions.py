"""
Demonstration of Claude Code interacting with the AI Employee vault.

This script shows how Claude can read from and write to the vault structure.
"""
import json
from pathlib import Path
from datetime import datetime
import os

def read_dashboard():
    """Read the current dashboard status."""
    dashboard_path = Path("Dashboard.md")
    if dashboard_path.exists():
        content = dashboard_path.read_text()
        print("Current Dashboard Content:")
        print("=" * 40)
        print(content)
        print("=" * 40)
        return content
    else:
        print("Dashboard.md not found!")
        return None

def update_dashboard(activity=None, stats_update=None):
    """Update the dashboard with new information."""
    dashboard_path = Path("Dashboard.md")

    if not dashboard_path.exists():
        print("Creating initial Dashboard.md")
        create_initial_dashboard()

    content = dashboard_path.read_text()

    # Update the dashboard with new information
    if activity:
        # Add to Recent Activity section
        activity_line = f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {activity}"
        content = content.replace("- No recent activity", f"{activity_line}\n- No recent activity")

    if stats_update:
        # Update statistics (simplified version)
        for stat, value in stats_update.items():
            if stat == "active_tasks":
                content = content.replace("- **Active Tasks:** 0", f"- **Active Tasks:** {value}")

    # Write updated content back
    dashboard_path.write_text(content)
    print(f"Dashboard updated at {datetime.now()}")

def create_initial_dashboard():
    """Create the initial dashboard if it doesn't exist."""
    initial_content = """# AI Employee Dashboard

## Overview
Welcome to your Personal AI Employee dashboard. This system works 24/7 managing your personal and business affairs.

## Current Status
- **System Status:** Operational
- **Last Check:** {{date}}
- **Active Tasks:** 0
- **Pending Approval:** 0
- **Completed Today:** 0

## Quick Stats
- **Messages Processed:** 0
- **Tasks Completed:** 0
- **Actions Taken:** 0

## Recent Activity
- No recent activity

## Upcoming Tasks
- No upcoming tasks

## Alerts
- No alerts

---
*AI Employee v0.1 - Running 24/7*
"""
    Path("Dashboard.md").write_text(initial_content)

def process_needs_action_files():
    """Process files in the Needs_Action folder."""
    needs_action_dir = Path("Needs_Action")
    if not needs_action_dir.exists():
        print("Needs_Action directory does not exist!")
        return

    action_files = list(needs_action_dir.glob("*.md"))
    print(f"Found {len(action_files)} action files to process:")

    for file_path in action_files:
        print(f"- {file_path.name}")

        # Read the file content
        content = file_path.read_text()

        # Look for action items (checkboxes)
        lines = content.split('\n')
        unchecked_items = [line.strip() for line in lines if '- [ ]' in line]

        if unchecked_items:
            print(f"  Unchecked items: {len(unchecked_items)}")
            for item in unchecked_items:
                print(f"    {item}")

        # Example: Move file to Done after processing (commented out for safety)
        # done_path = Path("Done") / file_path.name
        # file_path.rename(done_path)
        # print(f"  Moved to Done: {done_path.name}")

def create_sample_action_file():
    """Create a sample action file to demonstrate the workflow."""
    needs_action_dir = Path("Needs_Action")
    needs_action_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SAMPLE_ACTION_{timestamp}.md"
    filepath = needs_action_dir / filename

    content = f"""---
type: sample_task
priority: low
status: pending
created: {datetime.now().isoformat()}
---

# Sample Action Task

## Description
This is a sample task to demonstrate the action file workflow.

## Action Items
- [ ] Review this task
- [ ] Perform required actions
- [ ] Update status when complete
- [ ] Move to Done folder when finished

## Instructions
This file represents how tasks flow through the system:
1. Created in Needs_Action when a trigger occurs
2. Processed by Claude according to Company_Handbook.md rules
3. Actions taken as needed
4. File moved to Done when complete

## Metadata
- Created: {datetime.now()}
- Source: vault_interactions.py demonstration
"""

    filepath.write_text(content)
    print(f"Created sample action file: {filepath.name}")

def check_vault_structure():
    """Check if the required vault structure exists."""
    required_dirs = ["Inbox", "Needs_Action", "Done", "Plans", "Pending_Approval", "Approved", "Rejected", "Logs"]
    missing_dirs = []

    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            print(f"Missing directory: {dir_name}")
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            print(f"[OK] Found directory: {dir_name}")

    if missing_dirs:
        print(f"Created {len(missing_dirs)} missing directories: {', '.join(missing_dirs)}")
    else:
        print("All required directories exist!")

    return len(missing_dirs) == 0

def main():
    """Main function to demonstrate vault interactions."""
    print("AI Employee Vault Interaction Demo")
    print("=" * 40)

    # Check vault structure
    print("\n1. Checking vault structure...")
    check_vault_structure()

    # Read current dashboard
    print("\n2. Reading current dashboard...")
    read_dashboard()

    # Create a sample action file
    print("\n3. Creating sample action file...")
    create_sample_action_file()

    # Process action files
    print("\n4. Processing action files...")
    process_needs_action_files()

    # Update dashboard with activity
    print("\n5. Updating dashboard...")
    update_dashboard(
        activity="Processed sample action file",
        stats_update={"active_tasks": 1}
    )

    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()