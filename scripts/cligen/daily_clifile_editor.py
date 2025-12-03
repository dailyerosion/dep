"""DEP WEPP cli editor.

The concept of a tile here is somewhat tricky and needs some discussion.  Lets
assume the call defines south=43, north=48, west=-101, east=-96.  The DEP
precip grid is every 0.01 degrees and that point quasi represents the center
of a grid cell of 0.01 degrees aside.  As such, this defined tile has an
inclusive southern and western edge, ie the file at -96.0 and 48.0 would
**not** be included in the tile.

"""

import sys
from datetime import datetime

import click

from pydep.util import logger
from pydep.workflows.clifile import (
    CLIFileWorkflowFailure,
    Tile,
    daily_editor_workflow,
)

LOG = logger()


@click.command()
@click.option("--scenario", "-s", type=int, default=0, help="Scenario")
@click.option("--west", type=int, required=True, help="Left Longitude")
@click.option("--east", type=int, required=True, help="Right Longitude")
@click.option("--south", type=int, required=True, help="Bottom Latitude")
@click.option("--north", type=int, required=True, help="Top Latitude")
@click.option(
    "--date", "dt", type=click.DateTime(), required=True, help="Date"
)
@click.option(
    "--domain", default="", type=str, required=False, help="DEP Domain"
)
def main(
    scenario: int,
    west: int,
    east: int,
    south: int,
    north: int,
    dt: datetime,
    domain: str,
):
    """The workflow to get the weather data variables we want!"""
    tile = Tile(
        west=west,
        east=east,
        south=south,
        north=north,
        scenario=scenario,
        dt=dt.date(),
        domain=domain,
    )
    try:
        daily_editor_workflow(tile)
    except CLIFileWorkflowFailure as exp:
        LOG.exception(
            "CLIFileWorkflowFailure %s: %s",
            tile,
            exp,
        )
        # Allow calling scripts to see this failure
        sys.exit(3)


if __name__ == "__main__":
    main()
