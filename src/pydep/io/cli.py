"""DEP/WEPP Climate File Helpers."""
# pylint: disable=too-many-arguments


def daily_formatter(valid, bpdata, high, low, solar, wind, dwpt) -> str:
    """Generate string formatting the given data.

    This includes a trailing line feed.
    """
    bptext = "\n".join(bpdata)
    bptext2 = "\n" if bpdata else ""
    # https://peps.python.org/pep-0682/
    # Need to prevent the string -0.0 from appearing, so hackishness ensues
    return (
        f"{valid.day}\t{valid.month}\t{valid.year}\t{len(bpdata)}\t"
        f"{round(high, 1) + 0.0:.1f}\t{round(low, 1) + 0.0:.1f}\t"
        f"{solar:.0f}\t{wind:.1f}\t0\t{round(dwpt, 1) + 0.0:.1f}\n"
        f"{bptext}{bptext2}"
    )
