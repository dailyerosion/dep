"""Common utilities for DEP queue workers."""

from collections.abc import Callable
from concurrent.futures import Executor
from pathlib import Path

from dailyerosion.util import get_rabbitmqconn


def sanitize_exe(exe: str) -> str:
    """Reduce the blast radius of the naughty things that could come in.

    Enforces:
      - Filename has either `weps`, `sweep`, or `wepp` in the name
    """
    exe_path = Path(exe).resolve()
    allowed = ["weps", "sweep", "wepp"]
    if not any(keyword in exe_path.name for keyword in allowed):
        raise ValueError(f"Invalid executable name: {exe}")
    return str(exe_path)


def consume_queue(
    queue: str,
    jobfunc: Callable,
    executor: Executor,
    prefetch_count: int,
    log,
) -> None:
    """Consume jobs from RabbitMQ and submit processing to an executor."""
    log.info("Starting queue_worker for queue: %s", queue)

    conn, _config = get_rabbitmqconn()
    channel = conn.channel()
    # Declare queue as durable (must match producer)
    channel.queue_declare(queue, durable=True)
    # Limit unacknowledged messages to prevent overwhelming worker
    channel.basic_qos(prefetch_count=prefetch_count)

    def proxy(mychannel, method, _props, payload):
        """Wrapper around jobfunc."""
        delivery_tag = method.delivery_tag
        executor.submit(jobfunc, mychannel, delivery_tag, payload)

    # Consume from queue with manual acknowledgment for reliability
    channel.basic_consume(queue, proxy, auto_ack=False)
    # blocks
    channel.start_consuming()
