# Phase 2 Retrospective

## Outcomes
Successful TCP socket framing implementation.

## Challenges Resolved
- Fixed test slicing offsets by switching to dynamic `HEADER_SIZE` lookup parameters, preventing test breaks on layout changes.
