# PHASE 13 RETROSPECTIVE – Replicated Distributed State Machine & Metadata Store

**Phase**: 13  
**Date**: 2026-07-20  
**Team**: Flock Engineering  

---

## What Went Well

### 1. Separation of State Machine Engine and Store
Decoupling raw mutations (`ReplicatedStateStore`) from logical flow coordination (`StateMachineEngine`) made type checking and sequential verification clean. Testing collection operations (like set manipulation and map deltas) was done directly against the store without mock consensus overhead.

### 2. Async Lifecycle Event Integration
Publishing metadata transitions (`state.command.applied`, etc.) via task-wrapped calls in `_publish_event` allowed the synchronous state machine thread-locks to run seamlessly alongside `asyncio.Future` completion hooks in the high-level `StateMachineService`.

### 3. Checksum Verification
Implementing stable sorted key-value serialization for checksumming made it impossible to restore corrupt or modified snapshots.

---

## Challenges and Solutions

### 1. Mypy Variable Intersection
**Problem**: The compiler inferred the return type of `curr_val` in `store.apply` as a union of numeric and collection types (due to shared fallbacks and local assignments). This led to errors like `Item "int" of "int | float" has no attribute "append"`.

**Solution**: Avoided naming mutations on a single shared variable name (`curr_val`) inside the match-case blocks. Declaring separate scoped local variables (`curr_list`, `curr_map`, `curr_numeric`) completely resolved the compiler warnings.

### 2. Subscriptions Returning `None`
**Problem**: In Flock's EventBus, calling `subscribe` registers listeners and returns `None` instead of a string registration key. Using it to store `_subscription_id = subscribe()` resulted in type checks failing.

**Solution**: Replaced subscription ID tracking with a simple boolean flag `self._is_subscribed = True` to trace initialization state.

---

## Next Steps

**Phase 14 – Persistent Log Compaction & Snapshot Sync**  
In Phase 14, we will design remote streaming channels for the snapshot metadata produced in this phase, allowing nodes starting from zero to recover the full replicated state store.
