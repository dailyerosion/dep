"""Plot how our rates work."""

from datetime import date, timedelta

import numpy as np
from pyiem.plot import figure_axes

from pydep.workflows.dyntillage import (
    get_planting_fraction,
    get_soybeans_planting_fraction,
)


def main():
    """Go Main Go."""
    soybeans_frac = get_soybeans_planting_fraction()
    planting_frac = get_planting_fraction()
    soybeans_max = np.where(
        soybeans_frac > 0.4, planting_frac, soybeans_frac * planting_frac
    )

    (fig, ax) = figure_axes(
        title="DynTill v5 Planting Rates Illustration",
        logo="dep",
    )

    ax.plot(
        np.arange(len(soybeans_frac)),
        planting_frac * soybeans_frac,
        label="Soybeans Minimum v5.0",
        ds="steps-post",
    )
    ax.plot(
        np.arange(len(soybeans_frac)),
        soybeans_max,
        label="Soybeans Maximum v5.0",
        ds="steps-post",
    )
    ax.plot(
        np.arange(len(soybeans_frac)),
        planting_frac,
        label="Total",
        ds="steps-post",
    )
    xticks = []
    xticklabels = []
    for i in range(90, 160):
        dt = date(2000, 1, 1) + timedelta(days=i - 1)
        if dt.day in [1, 8, 15, 22]:
            xticks.append(i)
            xticklabels.append(dt.strftime("%-d\n%b"))
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)
    ax.grid(True)
    ax.set_xlim(90, 160)
    ax.set_ylabel("HUC12 Acres Fraction")
    ax.legend(loc=2)

    fig.savefig("plots/planting_rates.png")


if __name__ == "__main__":
    main()
