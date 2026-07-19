# Phase 3 Test Plan

## Objectives
Validate middleware chains execution order, Event Bus publish-subscribe flows, and RPC correlation tracking.

## Execution
- `test_router.py`: Checks registration.
- `test_middleware.py`: Asserts pre/post execution order.
- `test_event_bus.py`: Tests dynamic subscription.
- `test_request_response.py`: Asserts timeout and correlation.
