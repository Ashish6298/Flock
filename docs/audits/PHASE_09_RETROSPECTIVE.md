# Phase 09 - Retrospective

## What Went Well
- **Pluggable Executors**: Encapsulating thread, process, and coroutine execution behind a standard `Executor` interface made swapping concurrency models simple.
- **Context Isolation**: Placing checkpoints inside wrappers protected worker pools from processing cancelled targets.

## Challenges & Solutions
- **Cancellation Races in Tests**: Early iterations finished test runs before cancel requests resolved. Increasing the async sleep duration to 0.5s allowed the cancellation request to interrupt the mock coroutine successfully.
- **mypy Signature Annotations**: Nesting local coroutines inside test functions required adding complete return type signatures (`-> None`) to satisfy strict typing rules.
