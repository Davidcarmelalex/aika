"""
AIKA Core Agent

The central conversational agent — receives messages from connectors,
builds context, routes to Ayooni, and returns responses.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("aika.core")


@dataclass
class Message:
    user_id: str
    channel: str  # telegram | whatsapp | voice
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    text: str
    media: str | None = None
    quick_replies: list[str] = field(default_factory=list)


class AIKACoreAgent:
    """
    AIKA core agent — the primary conversation handler.
    
    Flow:
    1. Receive message from connector
    2. Load user context from memory
    3. Route to Ayooni for reasoning
    4. Format and return response
    """
    
    def __init__(self, ayooni_client, memory_store=None):
        self._ayooni = ayooni_client
        self._memory = memory_store
    
    async def handle(self, message: Message) -> Response:
        logger.info(f"Message from {message.user_id} via {message.channel}")
        
        # Load context
        context = await self._load_context(message.user_id)
        
        # Route to Ayooni
        try:
            result = await self._ayooni.process(
                user_id=message.user_id,
                text=message.text,
                context=context,
            )
            response_text = result.get("response", "I'm processing that.")
        except Exception as e:
            logger.error(f"Ayooni routing failed: {e}")
            response_text = "I encountered an issue processing that. Please try again."
        
        # Store interaction
        if self._memory:
            await self._memory.store(message.user_id, message.text, response_text)
        
        return Response(text=response_text)
    
    async def _load_context(self, user_id: str) -> dict:
        if not self._memory:
            return {}
        try:
            return await self._memory.get_context(user_id)
        except Exception:
            return {}
