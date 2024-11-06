
c     begin include file ccrpgro.inc

c     + + + COMMON BLOCK DESCRIPTION + + +
c     + + + INSERT DESCRIPTION HERE  + + +

      common /crpgro/   be(ntype),otemp(ntype),hi(ntype),hia(mxplan),
     1                  vdmx(mxplan),beinp(ntype),daymin,daylen,ytn,
     1                  y4(ntype),extnct(ntype)
     1                  ,beinpfac(ntype),yldrun,crpnm,crpno,
     1                  hitype(ntype);

c     + + + VARIABLE DECLARATIONS + + +

      real              be,otemp,hi,hia,vdmx,beinp,daymin,
     1                  daylen,ytn,y4,extnct,
     1                  beinpfac
      logical           yldrun
      character*8       crpnm
      integer           crpno, hitype

c     + + + VARIABLE DEFINITIONS + + +

c     be(ntype)           : adjusted biomass conversion factor (kg/MJ)
c     otemp(ntype)        : optimum temperature for plant growth (C)
c     hi(ntype)           : optimum harvest index
c     hia(mxplan)         : adjusted harvest index (water stress)
c     vdmx(mxplan)        : maximum biomass at maturity
c     beinp(ntype)        : input biomass conversion factor (kg/MJ)
c     daymin              : minimum day length (hours)
c     daylen              : day length (hours)
c     ytn                 : funtion of latitude - used in day length
c                           calculation (EPIC 2.194)
c     y4(ntype)           : pounds per bushel for grain crops
c     extnct(ntype)       : radiation extinction coefficient
c     hitype(ntype)       : harvest index type (1=above ground, 0=root)

c     end include file ccrpgro.inc

