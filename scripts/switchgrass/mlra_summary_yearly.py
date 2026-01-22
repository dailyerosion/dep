"""Summarize for MLRA."""

from pandas.io.sql import read_sql
from pyiem.database import get_dbconn

LABELS = {
    36: "Slopes > 3% to Switchgrass",
    37: "Slopes > 6% to Switchgrass",
    38: "Slopes > 10% to Switchgrass",
}


def main(argv):
    """Go Main Go"""
    mlra_id = int(argv[1])
    pgconn = get_dbconn("idep")

    mlraxref = read_sql(
        """
    with m as (
        select mlra_id, mlra_name, sum(st_area(geography(geom))) from mlra
        WHERE mlra_id = %s GROUP by mlra_id, mlra_name),
    h as (
        select mlra_id, sum(st_area(geography(st_transform(geom, 4326))))
        from huc12 WHERE scenario = 0 and mlra_id = %s GROUP by mlra_id
    )
    SELECT m.mlra_id, m.mlra_name, h.sum / m.sum * 100. as coverage
    from m JOIN h on (m.mlra_id = h.mlra_id)
    """,
        pgconn,
        params=(mlra_id, mlra_id),
        index_col="mlra_id",
    )

    df = read_sql(
        """
    with myhucs as (
        SELECT huc_12 from huc12 where scenario = 0 and mlra_id = %s
    )
    select r.huc_12, scenario, extract(year from valid)::int as year,
    sum(avg_loss) * 10. as loss, sum(avg_runoff) as runoff,
    sum(avg_delivery) * 10. as delivery, sum(qc_precip) as precip
    from results_by_huc12 r JOIN myhucs h on (r.huc_12 = h.huc_12)
    where r.valid >= '2008-01-01' and r.valid < '2017-01-01'
    and scenario in (0, 36, 37, 38)
    GROUP by r.huc_12, year, scenario
    """,
        pgconn,
        params=(mlra_id,),
        index_col=None,
    )
    if df.empty:
        return
    gdf = df.groupby(["scenario", "year"]).mean()
    print(
        "%s\t%s\t%.1f"
        % (
            mlra_id,
            mlraxref.at[mlra_id, "mlra_name"],
            mlraxref.at[mlra_id, "coverage"],
        ),
        end="\t",
    )
    for year in range(2008, 2017):
        for scenario in [0, 36, 37, 38]:
            df2 = gdf.loc[(scenario, year)]
            for col in ["precip", "runoff", "loss", "delivery"]:
                if col == "precip" and scenario > 0:
                    continue
                print("%.2f" % (df2[col],), end="\t")
    print()


if __name__ == "__main__":
    for mlraid in [
        106,
        107,
        108,
        109,
        121,
        137,
        150,
        155,
        166,
        175,
        176,
        177,
        178,
        179,
        181,
        182,
        186,
        187,
        188,
        196,
        197,
        204,
        205,
    ]:
        main([None, mlraid])
