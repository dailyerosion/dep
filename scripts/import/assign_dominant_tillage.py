"""Compute the dominant tillage code for each HUC12."""
# stdlib
import sys

# third party
from pyiem.util import get_dbconn


def main(argv):
    """Do great things."""
    scenario = int(argv[1])
    pgconn = get_dbconn("idep")
    cursor = pgconn.cursor()
    # Very small percentage have ties, so take max tillage code in that case
    cursor.execute(
        """
        with data as (
            select huc_12, regexp_split_to_table(management, '') as ch
            from flowpaths p JOIN flowpath_points t on (p.fid = t.flowpath)
            where p.scenario = %s
            ORDER by management desc, flowpath, fpath),
        agg as (select ch, huc_12, count(*) from data
            WHERE ch != '0' GROUP by ch, huc_12),
        agg2 as (select huc_12, ch::int, rank() OVER (PARTITION by huc_12
            ORDER by count DESC, ch DESC) from agg)

        UPDATE huc12 h SET dominant_tillage = a.ch FROM agg2 a
        WHERE h.scenario = %s and h.huc_12 = a.huc_12 and
        a.rank = 1 and
        (h.dominant_tillage is null or h.dominant_tillage != a.ch)
        """,
        (scenario, scenario),
    )
    print(f"Updated dominant_tillage for {cursor.rowcount} HUC12s")
    pgconn.commit()
    pgconn.close()


if __name__ == "__main__":
    main(sys.argv)
