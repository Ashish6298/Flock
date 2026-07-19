# Phase 05 - Retrospective

## What Went Well
- **Separation of Concerns**: Keeping the membership logic layered directly above discovery without discovery knowing about membership worked perfectly.
- **Event-Driven Decoupling**: Having the membership service subscribe to discovery alerts through the local EventBus ensured no direct coupling back.

## Challenges & Solutions
- **Port Mapping in Loopback Tests**: In dynamic integration test loops, connections originate from ephemeral ports. Passing the `reply_port` in metadata custom parameters allowed correct loopback replies.
- **Dynamic Discovery Interference**: Concurrently running discovery service loops expired peer entries during the handshake because of strict timeouts. Bypassing discovery start loops in the integration test prevented dynamic interference.
