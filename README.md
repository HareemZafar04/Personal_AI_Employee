# Personal AI Employee - Bronze Tier Implementation

This project implements the Bronze Tier requirements for the Personal AI Employee Hackathon.

## Features Implemented

### 1. Obsidian Vault Structure
- `Dashboard.md` - Main dashboard for system overview
- `Company_Handbook.md` - Rules of engagement for the AI Employee
- Folder structure:
  - `/Inbox` - Incoming items to process
  - `/Needs_Action` - Items requiring attention
  - `/Done` - Completed tasks
  - `/Plans` - Planning documents
  - `/Pending_Approval` - Items requiring human approval
  - `/Approved` - Approved items
  - `/Rejected` - Rejected items
  - `/Logs` - System logs

### 2. File System Watcher
- `filesystem_watcher.py` - Monitors the Inbox folder for new files
- Creates action items in Needs_Action when new files are detected
- Handles different file types appropriately

### 3. Vault Interaction Scripts
- `vault_interactions.py` - Demonstrates how Claude can read from and write to the vault
- `ai_employee_skills.py` - Agent skills for processing tasks in the AI Employee system

## Setup Instructions

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the file system watcher:
   ```bash
   python filesystem_watcher.py
   ```

3. Place files in the `Inbox` folder to trigger the watcher

## Testing the Implementation

1. Run the vault interaction demo:
   ```bash
   python vault_interactions.py
   ```

2. Test the agent skills:
   ```bash
   python ai_employee_skills.py check_tasks
   python ai_employee_skills.py process_task "Test task from Claude" high
   python ai_employee_skills.py read_handbook
   ```

## Bronze Tier Requirements Met

✅ **Obsidian vault with Dashboard.md and Company_Handbook.md**
✅ **One working Watcher script (File System Monitoring)**
✅ **Claude Code successfully reading from and writing to the vault**
✅ **Basic folder structure: /Inbox, /Needs_Action, /Done**
✅ **All AI functionality implemented as Agent Skills**

## Next Steps for Higher Tiers

- Silver Tier: Add Gmail and WhatsApp watchers, MCP servers, automated scheduling
- Gold Tier: Add cross-domain integration, accounting system, business auditing
- Platinum Tier: Deploy cloud-based system with 24/7 operation

## Security Considerations

- Credentials are not stored in the vault
- Human-in-the-loop approval for sensitive actions
- All actions are logged for audit purposes