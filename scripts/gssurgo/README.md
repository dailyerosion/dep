# DEP/ACPF GSSURGO PROCESSING

This content was handed over from David James to daryl on 11 Feb 2022.  The
`.docx` files were uploaded to Cybox team folder within `Data/David James Archive`.

## Notes

- The NRCS labels the data by fiscal year, while ACPF labels by the growing season.
So the FY2022 data would align with the 2021 ACPF year label.
- [Data Direct Download Page](https://gdg.sc.egov.usda.gov/GDGHome_DirectDownLoad.aspx).
- Currently takes us to this [box folder](https://nrcs.app.box.com/v/soils).
- Needed to use `7za` to extract the multipart zip file.
- In `Calc4`, I needed to update any `chorizon` `ecec_r` values of `0` to `null`
as there is a power function that fails in postgresql when the value is `0`. A
discussion with DJ settled that this situation is isolated to wonky soils like
`Sand Pit` and not relevant to DEP.

Ran the following commands to ingest the needed layers into postgresql

```bash
ogr2ogr -f "PostgreSQL" PG:"host=iemdb-idep.local dbname=idep" gSSURGO_CONUS_202110.gdb -nln public.component component
ogr2ogr -f "PostgreSQL" PG:"host=iemdb-idep.local dbname=idep" gSSURGO_CONUS_202110.gdb -nln public.mapunit mapunit -progress
ogr2ogr -f "PostgreSQL" PG:"host=iemdb-idep.local dbname=idep" gSSURGO_CONUS_202110.gdb -nln public.chorizon chorizon -progress
ogr2ogr -f "PostgreSQL" PG:"host=iemdb-idep.local dbname=idep" gSSURGO_CONUS_202110.gdb -nln public.chfrags chfrags -progress
ogr2ogr -f "PostgreSQL" PG:"host=iemdb-idep.local dbname=idep" gSSURGO_CONUS_202110.gdb -nln public.chtexturegrp  chtexturegrp  -progress
```
