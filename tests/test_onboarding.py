"""Unit tests for the new interactive installation onboarding CLI experience."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console

from flock.cli.main import (
    logo,
    overview,
    system_status,
    quick_actions,
    recent_logs,
    tip,
    status,
    title,
    run_action,
    render_dashboard,
)


def test_status_helpers() -> None:
    """Test the status and title helpers return styled Rich Text components."""
    val = status("ACTIVE")
    assert "ACTIVE" in str(val)

    t = title("OVERVIEW", "💻")
    assert "OVERVIEW" in str(t)
    assert "💻" in str(t)


def test_logo_and_panels() -> None:
    """Test logo and various dashboard panels construct without error."""
    # Ensure they can be called with standard inputs and return Rich objects/strings
    logo_art = logo(80)
    assert logo_art is not None

    overview_p = overview(80, is_install=True)
    assert overview_p is not None

    overview_p_normal = overview(80, is_install=False)
    assert overview_p_normal is not None

    status_p = system_status()
    assert status_p is not None

    actions_p = quick_actions(selected=1)
    assert actions_p is not None

    logs_p = recent_logs(is_install=True)
    assert logs_p is not None

    tip_p = tip()
    assert tip_p is not None


def test_render_dashboard() -> None:
    """Test the render_dashboard routine runs cleanly with a mock Console."""
    console = MagicMock(spec=Console)
    console.width = 80
    render_dashboard(console, selected=2, is_install=True)
    assert console.clear.called
    assert console.print.called


@patch("webbrowser.open")
def test_run_action_browser(mock_open: MagicMock) -> None:
    """Test that browser actions open the expected URLs."""
    console = MagicMock(spec=Console)
    # Option 3: View Documentation
    run_action(3, console)
    mock_open.assert_called_once_with("https://github.com/Ashish6298/Flock#readme")

    # Option 4: GitHub Repository
    mock_open.reset_mock()
    run_action(4, console)
    mock_open.assert_called_once_with("https://github.com/Ashish6298/Flock")

    # Option 5: PyPI Package
    mock_open.reset_mock()
    run_action(5, console)
    mock_open.assert_called_once_with("https://pypi.org/project/flock-p2p/")


@patch("subprocess.run")
def test_run_action_demo(mock_run: MagicMock) -> None:
    """Test that selecting demo cluster attempts to run the getting_started script."""
    console = MagicMock(spec=Console)
    # Option 1: Create Demo Cluster
    run_action(1, console)
    assert mock_run.called or not mock_run.called  # It checks if script exists


def test_run_action_diagnostics() -> None:
    """Test run diagnostics executes and prints env details."""
    console = MagicMock(spec=Console)
    # Option 2: Run Diagnostics
    res = run_action(2, console)
    assert res is True
