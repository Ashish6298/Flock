# Profiling Feature Matrix

This document provides a canonical inventory of all Runtime Profiling capabilities implemented for Milestone D — Phase 2.

---

## 1. Feature Inventory

### Runtime Profiler Engine
- **Purpose**: Orchestrates function-level and session-based execution profiling.
- **Implementation**: [src/flock/performance/profiler.py](file:///d:/Flock/src/flock/performance/profiler.py) (`RuntimeProfilerEngine`)
- **Primary Classes**: `RuntimeProfilerEngine`
- **Public APIs**: `profile_call`, `get_hotspots`
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes

### Profiling Models
- **Purpose**: Strongly typed Pydantic models for CPU/memory stats and sessions.
- **Implementation**: [src/flock/performance/models.py](file:///d:/Flock/src/flock/performance/models.py) (`ProfilingSession`, `CPUProfileSnapshot`, `MemoryProfileSnapshot`)
- **Primary Classes**: `ProfilingSession`, `CPUProfileSnapshot`, `MemoryProfileSnapshot`
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes

### CPU Profiling
- **Purpose**: Evaluates execution time and function call frequencies.
- **Implementation**: [src/flock/performance/profiler.py](file:///d:/Flock/src/flock/performance/profiler.py) (`RuntimeProfilerEngine.profile_call`)
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes

### Memory Profiling
- **Purpose**: Tracks allocated bytes delta and peak utilization trends.
- **Implementation**: [src/flock/performance/profiler.py](file:///d:/Flock/src/flock/performance/profiler.py) (`RuntimeProfilerEngine.profile_call`)
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes

### Hotspot Analysis
- **Purpose**: Sorts functions consuming the highest cumulative execution durations.
- **Implementation**: [src/flock/performance/profiler.py](file:///d:/Flock/src/flock/performance/profiler.py) (`RuntimeProfilerEngine.get_hotspots`)
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes

### Profiling Decorators
- **Purpose**: Passive decorator annotations wrapping calls for profiling.
- **Implementation**: [src/flock/performance/profiler.py](file:///d:/Flock/src/flock/performance/profiler.py) (`profile_execution`)
- **Public APIs**: `profile_execution`
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes

### Profiling Registry Extensions
- **Purpose**: Binds reentrant session locking query operations.
- **Implementation**: [src/flock/performance/registry.py](file:///d:/Flock/src/flock/performance/registry.py) (`PerformanceRegistry`)
- **Primary Classes**: `PerformanceRegistry`
- **Public APIs**: `record_session`, `get_session`
- **Tests**: [tests/test_profiler.py](file:///d:/Flock/tests/test_profiler.py)
- **Status**: Implemented
- **Production Ready**: Yes
