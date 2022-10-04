-- Create gssurgo table entries
-- CHECK that this matches what happens in write_DEP2020_WEPPSoils.py

INSERT into gssurgo(fiscal_year, mukey, label, kwfact, hydrogroup)
SELECT 2022, mukey::int, compname, kwfact::real, hydrogroup
FROM DEP_SoilParameters
WHERE HrzCount > 0 AND Albedo Is Not Null AND compname != 'Aquolls'
AND KI Is Not Null AND KR Is Not Null AND TC Is Not Null
AND KB Is Not Null;
