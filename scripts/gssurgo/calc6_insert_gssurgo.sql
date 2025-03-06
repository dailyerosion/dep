-- Create gssurgo table entries
-- CHECK that this matches what happens in write_DEP2020_WEPPSoils.py

INSERT into public.gssurgo(fiscal_year, mukey, label, kwfact, hydrogroup)
SELECT 2025, mukey::int, compname, kwfact::real, hydrogroup
FROM gssurgo25.DEP_SoilParameters
WHERE HrzCount > 0 AND Albedo Is Not Null AND compname != 'Aquolls'
AND KI Is Not Null AND KR Is Not Null AND TC Is Not Null
AND KB Is Not Null;

with data as (
    select mukey, clay, om, rank()
        OVER (PARTITION by mukey ORDER by depthto_mm ASC) from
    gssurgo25.dep_soilfractions)

update public.gssurgo g SET
plastic_limit = 14.22 + 0.005 * clay * clay + 3.63 * om - 0.048 * clay * om
from data d where d.rank = 1 and d.mukey::int = g.mukey and g.fiscal_year = 2025;
