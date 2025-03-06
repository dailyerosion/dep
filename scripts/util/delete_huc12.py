"""Delete all traces of a HUC12"""

import glob
import os

import click
from pyiem.database import get_sqlalchemy_conn, sql_helper


def do_delete(conn, huc12, scenario):
    """Delete all things."""
    params = {"huc12": huc12, "scenario": scenario}
    res = conn.execute(
        sql_helper("""
    delete from flowpath_ofes pts using flowpaths f where
    pts.flowpath = f.fid and f.huc_12 = :huc12 and f.scenario = :scenario
    """),
        params,
    )
    print(f"removed {res.rowcount} flowpath_ofes")

    res = conn.execute(
        sql_helper("""
    delete from field_operations o using fields f where
    o.field_id = f.field_id and f.huc12 = :huc12 and f.scenario = :scenario
    """),
        params,
    )
    print(f"removed {res.rowcount} field_operations")

    for table in ["flowpaths", "results_by_huc12", "huc12", "fields"]:
        hcol = "huc_12" if table != "fields" else "huc12"
        res = conn.execute(
            sql_helper(
                """
        DELETE from {table} where {hcol} = :huc12 and scenario = :scenario
        """,
                table=table,
                hcol=hcol,
            ),
            params,
        )
        print(f"removed {res.rowcount} from {table}")

    # Remove some files
    for prefix in "env error man prj run slp sol wb".split():
        dirname = f"/i/{scenario}/{prefix}/{huc12[:8]}/{huc12[8:]}"
        if not os.path.isdir(dirname):
            continue
        os.chdir(dirname)
        files = glob.glob("*.*")
        for fn in files:
            os.unlink(fn)
        os.rmdir(dirname)
        print(f"Removed {len(files)} files from {dirname}")

        # Try to remove the huc8 folder
        os.rmdir(f"/i/{scenario}/{prefix}/{huc12[:8]}")


@click.command()
@click.option("--huc12", required=True, help="HUC12 to delete")
@click.option("--scenario", required=True, help="Scenario", type=int)
def main(huc12: str, scenario: int):
    """Go Main Go"""
    with get_sqlalchemy_conn("idep") as conn:
        do_delete(conn, huc12, scenario)
        conn.commit()


if __name__ == "__main__":
    main()
