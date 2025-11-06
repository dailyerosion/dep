"""We do work when jobs are placed in the queue."""

import json
import os
import socket
import subprocess
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import click
import pika
from pydantic import ValidationError
from pyiem.util import logger

from pydep.workflows.wepprun import WeppJobPayload

LOG = logger()
MEMORY = {
    "runs": 0,
    "timestamp": time.time(),
}


def get_rabbitmqconn():
    """Load the configuration."""
    # load rabbitmq.json in the directory local to this script
    with open("rabbitmq.json", "r", encoding="utf-8") as fh:
        config = json.load(fh)
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=config["host"],
            port=config["port"],
            virtual_host=config["vhost"],
            credentials=pika.credentials.PlainCredentials(
                config["user"], config["password"]
            ),
        )
    )


def drain(ch, delivery_tag, _payload):
    """NOOP to clear out the queue via a hackery"""
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def run_wepp(payload: WeppJobPayload):
    """Actually run wepp, really.

    Parameters
    ----------
    payload : WeppJobPayload
        Validated WEPP job payload containing runfile content and executable.
    """
    # We run timeout to keep things from hanging indefinitely, we tried 60
    # seconds but it was too short as sometimes latency happens.
    with subprocess.Popen(
        ["timeout", "-s", "9", "600", payload.weppexe],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    ) as proc:
        (stdoutdata, stderrdata) = proc.communicate(
            payload.wepprun.encode("ascii")
        )
    if stdoutdata[-13:-1] != b"SUCCESSFULLY":
        # So our job failed and we now have to figure out a filename to use
        # for the error file.  This is a quasi-hack here, but the env file
        # should always point to the right scenario being run.
        error_path = Path(payload.errorfn)
        os.makedirs(error_path.parent, exist_ok=True)
        LOG.info("Errored: %s", payload.errorfn)
        with open(payload.errorfn, "wb") as fp:
            hn = f"Hostname: {socket.gethostname()}\n"
            fp.write(hn.encode("ascii"))
            fp.write(stdoutdata)
            fp.write(stderrdata)
        # Errored runs may leave incomplete output files, we should zap
        # those to prevent downstream impacts, this is poor code
        for prefix in ["wb", "env", "yld"]:
            fn = str(error_path).replace("error", prefix)
            if os.path.isfile(fn):
                os.unlink(fn)


def run(ch, delivery_tag, payload):
    """Actually run wepp for this event.

    Parameters
    ----------
    ch : pika.channel.Channel
        The RabbitMQ channel.
    delivery_tag : int
        The message delivery tag for acknowledgment.
    payload : bytes
        The raw message payload from RabbitMQ.
    """
    # We should be fully within a thread at this point...
    try:
        # Parse and validate the payload using Pydantic model
        job = WeppJobPayload.model_validate_json(payload)
        run_wepp(job)
    except ValidationError as exp:
        # Invalid payload structure - log the validation errors
        LOG.error("Invalid payload format: %s", exp)
        LOG.error("Raw payload: %s", payload[:200])  # Log first 200 chars
    except Exception as exp:
        LOG.error("run_wepp exception: %s", exp)
        LOG.error("Traceback: %s", traceback.format_exc())

    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def ack_message(ch, delivery_tag):
    """Note that `ch` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass
    MEMORY["runs"] += 1


def run_consumer(queue: str, jobfunc, executor):
    """Our main runloop."""
    LOG.info("Starting queue_worker for queue: %s", queue)

    conn = get_rabbitmqconn()
    channel = conn.channel()
    # Declare queue as durable (must match producer)
    # This is idempotent - safe to declare multiple times
    channel.queue_declare(queue, durable=True)
    # Limit unacknowledged messages to prevent overwhelming worker
    channel.basic_qos(prefetch_count=300)

    def proxy(mychannel, method, _props, payload):
        """Wrapper around jobfunc."""
        delivery_tag = method.delivery_tag
        executor.submit(jobfunc, mychannel, delivery_tag, payload)

    # Consume from queue with manual acknowledgment for reliability
    channel.basic_consume(queue, proxy, auto_ack=False)
    # blocks
    channel.start_consuming()


def print_timing():
    """Print timing information."""
    while True:
        time.sleep(300)
        runs = MEMORY["runs"]
        dt = time.time() - MEMORY["timestamp"]
        rate = runs / dt
        MEMORY["runs"] = 0
        MEMORY["timestamp"] = time.time()
        if runs == 0:
            continue
        LOG.info("%s runs over %.3fs for %.3f r/s", runs, dt, rate)


@click.command()
@click.option("--workers", type=int, required=True)
@click.option("--drainme", is_flag=True)
@click.option("--queue", default="dep", help="Queue name to consume from")
def main(workers: int, drainme: bool, queue: str):
    """Go main Go."""
    jobfunc = run if not drainme else drain
    # Start a thread to print timing every 300 seconds
    threading.Thread(target=print_timing).start()
    while True:
        # Start a threadpool executor that is associated with a rabbitmq
        # connection.  Run until something bad happens, then start again!
        try:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                run_consumer(queue, jobfunc, executor)
            LOG.warning("run_consumer exited cleanly, sleeping 30 seconds")
            time.sleep(30)
        except KeyboardInterrupt:
            LOG.critical("Exiting due to keyboard interrupt")
            break
        except Exception as exp:
            LOG.error("Exception %s, sleeping 30", exp)
            traceback.print_exc()
            time.sleep(30)


if __name__ == "__main__":
    main()
