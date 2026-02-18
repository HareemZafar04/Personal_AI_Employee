"""
Agent Skill: AI Employee Task Processor

This skill enables Claude to process tasks within the AI Employee system.
"""
import json
from pathlib import Path
from datetime import datetime
import sys

def process_task(task_description, priority="medium"):
    """
    Process a task according to AI Employee workflow.

    Args:
        task_description (str): Description of the task to process
        priority (str): Priority level (low, medium, high)

    Returns:
        dict: Result of the task processing
    """
    # Create a task file in Needs_Action
    needs_action_dir = Path("Needs_Action")
    needs_action_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_filename = f"TASK_{timestamp}_{priority.upper()}.md"
    task_filepath = needs_action_dir / task_filename

    task_content = f"""---
type: ai_employee_task
priority: {priority}
status: pending
created: {datetime.now().isoformat()}
source: claude_agent_skill
---

# AI Employee Task

## Task Description
{task_description}

## Action Items
- [ ] Analyze task requirements
- [ ] Determine appropriate response based on Company_Handbook.md
- [ ] Execute required actions
- [ ] Update status when complete
- [ ] Move to Done when finished

## Context
- Created by Claude Code AI Employee system
- Follow guidelines in Company_Handbook.md for processing
- Respect approval requirements for sensitive actions

## Next Steps
Review this task and process according to established workflows.
"""

    task_filepath.write_text(task_content)

    result = {
        "status": "success",
        "message": f"Task created: {task_filepath.name}",
        "task_file": str(task_filepath),
        "priority": priority,
        "timestamp": datetime.now().isoformat()
    }

    return result

def check_pending_tasks():
    """
    Check for pending tasks in the system.

    Returns:
        dict: Information about pending tasks
    """
    needs_action_dir = Path("Needs_Action")
    done_dir = Path("Done")
    pending_approval_dir = Path("Pending_Approval")

    needs_action_count = len(list(needs_action_dir.glob("*.md"))) if needs_action_dir.exists() else 0
    done_count = len(list(done_dir.glob("*.md"))) if done_dir.exists() else 0
    pending_approval_count = len(list(pending_approval_dir.glob("*.md"))) if pending_approval_dir.exists() else 0

    result = {
        "status": "success",
        "needs_action_count": needs_action_count,
        "done_count": done_count,
        "pending_approval_count": pending_approval_count,
        "summary": f"Found {needs_action_count} tasks needing action, {pending_approval_count} pending approval, {done_count} completed"
    }

    return result

def read_company_handbook():
    """
    Read the company handbook to understand processing rules.

    Returns:
        dict: Contents of the company handbook
    """
    handbook_path = Path("Company_Handbook.md")

    if handbook_path.exists():
        content = handbook_path.read_text()
        result = {
            "status": "success",
            "handbook_content": content,
            "length": len(content)
        }
    else:
        result = {
            "status": "error",
            "message": "Company_Handbook.md not found",
            "handbook_content": "",
            "length": 0
        }

    return result

def update_dashboard_status(status_message, stats_update=None):
    """
    Update the dashboard with a status message.

    Args:
        status_message (str): Message to add to recent activity
        stats_update (dict): Optional statistics to update

    Returns:
        dict: Result of the update operation
    """
    dashboard_path = Path("Dashboard.md")

    if not dashboard_path.exists():
        # Create a basic dashboard if it doesn't exist
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
        dashboard_path.write_text(initial_content)

    content = dashboard_path.read_text()

    # Add the status message to Recent Activity
    new_activity = f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {status_message}"

    # Replace the first occurrence of "No recent activity" with the new activity
    if "- No recent activity" in content:
        content = content.replace("- No recent activity", f"{new_activity}\n- No recent activity", 1)
    else:
        # If there's already activity, add to the beginning of the list
        content = content.replace("## Recent Activity\n", f"## Recent Activity\n{new_activity}\n", 1)

    # Update stats if provided
    if stats_update:
        for key, value in stats_update.items():
            if key == "active_tasks":
                content = content.replace("- **Active Tasks:** 0", f"- **Active Tasks:** {value}", 1)
            elif key == "pending_approval":
                content = content.replace("- **Pending Approval:** 0", f"- **Pending Approval:** {value}", 1)
            elif key == "completed_today":
                content = content.replace("- **Completed Today:** 0", f"- **Completed Today:** {value}", 1)

    dashboard_path.write_text(content)

    result = {
        "status": "success",
        "message": "Dashboard updated successfully",
        "dashboard_file": str(dashboard_path)
    }

    return result

def main():
    """Main function for testing the agent skills."""
    if len(sys.argv) < 2:
        print("Usage: python ai_employee_skills.py <command> [args]")
        print("Commands: process_task, check_tasks, read_handbook, update_dashboard")
        return

    command = sys.argv[1]

    if command == "process_task":
        if len(sys.argv) < 3:
            print("Usage: python ai_employee_skills.py process_task <task_description> [priority]")
            return

        task_desc = sys.argv[2]
        priority = sys.argv[3] if len(sys.argv) > 3 else "medium"

        result = process_task(task_desc, priority)
        print(json.dumps(result, indent=2))

    elif command == "check_tasks":
        result = check_pending_tasks()
        print(json.dumps(result, indent=2))

    elif command == "read_handbook":
        result = read_company_handbook()
        print(json.dumps(result, indent=2))

    elif command == "update_dashboard":
        if len(sys.argv) < 3:
            print("Usage: python ai_employee_skills.py update_dashboard <status_message>")
            return

        status_msg = sys.argv[2]
        result = update_dashboard_status(status_msg)
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        print("Available commands: process_task, check_tasks, read_handbook, update_dashboard")

if __name__ == "__main__":
    main()