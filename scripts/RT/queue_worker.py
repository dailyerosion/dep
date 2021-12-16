"""We do work when jobs are placed in the queue."""
from functools import partial
from multiprocessing import Pool
import re
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


def drain(_rundata):
    """NOOP to clear out the queue via a hackery"""
    return True


def run(rundata):
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
            with open(errorfn, "wb") as fp:
                hn = f"Hostname: {socket.gethostname()}\n"
                fp.write(hn.encode("ascii"))
                fp.write(stdoutdata)
                fp.write(stderrdata)
        return False
    return True


def cb(*args):
    """If apply_async has troubles?"""
    print("cb() called and got the following as args:")
    print(args)


def setup_connection(queuename, jobfunc):
    """Setup and run."""

    def consume(channel, method, props, message):
        jobfunc(message)

    conn = pika.BlockingConnection(
        pika.ConnectionParameters(host="iem-rabbitmq.local")
    )
    channel = conn.channel()
    channel.queue_declare(queuename, durable=True)
    channel.basic_consume(queuename, consume, auto_ack=True)
    channel.start_consuming()


def runloop(argv):
    """Our main runloop."""
    scenario = int(argv[1])
    start_threads = int(argv[2])
    jobfunc = run
    if len(argv) > 3:
        jobfunc = drain
        LOG.debug("Running in queue-draining mode")

    queuename = "dep" if scenario == 0 else "depscenario"

    pool = Pool(start_threads)
    f = partial(setup_connection, queuename, jobfunc)
    for _ in range(start_threads):
        pool.apply_async(f, callback=cb, error_callback=cb)
    pool.close()
    pool.join()


def main(argv):
    """Go main Go."""
    if len(argv) not in [3, 4]:
        print("USAGE: python queue_worker.py <scenario> <threads> <drainme?>")
        return
    while True:
        try:
            runloop(argv)
            print("runloop exited cleanly, sleeping 30 seconds")
            time.sleep(30)
        except KeyboardInterrupt:
            print("Exiting due to keyboard interrupt")
            break
        except Exception as exp:
            print("Encountered Exception, sleeping 30 seconds")
            print(exp)
            time.sleep(30)


if __name__ == "__main__":
    main(sys.argv)
