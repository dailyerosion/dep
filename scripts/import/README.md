
Brian Gelder provides me a 7zip file with individual flowpaths included.  There
is one file per HUC12.

1. `python flowpath_importer.py <scenario> <dirname in ../../data/>`
1. `python clear_files.py <scenario>`
1. go to ../mangen and run `python build_management.py <scenario>`
1. go to ../util and run `python make_dirs.py <scenario>`
1. `python flowpath2prj.py <scenario>`
1. `python prj2wepp.py <scenario>`
1. `python package_myhucs.py <scenario>`
1. go to ../cligen and run `python assign_climate_file.py <scenario>`
1. If new HUC12s are present, get an updated simplified HUC12 from Dave.
1. Copy laptop database tables `flowpaths` and `flowpath_points` to IEMDB
1. copy `myhucs.txt` up to IEM and run `python clear_files.py`
1. extract the `dep.tar` file on IEM
1. On IEM run `cligen/locate_clifile.py`

 insert into huc12
 (states, hu_12_name, huc_8, huc_12, simple_geom, geom, scenario)
 select states, name, huc_8, huc_12, st_geometryn(geom, 1),
 geom, 0 from p200 where huc_12 in
 	(select distinct huc_12 from flowpaths where huc_12 not in
 		(select huc_12 from huc12 where scenario = 0) and scenario = 0);