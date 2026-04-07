"""
################################################################################
#                                                                              #
#                           TAVUS SERVICE                                      #
#                                                                              #
#   Handles all Tavus API calls:                                               #
#   - create_conversation  → create a new avatar session                       #
#   - end_conversation     → end an existing avatar session                    #
#                                                                              #
################################################################################
"""

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

"""Call Tavus API to create a new conversation. Returns conversation_id and conversation_url."""

async def create_conversation(custom_greeting: str = None) -> dict:
    logger.info("[TAVUS] Creating conversation...")

    body = {"persona_id": settings.TAVUS_PERSONA_ID}
    if custom_greeting:
        body["custom_greeting"] = custom_greeting

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://tavusapi.com/v2/conversations",
            headers={
                "Content-Type": "application/json",
                "x-api-key": settings.TAVUS_API_KEY,
            },
            json=body,
        )

    if resp.status_code >= 400:
        logger.error(f"[TAVUS] Create failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=f"Tavus API error {resp.status_code}: {resp.text}")

    data = resp.json()
    logger.info(f"[TAVUS] Conversation created: {data.get('conversation_id')}")
    return {"conversation_id": data["conversation_id"], "conversation_url": data["conversation_url"]}


async def end_conversation(conversation_id: str) -> dict:
    """Call Tavus API to end an existing conversation."""
    logger.info(f"[TAVUS] Ending conversation: {conversation_id}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://tavusapi.com/v2/conversations/{conversation_id}/end",
            headers={"x-api-key": settings.TAVUS_API_KEY},
        )

    if resp.status_code >= 400:
        logger.error(f"[TAVUS] End failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail="Failed to end Tavus conversation")

    return {"success": True}
