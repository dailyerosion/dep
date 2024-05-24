USE DEP_Soils
GO
set search_path=gssurgo24;
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
  INTO MWDEP_SoilParameters
  FROM DEP_SoilParameters sp left join mw2018_mapunittable m on sp.mukey = m.mukey
  WHERE sp.mukey = m.mukey;

GO


