"""
Metrics & Telemetry System for Forge

Provides comprehensive observability through metrics collection,
performance tracking, cost estimation, and operational insights.

Features:
- Multiple metric types (counters, gauges, histograms, timers)
- Performance tracking with percentile calculations
- API cost estimation and token tracking
- Export to JSON, Prometheus, and dashboard formats
- Historical analysis with trend detection
"""

import asyncio
import functools
import json
import statistics
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from forge.utils.logger import logger


class MetricsError(Exception):
    """Base exception for metrics-related errors."""
    pass


# =============================================================================
# Metric Types
# =============================================================================

class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"          # Monotonically increasing value
    GAUGE = "gauge"              # Point-in-time value that can go up/down
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Events per time period


@dataclass
class MetricLabel:
    """Labels for metric dimensions."""
    name: str
    value: str

    def __hash__(self):
        return hash((self.name, self.value))

    def __eq__(self, other):
        if not isinstance(other, MetricLabel):
            return False
        return self.name == other.name and self.value == other.value


@dataclass
class Metric:
    """
    A single metric measurement.

    Attributes:
        name: Metric name (e.g., "generation_duration_seconds")
        metric_type: Type of metric
        value: Current value
        labels: Dimensional labels
        timestamp: When the metric was recorded
        unit: Unit of measurement
        description: Human-readable description
    """
    name: str
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metric':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            metric_type=MetricType(data["type"]),
            value=data["value"],
            labels=data.get("labels", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            unit=data.get("unit", ""),
            description=data.get("description", "")
        )


@dataclass
class HistogramBucket:
    """A bucket in a histogram."""
    le: float  # Less than or equal to
    count: int = 0


@dataclass
class HistogramMetric:
    """
    Histogram metric with configurable buckets.

    Tracks distribution of values across predefined buckets.
    """
    name: str
    buckets: List[HistogramBucket]
    sum_value: float = 0.0
    count: int = 0
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""

    @classmethod
    def create_default_buckets(cls) -> List[HistogramBucket]:
        """Create default bucket boundaries."""
        boundaries = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]
        return [HistogramBucket(le=b) for b in boundaries]

    @classmethod
    def create_duration_buckets(cls) -> List[HistogramBucket]:
        """Create buckets optimized for duration measurements."""
        boundaries = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float('inf')]
        return [HistogramBucket(le=b) for b in boundaries]

    def observe(self, value: float) -> None:
        """Record an observation."""
        self.sum_value += value
        self.count += 1

        for bucket in self.buckets:
            if value <= bucket.le:
                bucket.count += 1

    def percentile(self, p: float) -> float:
        """Estimate percentile from histogram buckets."""
        if self.count == 0:
            return 0.0

        target_count = self.count * p / 100.0
        prev_count = 0
        prev_bound = 0.0

        for bucket in self.buckets:
            if bucket.count >= target_count:
                # Linear interpolation within bucket
                if bucket.count == prev_count:
                    return bucket.le
                fraction = (target_count - prev_count) / (bucket.count - prev_count)
                return prev_bound + fraction * (bucket.le - prev_bound)
            prev_count = bucket.count
            prev_bound = bucket.le

        return self.buckets[-1].le if self.buckets else 0.0


# =============================================================================
# Metrics Collector
# =============================================================================

