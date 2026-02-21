---
skill_name: auto_post_linkedin
type: automation
category: social_media
description: Draft sales post for LinkedIn, put in Pending_Approval
parameters:
  - name: content
    type: string
    description: Content for the LinkedIn post
    required: true
  - name: target_audience
    type: string
    description: Target audience for the post
    required: false
    default: "business professionals"
  - name: hashtags
    type: array
    description: Hashtags to include in the post
    required: false
    default: ["#ai", "#automation", "#business"]
hooks:
  - name: approval_check
    type: validation
    trigger: after_draft
    condition: requires_approval
    description: Ensures post goes to Pending_Approval if needed
---

# Auto Post LinkedIn Skill

## Purpose
Drafts sales-generating content for LinkedIn and places it in Pending_Approval for review, ensuring compliance with Company_Handbook.md guidelines.

## Functionality
- Generates sales-focused content for LinkedIn
- Applies proper formatting and hashtags
- Determines approval requirements based on content type
- Places posts in Pending_Approval or auto-approves based on guidelines
- Creates action files for approval tracking

## Process
1. Analyze content requirements and target audience
2. Draft LinkedIn post following Company_Handbook.md guidelines
3. Add appropriate hashtags and tagging suggestions
4. Determine approval level based on content type
5. Create action file in Pending_Approval if required
6. Optionally publish immediately if auto-approved

## Example Usage
```
claude skill auto_post_linkedin "Discover how our AI can improve your business processes" --target_audience "marketing professionals" --hashtags "#ai #marketing #automation"
```

## Content Guidelines
The skill follows LinkedIn posting guidelines from Company_Handbook.md:
- Focus on providing value to the audience
- Avoid spammy or overly promotional language
- Include relevant hashtags
- Tag appropriate industry professionals when relevant

## Approval Logic
Based based on the Company_Handbook.md approval thresholds:
- Text-only posts under 280 characters: Conditional Approval
- Posts with financial figures: Management Approval Required
- Video/image posts: Management Approval Required
- Content with engagement targets over 500: Management Approval Required