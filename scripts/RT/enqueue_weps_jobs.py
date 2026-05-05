"""Enqueue WEPS jobs we want run.

The goal here is to run WEPS for "today" and generate the necessary SWEEP input
files with realistic values to run the model after DEP/WEPP runs.  We are
threading an ugly neddle here.

"""

import shutil
import subprocess
import time
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import click
import httpx
import pandas as pd
import pika
from enqueue_jobs import GRAPH_HUC12
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.util import logger

from dailyerosion.util import get_rabbitmqconn
from dailyerosion.workflows.sweeprun import SweepJobPayload

LOG = logger()
DAY1 = date(2007, 1, 1)


def generate_runfile(lon: float, lat: float):
    """Create the run file settings."""
    return f"""
#VERSION=1.05
#------------ WEPS SIMULATION RUN FILE ------------
# Note: Lines beginning with '#' are comment lines.
#       Lines beginning with '#   RFD' are comments used by the interface.
#
# --USER INFORMATION
#   RFD-UserName
Exercise 1
#   FarmId TractId FieldId runtypedisp RotationYears CycleCount
 |  |  | NRCS | 2 | 10
#   RFD-Site
FIPS:US-WI-097
#
# --SITE INFORMATION
#   Signed Latitude
+{lat}
#   Signed Longitude
{lon}
#   RFD-Elevation(meters)
337.99272
#   RFD-ClimateFlag|RFD-cligen.station
test1
#   RFD-WindFlag|RFD-windgen.station
test2
#
# --SIMULATION PERIOD
#   RFD-StartDate(day month year)
01 01 2007
#   RFD-EndDate(day month year)
31 12 2026
#   RFD-TimeSteps(per day)
24
#
# --RUN FILE FILENAMES (INPUT)
#   RFD-climate file
weps.cli
#   RFD-wind file
interpolated.win
#   RFD-sub-daily file
none
#   RFD-SoilFile
Bearden_I119A_70_SICL.ifc
#   RFD-ManageFile
corn_soybean_3high_mulch.man
#
# --WEPS OUTPUT OPTIONS
#   RFD-OutputFile
null
#   RFD-ReportForm
0 0 0 0 0 0
#   RFD-OutputPeriod
2
#   RFD-SubmodelOutput
0 1 0 0 0 0
#   RFD-DebugOutput
0 0 0 0 0 0
#
# --SIMULATION REGION INFORMATION
#   RFD-RegionAngle(degrees clockwise from North)
0.0
#   Origin coordinates of simulation region (meters)
0.0  0.0
#    RFD-XLength(meters)  RFD-YLength(meters)
714.08  714.08
#   RFD-Scales(place holder line - needed for older versions of WEPS)
5.5 5.5
#
#   RFD-AccNo
1
#   Accounting region coordinates (meters)
    0.0  0.0
714.08  714.08
#
#   RFD-SubregionNo
1
#   Subregion region coordinates (meters)
0.0  0.0
714.08  714.08
#   RFD-AverageSlope(ratio m/m)
-1
#   RFD-BarrierNo
0
0.0 0.0
0.0 0.0
none
0.0
0.0
0.0
#
# --CIRCULAR FIELD INFORMATION
# Note: These fields are not used by the weps simulation.
#       The shape and radius values are used by the user 
#       interface to approximate a rectangular field.  They
#       are included here so the reports can display the 
#       correct field shape.
#
#   RFD-Shape
circle
#   RFD-Radius
402.87
#   RFD-WaterErosionLoss
0.00
#   RFD-SoilRockFragments
-1
#---------- END OF SIMULATION RUN FILE ------------
"""


