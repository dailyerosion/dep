"""Plot a time-series with plastic_limit."""

import pandas as pd
from pydep.io.dep import read_wb
from pyiem.plot import figure_axes
from pyiem.util import get_dbconn


def main():
    """Go Main Go."""
    df = read_wb("/i/0/wb/10230007/0305/102300070305_60.wb")
    df = df[df["ofe"] == 2]

    cursor = get_dbconn("idep").cursor()
    cursor.execute(
        """
        SELECT plastic_limit from flowpath_ofes o, flowpaths f, gssurgo g
        WHERE o.flowpath = f.fid and o.gssurgo_id = g.id and
        f.huc_12 = '102300070305' and f.fpath = 60 and f.scenario = 0
        and o.ofe = 2
        """
    )
    pl = cursor.fetchone()[0] * 0.9

    fig, ax = figure_axes(
        title="DEP HUC12: 102300070305 Flowpath: 60 OFE: 2",
        subtitle="15 April - 1 June 0-10 cm Soil Moisture + Days below 0.9 PL",
        logo="dep",
    )
    for year in range(2007, 2023):
        sts = pd.Timestamp(year=year, month=4, day=15)
        ets = pd.Timestamp(year=year, month=6, day=1)
        df2 = df[(df["date"] >= sts) & (df["date"] < ets)].copy()
        cnt = len(df2[df2["sw1"] < pl].index)
        ax.text(
            df2["date"].values[0],
            df2["sw1"].max(),
            f"{cnt:.0f} Days",
            ha="center",
            rotation=45,
        )
        ax.plot(df2["date"].values, df2["sw1"].values)
    ax.set_ylim(10, 50)
    ax.axhline(pl)
    ax.set_ylabel("Volumetric Soil Moisture [%]")
    fig.savefig("test.png")


if __name__ == "__main__":
    main()
