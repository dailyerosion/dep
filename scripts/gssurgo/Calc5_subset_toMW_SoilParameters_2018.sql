USE DEP_Soils
GO

SELECT sp.mukey
      ,sp.cokey
      ,sp.compname
      ,sp.comppct_r
      ,sp.Albedo
      ,sp.HrzCount
      ,sp.Texture
      ,sp.chkey
      ,sp.hzname
      ,sp.hzdept_r
      ,sp.hzdepb_r
      ,sp.KI
      ,sp.KR
      ,sp.TC
      ,sp.KB
  INTO dbo.MWDEP_SoilParameters
  FROM dbo.DEP_SoilParameters sp left join dbo.mw2018_mapunittable m on sp.mukey = m.mukey
  WHERE sp.mukey = m.mukey

GO


