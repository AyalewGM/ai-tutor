"""Ephemeral board relay. Redis Pub/Sub provides cross-worker delivery, no storage."""

import json
from contextlib import asynccontextmanager
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from redis.asyncio import Redis

from app.core.settings import settings


class LivePoint(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x: float = Field(ge=0, le=1600)
    y: float = Field(ge=0, le=1000)


class LiveFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["pointer", "stroke", "clear"]
    page_id: str | None = Field(default=None, max_length=36)
    operation_id: str | None = Field(default=None, max_length=36)
    points: list[LivePoint] = Field(default_factory=list, max_length=128)
    point: LivePoint | None = None

    @model_validator(mode="after")
    def shape(self):
        import uuid

        if self.page_id is not None:
            self.page_id = str(uuid.UUID(self.page_id))
        if self.operation_id is not None:
            self.operation_id = str(uuid.UUID(self.operation_id))
        if self.kind == "pointer" and (self.point is None or self.points or self.operation_id):
            raise ValueError("Pointer requires one point only")
        if self.kind == "stroke" and (not self.points or self.operation_id is None or self.point):
            raise ValueError("Stroke requires an ID and points")
        if self.kind == "clear" and (self.points or self.point or self.operation_id):
            raise ValueError("Clear cannot carry drawing data")
        return self


@asynccontextmanager
async def open_live_channel(board_id):
    client = Redis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=0.4, socket_timeout=1
    )
    pubsub = client.pubsub()
    channel = f"mihur:board-live:{board_id}"
    try:
        await pubsub.subscribe(channel)
        # Consume subscription acknowledgement before advertising live readiness.
        acknowledgement = await pubsub.get_message(timeout=0.5)
        if not acknowledgement:
            raise ConnectionError("Live subscription unavailable")

        class Channel:
            async def publish(self, event):
                await client.publish(channel, json.dumps(event, separators=(",", ":")))

            async def receive(self):
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                return json.loads(message["data"]) if message else None

        yield Channel()
    finally:
        await pubsub.aclose()
        await client.aclose()
