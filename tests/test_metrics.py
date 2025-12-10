"""
Tests for the metrics module.

Tests metrics collection, performance tracking, cost estimation,
exporters, and aggregation functionality.
"""

import json
import pytest
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from forge.core.metrics import (
    MetricType,
    Metric,
    MetricLabel,
    HistogramBucket,
    HistogramMetric,
    MetricsCollector,
    PerformanceTracker,
    OperationTiming,
    TokenUsage,
    CostEstimate,
    CostTracker,
    MetricsExporter,
    MetricsAggregator,
    timed,
    counted,
)


# =============================================================================
# Metric Types Tests
# =============================================================================

class TestMetric:
    """Tests for Metric dataclass."""

    def test_create_metric(self):
        """Test metric creation."""
        metric = Metric(
            name="test_counter",
            metric_type=MetricType.COUNTER,
            value=42.0,
            labels={"env": "test"},
            unit="requests",
            description="Test counter"
        )

        assert metric.name == "test_counter"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.value == 42.0
        assert metric.labels["env"] == "test"

    def test_to_dict(self):
        """Test metric serialization."""
        metric = Metric(
            name="test",
            metric_type=MetricType.GAUGE,
            value=100.0
        )

        data = metric.to_dict()

        assert data["name"] == "test"
        assert data["type"] == "gauge"
        assert data["value"] == 100.0
        assert "timestamp" in data

    def test_from_dict(self):
        """Test metric deserialization."""
        data = {
            "name": "test",
            "type": "counter",
            "value": 50.0,
            "labels": {"key": "value"},
            "timestamp": "2024-01-01T00:00:00"
        }

        metric = Metric.from_dict(data)

        assert metric.name == "test"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.value == 50.0


class TestHistogramMetric:
    """Tests for HistogramMetric."""

    def test_create_default_buckets(self):
        """Test default bucket creation."""
        buckets = HistogramMetric.create_default_buckets()

        assert len(buckets) > 0
        assert buckets[-1].le == float('inf')

    def test_observe(self):
        """Test histogram observations."""
        hist = HistogramMetric(
            name="test_histogram",
            buckets=HistogramMetric.create_default_buckets()
        )

        hist.observe(0.1)
        hist.observe(0.5)
        hist.observe(1.0)

        assert hist.count == 3
        assert hist.sum_value == 1.6

    def test_percentile_calculation(self):
        """Test percentile estimation."""
        hist = HistogramMetric(
            name="test",
            buckets=[
                HistogramBucket(le=0.1),
                HistogramBucket(le=0.5),
                HistogramBucket(le=1.0),
                HistogramBucket(le=float('inf'))
            ]
        )

        # Add observations
        for _ in range(10):
            hist.observe(0.05)  # 10 in first bucket
        for _ in range(40):
            hist.observe(0.3)  # 40 in second bucket
        for _ in range(50):
            hist.observe(0.8)  # 50 in third bucket

        # P50 should be around 0.5
        p50 = hist.percentile(50)
        assert 0.1 < p50 < 1.0

    def test_empty_histogram_percentile(self):
        """Test percentile on empty histogram."""
        hist = HistogramMetric(
            name="empty",
            buckets=HistogramMetric.create_default_buckets()
        )

        assert hist.percentile(50) == 0.0


# =============================================================================
# Metrics Collector Tests
# =============================================================================

