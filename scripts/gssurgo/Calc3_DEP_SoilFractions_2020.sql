-- calc3_DEP_SoilFractions.sql
-- Extract soils horizon data to create the WEPP soil fractions table by 
-- extracting information from the NRCS Soils Data Mart (SDM) national
-- soils database -- also known as SSURGO by some.
--
-- In time, the data extracted here will be joined with the surfical data 
-- assembled in the WEPP soil Parameters database and used to develop WEPP 
-- soil files (.sol) in support of the Iowa Daily Erosion project
--
-- Note: This script requires that the DEP_SoilFrags table is available
--       Thus, the calc1_DEP_chFrags script must have been run
--
-- original coding: D. James 11/2012
--   Remove: where C.majcompflag = 'Yes'  -- no longer required as 
--           IA_DomComponents is the MU's single dominant component
--
--   04/30/2013 - exclude from further processing the last (deepest) horizon  
--     layers (rowNbr=1) that are missing CEC7, Clay, or Sand values. The 
--     remaining layers will be used, as long as no other CEC7, Clay, or 
--     Sand values are missing from the mupunit.
--
--   05/02/2013 - Replace missing CEC7 values with ECEC values, where there
--      is a valid ECEC value.
--
-- 09/2014 - Update to use FY2014 SDM and the newly generated IA_DomComp2014
-- 06/2015 - Update to use the newly generated MWDEP_DomComp2014
-- 04/2018 - Update to US NAtional
--         - The final ORDER BY statement is not working?? So modified the
--             Write_DEP2018_WEPPSoils..py to reorder at write time
 

USE DEPSoils2020

IF OBJECT_ID('dbo.DEP_SoilFractions') IS NOT NULL 
        DROP TABLE dbo.DEP_SoilFractions

SELECT mukey
      , cokey
      , compname
      , comppct_r
      , chkey
      , hzname
      , hzdept_r
      , hzdepb_r
      , HrzThick
      , DepthTo_mm
      , OM
      , ECEC
      , CEC7
      , Sand
      , VFSand
      , Silt
      , Clay
      , FragTot
      , rowNbr
 		  
      INTO DEP_SoilFractions 
          
      FROM
	(	SELECT dom.mukey
		      ,C.cokey
		      ,C.compname
		      ,C.comppct_r
		      ,hrz.chkey
		      ,hrz.hzname
		      ,hrz.hzdept_r
		      ,hrz.hzdepb_r
		      ,hrz.hzdepb_r - hrz.hzdept_r as HrzThick
		      ,hrz.hzdepb_r * 10 as DepthTo_mm
		      ,hrz.om_r as OM
		      ,hrz.ecec_r as ECEC
		      ,CASE
		         WHEN hrz.cec7_r IS NULL
		           THEN hrz.ecec_r
		         ELSE hrz.cec7_r
		       END as cec7
		      ,hrz.sandtotal_r as Sand
		      ,hrz.sandvf_r as VFSand
		      ,hrz.silttotal_r as Silt
		      ,hrz.claytotal_r as Clay
		      ,frg.FragTot
		      ,ROW_NUMBER() OVER (PARTITION BY C.cokey ORDER BY hrz.hzdepb_r DESC) as rowNbr

		  FROM US_DomComponents dom left join component C 
		         ON dom.cokey = C.cokey
		           LEFT JOIN chorizon hrz ON hrz.cokey = C.cokey 
	                   LEFT JOIN DEP_SoilFrags frg ON hrz.chkey = frg.chkey
               
          ) bRow
WHERE NOT (bRow.rowNbr = 1 and ( CEC7 is null or Clay is null or Sand is null))
ORDER BY mukey, hzdept_r
GO

-- Alter precision/scale and allow NULL 
ALTER TABLE DEP_SoilFractions ALTER COLUMN OM DECIMAL(8,3) NULL;
ALTER TABLE DEP_SoilFractions ALTER COLUMN Sand DECIMAL(8,3) NULL;
ALTER TABLE DEP_SoilFractions ALTER COLUMN VFSand DECIMAL(8,3) NULL;
ALTER TABLE DEP_SoilFractions ALTER COLUMN Silt DECIMAL(8,3) NULL;
ALTER TABLE DEP_SoilFractions ALTER COLUMN Clay DECIMAL(8,3) NULL;
ALTER TABLE DEP_SoilFractions ALTER COLUMN CEC7 DECIMAL(8,3) NULL;
GO

UPDATE DEP_SoilFractions
 SET FragTot = 0
WHERE FragTot IS NULL;
GO

  
  
  
