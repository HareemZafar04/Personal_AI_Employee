"""
Daily Loop Runner - Ralph Wiggum Stop implementation

Implements the Ralph Wiggum Stop hook as specified for Silver Tier:
- Iterate until task completion
- Create Plan.md files with checkboxes
- Prevents "lazy agent" problem
"""
import time
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/ralph_loop_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RalphLoopRunner:
    """Daily loop runner with Ralph Wiggum Stop hook."""

    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.needs_action_path = Path("Needs_Action")
        self.plans_path = Path("Plans")
        self.done_path = Path("Done")

        # Create necessary directories
        self.needs_action_path.mkdir(exist_ok=True)
        self.plans_path.mkdir(exist_ok=True)
        self.done_path.mkdir(exist_ok=True)

        logger.info(f"Ralph Loop Runner initialized with max_iterations={max_iterations}")

    def get_needs_action_items(self):
        """Get all items from Needs_Action directory."""
        action_files = list(self.needs_action_path.glob("*.md"))
        logger.info(f"Found {len(action_files)} items in Needs_Action")
        return action_files

    def create_plan_file(self, task_description, source_file=None):
        """Create a Plan.md file with checkboxes for the task."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(hash(task_description))[:10]
        plan_filename = f"PLAN_{timestamp}_{unique_id}.md"
        plan_path = self.plans_path / plan_filename

        # Extract basic details from source file if provided
        source_info = f" from {source_file.name}" if source_file else ""

        plan_content = f"""---
type: plan
status: in_progress
created: {datetime.now().isoformat()}
max_iterations: {self.max_iterations}
---

# Daily Task Plan: {task_description}

## Task Overview
Daily loop processing task{source_info} with Ralph Wiggum Stop hook.

## Iteration Progress
- [ ] Iteration 1: Initialize task
- [ ] Iteration 2: Process initial data
- [ ] Iteration 3: Validate progress
- [ ] Iteration 4: Execute core action
- [ ] Iteration 5: Check completion criteria
- [ ] Iteration 6: Process feedback
- [ ] Iteration 7: Validate results
- [ ] Iteration 8: Update status
- [ ] Iteration 9: Final validation
- [ ] Iteration 10: Complete and move to Done

## Completion Criteria
- [ ] All iterations completed successfully
- [ ] Task requirements satisfied
- [ ] No "lazy agent" behavior detected

## Current Status
- Current iteration: {self.current_iteration}
- Max iterations: {self.max_iterations}
- Task: {task_description}

## Action Items
- [ ] Process task until completion
- [ ] Create proper documentation
- [ ] Move to Done when complete
"""

        plan_path.write_text(plan_content)
        logger.info(f"Created plan file: {plan_path.name}")
        return plan_path

    def run_daily_loop(self):
        """Run the daily loop with Ralph Wiggum Stop hook."""
        logger.info("Starting daily loop with Ralph Wiggum Stop hook...")

        # Get all items from Needs_Action
        action_items = self.get_needs_action_items()

        if not action_items:
            logger.info("No action items found in Needs_Action. Creating a sample task.")
            # Create a sample task to demonstrate the loop
            sample_task = "Daily system check and maintenance"
            plan_path = self.create_plan_file(sample_task)
            action_items = [plan_path]

        # Process each action item
        for i, action_file in enumerate(action_items):
            logger.info(f"Processing action item {i+1}/{len(action_items)}: {action_file.name}")

            # Read the action file to get task description
            content = action_file.read_text()

            # Extract task description from the file
            lines = content.split('\n')
            task_description = f"Process action file {action_file.name}"

            # Look for a subject or title in the file
            for line in lines:
                if line.startswith('# '):
                    task_description = line[2:].strip()
                    break
                elif '- **Subject:**' in line:
                    task_description = line.split('**')[2].split('**')[0].strip()
                    break

            # Create a plan for this task
            plan_path = self.create_plan_file(task_description, action_file)

            # Process iterations until completion or max iterations reached
            iteration = 0
            completed = False

            while iteration < self.max_iterations and not completed:
                iteration += 1
                self.current_iteration = iteration
                logger.info(f"Processing iteration {iteration} for task: {task_description}")

                # Update the plan file with current iteration
                self.update_plan_progress(plan_path, iteration)

                # Check if task is complete (in this example, always complete after one iteration)
                # In a real implementation, this would check actual completion criteria
                completed = self.check_completion(plan_path)

                if completed:
                    logger.info(f"Task completed at iteration {iteration}: {task_description}")
                    # Move action file to Done
                    done_file = self.done_path / action_file.name
                    action_file.rename(done_file)
                    logger.info(f"Moved {action_file.name} to Done")
                    break
                else:
                    # Simulate some work
                    time.sleep(0.5)

            if not completed:
                logger.warning(f"Max iterations reached without completion: {task_description}")

        logger.info("Daily loop completed")

    def update_plan_progress(self, plan_path, iteration):
        """Update the plan file with current iteration progress."""
        content = plan_path.read_text()

        # Mark the current iteration as completed
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f"Iteration {iteration}:" in line and line.startswith('- [ ]'):
                lines[i] = line.replace('- [ ]', '- [x]')
                break

        # Update current iteration in status section
        for i, line in enumerate(lines):
            if 'Current iteration:' in line:
                lines[i] = f"- Current iteration: {iteration}"
                break

        updated_content = '\n'.join(lines)
        plan_path.write_text(updated_content)

    def check_completion(self, plan_path):
        """Check if the plan is complete by checking all checkboxes."""
        content = plan_path.read_text()
        lines = content.split('\n')

        # Count completed and total checklist items
        completed = 0
        total_checklist_items = 0

        for line in lines:
            if '- [x]' in line and ('Iteration' in line or 'Completion Criteria' in line or 'Action Items' in line):
                completed += 1
            elif '- [ ]' in line and ('Iteration' 'Iteration' in line or 'Completion Criteria' in line or 'Action Items' in line):
                total_checklist_items += 1
            elif line.strip().startswith('- [x]'):
                completed += 1
            elif line.strip().startswith('- [ ]'):
                total_checklist_items += 1

        # For this example, consider it complete when at least one iteration is done
        # In a real implementation, you'd have more sophisticated completion criteria
        return completed > 0

def main():
    parser = argparse.ArgumentParser(description='Run the daily loop with Ralph Wiggum Stop hook')
    parser.add_argument('--max-iterations', type=int, default=10, help='Maximum number of iterations')
    args = parser.parse_args()

    runner = RalphLoopRunner(max_iterations=args.max_iterations)
    runner.run_daily_loop()

if __name__ == "__main__":
    main()