class TestMetricsCollector:
    """Tests for MetricsCollector."""

    @pytest.fixture
    def collector(self):
        """Create fresh collector for testing."""
        coll = MetricsCollector()
        coll.reset()
        return coll

    def test_singleton_pattern(self):
        """Test collector is a singleton."""
        c1 = MetricsCollector()
        c2 = MetricsCollector()

        assert c1 is c2

    def test_increment_counter(self, collector):
        """Test counter increment."""
        collector.increment("requests_total", 1)
        collector.increment("requests_total", 1)

        assert collector.get_counter("requests_total") == 2

    def test_increment_with_labels(self, collector):
        """Test counter with labels."""
        collector.increment("requests", 1, {"method": "GET"})
        collector.increment("requests", 1, {"method": "POST"})
        collector.increment("requests", 1, {"method": "GET"})

        assert collector.get_counter("requests", {"method": "GET"}) == 2
        assert collector.get_counter("requests", {"method": "POST"}) == 1

    def test_set_gauge(self, collector):
        """Test gauge set."""
        collector.set_gauge("temperature", 72.5)

        assert collector.get_gauge("temperature") == 72.5

        collector.set_gauge("temperature", 68.0)

        assert collector.get_gauge("temperature") == 68.0

    def test_observe_histogram(self, collector):
        """Test histogram observation."""
        collector.observe_histogram("request_duration", 0.1)
        collector.observe_histogram("request_duration", 0.5)

        hist = collector.get_histogram("request_duration")

        assert hist is not None
        assert hist.count == 2

    def test_record_timer(self, collector):
        """Test timer recording."""
        collector.record_timer("operation_time", 1.5)
        collector.record_timer("operation_time", 2.0)

        stats = collector.get_timer_stats("operation_time")

        assert stats["count"] == 2
        assert stats["sum"] == 3.5
        assert stats["mean"] == 1.75

    def test_timer_context_manager(self, collector):
        """Test timer context manager."""
        with collector.timer("test_operation"):
            time.sleep(0.05)

        stats = collector.get_timer_stats("test_operation")

        assert stats["count"] == 1
        assert stats["mean"] >= 0.05

    def test_timer_stats_percentiles(self, collector):
        """Test timer statistics with percentiles."""
        for i in range(100):
            collector.record_timer("perf_test", i / 100.0)

        stats = collector.get_timer_stats("perf_test")

        assert stats["count"] == 100
        assert 0.45 <= stats["p50"] <= 0.55
        assert 0.85 <= stats["p90"] <= 0.95

    def test_get_all_metrics(self, collector):
        """Test getting all metrics."""
        collector.increment("counter1")
        collector.set_gauge("gauge1", 10)
        collector.record_timer("timer1", 0.5)

        all_metrics = collector.get_all_metrics()

        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "timers" in all_metrics
        assert "uptime_seconds" in all_metrics

    def test_reset(self, collector):
        """Test metrics reset."""
        collector.increment("test_counter", 100)
        collector.reset()

        assert collector.get_counter("test_counter") == 0

    def test_register_metric(self, collector):
        """Test metric registration."""
        collector.register_metric(
            "custom_metric",
            MetricType.COUNTER,
            description="A custom counter",
            unit="items"
        )

        all_metrics = collector.get_all_metrics()

        assert "custom_metric" in all_metrics["metadata"]


# =============================================================================
# Performance Tracker Tests
# =============================================================================

class TestPerformanceTracker:
    """Tests for PerformanceTracker."""

    @pytest.fixture
    def tracker(self):
        """Create fresh tracker for testing."""
        collector = MetricsCollector()
        collector.reset()
        return PerformanceTracker(collector)

    def test_start_operation(self, tracker):
        """Test starting an operation."""
        timing = tracker.start_operation(
            "op-123",
            "generation",
            labels={"task": "api"}
        )

        assert timing.operation == "generation"
        assert not timing.is_complete

    def test_end_operation(self, tracker):
        """Test ending an operation."""
        tracker.start_operation("op-123", "test")
        time.sleep(0.05)

        timing = tracker.end_operation("op-123", success=True)

        assert timing is not None
        assert timing.is_complete
        assert timing.duration_seconds >= 0.05

    def test_track_context_manager(self, tracker):
        """Test track context manager."""
        with tracker.track("generation") as timing:
            time.sleep(0.05)

        assert timing.is_complete
        assert timing.duration_seconds >= 0.05

    def test_track_with_exception(self, tracker):
        """Test tracking when exception occurs."""
        try:
            with tracker.track("failing_op") as timing:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Timing should still complete
        assert timing.is_complete

    def test_get_active_operations(self, tracker):
        """Test getting active operations."""
        tracker.start_operation("op-1", "type-a")
        tracker.start_operation("op-2", "type-b")

        active = tracker.get_active_operations()

        assert len(active) == 2

        tracker.end_operation("op-1")
        active = tracker.get_active_operations()

        assert len(active) == 1

    def test_end_nonexistent_operation(self, tracker):
        """Test ending operation that doesn't exist."""
        result = tracker.end_operation("nonexistent")
        assert result is None


