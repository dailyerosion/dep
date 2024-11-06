
c     begin include file ccrpvr1.inc

c     + + + COMMON BLOCK DESCRIPTION + + +
c     + + + INSERT DESCRIPTION HERE  + + +

      common /crpvr1/   rmogt(mxres,mxplan),rmagt(mxplan),
     1                  rtm(mxres,mxplan),smrm(mxres,mxplan),
     1                  mfo(mxtill,mxtlsq,ntype),pltol(mxplan),
     1                  rmfo(mxtill,mxtlsq,ntype),
     1                  allbiomass_sum(mxplan),
     1                  allerosion_sum(mxplan),days_sum,
     1                  resur(mxtill,mxtlsq,ntype)
c
c     + + + VARIABLE DECLARATIONS + + +

      real              rmogt,rmagt,rtm,smrm,mfo,pltol,rmfo
      real              resur
      real              allbiomass_sum, allerosion_sum
      integer           days_sum

c     + + + VARIABLE DEFINITIONS + + +

c     rmogt(mxres,mxplan)       : surface residue mass on the ground today
c                                 (kg/m^2)
c     rmagt(mxplan)             : surface residue mass above ground today
c                                 (kg/m^2)
c     rtm(mxres,mxplan)         : non living root mass (kg/m^2)
c     smrm(mxres,mxplan)        : submerged residue mass today (kg/m^2)
c     mfo(mxtill,mxtlsq,mxcrop) : fraction of initial surface residue
c                                 remaining after tillage (0-1, unitless)
c     pltol(mxplan)             : plant drought resistance factor (0 to 1),
c                                 unitless
c     rmfo(mxtill,mxtlsq,mxcrop): rill tillage intensity.  Fraction of
c                                 initial surface rill residue mass
c                                 buried by tillage (0-1, unitless)
c     allbiomass_sum(mxplan)    : total of resdue amounts, used for OM
c                                 factor calc of SCI
c     days_sum                  : total number of days simulated
c     allerosion_sum(mxplan)    : total of interrill erosion amounts, used
c                                 for ER calc of SCI (may not be needed)

c     end include file ccrpvr1.inc

