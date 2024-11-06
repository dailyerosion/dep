      subroutine initgrrcc(nowcrp)
c
c     + + + PURPOSE + + +
CAS   Duplicated this routine for initial conditions of released cover crop. 
CAS   Estimates the vegetative dry matter at maturity (VDMT), canopy height
CAS   (CANHGT), leaf area index (LAI), and accumulated growing degree days
CAS   (SUMGDD) from the initial canopy cover of released canopy cover (RCC).
CAS   A. Srivastava 2/13/2017
c
c     Called from PTGRP, INIT1
c     Author(s):  Alberts, Ghiddey, Ferris, Arnold
c     Reference in User Guide:
c
c     Changes:
c
c     Version: This module recoded from WEPP Version 92.25.
c     Date recoded: 08/25/92.
c     Recoded by: Charles R. Meyer.
c
c     + + + KEYWORDS + + +
c
c     + + + PARAMETERS + + +
      include 'pntype.inc'
      include 'pmxpln.inc'
      include 'pmxcrp.inc'
      include 'pmxres.inc'
      include 'pmxtls.inc'
      include 'pmxtil.inc'
      include 'pmxhil.inc'
      include 'pmxnsl.inc'
      include 'pmxcut.inc'
c
c     + + + ARGUMENT DECLARATIONS + + +
      integer nowcrp
c
c     + + + ARGUMENT DEFINITIONS + + +
c     nowcrp - the current crop
c
c     + + + COMMON BLOCKS + + +
      include 'ccover.inc'
c       read: cancov(mxplan)
c      write: canhgt(mxplan)
c
      include 'ccrpvr2.inc'
c     modify: vdmt(mxplan)
c
      include 'ccrpvr3.inc'
c       read: hmax(ntype), gddmaxi(ntype), bb(ntype), bbb(ntype),
c             xmxlai(ntype)
c     modify: sumgdd(mxplan)
c
      include 'ccrpprm.inc'
c       read: itype(mxcrop,mxplan)
c
      include 'ccrpout.inc'
c     modify: lai(mxplan)
c
      include 'cperen.inc'
c       read: imngmt(mxcrop,mxplan)
c
      include 'cstruc.inc'
c       read: iplane
c
c     + + + END SPECIFICATIONS + + +
c
c
CASnew Setting initial canopy cover for release crop
      cancov(iplane) = rcc(itype(nowcrp,iplane))
CASnew
c ---- Compute vegetative dry matter (VDMT), from canopy cover (CANCOV).
      if (bb(itype(nowcrp,iplane)).gt.0.0) then
        vdmt(iplane) = log(1.0-cancov(iplane)) / (-
     1    bb(itype(nowcrp,iplane)))
      else
        vdmt(iplane) = 0.0
      endif
        
      if (vdmt(iplane).lt.0.) vdmt(iplane) = 0.0
c
c     ---- Compute canopy height (CANHGT), from vegetative dry matter (VDMT)
c     and plant height at maturity (HMAX).
      canhgt(iplane) = (1.-exp(-bbb(itype(nowcrp,iplane))*vdmt(iplane)))
     1    * hmax(itype(nowcrp,iplane))
c
c     ---- Compute leaf area index (LAI), from maximum leaf area index
c     (XMXLAI) and vegetative dry matter (VDMT).
c     ** CROPLAND ANNUALS **
      if (imngmt(nowcrp,iplane).eq.1) then
        lai(iplane) = (xmxlai(itype(nowcrp,iplane))*vdmt(iplane)) / (
     1      vdmt(iplane)+0.5512*exp(-6.8*vdmt(iplane)))
c
c     ** PERENNIALS OR RANGELAND **
      else
CAS
          if(jdsene(nowcrp,iplane).eq.0) then
          lai(iplane) = (xmxlai(itype(nowcrp,iplane))*vdmt(iplane)) / (
     1      vdmt(iplane)+0.2756*exp(-13.6*vdmt(iplane)))
          else
          lai(iplane) = xmxlai(itype(nowcrp,iplane))*cancov(iplane)     
          endif
CAS end
      end if
c
c     ---- Compute cumulative growing degree days (SUMGDD), from growing
c     degree days at maturity (GDDMAX), leaf area index (LAI), and
c     maximum leaf area index (XMXLAI).
      sumgdd(iplane) = gddmax(itype(nowcrp,iplane)) * lai(iplane) /
     1    xmxlai(itype(nowcrp,iplane))
c
      return
      end
