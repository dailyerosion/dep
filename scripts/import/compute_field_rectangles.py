"""For WEPS, we need simplified field rectangles.

See dailyerosion/dep/issues/435
"""

import click
from pyiem.database import get_dbconn
from pyiem.util import logger

LOG = logger()


@click.command()
@click.option("-s", "--scenario", type=int, required=True)
def main(scenario: int):
    """Do great things."""
    pgconn = get_dbconn("dep")
    while True:
        cursor = pgconn.cursor()
        # Chunk it to manage memory, avoid long transaction
        cursor.execute(
            """
        with myfields as (
            select field_id, geom,
            ST_Area(geom) as poly_area,
            ST_OrientedEnvelope(geom) AS env
            from field where scenario_id = %s and
            rectangle_length_m is null LIMIT 10000
        ), pts as (
            select *,
            ST_PointN(ST_ExteriorRing(env), 1) AS p1,
            ST_PointN(ST_ExteriorRing(env), 2) AS p2,
            ST_PointN(ST_ExteriorRing(env), 3) AS p3
            FROM myfields
        ), edges AS (
            SELECT
            *,
            ST_Distance(p1, p2) AS d12,
            ST_Distance(p2, p3) AS d23,
            sqrt(poly_area / greatest(ST_Area(env), 0.1)) AS scale
            FROM pts
        ), newvals as (
        SELECT
        field_id, poly_area,

        -- area-preserving length
        CASE
            WHEN d12 >= d23 THEN d12 * scale
            ELSE d23 * scale
        END AS length,

        -- area-preserving width
        CASE
            WHEN d12 >= d23 THEN d23 * scale
            ELSE d12 * scale
        END AS width,

        -- rotation clockwise from north
        CASE
            WHEN d12 >= d23 THEN
                degrees(ST_Azimuth(p1, p2))
            ELSE
                degrees(ST_Azimuth(p2, p3))
        END AS rotation_deg

        FROM edges
        )
        UPDATE field f SET
        rectangle_length_m = n.length,
        rectangle_width_m = n.width,
        rectangle_rotation_deg =(
        case when n.rotation_deg > 180 then n.rotation_deg - 180
        else n.rotation_deg end)
        FROM newvals n WHERE f.field_id = n.field_id
            """,
            (scenario,),
        )
        updates = cursor.rowcount
        LOG.info(f"Computed {updates} field rectangles")
        cursor.close()
        if updates < 10_000:
            LOG.info("Exhausted...")
            break
        pgconn.commit()
    pgconn.close()


if __name__ == "__main__":
    main()
