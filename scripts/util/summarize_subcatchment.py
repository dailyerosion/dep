"""A one off."""

import pandas as pd

from pydep.reference import KG_M2_TO_TON_ACRE

DATA = {
    "070802090102": [
        92,
        2,
        100,
        93,
        429,
        261,
        317,
        450,
        52,
        205,
        170,
        192,
        54,
        33,
        47,
    ],
    "070802090301": [
        29,
        65,
        86,
        142,
        107,
        45,
        17,
        486,
        122,
        3,
        31,
        164,
        115,
        479,
        101,
        262,
        437,
        150,
        444,
        500,
        507,
        451,
        340,
        74,
        32,
        312,
    ],
    "070802090302": [
        302,
        170,
        440,
        224,
        27,
        482,
        567,
        639,
        819,
        885,
        400,
        82,
        286,
    ],
}


def main():
    """Go Main Go."""
    for huc12, catchments in DATA.items():
        bdf = pd.read_csv(f"fpresults_baseline_{huc12}.csv")
        bdf["catchment"] = (bdf["fpath"] / 10_000).astype(int)
        bdf = bdf[bdf["catchment"].isin(catchments)]
        print(len(bdf.index), len(catchments))
        sdf = pd.read_csv(f"fpresults_scenario_{huc12}.csv")
        sdf["catchment"] = (sdf["fpath"] / 10_000).astype(int)
        sdf = sdf[sdf["catchment"].isin(catchments)]
        print(len(sdf.index), len(catchments))
        print(f"{huc12}")
        d1 = bdf["delivery[t/a/yr]"].mean() * KG_M2_TO_TON_ACRE
        d2 = bdf["detach[t/a/yr]"].mean() * KG_M2_TO_TON_ACRE
        print(
            f" Baseline- "
            f"Runoff: {(bdf['runoff[mm/yr]'].mean() / 25.4):.2f} in/yr "
            f"Delivery: {d1:.2f} T/a/yr "
            f"Detachment: {d2:.2f} T/a/yr"
        )
        d1 = sdf["delivery[t/a/yr]"].mean() * KG_M2_TO_TON_ACRE
        d2 = sdf["detach[t/a/yr]"].mean() * KG_M2_TO_TON_ACRE
        print(
            f" Treatment- "
            f"Runoff: {(sdf['runoff[mm/yr]'].mean() / 25.4):.2f} in/yr "
            f"Delivery: {d1:.2f} T/a/yr "
            f"Detachment: {d2:.2f} T/a/yr"
        )


if __name__ == "__main__":
    main()
