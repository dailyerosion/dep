"""NOTE: Legacy code for job exec.

    $ python proctor.py <scenario>
"""
import sys
import os
import subprocess
import datetime
from multiprocessing.pool import ThreadPool

from pyiem.dep import load_scenarios
from pyiem.util import get_dbconn

YEARS = datetime.date.today().year - 2006
# need to regenerate run files on 2 January
FORCE_RUNFILE_REGEN = (
    datetime.date.today().month == 1 and datetime.date.today().day == 2
)


class WeppRun(object):
    """Represents a single run of WEPP

    Filenames have a 51 character restriction
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
        return "/i/%s/%s/%s/%s_%s.%s" % (
            self.scenario,
            prefix,
            self.subdir,
            self.huc12,
            self.fpid,
            prefix,
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

    def get_error_fn(self):
        """Return the event filename for this run"""
        return self._getfn("error")

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

    def make_runfile(self):
        """Create a runfile for our runs"""
        out = open(self.get_runfile_fn(), "w", encoding="utf8")
        out.write("E\n")  # English units
        out.write("Yes\n")  # Run Hillslope
        out.write("1\n")  # Continuous simulation
        out.write("1\n")  # hillslope version
        out.write("No\n")  # pass file output?
        out.write("1\n")  # abbreviated annual output
        out.write("No\n")  # initial conditions output
        out.write("/dev/null\n")  # soil loss output file
        out.write("No\n")  # Do water balance output
        # out.write("%s\n" % (self.get_wb_fn(),))   # water balance output file
        out.write("No\n")  # crop output
        # out.write("%s\n" % (self.get_crop_fn(),))  # crop output file
        out.write("No\n")  # soil output
        out.write("No\n")  # distance and sed output
        out.write("No\n")  # large graphics output
        out.write("Yes\n")  # event by event output
        out.write("%s\n" % (self.get_env_fn(),))  # event file output
        out.write("No\n")  # element output
        # out.write("%s\n" % (self.get_ofe_fn(),))
        out.write("No\n")  # final summary output
        out.write("No\n")  # daily winter output
        out.write("Yes\n")  # plant yield output
        out.write("%s\n" % (self.get_yield_fn(),))  # yield file
        out.write("%s\n" % (self.get_man_fn(),))  # management file
        out.write("%s\n" % (self.get_slope_fn(),))  # slope file
        out.write("%s\n" % (self.get_clifile_fn(),))  # climate file
        out.write("%s\n" % (self.get_soil_fn(),))  # soil file
        out.write("0\n")  # Irrigation
        out.write("%s\n" % (YEARS,))  # years 2007-
        out.write("0\n")  # route all events

        out.close()

    def run(self):
        """Actually run wepp for this event"""
        runfile = self.get_runfile_fn()
        if FORCE_RUNFILE_REGEN or not os.path.isfile(runfile):
            # If this scenario does not have a run file, hmmm
            self.make_runfile()
        proc = subprocess.Popen(
            ["wepp"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        (stdoutdata, stderrdata) = proc.communicate(open(runfile, "rb").read())
        if stdoutdata[-13:-1] != b"SUCCESSFULLY":
            print(
                ('Run HUC12: %s FPATH: %4s errored! "%s"')
                % (self.huc12, self.fpid, stdoutdata[-13:-1])
            )
            efp = open(self.get_error_fn(), "wb")
            efp.write(stdoutdata)
            efp.write(stderrdata)
            efp.close()
            return False
        return True


def realtime_run(config, scenario):
    """Do a realtime run, please"""
    idep = get_dbconn("idep")
    icursor = idep.cursor()

    icursor.execute(
        "SELECT huc_12, fpath, climate_file from flowpaths "
        "where scenario = %s",
        (int(config["flowpath_scenario"]),),
    )
    queue = []

    clscenario = int(config["climate_scenario"])
    for row in icursor:
        clifile = row[2]
        if scenario in [140, 141]:
            clifile = f"/i/{scenario}/cli/{row[0]}.cli"
        elif clscenario != 0:
            clifile = clifile.replace("/0/", f"/{clscenario}/")
        queue.append([row[0], row[1], clifile])
    return queue


def main(argv):
    """Go Main Go"""
    scenario = int(argv[1])
    sdf = load_scenarios()
    queue = realtime_run(sdf.loc[scenario], scenario)
    pool = ThreadPool()  # defaults to cpu-count
    sz = len(queue)
    failures = 0

    def _run(row):
        """Run !"""
        wr = WeppRun(row[0], row[1], row[2], scenario)
        return wr.run()

    sts00 = datetime.datetime.now()
    sts0 = datetime.datetime.now()
    for i, res in enumerate(pool.imap_unordered(_run, queue), 1):
        if not res:
            failures += 1
        if failures > 100:
            print("ABORT due to more than 100 failures...")
            sys.exit(10)
        if i > 0 and i % 5000 == 0:
            delta00 = datetime.datetime.now() - sts00
            delta0 = datetime.datetime.now() - sts0
            speed00 = i / delta00.total_seconds()
            speed0 = 5000 / delta0.total_seconds()
            remaining = ((sz - i) / speed00) / 3600.0
            sts0 = datetime.datetime.now()
            print(
                (
                    "%5.2fh Processed %6s/%6s [inst/tot %.2f/%.2f rps] "
                    "remaining: %5.2fh"
                )
                % (
                    delta00.total_seconds() / 3600.0,
                    i,
                    sz,
                    speed0,
                    speed00,
                    remaining,
                )
            )


if __name__ == "__main__":
    main(sys.argv)