def test(fieldsdf: pd.DataFrame, dt: date):
    """Test things before we run."""
    for _, row in fieldsdf.iterrows():
        with TemporaryDirectory(delete=False) as tmpdir:
            runfile = generate_runfile(row["lon"], row["lat"])
            with open(Path(tmpdir) / "weps.run", "w") as fh:
                fh.write(runfile)
            # WEPS can't deal with absolute paths.
            shutil.copyfile(
                "/i/0/cli/091x047/091.80x047.50.cli", Path(tmpdir) / "weps.cli"
            )
            for hack in [
                "interpolated.win",
                "Bearden_I119A_70_SICL.ifc",
                "corn_soybean_3high_mulch.man",
            ]:
                shutil.copyfile(f"/tmp/{hack}", Path(tmpdir) / hack)
            cmd = [
                "/opt/dep/bin/weps199_21835",
                "-c0",  # no soil conditioning output
                "-E0",  # Don't run soil erosion, which we should not need
                "-e1",  # Create SWEEP files
                "-H0",  # No heartbeat output
                "-i3",  # temp debuggin
                "-I2",  # Run the given management cycles, TODO
                "-n0",  # Don't create new input files
                f"-o{dt:%d%m%Y}",  # Generate SWEEP input on this date
                f"-P{tmpdir}",  # Path to files
                "-t0",  # No confidence interval reported
                "-T0",  # No deep furrow effect
                "-W1",  # simple runoff method, perf
                "-u0",  # No resurfacing of buried roots, perf opt?
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                LOG.info("STDOUT: %s", proc.stdout)
                LOG.info("STDERR: %s", proc.stderr)
            except subprocess.CalledProcessError as exp:
                LOG.error("WEPS command failed: %s", " ".join(exp.cmd))
                LOG.error("Return code: %s", exp.returncode)
                LOG.error("STDOUT: %s", exp.stdout)
                LOG.error("STDERR: %s", exp.stderr)


@click.command()
@click.option(
    "--date",
    "-d",
    required=True,
    type=click.DateTime(),
    help="Date to run for",
)
@click.option("-s", "--scenario", type=int, help="Scenario ID", default=0)
@click.option("--myhucs", help="Specify file of HUC12s to filter job.")
@click.option("--queue", help="RabbitMQ destination", default="depweps")
def main(date: datetime, scenario: int, myhucs: str | None, queue: str):
    """Go main Go."""
    dt = date.date()
    if myhucs:
        LOG.warning("Using %s to filter job submission", myhucs)
        with open(myhucs, encoding="ascii") as fh:
            myhucs = [s.strip() for s in fh]

    with get_sqlalchemy_conn("idep") as conn:
        fieldsdf = pd.read_sql(
            sql_helper(
                """
    with data as (
        select o.field_id,
        row_number() over (partition by field_id ORDER by fpath asc),
        substr(o.landuse, :charat, 1) as crop, f.fpath, h.huc_12,
        st_pointn(st_transform(o.geom, 4326), 1) as pt, c.filepath as clifile
        from flowpath_ofes o, flowpaths f, huc12 h, climate_files c
        where o.flowpath = f.fid and f.huc_12 = h.huc_12 and
        (h.states ~* 'MN' or h.huc_12 = ANY(:graphhucs))
        and f.scenario = 0 and o.ofe = 1 and f.climate_file_id = c.id)
    select field_id, fpath, huc_12, st_x(pt) as lon, st_y(pt) as lat, crop,
    clifile from data
    where row_number = 1 and crop in ('C', 'B') {huclimit} LIMIT 1
        """,
                huclimit=" and huc_12 = ANY(:hucs)" if myhucs else "",
            ),
            conn,
            params={
                "graphhucs": GRAPH_HUC12,
                "hucs": myhucs,
                "charat": dt.year - 2007 + 1,
            },
        )
    test(fieldsdf, dt)
    return
    totaljobs = len(fieldsdf.index)
    connection, rabbit_config = get_rabbitmqconn()
    channel = connection.channel()
    # Declare queue as durable (survives broker restart)
    # This is idempotent - safe to declare multiple times
    channel.queue_declare(queue=queue, durable=True)
    sts = datetime.now()

    for row in fieldsdf.itertuples():
        payload = SweepJobPayload(
            sweepexe="/opt/dep/bin/sweep",
            field_id=row.field_id,
            fpath=row.fpath,
            huc_12=row.huc_12,
            crop=row.crop,
            dt=dt,
            scenario=scenario,
            lon=row.lon,
            lat=row.lat,
        )
        # Publish to default exchange ("") with routing_key=queue name
        # This directly routes the message to the named queue
        channel.basic_publish(
            exchange="",  # Default exchange (nameless exchange)
            routing_key=queue,  # Queue name to route to
            body=payload.model_dump_json(),
            properties=pika.BasicProperties(
                # Message survives broker restart
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
    # Wait a few seconds for the dust to settle
    time.sleep(10)
    connection.close()
    percentile = 1.0001
    while True:
        now = datetime.now()
        req = httpx.get(
            f"http://{rabbit_config['host']}:15672/api/queues/%2F/{queue}",
            auth=(rabbit_config["user"], rabbit_config["password"]),
            timeout=60,
        )
        queueinfo = req.json()
        # jobs either ready or unawked
        jobsleft = queueinfo["messages_persistent"]
        done = totaljobs - jobsleft
        if (jobsleft / float(totaljobs)) < percentile:
            LOG.warning(
                "%6i/%s [%.3f /s]",
                jobsleft,
                totaljobs,
                done / (now - sts).total_seconds(),
            )
            percentile -= 0.1
        if (now - sts).total_seconds() > 36000:
            LOG.error("ERROR, 10 Hour Job Limit Hit")
            break
        if jobsleft == 0:
            LOG.warning("Done!")
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
