# Plan GitHub Issue

Read and plan the implementation for GitHub issue #$ARGUMENTS.

## Instructions

1. **Fetch the issue** using `gh issue view $ARGUMENTS` to get the full issue details including title, body, labels, and any comments.

2. **Summarize your understanding** of what the issue is asking for. Ask clarifying questions immediately if the issue description is ambiguous or incomplete - don't proceed until you understand the requirements.

3. **Explore the codebase** to understand:
   - Which files/components are affected
   - How the current implementation works
   - What tests already exist for related functionality

   As you explore, ask clarifying questions inline whenever you encounter ambiguity about intended behavior, scope, or approach. Don't batch questions - ask them as they arise so answers can inform subsequent exploration.

4. **Plan implementation in TDD stripes** using red-green-refactor:
   - Break the work into small, incremental slices
   - Each stripe should be completable in one focused session
   - For each stripe, specify:
     - **Red**: What test(s) to write first (describing expected behavior)
     - **Green**: Minimal implementation to make tests pass
     - **Refactor**: Any cleanup or improvements (if needed)

5. **Present the plan** with:
   - A summary of the approach
   - Numbered stripes with clear scope
   - Any risks or considerations
   - Suggested commit points

## Output Format

```
## Issue Summary
[Brief description of what needs to be done]

## Affected Files
[List of files that will likely need changes]

## Implementation Plan

### Stripe 1: [Description]
- **Red**: Write test for [specific behavior]
- **Green**: Implement [minimal change]
- **Refactor**: [cleanup if needed]
- **Commit**: "[commit message]"

### Stripe 2: [Description]
...
```

Wait for my confirmation before starting implementation.
