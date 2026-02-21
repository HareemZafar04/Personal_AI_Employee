---
skill_name: create_plan
type: planning
category: automation
description: Generate plans from Needs_Action, follow handbook guidelines
parameters:
  - name: action_file
    type: string
    description: Path to the action file in Needs_Action
    required: true
  - name: output_plan
    type: string
    description: Path for the output plan file
    required: false
    default: "Plans/Plan_{{timestamp}}.md"
hooks:
  - name: handbook_compliance
    type: validation
    trigger: before_creation
    condition: validate_against_handbook
    description: Ensures plan follows Company_Handbook.md guidelines
---

# Create Plan Skill

## Purpose
Generate detailed plans from action files in Needs_Action, ensuring compliance with the Company_Handbook.md guidelines.

## Functionality
- Reads action files from the Needs_Action directory
- Generates detailed plans with steps and progress indicators
- Ensures all plans follow Company_Handbook.md guidelines
- Creates Plan.md files with checkboxes for tracking

## Process
1. Parse the action file from Needs_Action
2. Extract key information (priority, type, description)
3. Consult Company_Handbook.md for relevant guidelines
4. Generate a structured plan with actionable steps
5. Include approval requirements where necessary
6. Create Plan.md file with checkboxes

## Example Usage
```
claude skill create_plan "Needs_Action/EMAIL_20241201_123456.md"
```

## Plan Structure
Each generated plan includes:
- Task summary
- Priority level
- Required resources
- Step-by-step action items with checkboxes
- Approval requirements
- Timeline estimates
- Success criteria

## Handbook Compliance
The plan generation process consults Company_Handbook.md to ensure:
- Proper priority levels are maintained
- Approval requirements are followed
- Response protocols are observed
- Security protocols are maintained
- Working hours guidelines are respected