"""Bootstrap database for dynamic tillage."""

from datetime import date

import click
from pandas.io.sql import read_sql
from pydep.tillage import make_tillage
from pyiem.database import get_dbconnc, get_sqlalchemy_conn
from pyiem.util import logger
from sqlalchemy import text

LOG = logger()


@click.command()
@click.option("--year", type=int, help="Year to bootstrap", required=True)
@click.option("--scenario", type=int, default=0)
def main(year, scenario):
    """Run for the given year."""
    with get_sqlalchemy_conn("idep") as conn:
        # Delete current year's data
        res = conn.execute(
            text("""
                 delete from field_operations o USING fields f
                 WHERE o.field_id = f.field_id and o.year = :year
                 and f.scenario = :scenario
                 """),
            {"year": year, "scenario": scenario},
        )
        LOG.info("deleted %s field operation rows", res.rowcount)
        conn.commit()
        # figure out the fields we need to compute
        fields = read_sql(
            text("""
                select field_id, landuse, management,
                st_y(st_centroid(st_transform(geom, 4326))) as lat
                from fields where scenario = :scenario
                and isag and landuse is not null and management is not null
            """),
            conn,
            params={"scenario": scenario},
            index_col="field_id",
        )
    LOG.info("Processing %s fields", len(fields.index))
    conn, cursor = get_dbconnc("idep")
    colidx = year - 2007
    inserts = 0
    for field_id, row in fields.iterrows():
        zone = "KS_NORTH"
        if row["lat"] >= 42.5:
            zone = "IA_NORTH"
        elif row["lat"] >= 41.5:
            zone = "IA_CENTRAL"
        elif row["lat"] >= 40.5:
            zone = "IA_SOUTH"
        res = make_tillage(
            scenario,
            zone,
            row["landuse"][colidx - 1],
            row["landuse"][colidx],
            row["landuse"][colidx - 2],  # HACK
            row["management"][colidx],
            year - 2006,
        )
        events = 0
        for line in res.split("\n"):
            tokens = line.split()
            if len(tokens) < 5 or tokens[4] != "Tillage" or int(tokens[0]) > 6:
                continue
            events += 1
        # till1, till2, till3, plant
        dates = [None, None, None, None]
        if events == 1:
            dates[3] = date(year, 6, 1)
        elif events == 2:
            dates[0] = date(year, 6, 1)
            dates[3] = date(year, 6, 2)
        elif events == 3:
            dates[0] = date(year, 6, 1)
            dates[1] = date(year, 6, 2)
            dates[3] = date(year, 6, 3)
        elif events == 4:
            dates[0] = date(year, 6, 1)
            dates[1] = date(year, 6, 2)
            dates[2] = date(year, 6, 3)
            dates[3] = date(year, 6, 4)
        elif events > 4:
            LOG.info("events: %s", events)
            LOG.info("res: %s", res)
            raise ValueError("too many events")
        cursor.execute(
            """
            INSERT into field_operations
            (field_id, year, till1, till2, till3, plant)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (field_id, year, dates[0], dates[1], dates[2], dates[3]),
        )
        inserts += 1
        if inserts % 10_000 == 0:
            cursor.close()
            conn.commit()
            cursor = conn.cursor()

    cursor.close()
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
