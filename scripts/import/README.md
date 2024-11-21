Gelder Data Import Procedure
============================

Brian Gelder provides me a 7zip file with individual flowpaths included.  There
is one file per HUC12.

1. `python flowpath_importer.py --scenario=<scenario> --datadir=<dirname in ../../data/>`
1. `python clear_files.py --scenario=<scenario>`
1. go to ../util and run `python make_dirs.py --scenario=<scenario>`
1. cd to ../import and run `python flowpath2prj.py --scenario=<scenario>`
1. `python prj2wepp.py --scenario=<scenario>`
1. do checks below for new HUC12s
1. `python compute_huc12_attrs.py --scenario=<scenario>`
1. `python package_myhucs.py --scenario=<scenario>`
1. `python check_huc12_zero_flowpaths.py --scenario=<scenario>`
1. If new HUC12s are present, get an updated simplified HUC12 from Dave.
1. Copy laptop database tables `huc12`, `flowpaths`, `flowpath_ofes`, `fields`,
and `general_landuse` to IEMDB
1. copy `myhucs.txt` up to IEM and
   run `python clear_files.py --scenario=<scenario>`
1. extract the `dep.tar` file on IEM
1. On IEM run `cligen/locate_clifile.py --scenario=<scenario>`
1. On IEM run `util/make_dirs.py --scenario=<scenario>`

This query finds any new HUC12s and inserts the geometry into a table.

    insert into huc12
    (states, name,  huc_12, simple_geom, geom, scenario)
    select states, name, huc12,
    ST_Transform(st_geometryn(simple_geom, 1), 5070),
    ST_Transform(geom, 5070), 0 from wbd_huc12 where huc12 in
    (select distinct huc_12 from flowpaths where huc_12 not in
    (select huc_12 from huc12 where scenario = 0) and scenario = 0);

    Update huc12 h SET simple_geom = st_geometryn(p.geom, 1) FROM huc12_p250 p
    WHERE h.huc_12 = p.huc12;

We should also check that we don't have unknown tables.

    select distinct huc_12 from flowpaths where scenario = 0 and huc_12 not in (select huc_12 from huc12 where scenario = 0) ORDER by huc_12;
