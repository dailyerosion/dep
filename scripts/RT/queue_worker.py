"""We do work when jobs are placed in the queue."""

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pika
from pyiem.util import logger

LOG = logger()
FILENAME_RE = re.compile(
    "/i/(?P<scenario>[0-9]+)/env/(?P<huc8>[0-9]{8})/(?P<huc812>[0-9]{4})/"
    "(?P<huc12>[0-9]{12})_(?P<fpath>[0-9]+).env"
)
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


def run_wepp(payload):
    """Actually run wepp, really."""
    # We run timeout to keep things from hanging indefinitely, we tried 60
    # seconds but it was too short as sometimes latency happens.
    with subprocess.Popen(
        ["timeout", "-s", "9", "600", payload["weppexe"]],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    ) as proc:
        (stdoutdata, stderrdata) = proc.communicate(
            payload["wepprun"].encode("ascii")
        )
    if stdoutdata[-13:-1] != b"SUCCESSFULLY":
        # So our job failed and we now have to figure out a filename to use
        # for the error file.  This is a quasi-hack here, but the env file
        # should always point to the right scenario being run.
        m = FILENAME_RE.search(payload["wepprun"])
        if m:
            d = m.groupdict()
            errorfn = (
                f"/i/{d['scenario']}/error/{d['huc8']}/{d['huc812']}/"
                f"{d['huc12']}_{d['fpath']}.error"
            )
            LOG.info("Errored: %s", errorfn)
            os.makedirs(os.path.dirname(errorfn), exist_ok=True)
            with open(errorfn, "wb") as fp:
                hn = f"Hostname: {socket.gethostname()}\n"
                fp.write(hn.encode("ascii"))
                fp.write(stdoutdata)
                fp.write(stderrdata)
            # Errored runs may leave incomplete output files, we should zap
            # those to prevent downstream impacts
            for prefix in ["wb", "env", "yld"]:
                fn = errorfn.replace("error", prefix)
                if os.path.isfile(fn):
                    os.unlink(fn)


def run(ch, delivery_tag, payload):
    """Actually run wepp for this event"""
    # We should be fully within a thread at this point...
    try:
        payload = json.loads(payload)
        run_wepp(payload)
    except Exception as exp:
        print(f"run_wepp exception {exp}")

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


def run_consumer(jobfunc, executor):
    """Our main runloop."""
    LOG.info("Starting queue_worker")

    conn = get_rabbitmqconn()
    channel = conn.channel()
    channel.queue_declare("dep", durable=True)
    # otherwise rabbitmq will send everything
    channel.basic_qos(prefetch_count=300)

    def proxy(mychannel, method, _props, payload):
        """Wrapper around jobfunc."""
        delivery_tag = method.delivery_tag
        executor.submit(jobfunc, mychannel, delivery_tag, payload)

    # make us acknowledge the message
    channel.basic_consume("dep", proxy, auto_ack=False)
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


def main(argv):
    """Go main Go."""
    if len(argv) not in [3, 4]:
        print("USAGE: python queue_worker.py <scenario> <threads> <drainme?>")
        return
    # argv[1] is the scenario and unused
    num_workers = int(argv[2])
    jobfunc = run if len(argv) < 4 else drain
    # Start a thread to print timing every 300 seconds
    threading.Thread(target=print_timing).start()
    while True:
        # Start a threadpool executor that is associated with a rabbitmq
        # connection.  Run until something bad happens, then start again!
        try:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                run_consumer(jobfunc, executor)
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
    main(sys.argv)
