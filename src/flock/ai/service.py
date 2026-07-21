"""High-level AIService exposing prediction routes."""

from __future__ import annotations

from typing import Any, Dict, List

import structlog

from flock.events.bus import EventBus
from flock.messaging.bus import MessageBus
from flock.messaging.handlers import MessageHandler
from flock.protocol.packet import MessageType
from flock.ai.analyzer import ClusterIntelligenceEngine
from flock.ai.anomaly import AnomalyDetectionEngine
from flock.ai.forecast import ForecastEngine
from flock.ai.learning import LearningEngine
from flock.ai.models import PredictionRequest, PredictionResult
from flock.ai.optimizer import AutonomousOptimizationEngine
from flock.ai.predictor import MachineLearningPredictionEngine
from flock.ai.recommendation import AIRecommendationEngine
from flock.ai.scheduler import PredictiveScheduler

logger = structlog.get_logger()


class AIService:
    """Wires prediction engines, optimizers, learning loops, and service routes."""

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
        self.predictor = MachineLearningPredictionEngine()
        self.scheduler = PredictiveScheduler()
        self.optimizer = AutonomousOptimizationEngine()
        self.analyzer = ClusterIntelligenceEngine()
        self.anomaly = AnomalyDetectionEngine()
        self.forecaster = ForecastEngine()
        self.recommendation = AIRecommendationEngine()
        self.learning = LearningEngine()

        self._running = False

    async def start(self) -> None:
        """Start AI telemetry hooks."""
        if self._running:
            return
        self._running = True

        self._register_handlers()
        logger.info("AIService started", node_id=self.node_id)

    async def stop(self) -> None:
        """Stop AI operations."""
        self._running = False
        logger.info("AIService stopped", node_id=self.node_id)

    # ------------------------------------------------------------------
    # Network message queries wiring
    # ------------------------------------------------------------------

    def _register_handlers(self) -> None:
        """Register AI sync handlers on message bus."""
        router = self._bus.router

        async def handle_ai_prediction(context: Any) -> None:
            payload = context.payload or {}
            features = payload.get("features", [])

            reply_target = context.sender
            try:
                req = PredictionRequest(
                    predictor_name="workload-forecast",
                    features=[float(f) for f in features],
                )
                res = self.predictor.predict(req)

                await self._bus.send(
                    reply_target,
                    MessageType.AI_PREDICTION_RESPONSE,
                    {
                        "success": True,
                        "prediction_value": res.prediction_value,
                        "confidence": res.confidence,
                    },
                )
            except Exception as exc:
                await self._bus.send(
                    reply_target,
                    MessageType.AI_PREDICTION_RESPONSE,
                    {"success": False, "error": str(exc)},
                )

        router.register(
            MessageType.AI_PREDICTION_REQUEST,
            _AIPredictionHandler(handle_ai_prediction),
        )


class _AIPredictionHandler(MessageHandler):
    def __init__(self, callback: Any) -> None:
        self.callback = callback

    async def handle(self, context: Any) -> None:
        await self.callback(context)
