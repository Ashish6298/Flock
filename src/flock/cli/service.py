"""High-level Enterprise CLIService."""

from __future__ import annotations

from typing import Any

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.cli.commands import CommandRegistry
from flock.cli.configuration import ConfigurationManager
from flock.cli.executor import CommandExecutionEngine
from flock.cli.formatter import CommandFormatter
from flock.cli.history import HistoryLogger
from flock.cli.parser import CommandParser
from flock.cli.profiles import ProfileManager
from flock.cli.session import SessionManager
from flock.cli.shell import ReplEngine

logger = structlog.get_logger()


class CliService:
    """Wires command executors, configuration context parameters, and local routers."""

    def __init__(
        self,
        node_id: str,
        message_bus: MessageBus,
        event_bus: EventBus,
    ) -> None:
        self.node_id = node_id
        self._bus = message_bus
        self._events = event_bus

        # Setup subsystems
        self.registry = CommandRegistry()
        self.parser = CommandParser()
        self.shell = ReplEngine()
        self.formatter = CommandFormatter()
        self.config = ConfigurationManager()
        self.profiles = ProfileManager()
        self.history = HistoryLogger()
        self.sessions = SessionManager()
        self.executor = CommandExecutionEngine(self.registry)

        self._running = False

    async def start(self) -> None:
        """Start CLI operational hooks."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("CliService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop CLI operations."""
        self._running = False
        logger.info("CliService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register CLI sync handlers on message bus."""
        router = self._bus.router

        async def handle_cli_command(context: Any) -> None:
            payload = context.payload or {}
            cmd_line = payload.get("command_line", "")

            reply_target = context.sender
            try:
                tokens = self.parser.parse(cmd_line)
                if not tokens:
                    raise ValueError("Empty tokens.")

                await self._bus.send(
                    reply_target,
                    MessageType.CLI_COMMAND_RESPONSE,
                    {
                        "success": True,
                        "output": f"Executed command: {tokens[0]}",
                    },
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.CLI_COMMAND_RESPONSE,
                    {"success": False, "output": "", "error": str(exc)},
                )

        router.register(
            MessageType.CLI_COMMAND_REQUEST,
            _CliCommandHandler(handle_cli_command),
        )


class _CliCommandHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
