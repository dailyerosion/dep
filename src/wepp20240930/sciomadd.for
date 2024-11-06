      subroutine sciomeradd
c
c     + + + PURPOSE + + +
c     Accumulates the biomass that is used in the calculation of the
c     OM factor portions of the NRCS SCI. This is done for each OFE and
c     tracked seperately. These are only the raw numbers, they still need to be scaled
c     by Renner factors which is left to the interface to do.
c
c     + + + KEYWORDS + + +
c        
c     + + + PARAMETERS + + +
c
c     + + + COMMON BLOCKS + + +
       include 'pmxres.inc'
       include 'pmxtil.inc'
       include 'pmxpln.inc'
       include 'pmxtls.inc'
       include 'pntype.inc'
       include 'cstruc.inc'
       include 'ccrpvr1.inc'
c
c     + + + LOCAL VARIABLES + + +
      real resonground,standdead, ressub,resroot
      integer i
c
c     + + + LOCAL DEFINITIONS + + +
     
c
c     + + + SUBROUTINES CALLED + + +
c
c     + + + END SPECIFICATIONS + + +
c
      do 100 i = 1, nplane
c       all residue on ground - current, old, previous
        resonground = rmogt(1,i) + rmogt(2,i) + rmogt(3,i)
     
c       standing dead biomass
        standdead = rmagt(i)

c       all submerged residue - current, old, previous            
        ressub = smrm(1,i) + smrm(2,i) + smrm(3,i)      

c       all dead root in top 15cm - current, old, previous
        resroot = rtm(1,i) + rtm(2,i) + rtm(3,i)
      
        allbiomass_sum(i) = allbiomass_sum(i) + resonground + 
     1    standdead + ressub + resroot
 100  continue
  
      days_sum = days_sum + 1
      
      return
      end
