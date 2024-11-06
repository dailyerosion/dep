      subroutine resup2(nowcrp,isenes,pyld)
c
c     + + + PURPOSE + + +
c     This subroutine is called at harvest ,senescence and
c     when residue is added, to update the residue partitions.
c
c  *********************************************************************
c  * NOTE: Variable RESMGT is read by subroutine TILAGE, and is stored *
c  *       in common block CRPPRM, but is apparently NEVER USED!       *
c  *      -- CRM -- 12/01/92.                                          *
c  *********************************************************************
c
c  *********************************************************************
c  *   At senescence, or at harvest before senescence, the previous    *
c  *   residue is added to the old residue, and the current is shifted *
c  *   to the previous residue.  At senescence for annuals, and at the *
c  *   stop date for perennials, all current residues are initialized  *
c  *   to zero.  At harvest the residues are calculated as a fraction  *
c  *   of the biomass.  At harvest after senescence, the fraction of   *
c  *   the biomass is added to the current residue.                    *
c  *                                                                   *
c  *   At harvest date the root mass is updated.                       *
c  *********************************************************************
c
c     Called from DECOMP, GROW, PTGRA, and PTGRP.
c     Author(s):
c     Reference in User Guide: Chapter 8
c
c     Changes:
c          1) Removed local variable NUMRES, which was always set to '3',
c             and substituted '3' for it, and '2' for NUMRES-1.
c          2) Removed local variable NRES, which was always set to '4'.
c          3) Removed local variable NOWRES, which was always set to '1'.
c          4) The lines below seemed to exist for the sole purpose of
c             communicating with DECOMP.  Most of the values don't even
c             seem to be used.  The arrays are dimensioned to (mxcrop,mxplan)
c             in common block CRPPRM, and MXCROP is set to 5 in PMXCRP.INC.
c             Seems like a waste of memory space!  In DECOMP the code was
c             changed from XXXXXX(4,iplane) to XXXXXX(nowcrp,iplane).
c             -- CRM -- 12/01/92
c
c                jdplt(4,iplane)   = jdplt(nowcrp,iplane)
c                jdharv(4,iplane)  = jdharv(nowcrp,iplane)
c                rw(4,iplane)      = rw(nowcrp,iplane)
c                resmgt(4,iplane)  = resmgt(nowcrp,iplane)
c                jdherb(4,iplane)  = jdherb(nowcrp,iplane)
c                jdburn(4,iplane)  = jdburn(nowcrp,iplane)
c                jdslge(4,iplane)  = jdslge(nowcrp,iplane)
c                jdcut(4,iplane)   = jdcut(nowcrp,iplane)
c                jdmove(4,iplane)  = jdmove(nowcrp,iplane)
c                fbrnag(4,iplane)  = fbrnag(nowcrp,iplane)
c                fbrnog(4,iplane)  = fbrnog(nowcrp,iplane)
c                frmove(4,iplane)  = frmove(nowcrp,iplane)
c                jdstop(4,iplane)  = jdstop(nowcrp,iplane)
c                tothav(4,iplane)  = tothav(nowcrp,iplane)
c                frcut(4,iplane)   = frcut(nowcrp,iplane)
c
c     Version: This module recoded from WEPP version 91.50.
c     Date recoded: 12/06/91 - 12/24/91.
c     Updated to version 92.25.
c     Date recoded: 12/01/92 - 12/09/92.
c     Recoded by: Charles R. Meyer.
c
c     + + + KEYWORDS + + +
c
c     + + + PARAMETERS + + +
      include 'pntype.inc'
      include 'pmxtls.inc'
      include 'pmxnsl.inc'
      include 'pmxtil.inc'
      include 'ptilty.inc'
      include 'pmxpln.inc'
      include 'pmxres.inc'
      include 'pmxcrp.inc'
      include 'pmxcut.inc'
c
c     + + + ARGUMENT DECLARATIONS + + +
      integer nowcrp, isenes
CAS
      real pyld