# =============================================================================
# Cost Tracker Tests
# =============================================================================

class TestTokenUsage:
    """Tests for TokenUsage."""

    def test_create_usage(self):
        """Test token usage creation."""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )

        assert usage.input_tokens == 100
        assert usage.output_tokens == 50

    def test_add_usage(self):
        """Test adding token usage."""
        u1 = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        u2 = TokenUsage(input_tokens=200, output_tokens=100, total_tokens=300)

        combined = u1 + u2

        assert combined.input_tokens == 300
        assert combined.output_tokens == 150
        assert combined.total_tokens == 450


class TestCostTracker:
    """Tests for CostTracker."""

    @pytest.fixture
    def tracker(self):
        """Create fresh cost tracker."""
        collector = MetricsCollector()
        collector.reset()
        return CostTracker(collector)

    def test_record_usage(self, tracker):
        """Test recording API usage."""
        estimate = tracker.record_usage(
            model="claude-3-sonnet",
            input_tokens=1000,
            output_tokens=500
        )

        assert estimate.tokens.input_tokens == 1000
        assert estimate.tokens.output_tokens == 500
        assert estimate.total_cost > 0

    def test_get_total_usage(self, tracker):
        """Test getting total usage."""
        tracker.record_usage("claude-3-sonnet", 1000, 500)
        tracker.record_usage("claude-3-sonnet", 2000, 1000)

        total = tracker.get_total_usage()

        assert total.input_tokens == 3000
        assert total.output_tokens == 1500

    def test_get_total_cost(self, tracker):
        """Test getting total cost."""
        tracker.record_usage("claude-3-sonnet", 1000000, 500000)

        cost = tracker.get_total_cost()

        # Should be roughly $3 input + $7.5 output = $10.5
        assert cost > 0

    def test_usage_by_model(self, tracker):
        """Test usage breakdown by model."""
        tracker.record_usage("claude-3-sonnet", 1000, 500)
        tracker.record_usage("claude-3-haiku", 2000, 1000)

        by_model = tracker.get_usage_by_model()

        assert "claude-3-sonnet" in by_model
        assert "claude-3-haiku" in by_model
        assert by_model["claude-3-sonnet"]["calls"] == 1

    def test_model_name_normalization(self, tracker):
        """Test model name normalization."""
        tracker.record_usage("claude-3.5-sonnet-20241022", 100, 50)

        by_model = tracker.get_usage_by_model()

        assert "claude-3.5-sonnet" in by_model

    def test_cached_tokens_discount(self, tracker):
        """Test cached tokens reduce cost."""
        estimate_no_cache = tracker.record_usage("claude-3-sonnet", 1000, 500)
        tracker.reset()

        estimate_with_cache = tracker.record_usage(
            "claude-3-sonnet", 1000, 500, cached_tokens=500
        )

        # Cached version should be cheaper
        assert estimate_with_cache.total_cost < estimate_no_cache.total_cost

    def test_reset(self, tracker):
        """Test reset clears all tracking."""
        tracker.record_usage("claude-3-sonnet", 1000, 500)
        tracker.reset()

        assert tracker.get_total_cost() == 0
        assert tracker.get_total_usage().total_tokens == 0


# =============================================================================
# Metrics Exporter Tests
# =============================================================================

