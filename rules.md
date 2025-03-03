# LinkedIn AI Agent - Operating Rules

## Pacing and Scope Control
1. **Explicit Checkpoint Requirements**
   - You must pause after completing each logical unit of work and wait for explicit approval before continuing.
   - Never implement more than one task in a single session without confirmation.

2. **Minimalist Implementation Rule**
   - Always implement the absolute minimum to meet the specified task requirements.
   - When in doubt about scope, choose the narrower interpretation.

3. **Staged Development Protocol**
   - Follow a strict 'propose → approve → implement → review' cycle for every change.
   - After implementing each component, stop and provide a clear summary of what was changed and what remains to be done.

4. **Scope Boundary Enforcement**
   - If a task appears to require changes outside the initially identified files or components, pause and request explicit permission.
   - Never perform 'while I'm at it' improvements without prior approval.

## Communications
1. **Mandatory Checkpoints**
   - After every change, pause and summarize what you've done and what you're planning next.
   - Mark each implemented feature as [COMPLETE] and ask if you should continue to the next item.

2. **Complexity Warning System**
   - If implementation requires touching more than 3 files, flag this as [COMPLEX CHANGE] and wait for confirmation.
   - Proactively identify potential ripple effects before implementing any change.

3. **Change Magnitude Indicators**
   - Classify all proposed changes as [MINOR] (1-5 lines), [MODERATE] (5-20 lines), or [MAJOR] (20+ lines).
   - For [MAJOR] changes, provide a detailed implementation plan and wait for explicit approval.

4. **Testability Focus**
   - Every implementation must pause at the earliest point where testing is possible.
   - Never proceed past a testable checkpoint without confirmation that the current implementation works.

## LinkedIn-Specific Rules

1. **Anti-Detection Measures**
   - Never perform more than 50 profile views in a single session.
   - Maintain random delays between 1-5 seconds between any consecutive actions.
   - Implement natural scrolling patterns with variable speeds and pauses.
   - Avoid repetitive patterns in mouse movements and clicks.

2. **Data Extraction Ethics**
   - Only extract publicly available information.
   - Do not attempt to bypass LinkedIn's privacy settings.
   - Respect "Do Not Contact" indicators in profiles.
   - Store extracted data securely and in compliance with privacy regulations.

3. **Session Management**
   - Limit continuous operation to 30 minutes per session.
   - Implement automatic cooldown periods of 15+ minutes between sessions.
   - Rotate IP addresses and user agents when possible.
   - Gracefully handle and recover from rate limiting or security challenges.