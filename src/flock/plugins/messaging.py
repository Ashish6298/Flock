"""Plugin Messaging Engine.

Handles point-to-point requests, responses, broadcast messages, validation,
timeouts, and delivery acknowledgements.
"""

from __future__ import annotations

import threading
import uuid
import time
from typing import Dict, Optional

import structlog

from flock.plugins.exceptions import (
    PluginMessageValidationError,
    PluginMessageTimeoutError,
    PluginMessageDeliveryError,
)
from flock.plugins.models import PluginMessage, PluginResponse, PluginBroadcast
from flock.plugins.registry import PluginRegistry

logger = structlog.get_logger()


class PluginMessagingEngine:
    """Thread-safe point-to-point and broadcast messaging engine for plugins.

    Maintains strict schema validation, request/response pairing, timeouts,
    and history persistence through the PluginRegistry.
    """

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._lock = threading.RLock()
        self._pending_requests: Dict[str, tuple[float, threading.Event, Optional[PluginResponse]]] = {}

    def send_message(self, msg: PluginMessage) -> PluginResponse:
        """Sends a direct message to a target plugin and waits for a response.

        Supports synchronous request-response pairing, validation, timeouts,
        and persistence.

        Raises:
            PluginMessageValidationError: If validation fails.
            PluginMessageTimeoutError: If request times out.
            PluginMessageDeliveryError: If delivery fails.
        """
        # 1. Validation
        if not msg.sender_id or not msg.recipient_id or not msg.subject:
            raise PluginMessageValidationError("Message must have sender, recipient, and subject.")

        # Ensure sender and recipient exist/are registered
        if self._registry.get_plugin(msg.recipient_id) is None:
            raise PluginMessageDeliveryError(f"Recipient plugin '{msg.recipient_id}' not found.")

        # Log the message to history
        self._registry.log_message(msg)

        # 2. Get handler
        handler = self._registry.get_message_handler(msg.recipient_id, msg.subject)
        if handler is None:
            raise PluginMessageDeliveryError(
                f"No handler registered for subject '{msg.subject}' on plugin '{msg.recipient_id}'."
            )

        # 3. Setup correlation / timeout
        response_event = threading.Event()
        timeout = msg.timeout or 5.0
        deadline = time.time() + timeout

        with self._lock:
            self._pending_requests[msg.message_id] = (deadline, response_event, None)

        # Invoke handler synchronously
        try:
            handler_result = handler(msg)
            
            # Format response
            response = PluginResponse(
                response_id=str(uuid.uuid4()),
                request_id=msg.message_id,
                sender_id=msg.recipient_id,
                recipient_id=msg.sender_id,
                success=True,
                payload=handler_result if isinstance(handler_result, dict) else {"result": handler_result},
            )
        except Exception as exc:
            logger.error(
                "Handler failed during message execution",
                message_id=msg.message_id,
                error=str(exc),
            )
            response = PluginResponse(
                response_id=str(uuid.uuid4()),
                request_id=msg.message_id,
                sender_id=msg.recipient_id,
                recipient_id=msg.sender_id,
                success=False,
                error_message=str(exc),
            )

        # 4. Handle response / Wait simulation
        with self._lock:
            if msg.message_id in self._pending_requests:
                # Save response and signal event
                self._pending_requests[msg.message_id] = (deadline, response_event, response)
                response_event.set()

        # Perform wait check (with timeout)
        wait_success = response_event.wait(timeout)
        if not wait_success:
            with self._lock:
                self._pending_requests.pop(msg.message_id, None)
            raise PluginMessageTimeoutError(f"Request '{msg.message_id}' timed out after {timeout} seconds.")

        # Retrieve response
        with self._lock:
            _, _, final_resp = self._pending_requests.pop(msg.message_id, (0.0, response_event, None))

        if final_resp is None:
            raise PluginMessageDeliveryError("Failed to fetch response.")

        # Log response
        self._registry.log_response(final_resp)
        return final_resp

    def send_broadcast(self, bcast: PluginBroadcast) -> int:
        """Broadcasts a message to all registered active plugins except the sender."""
        if not bcast.sender_id or not bcast.subject:
            raise PluginMessageValidationError("Broadcast must have sender and subject.")

        self._registry.log_broadcast(bcast)

        active_plugins = self._registry.list_plugins()
        delivery_count = 0

        # Deliver to all registered plugins that have a registered handler for this subject
        for plugin in active_plugins:
            if plugin.plugin_id == bcast.sender_id:
                continue

            handler = self._registry.get_message_handler(plugin.plugin_id, bcast.subject)
            if handler is not None:
                # Construct equivalent PluginMessage to invoke handler
                msg = PluginMessage(
                    message_id=str(uuid.uuid4()),
                    sender_id=bcast.sender_id,
                    recipient_id=plugin.plugin_id,
                    subject=bcast.subject,
                    body=bcast.body,
                    metadata=bcast.metadata,
                )
                try:
                    handler(msg)
                    delivery_count += 1
                except Exception as exc:
                    logger.error(
                        "Broadcast delivery failed for recipient",
                        recipient_id=plugin.plugin_id,
                        error=str(exc),
                    )

        return delivery_count
