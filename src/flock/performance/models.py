"""Performance Pydantic configurations and metrics models."""

from __future__ import annotations

import time
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkDefinition(BaseModel):
    """Benchmark configuration coordinates."""

    name: str
    warmup_iterations: int = 5
    measured_iterations: int = 20
    parameters: Dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True}


class BenchmarkResult(BaseModel):
    """Repeatable benchmark workload execution outputs report."""

    name: str
    mean_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_dev_ms: float
    throughput: float  # operations per second
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class PerformanceValidationResult(BaseModel):
    """Validation report mapping errors."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class CPUProfileSnapshot(BaseModel):
    """CPU stats profiling details."""

    function_name: str
    call_count: int
    total_time_ms: float
    exclusive_time_ms: float

    model_config = {"frozen": True}


class MemoryProfileSnapshot(BaseModel):
    """Memory stats profiling details."""

    allocation_bytes: int
    peak_bytes: int
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class ProfilingSession(BaseModel):
    """Profiling session tracking records."""

    session_id: str
    cpu_snapshots: List[CPUProfileSnapshot] = Field(default_factory=list)
    memory_snapshots: List[MemoryProfileSnapshot] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class PerformanceBaseline(BaseModel):
    """Named performance baseline wrapper."""

    name: str
    target_mean_duration_ms: float
    target_throughput: float
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class RegressionThreshold(BaseModel):
    """Configuration mapping allowed regression limits."""

    latency_increase_percent_limit: float = 10.0
    throughput_degradation_percent_limit: float = 10.0

    model_config = {"frozen": True}


class RegressionResult(BaseModel):
    """Output details representing regression checks results."""

    name: str
    status: str  # "PASSED", "WARNING", "FAILED"
    latency_change_percent: float
    throughput_change_percent: float
    message: str

    model_config = {"frozen": True}


class PerformanceTrend(BaseModel):
    """Historical statistics summarizing performance trends."""

    name: str
    direction: str  # "STABLE", "DEGRADING", "IMPROVING"
    history_count: int

    model_config = {"frozen": True}


class OptimizationPriority(str, Enum):
    """Priority levels for performance optimization recommendations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OptimizationRecommendation(BaseModel):
    """Specific actionable recommendation for performance improvement."""

    affected_subsystem: str
    priority: OptimizationPriority
    metrics: Dict[str, float] = Field(default_factory=dict)
    expected_impact: str
    confidence_level: float
    explanation: str

    model_config = {"frozen": True}


class ResourceUtilization(BaseModel):
    """Container tracking resource usage patterns."""

    cpu_percent: float
    memory_mb: float
    network_bandwidth_mbps: float = 0.0

    model_config = {"frozen": True}


class PerformanceBottleneck(BaseModel):
    """Specific bottleneck detected during analysis."""

    category: str
    metric_value: float
    threshold_value: float
    description: str

    model_config = {"frozen": True}


class ExecutionAnalysis(BaseModel):
    """Detailed analytics summarizing stability and variability."""

    mean_latency_ms: float
    standard_deviation_ms: float
    throughput_ops: float
    stability_score: float

    model_config = {"frozen": True}


class OptimizationReport(BaseModel):
    """Comprehensive execution optimization report containing recommendations."""

    name: str
    recommendations: List[OptimizationRecommendation] = Field(default_factory=list)
    bottlenecks: List[PerformanceBottleneck] = Field(default_factory=list)
    resource_usage: Optional[ResourceUtilization] = None
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class PerformanceMetric(BaseModel):
    """Represents a single performance measurement metric."""

    name: str
    value: float
    timestamp: float = Field(default_factory=time.time)

    model_config = {"frozen": True}


class MetricsSnapshot(BaseModel):
    """Snapshot containing multiple performance metrics captured at a single point."""

    timestamp: float = Field(default_factory=time.time)
    metrics: Dict[str, PerformanceMetric] = Field(default_factory=dict)

    model_config = {"frozen": True}


class DashboardSeries(BaseModel):
    """A series of metrics plotted over time."""

    name: str
    values: List[float] = Field(default_factory=list)
    timestamps: List[float] = Field(default_factory=list)

    model_config = {"frozen": True}


class DashboardSnapshot(BaseModel):
    """Consolidated state representing a real-time live performance dashboard view."""

    timestamp: float = Field(default_factory=time.time)
    health_status: str  # e.g., "HEALTHY", "DEGRADED", "CRITICAL"
    active_metrics: Dict[str, float] = Field(default_factory=dict)
    series: List[DashboardSeries] = Field(default_factory=list)

    model_config = {"frozen": True}


class MetricsThreshold(BaseModel):
    """Alert threshold values for a specific metric."""

    metric_name: str
    warning_limit: float
    error_limit: float

    model_config = {"frozen": True}


class MetricsAlert(BaseModel):
    """Represents an alert triggered by a metric exceeding a threshold."""

    timestamp: float = Field(default_factory=time.time)
    metric_name: str
    observed_value: float
    threshold_value: float
    severity: str  # "INFO", "WARNING", "ERROR", "CRITICAL"
    explanation: str

    model_config = {"frozen": True}


class MetricsHistory(BaseModel):
    """Historical collection of metrics snapshots and alerts."""

    snapshots: List[MetricsSnapshot] = Field(default_factory=list)
    alerts: List[MetricsAlert] = Field(default_factory=list)

    model_config = {"frozen": True}


class PerformanceFinding(BaseModel):
    """A specific performance finding from the reporting engine."""

    severity: str  # "INFO", "WARNING", "ERROR", "CRITICAL"
    description: str
    impacted_area: str

    model_config = {"frozen": True}


class PerformanceScorecard(BaseModel):
    """A high-level scorecard representing grades and stability indicators."""

    overall_score: float
    latency_rating: str  # e.g., "A", "B", "C", "F"
    throughput_rating: str
    stability_rating: str

    model_config = {"frozen": True}


class PerformanceCertification(BaseModel):
    """A certificate confirming production readiness of a release."""

    is_certified: bool
    release_version: str
    environment: str
    summary_verdict: str

    model_config = {"frozen": True}


class HistoricalComparison(BaseModel):
    """Direct comparison details comparing two metric runs."""

    base_version: str
    target_version: str
    latency_delta_percent: float
    throughput_delta_percent: float
    improvement_detected: bool

    model_config = {"frozen": True}


class PerformanceReport(BaseModel):
    """Unified report combining scorecard, certification, findings and baseline comparisons."""

    name: str
    timestamp: float = Field(default_factory=time.time)
    scorecard: PerformanceScorecard
    certification: PerformanceCertification
    findings: List[PerformanceFinding] = Field(default_factory=list)
    baseline_comparisons: List[HistoricalComparison] = Field(default_factory=list)

    model_config = {"frozen": True}
