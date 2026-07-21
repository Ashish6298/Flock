"""High-level QueryService exposing query endpoints."""

from __future__ import annotations

from typing import Any, Dict, List

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.query.catalog import QueryCatalog
from flock.query.executor import QueryExecutor
from flock.query.functions import QueryFunctionRegistry
from flock.query.optimizer import QueryOptimizer
from flock.query.parser import QueryParser
from flock.query.planner import QueryPlanner

logger = structlog.get_logger()


class QueryService:
    """Wires parsers, optimizers, planners, executors, and endpoints."""

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
        self.catalog = QueryCatalog()
        self.parser = QueryParser()
        self.planner = QueryPlanner()
        self.optimizer = QueryOptimizer()
        self.executor = QueryExecutor()
        self.functions = QueryFunctionRegistry()

        self._running = False

    async def start(self) -> None:
        """Start query listeners."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("QueryService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop query operations."""
        self._running = False
        logger.info("QueryService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register query sync handlers on message bus."""
        router = self._bus.router

        async def handle_query_submit(context: Any) -> None:
            payload = context.payload or {}
            sql = payload.get("sql", "")

            reply_target = context.sender
            try:
                ast = self.parser.parse_sql(str(sql))
                plan = self.planner.build_plan(ast)
                opt = self.optimizer.optimize_plan(plan)

                # Mock dataset to avoid dependencies on remote Grid databases
                dataset: Dict[str, List[List[Any]]] = {
                    "users": [
                        [1, "Alice", "active"],
                        [2, "Bob", "inactive"],
                    ]
                }
                cols = ["id", "name", "status"]

                res = self.executor.execute_plan(opt, dataset, cols)

                await self._bus.send(
                    reply_target,
                    MessageType.QUERY_RESULT,
                    {
                        "success": True,
                        "rows": res.rows,
                        "columns": res.columns,
                    },
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.QUERY_RESULT,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.QUERY_SUBMIT,
            _QuerySubmitHandler(handle_query_submit),
        )


class _QuerySubmitHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
