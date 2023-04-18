-- calc_mwDEP_chFrags.sql
-- Extract soils horizon data to create the WEPP Soil Frags table by 
-- extracting information from the NRCS Soils Data Mart (SDM) national
-- soils database -- also known as SSURGO by some.
--
-- In time, the data extracted here will be joined with the surfical data 
-- assembled in the WEPP soil Parameters database and used to develop WEPP 
-- soil files (.sol) in support of the Daily Erosion project
--
-- Note: This script is required by the Calc_mwDEP_SoilFractions script
--       Thus, this script must have been run and requires the current
--       version of the dominant Components table to be present
--
-- original coding: D. James 11/2012
--  09/2014 - Updated to use FY2014 SDM data
--  06/2015 - Updated to 8-state MWDEP
--  04/2018 - Updated to US National

USE DEPSoils2020

IF OBJECT_ID('dbo.DEP_SoilFrags') IS NOT NULL 
        DROP TABLE dbo.DEP_SoilFrags

set search_path=gssurgo23;
SELECT hrz.chkey
      ,SUM(frg.fragvol_r) as FragTot
  INTO DEP_SoilFrags
  FROM US_DomComponents dom left join component C 
         ON dom.cokey = C.cokey
           LEFT JOIN chorizon hrz ON hrz.cokey = C.cokey 
           INNER JOIN CHFRAGS frg ON frg.chkey = hrz.chkey
           
  where hrz.chkey is not null
  group by hrz.chkey
  order by hrz.chkey;

  GO
  
