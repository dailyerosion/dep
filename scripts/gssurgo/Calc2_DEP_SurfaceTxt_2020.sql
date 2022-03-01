-- calc_mwDEP_SurfaceTexture.sql
-- Extract soils horizon data to create the WEPP soil fractions table by 
-- extracting information from the NRCS Soils Data Mart (SDM) national
-- soils database -- also known as SSURGO by some.
--
-- In time, the data extracted here will be joined with the surfical data 
-- assembled in the WEPP soil Parameters database and used to develop WEPP 
-- soil files (.sol) in support of the Iowa daily Erosion project
--
-- Note: This script is required input to the mwDEP_Soilparameters table
--       Thus, this script must have been run prior to Calc_mwDEP_spoilParameters
--
-- Extract the first (rowNbr = 1) surface texture value for each cokey
-- original coding: D. James 11/2012
--  4/19/2013 - use of the chtgrp.rvindicator deprecated due to poor values in 
--              a few records.
--
-- 09/2014 - Update to use FY2014 SDM data and the newly created IA_MapUnits2014  
-- 06/2015 - Update to use the newly created MWDEP_MapUnits2014  
-- 2018 - National

USE DEPSoils2020

IF OBJECT_ID('dbo.DEP_SurfaceTexture') IS NOT NULL 
        DROP TABLE dbo.DEP_SurfaceTexture

SELECT cokey
      ,compname
      ,comppct_r
      ,chkey
      ,tgTexture
      ,txTxtClass
      ,tgRVind
      
  INTO DEP_SurfaceTexture
  FROM 
     ( SELECT MU.mukey
             ,C.cokey
             ,C.compname
             ,C.comppct_r
             ,hrz.chkey 
             ,hrz.hzdept_r
             ,hrz.hzdepb_r
             ,tgrp.texture as tgTexture
             ,tgrp.rvindicator as tgRVind
             ,txt.texcl as txTxtClass
             ,ROW_NUMBER() OVER (PARTITION BY hrz.chkey ORDER BY C.cokey) as rowNbr
        
        FROM MAPUNIT MU left join component C ON  MU.mukey = C.mukey
         LEFT JOIN chorizon hrz ON hrz.cokey = C.cokey 
          LEFT JOIN chtexturegrp tgrp ON hrz.chkey = tgrp.chkey 
           LEFT JOIN chtexture txt ON txt.chtgkey = tgrp.chtgkey 
        
        WHERE  C.majcompflag = 'Yes' and hrz.hzdept_r = 0 
      ) txtQ  
  where txtQ.rowNbr = 1 --and chtgrp.rvindicator = 'Yes'
  order by mukey, comppct_r DESC
GO


