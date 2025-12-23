"""Find an available precip file after we do expansion."""

import os
import subprocess

import click
import geopandas as gpd
from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.util import logger
from tqdm import tqdm

LOG = logger()


@click.command()
@click.option("--scenario", "-s", type=int, required=True, help="Scenario ID")
def main(scenario: int):
    """Go Main Go."""
    # Load up the climate_files
    with get_sqlalchemy_conn("idep") as conn:
        clidf = gpd.read_postgis(
            sql_helper("""
    select id, filepath, geom, st_x(geom) as lon, st_y(geom) as lat
    from climate_files WHERE scenario = :scenario
                 """),
            conn,
            params={"scenario": scenario},
            index_col="id",
            geom_col="geom",
        ).to_crs(epsg=5070)  # Otherwise will complain about geographic CRS
    LOG.info("Found %s climate files", len(clidf.index))

    created = 0
    failed = 0
    progress = tqdm(clidf.iterrows(), total=len(clidf.index))
    for _, row in progress:
        progress.set_description(f"Created {created}, Failed: {failed}")
        fn = row["filepath"]
        if os.path.isfile(fn):
            continue
        # Find the nearest 1_000 files
        dist = clidf.geometry.distance(row["geom"]).sort_values(ascending=True)
        copyfn = None
        for nbrid in dist.index[1:1001]:
            nbrfn = clidf.at[nbrid, "filepath"]
            if os.path.isfile(nbrfn):
                copyfn = nbrfn
                break
        if copyfn is None:
            progress.write(f"Error: {row['filepath']} has no neighbors")
            failed += 1
            continue
        mydir = os.path.dirname(fn)
        if not os.path.isdir(mydir):
            os.makedirs(mydir)
        progress.write(f"Copying {copyfn} to {fn}")
        subprocess.run(["cp", copyfn, fn], check=True)
        # Now fix the header to match its location
        subprocess.run(
            [
                "python",
                "edit_cli_header.py",
                f"--filename={fn}",
                f"--lat={row['lat']}",
                f"--lon={row['lon']}",
            ],
            check=True,
        )
        created += 1


if __name__ == "__main__":
    main()
