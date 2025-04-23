"""Place jobs into our DEP queue!"""

import datetime
import json
import os
import time
from io import StringIO

import click
import pika
import requests
from pyiem.database import get_dbconn
from pyiem.util import logger

YEARS = datetime.date.today().year - 2006
WEPPEXE = "wepp20240930"

# These are HUC12s that we currently need graph output for SWEEP
GRAPH_HUC12 = (
    "090201081101 090201081102 090201060605 102702040203 101500041202 "
    "090203010403 070200070501 070102050503 090203030703 090203030702"
).split()


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


class WeppRun:
    """Represents a single run of WEPP.

    Filenames have a 51 character restriction.
    """

    def __init__(self, huc12, fpid, clifile, scenario, ofe_count, is_irr):
        """We initialize with a huc12 identifier and a flowpath id"""
        self.huc12 = huc12
        self.huc8 = huc12[:8]
        self.subdir = f"{huc12[:8]}/{huc12[8:]}"
        self.fpid = fpid
        self.clifile = clifile
        self.scenario = scenario
        self.ofe_count = ofe_count
        self.is_irr = is_irr

    def _getfn(self, prefix):
        """boilerplate code to get a filename."""
        return (
            f"/i/{self.scenario}/{prefix}/{self.subdir}/"
            f"{self.huc12}_{self.fpid}.{prefix}"
        )

    def get_wb_fn(self):
        """Return the water balance filename for this run"""
        return self._getfn("wb")

    def get_env_fn(self):
        """Return the event filename for this run"""
        return self._getfn("env")

    def get_ofe_fn(self):
        """Return the filename used for OFE output"""
        return self._getfn("ofe")

    def get_man_fn(self):
        """Return the management filename for this run"""
        return self._getfn("man")

    def get_slope_fn(self):
        """Return the slope filename for this run"""
        return self._getfn("slp")

    def get_soil_fn(self):
        """Return the soil filename for this run"""
        return self._getfn("sol")

    def get_clifile_fn(self):
        """Return the climate filename for this run"""
        return self.clifile

    def get_runfile_fn(self):
        """Return the run filename for this run"""
        return self._getfn("run")

    def get_yield_fn(self):
        """Filename to be used for yield output"""
        return self._getfn("yld")

    def get_event_fn(self):
        """Filename to be used for event output"""
        return self._getfn("event")

    def get_crop_fn(self):
        """Filename to be used for crop output."""
        return self._getfn("crop")

    def get_graphics_fn(self):
        """Filename to be used for crop output."""
        return self._getfn("grph")

    def get_out_fn(self):
        """Filename to be used for soil loss output."""
        return self._getfn("out")

    def get_irrigation_fn(self):
        """Filename providing irrigation data."""
        return f"/i/{self.scenario}/irrigation/ofe{self.ofe_count}.txt"

    def make_runfile(self):
        """Create a runfile for our runs"""
        out = StringIO()
        out.write("E\n")  # English units
        out.write("Yes\n")  # Run Hillslope
        out.write("1\n")  # Continuous simulation
        out.write("1\n")  # hillslope version
        out.write("No\n")  # pass file output?
        out.write("1\n")  # abbreviated annual output
        out.write("No\n")  # initial conditions output
        out.write("/dev/null\n")  # soil loss output file
        # out.write(f"{self.get_out_fn()}\n")  # soil loss output file
        if self.scenario == 0:
            out.write("Yes\n")  # Do water balance output
            out.write(f"{self.get_wb_fn()}\n")  # water balance output file
        else:
            out.write("No\n")
        out.write("No\n")  # crop output
        # out.write("%s\n" % (self.get_crop_fn(),))  # crop output file
        out.write("No\n")  # soil output
        out.write("No\n")  # distance and sed output
        if self.huc12 in GRAPH_HUC12:
            out.write("Yes\n")  # large graphics output
            out.write(f"{self.get_graphics_fn()}\n")
        else:
            out.write("No\n")  # large graphics output
        out.write("Yes\n")  # event by event output
        out.write(f"{self.get_env_fn()}\n")  # event file output
        out.write("No\n")  # element output
        # out.write("%s\n" % (self.get_ofe_fn(),))
        out.write("No\n")  # final summary output
        out.write("No\n")  # daily winter output
        out.write("Yes\n")  # plant yield output
        out.write(f"{self.get_yield_fn()}\n")  # yield file
        out.write(f"{self.get_man_fn()}\n")  # management file
        out.write(f"{self.get_slope_fn()}\n")  # slope file
        out.write(f"{self.get_clifile_fn()}\n")  # climate file
        out.write(f"{self.get_soil_fn()}\n")  # soil file
        if self.is_irr:
            out.write("2\n")  # Irrigation
            out.write(f"{self.get_irrigation_fn()}\n")
        else:
            out.write("0\n")  # Irrigation
        out.write(f"{YEARS}\n")  # years 2007-
        out.write("0\n")  # route all events
        out.seek(0)
        return out.read()


