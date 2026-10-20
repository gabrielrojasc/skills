"""Delayed delivery queue."""

import json
import os
import time
from dataclasses import asdict, dataclass, replace

import redis

DELAYED_KEY = "relay:delayed"

client = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))


@dataclass(frozen=True)
class Job:
    id: str
    url: str
    payload: dict
    attempt: int = 1

    def retry(self):
        return replace(self, attempt=self.attempt + 1)


def schedule(job, delay):
    """Make a job available to workers after `delay` seconds."""
    client.zadd(DELAYED_KEY, {json.dumps(asdict(job)): time.time() + delay})
