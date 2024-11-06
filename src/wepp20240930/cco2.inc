c     begin include file cco2.inc

c     + + + COMMON BLOCK DESCRIPTION + + +
c     + + + INSERT DESCRIPTION HERE  + + +

c     NOTE : cco2.inc is used in infile.for, evap.for and grow.for.

      common /cco2/ co2run, co2, vpd(ntype), vpth(ntype), 
     1              vpd2(ntype), gsi(ntype), wac21(ntype), 
     1              wac22(ntype), wavp(ntype)

c     + + + VARIABLE DECLARATIONS + + +

      logical    co2run
      real       vpd, vpth, vpd2, gsi, co2, wac21, wac22, wavp

c     + + + VARIABLE DEFINITIONS + + +

c     vpd     : vpd=ee-ed
c     vpth    : vpth is threshold vpd for the crop
c     vpd2    : is a crop coefficient
c     gsi     : the crops leaf resistance when the vpd is less than the 
c             : crops threshold vpd
c     co2     : is the carbon dioxide level in the atmosphere in ppm
c     wac21   : crop coefficient
c     wac22   : crop coefficient
c     wavp    : radiation-use efficiency sensitivity to vpd. values of wavp
c             : are species dependent. A value of 6-8 is suggested as a first 
c             : approximation (Stockle & Kiniry, 1990)

c     end include file cco2.inc


