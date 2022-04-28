"""We do work when jobs are placed in the queue."""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import re
import os
import socket
import subprocess
import sys
import time

import pika
from pyiem.util import logger

LOG = logger()
FILENAME_RE = re.compile(
    "/i/(?P<scenario>[0-9]+)/env/(?P<huc8>[0-9]{8})/(?P<huc812>[0-9]{4})/"
    "(?P<huc12>[0-9]{12})_(?P<fpath>[0-9]+).env"
)


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


def drain(ch, delivery_tag, _rundata):
    """NOOP to clear out the queue via a hackery"""
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def run(ch, delivery_tag, rundata):
    """Actually run wepp for this event"""
    with subprocess.Popen(
        ["timeout", "60", "wepp"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
    ) as proc:
        (stdoutdata, stderrdata) = proc.communicate(rundata)
    if stdoutdata[-13:-1] != b"SUCCESSFULLY":
        # So our job failed and we now have to figure out a filename to use
        # for the error file.  This is a quasi-hack here, but the env file
        # should always point to the right scenario being run.
        m = FILENAME_RE.search(rundata.decode("ascii"))
        if m:
            d = m.groupdict()
            errorfn = (
                f"/i/{d['scenario']}/error/{d['huc8']}/{d['huc812']}/"
                f"{d['huc12']}_{d['fpath']}.error"
            )
            LOG.warning("Errored: %s", errorfn)
            os.makedirs(os.path.dirname(errorfn), exist_ok=True)
            with open(errorfn, "wb") as fp:
                hn = f"Hostname: {socket.gethostname()}\n"
                fp.write(hn.encode("ascii"))
                fp.write(stdoutdata)
                fp.write(stderrdata)
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


def run_consumer(jobfunc, executor):
    """Our main runloop."""
    LOG.info("Starting queue_worker")

    conn = get_rabbitmqconn()
    channel = conn.channel()
    channel.queue_declare("dep", durable=True)
    # otherwise rabbitmq will send everything
    channel.basic_qos(prefetch_count=300)

    def proxy(mychannel, method, _props, rundata):
        """Wrapper around jobfunc."""
        delivery_tag = method.delivery_tag
        executor.submit(jobfunc, mychannel, delivery_tag, rundata)

    # make us acknowledge the message
    channel.basic_consume("dep", proxy, auto_ack=False)
    # blocks
    channel.start_consuming()


def main(argv):
    """Go main Go."""
    if len(argv) not in [3, 4]:
        print("USAGE: python queue_worker.py <scenario> <threads> <drainme?>")
        return
    # argv[1] is the scenario and unused
    num_workers = int(argv[2])
    jobfunc = run if len(argv) < 4 else drain
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
            LOG.warning("Encountered Exception, sleeping 30 seconds")
            LOG.exception(exp)
            time.sleep(30)


if __name__ == "__main__":
    main(sys.argv)
