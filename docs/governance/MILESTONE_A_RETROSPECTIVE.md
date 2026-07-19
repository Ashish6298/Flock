# Milestone A Retrospective

## Architectural Insights
Decoupling the `Transport` from the `MessageBus` was highly beneficial. It allowed mocking networking streams cleanly inside unit tests, preventing the need to spin up physical TCP servers for simple pipeline tests (e.g. middleware verification).

## Challenges Resolved
- **Ephemeral Port Routing**: During loopback TCP testing, client sockets use dynamic ephemeral ports. The message envelope was upgraded to carry a `reply_port` in its custom metadata dictionary, allowing servers to correctly identify the listener port of the client node.
- **Mypy Strict Constraints**: Strict mypy rules caught various typing edge cases such as missing return annotations on test cases and raw `Any` propagation on serializers.

## Lessons Learned & Future Recommendations
1. Ensure all custom framing protocols support a dynamic length envelope size rather than hardcoding header offsets.
2. For Milestone B (Cluster Formation), keep heartbeats decoupled from primary client routing blocks using separate event triggers.