@click.command()
@click.option(
    "--scenario", "s", type=int, help="Scenario ID to run", default=0
)
@click.option(
    "--runerrors", is_flag=True, help="Run previous runs that errored."
)
def main(scenario: int, runerrors: bool):
    """Go main Go."""
    log = logger()
    myhucs = []
    if os.path.isfile("myhucs.txt"):
        log.warning("Using myhucs.txt to filter job submission")
        with open("myhucs.txt", encoding="ascii") as fh:
            myhucs = [s.strip() for s in fh]
    idep = get_dbconn("idep")
    icursor = idep.cursor()

    # Figure out the source of flowpaths
    icursor.execute(
        "SELECT flowpath_scenario, climate_scenario from scenarios "
        "where id = %s",
        (scenario,),
    )
    flscenario, _clscenario = icursor.fetchone()

    icursor.execute(
        "SELECT huc_12, fpath, filepath, ofe_count, irrigated "
        "from flowpaths f JOIN climate_files c on (f.climate_file_id = c.id) "
        "where f.scenario = %s",
        (flscenario,),
    )
    totaljobs = icursor.rowcount
    connection = get_rabbitmqconn()
    channel = connection.channel()
    channel.queue_declare(queue="dep", durable=True)
    sts = datetime.datetime.now()
    for row in icursor:
        if myhucs and row[0] not in myhucs:
            continue
        clfile = row[2]
        if scenario >= 142:
            # le sigh
            clfile = clfile.replace("/0/", f"/{scenario}/")
        if runerrors:
            errfn = (
                f"/i/0/error/{row[0][:8]}/{row[0][8:]}/{row[0]}_{row[1]}.error"
            )
            if not os.path.isfile(errfn):
                continue
            os.unlink(errfn)

        wr = WeppRun(row[0], row[1], clfile, scenario, row[3], row[4])
        payload = {
            "wepprun": wr.make_runfile(),
            "weppexe": WEPPEXE,
        }
        channel.basic_publish(
            exchange="",
            routing_key="dep",
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            ),
        )
    # Wait a few seconds for the dust to settle
    time.sleep(10)
    connection.close()
    percentile = 1.0001
    while True:
        now = datetime.datetime.now()
        # Good grief, we have to manually query the queue via the API to
        # get actual unack'd messages.
        # pylint: disable=protected-access
        req = requests.get(
            f"http://{connection._impl.params.host}:15672/api/queues/%2F/dep",
            auth=("guest", "guest"),
            timeout=60,
        )
        queueinfo = req.json()
        # jobs either ready or unawked
        jobsleft = queueinfo["messages_persistent"]
        done = totaljobs - jobsleft
        if (jobsleft / float(totaljobs)) < percentile:
            log.warning(
                "%6i/%s [%.3f /s]",
                jobsleft,
                totaljobs,
                done / (now - sts).total_seconds(),
            )
            percentile -= 0.1
        if (now - sts).total_seconds() > 36000:
            log.error("ERROR, 10 Hour Job Limit Hit")
            break
        if jobsleft == 0:
            log.warning("Done!")
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