class TestMetricsExporter:
    """Tests for MetricsExporter."""

    @pytest.fixture
    def exporter(self):
        """Create exporter with test data."""
        collector = MetricsCollector()
        collector.reset()
        collector.increment("test_counter", 10, {"env": "test"})
        collector.set_gauge("test_gauge", 50)
        collector.record_timer("test_timer", 0.5)
        return MetricsExporter(collector)

    def test_to_json(self, exporter):
        """Test JSON export."""
        json_output = exporter.to_json()
        data = json.loads(json_output)

        assert "counters" in data
        assert "gauges" in data

    def test_to_prometheus(self, exporter):
        """Test Prometheus format export."""
        prom_output = exporter.to_prometheus()

        assert "test_counter" in prom_output
        assert "test_gauge" in prom_output
        assert "# TYPE" in prom_output

    def test_to_dashboard(self, exporter):
        """Test dashboard format export."""
        dashboard = exporter.to_dashboard()

        assert "summary" in dashboard
        assert "counters" in dashboard
        assert "gauges" in dashboard

    def test_save_to_file(self, exporter, tmp_path):
        """Test saving to file."""
        output_path = tmp_path / "metrics.json"
        exporter.save_to_file(output_path, "json")

        assert output_path.exists()

        content = json.loads(output_path.read_text())
        assert "counters" in content


# =============================================================================
# Metrics Aggregator Tests
# =============================================================================

class TestMetricsAggregator:
    """Tests for MetricsAggregator."""

    @pytest.fixture
    def aggregator(self, tmp_path):
        """Create aggregator with test data."""
        collector = MetricsCollector()
        collector.reset()

        # Add test timer data
        for i in range(100):
            collector.record_timer("test_op", i / 100.0)

        return MetricsAggregator(collector, storage_path=tmp_path / "history")

    def test_aggregate_timer(self, aggregator):
        """Test timer aggregation."""
        agg = aggregator.aggregate_timer("test_op")

        assert agg is not None
        assert agg.count == 100
        assert agg.mean > 0

    def test_aggregate_nonexistent_timer(self, aggregator):
        """Test aggregating nonexistent timer."""
        agg = aggregator.aggregate_timer("nonexistent")
        assert agg is None

    def test_detect_anomalies(self, aggregator):
        """Test anomaly detection."""
        # Add some outliers
        aggregator.collector.record_timer("test_op", 100.0)  # Big outlier
        aggregator.collector.record_timer("test_op", -50.0)  # Negative outlier

        anomalies = aggregator.detect_anomalies("test_op", threshold_stddev=2.0)

        assert len(anomalies) > 0

    def test_calculate_trend(self, aggregator):
        """Test trend calculation."""
        trend = aggregator.calculate_trend("test_op", window_size=10)

        assert trend is not None
        assert "direction" in trend
        assert trend["direction"] in ["increasing", "decreasing", "stable"]

    def test_save_and_load_snapshot(self, aggregator):
        """Test saving and loading snapshots."""
        path = aggregator.save_snapshot()
        assert path.exists()

        snapshots = aggregator.load_snapshots(limit=5)
        assert len(snapshots) > 0

    def test_load_no_snapshots(self, tmp_path):
        """Test loading when no snapshots exist."""
        collector = MetricsCollector()
        aggregator = MetricsAggregator(
            collector,
            storage_path=tmp_path / "empty_history"
        )

        snapshots = aggregator.load_snapshots()
        assert snapshots == []


# =============================================================================
# Decorator Tests
# =============================================================================