CAS
c
c     + + + ARGUMENT DEFINITIONS + + +
c     nowcrp - index of current crop
c     isenes - flag used in resup to indicate type of update for residue
c              13 - residue removal with disturbance
c              12 - residue addition with disturbance
c              11 - residue removal with no disturbance
c              10 - residue addition with no disturbance
c               1 - harvest after senescence
c               0 - harvest before senescence
c              -1 - stop(kill) date for a perennial
c              -2 - senescence (annual)  or  1st freeze of perennial
c              14 - residue addition at annual crop cutting
c
c     + + + COMMON BLOCKS + + +
      include 'ccontcv.inc'
c     read: tilseq(
      include 'ccrpprm.inc'
c       read: itype
c     modify: iresd(mxres,mxplan), jdplt(mxcrop,mxplan),
c             jdharv(mxcrop,mxplan), rw(mxcrop,mxplan),
c             resmgt(mxcrop,mxplan), iroot(mxres,mxplan)
c
      include 'ccrpgro.inc'
c       read: vdmx(mxplan), hia(mxplan), y4(ntype)
c
      include 'ccrpout.inc'
c     modify: rtm15(mxplan)
c      write: rtm30(mxplan), rtm60(mxplan), rtmass(mxplan)
c
      include 'ccrpvr1.inc'
c     modify: smrm(mxres,mxplan), rmogt(mxres,mxplan), rmagt(mxplan)
c             rtm(mxres,mxplan)
c
      include 'ccrpvr2.inc'
c       read: vdmt(mxplan)
c
c     include 'ccrpvr3.inc'
c
      include 'ccrpvr5.inc'
c       read: pltsp(ntype), diam(ntype)
c      write: basmat(mxplan)
c
      include 'cdecvar.inc'
c     modify: benvin(mxres,mxplan), fenvin(mxres,mxplan)
c      write: senvin(mxres, mxplan)
c
      include 'cflags.inc'
c     read: yldflg
c
      include 'cperen.inc'
c       read: partcf(ntype)
c     modify: jdherb(mxcrop,mxplan), jdburn(mxcrop,mxplan),
c             jdslge(mxcrop,mxplan), jdcut(mxcrop,mxplan),
c             jdmove(mxcrop,mxplan), fbrnag(mxcrop,mxplan),
c             fbrnog(mxcrop,mxplan), frmove(mxcrop,mxplan),
c             jdstop(mxcrop,mxplan), tothav(mxcrop,mxplan),
c             frcut(mxcrop,mxplan), popmat(mxplan),
c             srmhav(mxplan)
c     modify: popmat(mxplan), srmhav(mxplan)
c
      include 'cptgrow.inc'
c     modify: idecom(mxplan)
c
      include 'cridge.inc'
c     modify: rilrm(mxres,mxplan), rigrm(mxres,mxplan)
c
      include 'cstruc.inc'
c     read: ivers
c
      include 'ctillge.inc'
c     read: resman(indxy(iplane),tillseq(nowcrp,iplane)
c
      include 'cupdate.inc'
c       read: sdate, indxy(iplane)
c
      include 'cyield.inc'
c     modify: sumyld(ntype,mxplan),sumbsh(ntype,mxplan),
c             iyldct(ntype,mxplan)
c
c     + + + LOCAL VARIABLES + + +
      !!real areacv, stemar, hyield, aghyield
      !!integer aboveYld
      !!character*30 ystr
c
c     + + + LOCAL DEFINITIONS + + +
c     nowres - 1 = current residue
c              2 = previous residue
c              3 = total of all residue prior to the previous
c
c     + + + OUTPUT FORMATS + + +
c
c     + + + END SPECIFICATIONS + + +
c
c
CAS
      integer numres
      real rmogt2, rmogt3, cf2, cf3
c     Determine number of residue groups currently being tracked
c
      if (iresd(3,iplane).ne.0) then
        numres = 3
      else if (iresd(2,iplane).ne.0) then
        numres = 2
      else
        numres = 1
      end if
CAS
      if(isenes.eq.14)then
CAS Modified codes to compute weighted average surface decomposition rates and cover factor
CAS for OLD RESIDUE POOL for senescence before harvest.
CAS
        !!write(63,*)'shifting SENES before HARVEST'
          rmogt2 = 0.0
          rmogt3 = 0.0
          rmogt2 = rmogt(2,iplane)
          rmogt3 = rmogt(3,iplane)
          
          cf2 = 0.0
          cf3 = 0.0
          cf2 = cf(2)
          cf3 = cf(3)
          
        iresd(3,iplane) = iresd(2,iplane)
        iresd(2,iplane) = iresd(1,iplane)
        iresd(1,iplane) = itype(nowcrp,iplane)
          
      !!if (iresd(3,iplane).ne.0) then
      !!  numres = 3
      !!else if (iresd(2,iplane).ne.0) then
      !!  numres = 2
      !!else
      !!  numres = 1
      !!end if
      if(numres .eq. 3) then
          cntres = cntres + 1
      else
          cntres = 0
      endif
      if(cntres .eq. 1) then
          neworatea(3,iplane) = oratea(iresd(3,iplane))
          orateawt = 0.
          
          newcf(3) = cf(iresd(3,iplane))
          cfwt = 0.0
      else if (cntres .gt. 1) then
              orateawt = 
     1        ((rmogt2*neworatea(2,iplane))+
     1        (rmogt3*neworatea(3,iplane)))/
     1        (rmogt2+rmogt3)
              
              cfwt = 
     1        ((rmogt2*newcf(2))+
     1        (rmogt3*newcf(3)))/
     1        (rmogt2+rmogt3)
CAS testing
          !!write(63,2000)sdate, year, rmogt2,neworatea(2,iplane),newcf(2)
          !!write(63,2000)sdate, year, rmogt3,neworatea(3,iplane),newcf(3)
          !!write(63,2000)sdate, year, orateawt, cfwt
          !!write(63,*) cntres
CAS end testing
              neworatea(3,iplane) = orateawt
              newcf(3) = cfwt
CAS Residue shifting in the third pool is added here. AS 5/13/2021 
              iresd(3,iplane) = iresd(2,iplane)
      endif
      neworatea(1,iplane) = oratea(iresd(1,iplane))
      neworatea(2,iplane) = oratea(iresd(2,iplane))
      newcf(1) = cf(iresd(1,iplane))
      newcf(2) = cf(iresd(2,iplane))
CAS
CAS
c
c       Shift current residue to previous residue
c
        rmogt(2,iplane) = rmogt(1,iplane)
        rilrm(2,iplane) = rilrm(1,iplane)
        rigrm(2,iplane) = rigrm(1,iplane)
c
c       Add residue from previous crop; ie, crop before current crop
c       (RMOGT(2,iplane)), to oldest residue total (RMOGT(3,iplane))
c
        rmogt(3,iplane) = rmogt(3,iplane) + rmogt(2,iplane)
        rilrm(3,iplane) = rilrm(3,iplane) + rilrm(2,iplane)
        rigrm(3,iplane) = rigrm(3,iplane) + rigrm(2,iplane)
c
c
c       Shift residue type,
CAS The reside shifting in the third pool is commented here and moved above. AS 5/13/2021 
!        iresd(3,iplane) = iresd(2,iplane)
        iresd(2,iplane) = iresd(1,iplane)
c       ------ submerged residue for new residue is zero until tillage
c
        smrm(3,iplane) = smrm(3,iplane) + smrm(2,iplane)
c
c         shift submerged residues from current to previous
c
        smrm(2,iplane) = smrm(1,iplane)
c
c.........set current submerged residue to 0.00001
        smrm(1,iplane) = 0.00001
c
        rmogt(1,iplane) = pyld
c
        rilrm(1,iplane)=rmogt(1,iplane)
        rigrm(1,iplane)=rmogt(1,iplane)

CAS End adding
CAS Added to update rill and interrill cover on the harvest day 1/25/2017 A. Srivastava
      call covcal(iresd,iplane)
CAS End adding
      endif
      return
      end
