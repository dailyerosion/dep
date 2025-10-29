-- calc_mwDEP_SoilParameters.sql
-- Based on a 2003 AML, calculate soil paramters for WEPP soil loss modeling
-- This program create the soil paramater table andfollws with an update procedure 
-- for custom assignment of KI, KR, TC, and KB based on varying soil particle
-- fractions.
--
-- In time, the data extracted here will be used to develop WEPP soil files (.sol)
-- in order to assign values to soils profiles for individual mapunit components.
--
-- Note: this script requires the mwDEP_SurfaceTexture table to be present
--
-- original coding: D. James 11/2012
--  4/3/2013- Changed the horizon counter to use chkey due to missing hzname records
--  4/19/2013 - instituted the use of the mwDEP_SurfaceTexture file to account for 
--     TextureGroup RV indicator values either missing or incorrect (dave's supposition)
--     see Calc_WEPP_SurfaceTxt_withsubQuery.sql
--
--   05/02/2013 - Replace missing CEC7 values with ECEC values, where there
--      is a valid ECEC value to populate the KB field.
--
--  7/2014 - modify to reflect the current state of the WEPP soil parameters as derived
--     from the SSURGO data...and fix a couple of errors
--
-- 09/2014 - Update to use FY2014 soils and the newly created IA_DomComp2014 table
-- 06/2015 - Update to use the newly created MWDEP_DomComp2014 table
--           Add seetting ARITHABORT & ANSI_WARNINGS to allow for divide by 0 for
--            what appear to non-soil entries, i.e. HrzCount = 0
-- 10/28/2019 - Modify write to Kr to be 8.4

SET ARITHABORT OFF
SET ANSI_WARNINGS OFF
USE DEPSoils2020

IF OBJECT_ID('dbo.DEP_HrzCount') IS NOT NULL 
        DROP TABLE dbo.DEP_HrzCount
set search_path=gssurgo25;
 SELECT dom.cokey
      , Count(F.chkey) as HrzCount
      
   INTO DEP_HrzCount
   FROM US_DomComponents dom left join DEP_SoilFractions F 
        ON F.cokey = dom.cokey       
   GROUP BY dom.cokey
   ORDER BY dom.cokey;


IF OBJECT_ID('dbo.DEP_SoilParameters') IS NOT NULL 
        DROP TABLE dbo.DEP_SoilParameters

-- check this (3,118 rows updated)
update chorizon SET ecec_r = null where ecec_r = 0;

Print 'Extract & create WEPP Parameter table'
SELECT DOM.mukey
    ,C.hydgrp as hydrogroup
      ,C.cokey
      ,C.compname
      ,C.comppct_r
      ,C.albedodry_r as Albedo
      ,HC.HrzCount
      ,chtgrp.tgtexture as Texture
      ,chtgrp.txtxtclass as TextureClass
      ,hrz.chkey 
      ,hrz.hzname
      ,hrz.hzdept_r
      ,hrz.hzdepb_r
      ,hrz.kwfact
      ,CASE
          WHEN hrz.sandtotal_r >= 30 THEN
            2728000 + ( 192100 * hrz.sandvf_r )
          WHEN hrz.sandtotal_r < 30 and hrz.claytotal_r <= 40 THEN
            6054000 - ( hrz.claytotal_r * 55130 )
          ELSE 
            6054000 - ( 40 * 55130 )
        END as KI
        
      ,CASE
          WHEN hrz.sandtotal_r >= 30 THEN
            ( 0.00197 + (hrz.sandvf_r * 0.0003 )) + ( 0.03863 * EXP( -1.84 * hrz.om_r) )
          WHEN hrz.sandtotal_r < 30 and hrz.claytotal_r <= 40 THEN
            0.0069 + (0.134 * EXP(hrz.claytotal_r * -0.2))
          ELSE
            0.0069 + (0.134 * EXP(40 * -0.2))
        END as KR
        
      ,CASE
          WHEN hrz.sandtotal_r >= 30 and hrz.claytotal_r <= 40 THEN
            2.67 + (hrz.claytotal_r * 0.065) - (hrz.sandvf_r * 0.058)
          WHEN hrz.sandtotal_r < 30 and hrz.claytotal_r > 40 THEN
            2.67 + (40 * 0.065) - (hrz.sandvf_r * 0.058)
          ELSE
            3.5 
         END as TC
         
      ,CASE 
           WHEN hrz.claytotal_r > 40 THEN
              0.0066 * EXP(244.0 / hrz.claytotal_r)
           ELSE
              CASE
                WHEN hrz.cec7_r Is Null THEN
                   -0.265 + (0.0086 * POWER(hrz.sandtotal_r, 1.8)) + ( 11.46 * POWER(hrz.ecec_r, -0.75))
                WHEN hrz.cec7_r <= 1 THEN
                   11.195 + (0.0086 * POWER(hrz.sandtotal_r, 1.8))
                ELSE
                   -0.265 + (0.0086 * POWER(hrz.sandtotal_r, 1.8)) + ( 11.46 * POWER(hrz.cec7_r, -0.75))
              END
           END as KB

  INTO DEP_SoilParameters
  FROM US_DomComponents dom left join component C 
  ON  dom.cokey = C.cokey
         LEFT JOIN chorizon hrz ON hrz.cokey = C.cokey 
          LEFT JOIN DEP_HrzCount HC ON HC.cokey = C.cokey 
            LEFT OUTER JOIN DEP_SurfaceTexture chtgrp ON hrz.chkey = chtgrp.chkey 
  where hrz.hzdept_r = 0 -- and hrz.claytotal_r > 0 -- C.majcompflag = 'Yes' and
  order by dom.mukey, C.comppct_r DESC;
GO

Print ''
Print 'Alter columns to accept NULL'
ALTER TABLE DEP_SoilParameters ALTER COLUMN Albedo DECIMAL(8,2) NULL
ALTER TABLE DEP_SoilParameters ALTER COLUMN KI DECIMAL(18,3) NULL
ALTER TABLE DEP_SoilParameters ALTER COLUMN TC DECIMAL(8,3) NULL
ALTER TABLE DEP_SoilParameters ALTER COLUMN KR DECIMAL(8,4) NULL
ALTER TABLE DEP_SoilParameters ALTER COLUMN KB DECIMAL(8,3) NULL
GO


DELETE FROM DEP_SoilParameters 
WHERE mukey IN
(SELECT distinct mukey
  FROM DEP_SoilFractions
  WHERE (CEC7 is null and ECEC is null) or VFSand is null or Clay is null);
GO