class TestDecorators:
    """Tests for metric decorators."""

    @pytest.fixture(autouse=True)
    def reset_collector(self):
        """Reset collector before each test."""
        collector = MetricsCollector()
        collector.reset()

    def test_timed_decorator_sync(self):
        """Test @timed decorator on sync function."""
        @timed("test_sync_func")
        def slow_function():
            time.sleep(0.05)
            return "done"

        result = slow_function()

        assert result == "done"

        collector = MetricsCollector()
        stats = collector.get_timer_stats("test_sync_func")

        assert stats["count"] == 1
        assert stats["mean"] >= 0.05

    @pytest.mark.asyncio
    async def test_timed_decorator_async(self):
        """Test @timed decorator on async function."""
        import asyncio

        @timed("test_async_func")
        async def async_slow_function():
            await asyncio.sleep(0.05)
            return "async_done"

        result = await async_slow_function()

        assert result == "async_done"

        collector = MetricsCollector()
        stats = collector.get_timer_stats("test_async_func")

        assert stats["count"] == 1

    def test_counted_decorator_sync(self):
        """Test @counted decorator on sync function."""
        @counted("test_calls")
        def count_me():
            return "counted"

        count_me()
        count_me()
        count_me()

        collector = MetricsCollector()
        count = collector.get_counter("test_calls")

        assert count == 3

    @pytest.mark.asyncio
    async def test_counted_decorator_async(self):
        """Test @counted decorator on async function."""
        @counted("async_calls")
        async def async_count_me():
            return "async_counted"

        await async_count_me()
        await async_count_me()

        collector = MetricsCollector()
        count = collector.get_counter("async_calls")

        assert count == 2

    def test_timed_with_labels(self):
        """Test @timed with labels."""
        @timed("labeled_op", labels={"type": "test"})
        def labeled_function():
            return True

        labeled_function()

        # Timer should be recorded
        collector = MetricsCollector()
        stats = collector.get_timer_stats("labeled_op", {"type": "test"})

        assert stats["count"] == 1


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

class TestEdgeCases:
    """Edge case and integration tests."""

    def test_concurrent_counter_updates(self):
        """Test thread-safe counter updates."""
        import threading

        collector = MetricsCollector()
        collector.reset()

        def increment_many():
            for _ in range(100):
                collector.increment("concurrent_counter")

        threads = [threading.Thread(target=increment_many) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have exactly 1000 increments
        assert collector.get_counter("concurrent_counter") == 1000

    def test_labels_with_special_characters(self):
        """Test labels with special characters."""
        collector = MetricsCollector()
        collector.reset()

        collector.increment(
            "special_metric",
            labels={"path": "/api/v1/users", "method": "GET"}
        )

        count = collector.get_counter(
            "special_metric",
            labels={"path": "/api/v1/users", "method": "GET"}
        )

        assert count == 1

    def test_empty_timer_stats(self):
        """Test stats for empty timer."""
        collector = MetricsCollector()
        collector.reset()

        stats = collector.get_timer_stats("nonexistent_timer")

        assert stats["count"] == 0
        assert stats["mean"] == 0.0

    def test_histogram_with_extreme_values(self):
        """Test histogram with extreme values."""
        collector = MetricsCollector()
        collector.reset()

        collector.observe_histogram("extreme", 0.0)
        collector.observe_histogram("extreme", 1000000.0)
        collector.observe_histogram("extreme", -1000.0)

        hist = collector.get_histogram("extreme")

        assert hist.count == 3

    def test_cost_tracker_unknown_model(self):
        """Test cost tracking with unknown model."""
        collector = MetricsCollector()
        tracker = CostTracker(collector)

        # Should not raise, uses default pricing
        estimate = tracker.record_usage(
            "unknown-future-model",
            input_tokens=100,
            output_tokens=50
        )

        assert estimate.total_cost > 0

    def test_prometheus_export_with_histograms(self):
        """Test Prometheus export includes histogram data."""
        collector = MetricsCollector()
        collector.reset()

        for i in range(10):
            collector.observe_histogram("request_duration", i * 0.1)

        exporter = MetricsExporter(collector)
        prom = exporter.to_prometheus()

        assert "request_duration_bucket" in prom
        assert "request_duration_sum" in prom
        assert "request_duration_count" in prom

    def test_metrics_persistence_across_operations(self):
        """Test metrics persist across multiple operations."""
        collector = MetricsCollector()
        collector.reset()
        tracker = PerformanceTracker(collector)

        # Track several operations
        for i in range(5):
            with tracker.track("batch_op"):
                time.sleep(0.01)

        all_metrics = collector.get_all_metrics()

        # Should have operation metrics
        assert any("operation" in k for k in all_metrics["counters"].keys())