class MetricsCollector:
    """
    Central collector for all metrics.

    Thread-safe collection and aggregation of metrics from
    various sources throughout the application.
    """

    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'MetricsCollector':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[str, HistogramMetric]] = defaultdict(dict)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._start_time = datetime.now()
        self._data_lock = threading.Lock()
        self._initialized = True

    def _labels_key(self, labels: Dict[str, str]) -> str:
        """Create a hashable key from labels."""
        if not labels:
            return ""
        return "|".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str = "",
        unit: str = "",
        buckets: Optional[List[float]] = None
    ) -> None:
        """
        Register a new metric.

        Args:
            name: Metric name
            metric_type: Type of metric
            description: Human-readable description
            unit: Unit of measurement
            buckets: Bucket boundaries for histograms
        """
        with self._data_lock:
            self._metadata[name] = {
                "type": metric_type,
                "description": description,
                "unit": unit,
                "buckets": buckets,
                "registered_at": datetime.now().isoformat()
            }

    def increment(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter.

        Args:
            name: Counter name
            value: Amount to increment by
            labels: Dimensional labels
        """
        key = self._labels_key(labels or {})
        with self._data_lock:
            self._counters[name][key] += value

    def decrement(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Decrement a counter (for gauges).

        Args:
            name: Gauge name
            value: Amount to decrement by
            labels: Dimensional labels
        """
        key = self._labels_key(labels or {})
        with self._data_lock:
            self._gauges[name][key] -= value

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge value.

        Args:
            name: Gauge name
            value: Value to set
            labels: Dimensional labels
        """
        key = self._labels_key(labels or {})
        with self._data_lock:
            self._gauges[name][key] = value

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram observation.

        Args:
            name: Histogram name
            value: Value to record
            labels: Dimensional labels
        """
        key = self._labels_key(labels or {})
        with self._data_lock:
            if key not in self._histograms[name]:
                # Get bucket config from metadata or use defaults
                meta = self._metadata.get(name, {})
                if meta.get("buckets"):
                    buckets = [HistogramBucket(le=b) for b in meta["buckets"]]
                else:
                    buckets = HistogramMetric.create_default_buckets()

                self._histograms[name][key] = HistogramMetric(
                    name=name,
                    buckets=buckets,
                    labels=labels or {},
                    description=meta.get("description", "")
                )

            self._histograms[name][key].observe(value)

    def record_timer(
        self,
        name: str,
        duration: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timer measurement.

        Args:
            name: Timer name
            duration: Duration in seconds
            labels: Dimensional labels
        """
        key = f"{name}:{self._labels_key(labels or {})}"
        with self._data_lock:
            self._timers[key].append(duration)

        # Also record in histogram for percentile calculations
        self.observe_histogram(f"{name}_histogram", duration, labels)

    @contextmanager
    def timer(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Generator[None, None, None]:
        """
        Context manager for timing operations.

        Args:
            name: Timer name
            labels: Dimensional labels

        Yields:
            None
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record_timer(name, duration, labels)

    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Get counter value."""
        key = self._labels_key(labels or {})
        with self._data_lock:
            return self._counters[name][key]

    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Get gauge value."""
        key = self._labels_key(labels or {})
        with self._data_lock:
            return self._gauges[name][key]

    def get_histogram(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[HistogramMetric]:
        """Get histogram metric."""
        key = self._labels_key(labels or {})
        with self._data_lock:
            return self._histograms[name].get(key)

    def get_timer_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """
        Get statistics for a timer.

        Returns:
            Dictionary with count, sum, mean, min, max, p50, p90, p99
        """
        key = f"{name}:{self._labels_key(labels or {})}"
        with self._data_lock:
            values = self._timers.get(key, [])

        if not values:
            return {
                "count": 0,
                "sum": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0
            }

        sorted_values = sorted(values)
        return {
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p50": self._percentile(sorted_values, 50),
            "p90": self._percentile(sorted_values, 90),
            "p99": self._percentile(sorted_values, 99)
        }

    def _percentile(self, sorted_values: List[float], p: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * p / 100.0
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f
        if f == c:
            return sorted_values[f]
        return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.

        Returns:
            Dictionary with all counters, gauges, histograms, and timers
        """
        with self._data_lock:
            # Copy data while holding lock
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            histograms_data = {
                name: {
                    key: {
                        "count": h.count,
                        "sum": h.sum_value,
                        "buckets": [(b.le, b.count) for b in h.buckets]
                    }
                    for key, h in histograms.items()
                }
                for name, histograms in self._histograms.items()
            }
            timer_keys = list(self._timers.keys())
            metadata = dict(self._metadata)
            uptime = (datetime.now() - self._start_time).total_seconds()

        # Calculate timer stats outside the lock to avoid deadlock
        timers_data = {}
        for timer_key in timer_keys:
            timer_name = timer_key.split(":")[0]
            if timer_name not in timers_data:
                timers_data[timer_name] = self.get_timer_stats(timer_name)

        return {
            "counters": counters,
            "gauges": gauges,
            "histograms": histograms_data,
            "timers": timers_data,
            "metadata": metadata,
            "uptime_seconds": uptime
        }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._data_lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._start_time = datetime.now()


# =============================================================================
# Performance Tracker
# =============================================================================

@dataclass
class OperationTiming:
    """Timing information for an operation."""
    operation: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return self.ended_at is not None


class PerformanceTracker:
    """
    Tracks performance of operations.

    Provides detailed timing, throughput, and resource usage metrics.
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Initialize performance tracker.

        Args:
            collector: Metrics collector to use
        """
        self.collector = collector or MetricsCollector()
        self._active_operations: Dict[str, OperationTiming] = {}
        self._lock = threading.Lock()

    def start_operation(
        self,
        operation_id: str,
        operation_type: str,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OperationTiming:
        """
        Start tracking an operation.

        Args:
            operation_id: Unique identifier for this operation
            operation_type: Type of operation (e.g., "generation", "test")
            labels: Dimensional labels
            metadata: Additional metadata

        Returns:
            OperationTiming instance
        """
        timing = OperationTiming(
            operation=operation_type,
            started_at=datetime.now(),
            labels=labels or {},
            metadata=metadata or {}
        )

        with self._lock:
            self._active_operations[operation_id] = timing

        # Increment active operations gauge
        self.collector.set_gauge(
            "active_operations",
            len(self._active_operations),
            {"type": operation_type}
        )

        return timing

    def end_operation(
        self,
        operation_id: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[OperationTiming]:
        """
        End tracking an operation.

        Args:
            operation_id: Operation identifier
            success: Whether operation succeeded
            metadata: Additional metadata to record

        Returns:
            Completed OperationTiming or None
        """
        with self._lock:
            timing = self._active_operations.pop(operation_id, None)

        if timing is None:
            return None

        timing.ended_at = datetime.now()
        timing.duration_seconds = (timing.ended_at - timing.started_at).total_seconds()

        if metadata:
            timing.metadata.update(metadata)

        # Record metrics
        labels = {"type": timing.operation, "success": str(success).lower()}
        labels.update(timing.labels)

        self.collector.record_timer(
            f"operation_duration_{timing.operation}",
            timing.duration_seconds,
            labels
        )

        self.collector.increment(
            f"operations_total",
            labels={"type": timing.operation, "success": str(success).lower()}
        )

        # Update active operations gauge
        self.collector.set_gauge(
            "active_operations",
            len(self._active_operations),
            {"type": timing.operation}
        )

        return timing

    @contextmanager
    def track(
        self,
        operation_type: str,
        operation_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Generator[OperationTiming, None, None]:
        """
        Context manager for tracking operations.

        Args:
            operation_type: Type of operation
            operation_id: Optional ID (auto-generated if not provided)
            labels: Dimensional labels

        Yields:
            OperationTiming instance
        """
        op_id = operation_id or f"{operation_type}_{time.time_ns()}"
        timing = self.start_operation(op_id, operation_type, labels)
        success = True

        try:
            yield timing
        except Exception:
            success = False
            raise
        finally:
            self.end_operation(op_id, success)

    def get_active_operations(self) -> List[OperationTiming]:
        """Get list of active operations."""
        with self._lock:
            return list(self._active_operations.values())


# =============================================================================
# Cost Tracker
# =============================================================================

@dataclass
class TokenUsage:
    """Token usage for an API call."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    def __add__(self, other: 'TokenUsage') -> 'TokenUsage':
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens
        )


@dataclass
class CostEstimate:
    """Estimated cost for API usage."""
    model: str
    tokens: TokenUsage
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: datetime = field(default_factory=datetime.now)


class CostTracker:
    """
    Tracks API usage and estimates costs.

    Supports multiple models with configurable pricing.
    """

    # Default pricing per 1M tokens (as of 2024)
    DEFAULT_PRICING = {
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }

    def __init__(
        self,
        collector: Optional[MetricsCollector] = None,
        pricing: Optional[Dict[str, Dict[str, float]]] = None
    ):
        """
        Initialize cost tracker.

        Args:
            collector: Metrics collector to use
            pricing: Custom pricing per 1M tokens
        """
        self.collector = collector or MetricsCollector()
        self.pricing = pricing or self.DEFAULT_PRICING.copy()
        self._usage_history: List[CostEstimate] = []
        self._total_usage = TokenUsage()
        self._total_cost = 0.0
        self._lock = threading.Lock()

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> CostEstimate:
        """
        Record API usage and calculate cost.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached tokens (reduced cost)

        Returns:
            CostEstimate with calculated costs
        """
        tokens = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cached_tokens=cached_tokens
        )

        # Get pricing (default to claude-3-sonnet if unknown)
        model_key = self._normalize_model_name(model)
        prices = self.pricing.get(model_key, self.pricing.get("claude-3-sonnet", {"input": 3.0, "output": 15.0}))

        # Calculate costs (per 1M tokens, cached tokens at 10% cost)
        effective_input = input_tokens - cached_tokens * 0.9
        input_cost = (effective_input / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        total_cost = input_cost + output_cost

        estimate = CostEstimate(
            model=model_key,  # Use normalized model name for consistency
            tokens=tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost
        )

        with self._lock:
            self._usage_history.append(estimate)
            self._total_usage = self._total_usage + tokens
            self._total_cost += total_cost

        # Record in metrics collector
        labels = {"model": model_key}
        self.collector.increment("tokens_input_total", input_tokens, labels)
        self.collector.increment("tokens_output_total", output_tokens, labels)
        self.collector.increment("tokens_cached_total", cached_tokens, labels)
        self.collector.increment("api_cost_dollars", total_cost, labels)
        self.collector.increment("api_calls_total", 1, labels)

        return estimate

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for pricing lookup."""
        model_lower = model.lower()

        # Map common variations
        if "opus" in model_lower:
            if "4" in model_lower:
                return "claude-opus-4"
            return "claude-3-opus"
        elif "sonnet" in model_lower:
            if "3.5" in model_lower or "3-5" in model_lower:
                return "claude-3.5-sonnet"
            return "claude-3-sonnet"
        elif "haiku" in model_lower:
            return "claude-3-haiku"
        elif "gpt-4" in model_lower:
            if "turbo" in model_lower:
                return "gpt-4-turbo"
            return "gpt-4"
        elif "gpt-3.5" in model_lower:
            return "gpt-3.5-turbo"

        return model_lower

    def get_total_usage(self) -> TokenUsage:
        """Get total token usage."""
        with self._lock:
            return self._total_usage

    def get_total_cost(self) -> float:
        """Get total estimated cost."""
        with self._lock:
            return self._total_cost

    def get_usage_by_model(self) -> Dict[str, Dict[str, Any]]:
        """Get usage breakdown by model."""
        with self._lock:
            by_model: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "total_cost": 0.0
            })

            for estimate in self._usage_history:
                model = estimate.model
                by_model[model]["calls"] += 1
                by_model[model]["input_tokens"] += estimate.tokens.input_tokens
                by_model[model]["output_tokens"] += estimate.tokens.output_tokens
                by_model[model]["cached_tokens"] += estimate.tokens.cached_tokens
                by_model[model]["total_cost"] += estimate.total_cost

            return dict(by_model)

    def get_recent_usage(
        self,
        hours: int = 24
    ) -> List[CostEstimate]:
        """Get usage from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return [e for e in self._usage_history if e.timestamp >= cutoff]

    def reset(self) -> None:
        """Reset all usage tracking."""
        with self._lock:
            self._usage_history.clear()
            self._total_usage = TokenUsage()
            self._total_cost = 0.0


# =============================================================================
# Metrics Exporter
# =============================================================================

class MetricsExporter:
    """
    Exports metrics in various formats.

    Supports JSON, Prometheus, and dashboard-friendly formats.
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize exporter.

        Args:
            collector: Metrics collector to export from
        """
        self.collector = collector

    def to_json(self, pretty: bool = True) -> str:
        """
        Export metrics as JSON.

        Args:
            pretty: Whether to pretty-print

        Returns:
            JSON string
        """
        metrics = self.collector.get_all_metrics()
        indent = 2 if pretty else None
        return json.dumps(metrics, indent=indent, default=str)

    def to_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus exposition format string
        """
        lines = []
        metrics = self.collector.get_all_metrics()

        # Export counters
        for name, values in metrics["counters"].items():
            prom_name = self._to_prometheus_name(name)
            meta = metrics["metadata"].get(name, {})

            if meta.get("description"):
                lines.append(f"# HELP {prom_name} {meta['description']}")
            lines.append(f"# TYPE {prom_name} counter")

            for labels_str, value in values.items():
                labels = self._parse_labels(labels_str)
                lines.append(f"{prom_name}{labels} {value}")

        # Export gauges
        for name, values in metrics["gauges"].items():
            prom_name = self._to_prometheus_name(name)
            meta = metrics["metadata"].get(name, {})

            if meta.get("description"):
                lines.append(f"# HELP {prom_name} {meta['description']}")
            lines.append(f"# TYPE {prom_name} gauge")

            for labels_str, value in values.items():
                labels = self._parse_labels(labels_str)
                lines.append(f"{prom_name}{labels} {value}")

        # Export histograms
        for name, histograms in metrics["histograms"].items():
            prom_name = self._to_prometheus_name(name)

            lines.append(f"# TYPE {prom_name} histogram")

            for labels_str, hist_data in histograms.items():
                base_labels = self._parse_labels(labels_str)

                # Bucket lines
                for le, count in hist_data["buckets"]:
                    le_str = "+Inf" if le == float('inf') else str(le)
                    bucket_labels = base_labels.rstrip("}") + f',le="{le_str}"}}' if base_labels != "{}" else f'{{le="{le_str}"}}'
                    lines.append(f"{prom_name}_bucket{bucket_labels} {count}")

                # Sum and count
                lines.append(f"{prom_name}_sum{base_labels} {hist_data['sum']}")
                lines.append(f"{prom_name}_count{base_labels} {hist_data['count']}")

        return "\n".join(lines)

    def _to_prometheus_name(self, name: str) -> str:
        """Convert metric name to Prometheus format."""
        return name.replace(".", "_").replace("-", "_")

    def _parse_labels(self, labels_str: str) -> str:
        """Parse labels string to Prometheus format."""
        if not labels_str:
            return "{}"

        pairs = labels_str.split("|")
        formatted = ",".join(f'{p.split("=")[0]}="{p.split("=")[1]}"' for p in pairs if "=" in p)
        return f"{{{formatted}}}" if formatted else "{}"

    def to_dashboard(self) -> Dict[str, Any]:
        """
        Export metrics in dashboard-friendly format.

        Returns:
            Dictionary optimized for dashboard display
        """
        metrics = self.collector.get_all_metrics()

        return {
            "summary": {
                "uptime_seconds": metrics["uptime_seconds"],
                "total_counters": len(metrics["counters"]),
                "total_gauges": len(metrics["gauges"]),
                "total_histograms": len(metrics["histograms"]),
                "timestamp": datetime.now().isoformat()
            },
            "counters": [
                {
                    "name": name,
                    "values": [
                        {"labels": dict(pair.split("=") for pair in labels.split("|") if "=" in pair) if labels else {},
                         "value": value}
                        for labels, value in values.items()
                    ]
                }
                for name, values in metrics["counters"].items()
            ],
            "gauges": [
                {
                    "name": name,
                    "values": [
                        {"labels": dict(pair.split("=") for pair in labels.split("|") if "=" in pair) if labels else {},
                         "value": value}
                        for labels, value in values.items()
                    ]
                }
                for name, values in metrics["gauges"].items()
            ],
            "timers": metrics["timers"]
        }

    def save_to_file(self, path: Path, format: str = "json") -> None:
        """
        Save metrics to file.

        Args:
            path: Output file path
            format: Output format (json, prometheus)
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "prometheus":
            content = self.to_prometheus()
        else:
            content = self.to_json()

        path.write_text(content)
        logger.info(f"Metrics exported to {path}")


# =============================================================================
# Metrics Aggregator
# =============================================================================

@dataclass
class AggregatedMetric:
    """Aggregated metric with statistics."""
    name: str
    period_start: datetime
    period_end: datetime
    count: int
    sum_value: float
    mean: float
    min_value: float
    max_value: float
    stddev: float
    p50: float
    p90: float
    p99: float


class MetricsAggregator:
    """
    Aggregates metrics for analysis.

    Provides statistical analysis, trend detection, and anomaly identification.
    """

    def __init__(
        self,
        collector: MetricsCollector,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize aggregator.

        Args:
            collector: Metrics collector
            storage_path: Path for persistent storage
        """
        self.collector = collector
        self.storage_path = storage_path or Path(".forge/metrics/history")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._historical_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def aggregate_timer(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[AggregatedMetric]:
        """
        Aggregate a timer metric.

        Args:
            name: Timer name
            labels: Optional labels filter

        Returns:
            AggregatedMetric or None
        """
        stats = self.collector.get_timer_stats(name, labels)

        if stats["count"] == 0:
            return None

        # Get raw values for stddev calculation
        key = f"{name}:{self.collector._labels_key(labels or {})}"
        with self.collector._data_lock:
            values = self.collector._timers.get(key, [])

        stddev = statistics.stdev(values) if len(values) > 1 else 0.0

        return AggregatedMetric(
            name=name,
            period_start=self.collector._start_time,
            period_end=datetime.now(),
            count=stats["count"],
            sum_value=stats["sum"],
            mean=stats["mean"],
            min_value=stats["min"],
            max_value=stats["max"],
            stddev=stddev,
            p50=stats["p50"],
            p90=stats["p90"],
            p99=stats["p99"]
        )

    def detect_anomalies(
        self,
        name: str,
        threshold_stddev: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous values in a metric.

        Args:
            name: Metric name
            threshold_stddev: Standard deviations from mean to consider anomaly

        Returns:
            List of anomalous observations
        """
        key = f"{name}:"
        with self.collector._data_lock:
            # Find matching timer keys
            matching_keys = [k for k in self.collector._timers.keys() if k.startswith(key)]

            all_values = []
            for k in matching_keys:
                all_values.extend(self.collector._timers[k])

        if len(all_values) < 3:
            return []

        mean = statistics.mean(all_values)
        stddev = statistics.stdev(all_values)

        if stddev == 0:
            return []

        anomalies = []
        for i, value in enumerate(all_values):
            z_score = abs(value - mean) / stddev
            if z_score > threshold_stddev:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": z_score,
                    "mean": mean,
                    "stddev": stddev
                })

        return anomalies

    def calculate_trend(
        self,
        name: str,
        window_size: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate trend for a metric.

        Args:
            name: Metric name
            window_size: Number of recent values to analyze

        Returns:
            Trend information or None
        """
        key = f"{name}:"
        with self.collector._data_lock:
            matching_keys = [k for k in self.collector._timers.keys() if k.startswith(key)]

            all_values = []
            for k in matching_keys:
                all_values.extend(self.collector._timers[k])

        if len(all_values) < window_size:
            return None

        recent = all_values[-window_size:]
        older = all_values[-2 * window_size:-window_size] if len(all_values) >= 2 * window_size else all_values[:window_size]

        recent_mean = statistics.mean(recent)
        older_mean = statistics.mean(older)

        if older_mean == 0:
            change_percent = 0.0
        else:
            change_percent = ((recent_mean - older_mean) / older_mean) * 100

        # Determine trend direction
        if change_percent > 10:
            direction = "increasing"
        elif change_percent < -10:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change_percent": change_percent,
            "recent_mean": recent_mean,
            "older_mean": older_mean,
            "window_size": window_size
        }

    def save_snapshot(self) -> Path:
        """
        Save current metrics snapshot to disk.

        Returns:
            Path to saved snapshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.storage_path / f"snapshot_{timestamp}.json"

        metrics = self.collector.get_all_metrics()
        metrics["snapshot_time"] = datetime.now().isoformat()

        snapshot_path.write_text(json.dumps(metrics, indent=2, default=str))
        logger.info(f"Metrics snapshot saved to {snapshot_path}")

        return snapshot_path

    def load_snapshots(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Load recent metrics snapshots.

        Args:
            limit: Maximum number of snapshots to load

        Returns:
            List of snapshot data
        """
        snapshots = []
        snapshot_files = sorted(
            self.storage_path.glob("snapshot_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        for path in snapshot_files:
            try:
                data = json.loads(path.read_text())
                data["_file"] = path.name
                snapshots.append(data)
            except Exception as e:
                logger.warning(f"Failed to load snapshot {path}: {e}")

        return snapshots


# =============================================================================
# Decorators
# =============================================================================

T = TypeVar('T')


def timed(
    name: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None
) -> Callable:
    """
    Decorator to time function execution.

    Args:
        name: Timer name (defaults to function name)
        labels: Dimensional labels

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        timer_name = name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                collector = MetricsCollector()
                with collector.timer(timer_name, labels):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                collector = MetricsCollector()
                with collector.timer(timer_name, labels):
                    return func(*args, **kwargs)
            return sync_wrapper

    return decorator


def counted(
    name: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None
) -> Callable:
    """
    Decorator to count function calls.

    Args:
        name: Counter name (defaults to function name)
        labels: Dimensional labels

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        counter_name = name or f"{func.__module__}.{func.__name__}_calls"

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                collector = MetricsCollector()
                collector.increment(counter_name, labels=labels)
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                collector = MetricsCollector()
                collector.increment(counter_name, labels=labels)
                return func(*args, **kwargs)
            return sync_wrapper

    return decorator


# =============================================================================
# Global Instances
# =============================================================================

# Global metrics collector singleton
metrics_collector = MetricsCollector()

# Global cost tracker
cost_tracker = CostTracker(metrics_collector)

# Global performance tracker
performance_tracker = PerformanceTracker(metrics_collector)
