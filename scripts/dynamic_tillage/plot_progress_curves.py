"""See that we have seperation."""

import pandas as pd
from pyiem.plot import figure


def main():
    """Go Main Go."""
    fig = figure(
        title="2019 Planting Progress",
        figsize=(10.72, 7.2),
        logo="dep",
    )
    ax = fig.add_axes((0.1, 0.55, 0.7, 0.35))
    for state in ["MN", "IA"]:
        for crop in ["corn", "soybeans"]:
            progress = pd.read_csv(
                f"plots/{crop}_2019_{state}.csv",
                parse_dates=["date"],
            )
            lp = ax.plot(
                progress["date"],
                progress[f"dep_{crop}_pct"],
                label=f"DEP {crop} {state}",
            )
            ax.plot(
                progress["date"],
                progress[f"deines2023_{crop}_pct"],
                label=f"Deines2023 {crop} {state}",
                color=lp[0].get_color(),
                linestyle=":",
            )
            df = progress[progress[f"nass_{crop}_pct"].notna()]
            ax.plot(
                df["date"],
                df[f"nass_{crop}_pct"],
                label=f"Nass {crop} {state}",
                color=lp[0].get_color(),
                marker="s",
                linestyle="-.",
            )

    ax.legend(loc=(0.95, 0))
    ax.grid(True)

    ax2 = fig.add_axes((0.1, 0.1, 0.7, 0.35), sharex=ax)
    for state in ["MN", "IA"]:
        progress = (
            pd.read_csv(
                f"plots/corn_2019_{state}.csv",
                parse_dates=["date"],
            )
            .set_index("date")
            .join(
                pd.read_csv(
                    f"plots/soybeans_2019_{state}.csv",
                    parse_dates=["date"],
                ).set_index("date"),
                lsuffix="_corn",
                rsuffix="_soybeans",
            )
        )
        progress["dep_soybean_ratio"] = (
            progress["dep_soybeans_acres"]
            / (progress["dep_corn_acres"] + progress["dep_soybeans_acres"])
            * 100.0
        )
        progress["deines2023_soybean_ratio"] = (
            progress["deines2023_soybeans_acres"]
            / (
                progress["deines2023_corn_acres"]
                + progress["deines2023_soybeans_acres"]
            )
            * 100.0
        )
        progress.to_csv(f"{state}.csv")

        lp = ax2.plot(
            progress.index,
            progress["dep_soybean_ratio"],
            label=f"DEP Soybeans / (Corn + Soybeans) {state}",
        )
        ax2.plot(
            progress.index,
            progress["deines2023_soybean_ratio"],
            label=f"Deines2023 Soybeans / (Corn + Soybeans) {state} %",
            linestyle=":",
            color=lp[0].get_color(),
        )
    ax2.grid(True)
    ax2.legend()

    fig.savefig("plots/progress.png")


if __name__ == "__main__":
    main()
