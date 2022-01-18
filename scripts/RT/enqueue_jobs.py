"""Place jobs into our DEP queue!"""
import sys
import os
import datetime
import time
from io import StringIO

import pika
import requests
from pyiem.util import get_dbconn, logger

YEARS = datetime.date.today().year - 2006


class WeppRun:
    """Represents a single run of WEPP.

    Filenames have a 51 character restriction.
    """

    def __init__(self, huc12, fpid, clifile, scenario):
        """We initialize with a huc12 identifier and a flowpath id"""
        self.huc12 = huc12
        self.huc8 = huc12[:8]
        self.subdir = f"{huc12[:8]}/{huc12[8:]}"
        self.fpid = fpid
        self.clifile = clifile
        self.scenario = scenario

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
        out.write("Yes\n")  # Do water balance output
        out.write(f"{self.get_wb_fn()}\n")  # water balance output file
        out.write("No\n")  # crop output
        # out.write("%s\n" % (self.get_crop_fn(),))  # crop output file
        out.write("No\n")  # soil output
        out.write("No\n")  # distance and sed output
        if self.huc12 in ["090201081101", "090201081102", "090201060605"]:
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
        out.write("0\n")  # Irrigation
        out.write(f"{YEARS}\n")  # years 2007-
        out.write("0\n")  # route all events
        out.seek(0)
        return out.read()


def main(argv):
    """Go main Go."""
    scenario = int(argv[1])
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
        "SELECT huc_12, fpath, climate_file from flowpaths "
        "where scenario = %s",
        (flscenario,),
    )
    totaljobs = icursor.rowcount
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="iem-rabbitmq.local")
    )
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
        wr = WeppRun(row[0], row[1], clfile, scenario)
        channel.basic_publish(
            exchange="",
            routing_key="dep",
            body=wr.make_runfile(),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            ),
        )
    # Wait a few seconds for the dust to settle
    time.sleep(10)
    percentile = 1.0001
    while True:
        now = datetime.datetime.now()
        # Good grief, we have to manually query the queue via the API to
        # get actual unack'd messages.
        req = requests.get(
            "http://iem-rabbitmq.local:15672/api/queues/%2F/dep",
            auth=("guest", "guest"),
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
    main(sys.argv)
