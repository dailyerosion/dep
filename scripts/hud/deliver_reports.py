"""Generate and upload DEP reports."""

import geopandas as gpd
import pandas as pd
import requests
from pyiem.util import get_sqlalchemy_conn

LOOKUP = {
    "10240003": "East Nishnabotna River",
    "07080205": "Middle Cedar River",
    "07100006": "North Raccoon River",
    "07060002": "Upper Iowa River",
    "07080102": "Upper Wapsipinicon River",
    "10240002": "West Nishnabotna River",
}


def build_xref():
    """Figure out which HUC12s we need and where to file them."""
    xref = {}
    # exporthucs can use the LOOKUP
    df = gpd.read_file("exporthucs.shp")
    for _i, row in df.iterrows():
        huc8 = row["HUC_12"][:8]
        # A misfire of some HUCs in South Dakota
        if huc8 not in LOOKUP:
            continue
        refs = xref.setdefault(LOOKUP[huc8], [])
        refs.append(row["HUC_12"])

    # English River
    df = gpd.read_file("english.shp")
    for _i, row in df.iterrows():
        refs = xref.setdefault("English River", [])
        refs.append(row["HUC_12"])

    # Clear Creek
    xref["Clear Creek"] = ["070802090101", "070802090102", "070802090103"]
    # TODO Dubuque and Bee Branch Creek
    return xref


def excel_summary(hucs, name):
    """Generate a Excel file with yearly summaries."""
    with get_sqlalchemy_conn("idep") as pgconn:
        df = pd.read_sql(
            """
            SELECT huc_12, extract(year from valid) as year,
            sum(avg_loss) * 4.463 as loss_ton_per_acre,
            sum(avg_delivery) * 4.463 as delivery_ton_per_acre,
            sum(qc_precip) / 25.4 as precip_inch,
            sum(avg_runoff) / 25.4 as runoff_inch
            from results_by_huc12 WHERE
            scenario = 0 and huc_12 in %s and valid >= '2007-01-01'
            and valid < '2018-01-01' GROUP by huc_12, year
        """,
            pgconn,
            params=(tuple(hucs),),
        )
    with pd.ExcelWriter(f"{name}.xlsx") as writer:
        df.to_excel(writer, "Yearly Totals", index=False)
        gdf = df.groupby("huc_12").mean()
        gdf[
            [
                "loss_ton_per_acre",
                "delivery_ton_per_acre",
                "precip_inch",
                "runoff_inch",
            ]
        ].to_excel(writer, "Yearly Averages")
        format1 = writer.book.add_format({"num_format": "0.00"})
        worksheet = writer.sheets["Yearly Totals"]
        worksheet.set_column("A:A", 18)
        worksheet.set_column("C:F", 20, format1)
        worksheet = writer.sheets["Yearly Averages"]
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:E", 20, format1)


def workflow(hucs):
    """Do our processing please."""
    # Construct the lookup table
    with get_sqlalchemy_conn("idep") as pgconn:
        df = pd.read_sql(
            """
        select huc_12, name from huc12 where scenario = 0
        and huc_12 in %s
        """,
            pgconn,
            params=(tuple(hucs),),
            index_col="huc_12",
        )
    filenames = []
    for huc in hucs:
        if huc not in df.index.values:
            print("Huc: %s is unknown to DEP" % (huc,))
            continue
        uri = "http://depbackend.local/auto/huc12report.py?huc=%s" % (huc,)
        req = requests.get(uri)
        if req.status_code != 200:
            print("Uri: %s failed with: %s" % (uri, req.status_code))
            continue
        fn = "%s-%s.pdf" % (huc, df.at[huc, "name"].replace(" ", "_"))
        fp = open(fn, "wb")
        fp.write(req.content)
        fp.close()
        filenames.append(fn)
    return filenames


def main():
    """Go Main Go."""
    xref = build_xref()
    for name, hucs in xref.items():
        # fns = []
        fns = workflow(hucs)
        excel_summary(hucs, name)
        fns.append("%s.xlsx" % (name,))


if __name__ == "__main__":
    main()
