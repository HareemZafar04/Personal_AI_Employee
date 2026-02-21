---
skill_name: reasoning_loop
type: loop
category: planning
description: Implements Ralph Wiggum Stop hook - iterate until task complete, create Plan.md files with checkboxes.
parameters:
  - name: task
    type: string
    description: The task to be completed
    required: true
  - name: max_iterations
    type: integer
    description: Maximum number of iterations before stopping
    default: 10
hooks:
  - name: ralph_wiggum_stop
    type: conditional
    trigger: after_each_iteration
    condition: task_complete or max_iterations_reached
    description: Stop the loop when task is complete or max iterations reached
---

# Reasoning Loop Skill

## Purpose
Implements a reasoning loop with Ralph Wiggum Stop hook that iterates until a task is complete. Creates Plan.md files with checkboxes to track progress and ensure tasks are not left incomplete.

## Functionality
- Continuously evaluates the current state of a task
- Creates Plan.md files with progress indicators
- Stops iteration when the task is complete or max iterations reached
- Prevents the "lazy agent" problem where incomplete work gets lost

## Process
1. Initialize the task
2. Create a Plan.md file for the task with progress indicators
3. Execute one iteration of reasoning
4. Check if task is complete
5. If not complete, update progress indicators
6. Repeat until task is complete or max iterations reached

## Example Usage
```
claude skill reasoning_loop "Create a monthly marketing strategy" --max_iterations 5
```

## Iteration Logic
For each iteration:
- Assess current progress against the plan
- Identify next steps
- Execute next steps
- Update progress indicators
- Check completion criteria

## Preventing Lazy Agent Problem
This skill prevents the "lazy agent" problem by:
- Requiring explicit completion confirmation
- Creating accountability through progress tracking
- Forcing iteration until actual completion
- Generating follow-up tasks if needed