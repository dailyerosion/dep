"""We do work when jobs are placed in the queue."""
import sys
import re
import subprocess
from multiprocessing.pool import ThreadPool
import time

import rabbitpy

URL = 'amqp://guest:guest@iem-rabbitmq.local:5672/%2f'
FILENAME_RE = re.compile((
    "/i/(?P<scenario>[0-9]+)/env/(?P<huc8>[0-9]{8})/(?P<huc812>[0-9]{4})/"
    "(?P<huc12>[0-9]{12})_(?P<fpath>[0-9]+).env"))


def run(rundata):
    ''' Actually run wepp for this event '''
    proc = subprocess.Popen(
        ["wepp", ],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    (stdoutdata, stderrdata) = proc.communicate(rundata)
    if stdoutdata[-13:-1] != b'SUCCESSFULLY':
        # So our job failed and we now have to figure out a filename to use
        # for the error file.  This is a quasi-hack here, but the env file
        # should always point to the right scenario being run.
        m = FILENAME_RE.search(rundata.decode('ascii'))
        if m:
            d = m.groupdict()
            errorfn = "/i/%s/error/%s/%s/%s_%s.error" % (
                d['scenario'], d['huc8'], d['huc812'], d['huc12'], d['fpath']
            )
            with open(errorfn, 'wb') as fp:
                fp.write(stdoutdata)
                fp.write(stderrdata)
        return False
    return True


def runloop(argv):
    """Our main runloop."""
    scenario = int(argv[1])
    start_threads = int(argv[2])

    queuename = 'dep' if scenario == 0 else 'depscenario'

    def setup_connection():
        def consume(message):
            run(message.body)
            message.ack()

        # Use context managers as we had some strange thread issues otherwise?
        with rabbitpy.Connection(URL) as conn:
            with conn.channel() as channel:
                channel.prefetch_count(10)
                queue = rabbitpy.Queue(channel, name=queuename, durable=True)
                for message in queue:
                    consume(message)

    pool = ThreadPool(start_threads)
    for _ in range(start_threads):
        pool.apply_async(setup_connection)
    pool.close()
    pool.join()


def main(argv):
    """Go main Go."""
    if len(argv) != 3:
        print("USAGE: python queue_worker.py <scenario> <threads>")
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


if __name__ == '__main__':
    main(sys.argv)
