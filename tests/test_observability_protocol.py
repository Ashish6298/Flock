"""Unit tests for Phase 34 protocol message types."""

from flock.protocol.packet import MessageType


def test_phase34_telemetry_submit() -> None:
    assert MessageType.TELEMETRY_SUBMIT == 262


def test_phase34_telemetry_batch() -> None:
    assert MessageType.TELEMETRY_BATCH == 263


def test_phase34_metrics_collect_request() -> None:
    assert MessageType.METRICS_COLLECT_REQUEST == 264


def test_phase34_metrics_collect_response() -> None:
    assert MessageType.METRICS_COLLECT_RESPONSE == 265


def test_phase34_trace_submit() -> None:
    assert MessageType.TRACE_SUBMIT == 266


def test_phase34_trace_response() -> None:
    assert MessageType.TRACE_RESPONSE == 267


def test_phase34_health_status_sync() -> None:
    assert MessageType.HEALTH_STATUS_SYNC == 268


def test_phase34_alert_notification() -> None:
    assert MessageType.ALERT_NOTIFICATION == 269


def test_phase34_observability_export() -> None:
    assert MessageType.OBSERVABILITY_EXPORT == 270


def test_phase34_observability_state_sync() -> None:
    assert MessageType.OBSERVABILITY_STATE_SYNC == 271


def test_phase33_dashboard_types_present() -> None:
    assert MessageType.DASHBOARD_SESSION_CREATE == 252
    assert MessageType.DASHBOARD_WIDGET_RENDER == 253
    assert MessageType.DASHBOARD_STATE_SYNC == 261


def test_no_duplicate_message_type_values() -> None:
    """Ensure no two message type names share the same integer value."""
    attrs = {
        k: v for k, v in vars(MessageType).items()
        if not k.startswith("_") and isinstance(v, int)
    }
    values = list(attrs.values())
    assert len(values) == len(set(values)), "Duplicate message type values detected"
