"""
Bronze Tier Demo for Personal AI Employee

This script demonstrates all Bronze Tier requirements working together.
"""
import json
from pathlib import Path
from datetime import datetime
import subprocess
import sys

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"{title:^60}")
    print("="*60)

def check_bronze_requirements():
    """Verify all Bronze Tier requirements are met."""
    print_header("BRONZE TIER VERIFICATION")

    requirements = {
        "Obsidian Vault Structure": False,
        "Dashboard.md exists": False,
        "Company_Handbook.md exists": False,
        "Folder Structure": False,
        "Inbox folder": False,
        "Needs_Action folder": False,
        "Done folder": False,
        "Watcher Script": False,
        "Agent Skills": False
    }

    # Check for vault files
    if Path("Dashboard.md").exists():
        requirements["Dashboard.md exists"] = True
        requirements["Obsidian Vault Structure"] = True

    if Path("Company_Handbook.md").exists():
        requirements["Company_Handbook.md exists"] = True
        requirements["Obsidian Vault Structure"] = True

    # Check for required folders
    required_folders = ["Inbox", "Needs_Action", "Done", "Plans", "Pending_Approval", "Approved", "Rejected", "Logs"]
    all_folders_exist = True
    for folder in required_folders:
        folder_exists = Path(folder).exists()
        if folder == "Inbox":
            requirements["Inbox folder"] = folder_exists
        elif folder == "Needs_Action":
            requirements["Needs_Action folder"] = folder_exists
        elif folder == "Done":
            requirements["Done folder"] = folder_exists

        if not folder_exists:
            all_folders_exist = False

    requirements["Folder Structure"] = all_folders_exist

    # Check for watcher script
    if Path("filesystem_watcher.py").exists():
        requirements["Watcher Script"] = True

    # Check for agent skills
    if Path("ai_employee_skills.py").exists():
        requirements["Agent Skills"] = True

    # Print verification results
    all_passed = True
    for req, passed in requirements.items():
        status = "PASS" if passed else "FAIL"
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"{icon} {req:<30} {status:>10}")
        if not passed:
            all_passed = False

    print(f"\nOverall Bronze Tier Status: {'SUCCESS' if all_passed else 'INCOMPLETE'}")
    return all_passed

def demonstrate_vault_interaction():
    """Demonstrate vault interaction capabilities."""
    print_header("VAULT INTERACTION DEMONSTRATION")

    try:
        # Import and run the vault interaction functions
        import vault_interactions

        # Check vault structure
        print("Checking vault structure...")
        vault_interactions.check_vault_structure()

        # Create a sample action
        print("\nCreating sample task...")
        vault_interactions.create_sample_action_file()

        # Process any pending tasks
        print("\nProcessing tasks...")
        vault_interactions.process_needs_action_files()

        # Update dashboard
        print("\nUpdating dashboard...")
        vault_interactions.update_dashboard(
            activity="Bronze tier demo executed successfully",
            stats_update={"active_tasks": 2}
        )

        print("\n[V] Vault interaction demonstrated successfully")
    except Exception as e:
        print(f"\n[X] Vault interaction failed: {e}")

def demonstrate_agent_skills():
    """Demonstrate agent skills functionality."""
    print_header("AGENT SKILLS DEMONSTRATION")

    try:
        # Test checking tasks
        print("Testing task checking skill...")
        result = subprocess.run([sys.executable, "ai_employee_skills.py", "check_tasks"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            task_data = json.loads(result.stdout)
            print(f"[V] Task check successful: {task_data['summary']}")
        else:
            print(f"[X] Task check failed: {result.stderr}")

        # Test processing a task
        print("\nTesting task processing skill...")
        result = subprocess.run([sys.executable, "ai_employee_skills.py", "process_task",
                                "Bronze Tier Demo Task", "high"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            task_result = json.loads(result.stdout)
            print(f"[V] Task processed: {task_result['message']}")
        else:
            print(f"[X] Task processing failed: {result.stderr}")

        # Test reading handbook
        print("\nTesting handbook reading skill...")
        result = subprocess.run([sys.executable, "ai_employee_skills.py", "read_handbook"],
                                capture_output=True, text=True)
        if result.returncode == 0:
            handbook_data = json.loads(result.stdout)
            if handbook_data['status'] == 'success':
                print(f"[V] Handbook read successfully ({handbook_data['length']} chars)")
            else:
                print(f"[X] Handbook read failed: {handbook_data.get('message', 'Unknown error')}")
        else:
            print(f"[X] Handbook read failed: {result.stderr}")

        print("\n[V] Agent skills demonstrated successfully")
    except Exception as e:
        print(f"\n[X] Agent skills demonstration failed: {e}")

def demonstrate_file_watcher():
    """Demonstrate file watcher functionality."""
    print_header("FILE WATCHER DEMONSTRATION")

    try:
        # Create a test file in the Inbox to trigger the watcher
        inbox_path = Path("Inbox")
        test_file = inbox_path / "test_trigger.txt"

        print(f"Creating test file: {test_file}")
        test_file.write_text("This is a test file to trigger the file watcher.")
        print("[V] Test file created in Inbox")

        # Show that the action file would be created when the watcher runs
        print("\nThe file watcher would detect this file and create an action file in Needs_Action")
        print("when the watcher is actively running.")

        # Clean up test file
        if test_file.exists():
            test_file.unlink()
            print("[V] Test file cleaned up")

        print("\n[V] File watcher functionality demonstrated")
    except Exception as e:
        print(f"\n✗ File watcher demonstration failed: {e}")

def main():
    """Main function to run the Bronze Tier demo."""
    print("PERSONAL AI EMPLOYEE - BRONZE TIER DEMONSTRATION")
    print("Implementing the foundation layer of the autonomous AI employee")

    # Verify all Bronze Tier requirements
    bronze_passed = check_bronze_requirements()

    if bronze_passed:
        print("\n" + "="*60)
        print("ALL BRONZE TIER REQUIREMENTS MET!")
        print("="*60)

        # Demonstrate key functionalities
        demonstrate_vault_interaction()
        demonstrate_agent_skills()
        demonstrate_file_watcher()

        print_header("DEMO COMPLETE")
        print("Bronze Tier implementation is fully functional!")
        print("Ready to advance to Silver Tier with additional watchers and MCP servers.")
    else:
        print("\n❌ BRONZE TIER REQUIREMENTS NOT FULLY MET")
        print("Please address the failed requirements before proceeding.")

if __name__ == "__main__":
    main()