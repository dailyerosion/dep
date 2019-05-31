"""We do work when jobs are placed in the queue."""
import sys
import subprocess
from multiprocessing.pool import ThreadPool
import time

import rabbitpy

URL = 'amqp://guest:guest@iem-rabbitmq.local:5672/%2f'


def run(rundata):
    ''' Actually run wepp for this event '''
    proc = subprocess.Popen(
        ["wepp", ],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    (stdoutdata, _stderrdata) = proc.communicate(rundata)
    if stdoutdata[-13:-1] != b'SUCCESSFULLY':
        print("ERROR!")
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

        connection = rabbitpy.Connection(URL)
        channel = connection.channel()
        channel.prefetch_count(10)
        for message in rabbitpy.Queue(channel, name=queuename):
            consume(message)

    pool = ThreadPool(start_threads)
    for _ in range(start_threads):
        pool.apply_async(setup_connection)
    pool.close()
    pool.join()


def main(argv):
    """Go main Go."""
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
