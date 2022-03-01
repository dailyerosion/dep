-- Extract_USSoils2021_DominantComponent.sql
-- Select the dominant component for each Mapunit in US
-- This will be the first (Row Number = 1) of the components
-- sorted by compct_r in a descending order
--
-- Only the dominant component will be used to extract the 
-- soil prarmeters for use in WEPP soil loss modeling
-- original coding: D. James 03/2013, updated 06/2020
--                  updated 12/2021 (using FY2022 soils db)

USE US_Soils2

IF OBJECT_ID('dbo.US_DomComponents') IS NOT NULL 
        DROP TABLE dbo.US_DomComponents

SELECT mukey
      ,cokey
      ,compname
      ,comppct_r   
  INTO US_DomComponents
  FROM 
     ( SELECT MU.mukey
             ,C.cokey
             ,C.compname
             ,C.comppct_r
             ,ROW_NUMBER() OVER (PARTITION BY MU.mukey ORDER BY C.comppct_r DESC) as rowNbr
        
        FROM MAPUNIT MU left join COMPONENT C ON  MU.mukey = C.mukey  
        WHERE  C.majcompflag = 'Yes' 
      ) muSelect
  where muSelect.rowNbr = 1 
  order by mukey, comppct_r DESC
GO


