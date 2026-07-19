# Phase 10 - Retrospective

## What Went Well
- **Integrity Validation Check**: Validating SHA256 checksum hashes on incoming result packets before committing updates to the registry prevented corrupted results.
- **Waiters Resolution Loop**: Resolving pending waiter futures inside `ResultRegistry` directly from inbound collectors ensured fast completions.

## Challenges & Solutions
- **JSON Encoding of Bytes**: Serializing binary payloads over JSON packages sometimes corrupted binary structures. Casting raw bytes to strings via `latin-1` encoding resolved transport encoding issues.
- **Routing Handshake Errors**: Sending results back to coordinators triggered `RoutingError` when `TASK_RESULT_ACK` handler was missing. Registering a placeholder `_TaskResultAckHandler` on the worker node resolved the issue.
