"""We do work when jobs are placed in the queue."""

import os
import shutil
import subprocess
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import partial

import click
import requests
from pika.channel import Channel
from pydantic import ValidationError
from pyiem.util import logger

from dailyerosion.util import get_rabbitmqconn
from dailyerosion.workflows.sweeprun import SweepJobPayload, SweepJobResult

LOG = logger()
MEMORY = {
    "runs": 0,
    "timestamp": time.time(),
}
IEMRE = "http://mesonet.agron.iastate.edu/iemre/hourly"


def drain(ch, delivery_tag, _payload):
    """NOOP to clear out the queue via a hackery"""
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def run_command(cmd: list[str]) -> bool:
    """Common command running logic."""
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as proc:
        (stdout, stderr) = proc.communicate()
        if proc.returncode != 0:
            LOG.error(
                "Command %s failed with %s\n%s",
                " ".join(cmd),
                stdout.decode("utf-8"),
                stderr.decode("utf-8"),
            )
            return False
    return True


def get_wind_obs(dt: date, lon: float, lat: float) -> list[float]:
    """Get what we need from IEMRE."""
    # Hopefully the two decimal degrees results in some caching
    uri = f"{IEMRE}/{dt:%Y-%m-%d}/{lat:.2f}/{lon:.2f}/json"
    attempts = 0
    res = {"data": []}
    while attempts < 3:
        try:
            resp = requests.get(uri, timeout=30)
            resp.raise_for_status()
            res = resp.json()
            break
        except Exception as exp:
            print(uri)
            LOG.exception(exp)
        attempts += 1
        if attempts == 3:
            LOG.warning("Failed to get %s, returning 1s", uri)
            return [1.0] * 24
    hourly = []
    for entry in res["data"]:
        try:
            vel = (entry["uwnd_mps"] ** 2 + entry["vwnd_mps"] ** 2) ** 0.5
        except Exception:
            vel = 1.0
        hourly.append(vel)
    for _i in range(len(hourly), 24):
        hourly.append(1.0)
    return hourly


def run_sweep(payload: SweepJobPayload) -> SweepJobResult | None:
    """Actually run wepp, really.

    Parameters
    ----------
    payload : SweepJobPayload
        Validated SWEEP job payload containing runfile content and executable.
    """
    # We run timeout to keep things from hanging indefinitely, we tried 60
    # seconds but it was too short as sometimes latency happens.
    sweepinfn = (
        f"/i/{payload.scenario}/sweepin/{payload.huc_12[:8]}/"
        f"{payload.huc_12[8:12]}/{payload.huc_12}_{payload.fpath}.sweepin"
    )
    # Compute the management df to get the crop code needed for downstream
    if not os.path.isfile(sweepinfn):
        LOG.warning("%s does not exist, copying template", sweepinfn)
        shutil.copyfile("sweepin_template.txt", sweepinfn)
    sweepoutfn = sweepinfn.replace("sweepin", "sweepout")
    # sweep arbitarily sets the erod output file to be the same as the
    # sweepin, but with a erod extension.
    erodfn = sweepinfn.replace(".sweepin", ".erod")
    windobs = get_wind_obs(payload.dt, payload.lon, payload.lat)
    with open(sweepinfn, "r", encoding="utf-8") as fh:
        lines = list(fh.readlines())
    found = False
    for linenum, line in enumerate(lines):
        if not found and line.find(" awu(i)") > -1:
            found = True
            continue
        if found and not line.startswith("#"):
            for i in range(4):
                sl = slice(i * 6, (i + 1) * 6)
                lines[linenum + i] = (
                    " ".join([str(round(x, 2)) for x in windobs[sl]]) + "\n"
                )
            break
    with open(sweepinfn, "w", encoding="utf-8") as fh:
        fh.write("".join(lines))
    # 2. Run Rscript to replace grph file content
    cmd = [
        "Rscript",
        "--vanilla",
        "magic.R",
        sweepinfn,
        sweepinfn.replace("sweepin", "grph"),
        sweepinfn.replace("sweepin", "sol"),
        f"{payload.dt.year}",
        sweepinfn.replace("sweepin", "rot")[:-4] + "_1.txt",
        f"{payload.dt:%j}",
        f"{payload.crop}",
    ]
    if not run_command(cmd):
        return None
    # 3. Run sweep with given sweepin file, writing to sweepout
    cmd = [
        payload.sweepexe,
        f"-i{sweepinfn}",  # yuck
        "-Erod",
    ]
    if not run_command(cmd):
        return None
    # Move the erod file into the sweepout directory
    shutil.move(erodfn, sweepoutfn)
    # 4. Harvest the result and profit.
    erosion = None
    with open(sweepoutfn, encoding="utf-8") as fh:
        tokens = fh.read().strip().split()
        # total soil loss, saltation loss, suspension loss, PM10 loss
        erosion = float(tokens[0])
    return SweepJobResult(
        field_id=payload.field_id,
        dt=payload.dt,
        scenario=payload.scenario,
        erosion=erosion,
        max_wmps=max(windobs),
        avg_wmps=sum(windobs) / len(windobs),
        drct=0,  # hard coded at the moment
    )


def send_result(ch: Channel, payload: str):
    """Send to RabbitMQ, back on the main thread."""
    ch.basic_publish(
        exchange="",
        routing_key="sweep_results",
        body=payload,
    )


def run(ch: Channel, delivery_tag, payload):
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
        job = SweepJobPayload.model_validate_json(payload)
        result = run_sweep(job)
        if result is not None:
            cb = partial(send_result, ch, result.model_dump_json())
            ch.connection.add_callback_threadsafe(cb)

    except ValidationError as exp:
        # Invalid payload structure - log the validation errors
        LOG.error("Invalid payload format: %s", exp)
        LOG.error("Raw payload: %s", payload[:200])  # Log first 200 chars
    except Exception as exp:
        LOG.error("run_sweep exception: %s", exp)
        LOG.error("Traceback: %s", traceback.format_exc())

    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def ack_message(ch: Channel, delivery_tag):
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

    conn, _config = get_rabbitmqconn()
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
@click.option("--queue", default="depsweep", help="Queue name to consume from")
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
