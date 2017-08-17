
Brian Gelder provides me a 7zip file with individual flowpaths included.  There
is one file per HUC12.

1. `python flowpath_importer.py <scenario> <dirname in ../../data/>`
2. go to ../mangen and run `python build_management.py <scenario>`
3. go to ../util and run `python make_dirs.py <scenario>`
4. `python flowpath2prj.py <scenario>`
5. `python prj2wepp.py <scenario>`
6. If new HUC12s are present, get an updated simplified HUC12 from Dave.

 insert into huc12
 (states, hu_12_name, huc_8, huc_12, simple_geom, geom, scenario)
 select states, name, huc_8, huc_12, st_geometryn(geom, 1),
 geom, 0 from p200 where huc_12 in
 	(select distinct huc_12 from flowpaths where huc_12 not in
 		(select huc_12 from huc12));