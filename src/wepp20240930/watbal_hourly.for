       subroutine watbal_hourly(lunp,luns,lunw,nowcrp,elevm)
c
c     + + + PURPOSE + + +
c     Updates the soil water balance during the simulation period.
c     This has an hourly timestep as proposed by Erin Brooks, implemented by S. Dun.
c
c     This code needs work, it has not been tested with the new winter or subsurface code
c     and has not kept up with other changes in watbal. Watbal also needs to be written - 
c     it has too many special conditions and is too large. JRF = 2/15/2012
c
c     Called from CONTIN
c     Author(s): Savabi
c     Reference in User Guide: Chapters 4, 6, 7, and 8.
c                Also see "A Compendium of Soil Erodibility Data from
c               WEPP Cropland Soil Field Erodibility Experiments 1987
c               & 88", NSERL Report No. 3.
c                Also see "EPIC -- Erosion Productivity Impact Calcu-
c               lator (EPIC Model Documentation) printed Sept. 1990.
c                Also see "Microclimate, the Biological Environment"
c               by Norman J. Rosenberg, et. al. 1983.
c                Also see "Soil Cover Prediction with Various Amounts
c               and Types of Crop Residue".  1982.  James M. Gregory.
c               Trans. ASAE.  pp 1333-1337.
c
c
c     Changes:
c           1) Changed setup of do-loop from:
c                 do 989 nowres = 1,3
c              to:
c                 do 40 nowres = 1,mxres
c           2) De-referenced PTILTY.INC.
c           3) De-referenced: CCRPVR3.INC, CRINPT1.INC, CRINPT3.INC,
c              and CRINPT5.INC.
c           4) Changed parameter order in call to DRAIN to conform
c              to WEPP Coding Convention: 2nd moved to 6th; 3rd moved
c              to 8th moved to 7th.  ALSO NEED TO CHANGE *DRAIN*.
c           5) Introduced TMPVR1 to eliminate recalculation of:
c                 xfin*dg(i,iplane)/tillay(2,iplane)
c           6) Eliminated local variables TDEP & RSD.
c           7) Substituted:
c                 soldep=solthk(nsl(iplane),iplane)
c              for the iterative use of:
c                 soldep = soldep + dg(i,iplane)
c           8) CHANGES made by Dennis Flanagan 5/21/93 to make this
c              routine compatible with WEPP version 93.04 include:
c               a) addition of NBEG to argument list, declarations, def
c               b) addition of "include 'pxstep.inc'
c               c) dimensioning of WATCON to mxplan and changing all
c                  occurences of WATCON to WATCON(iplane).
c               d) IRDEPT changed to IRDEPT(iplane)
c               e) Correction added for case where FIN calculation
c                  yields a negative value because of Case 3
c                  hydrologic plane
c               f) addition of Savabi's correction to calculation of
c                  surface drainage water (SURDRA), which prevents
c                  the water content of any layer from now exceeding
c                  the upper limit for that layer.
c               g) changed L1 IF to "if(idrain.eq.1)" since idrain
c                  can only be 0 (no drainage) or 1 (drainage)
c               h) removal of "if(idrain.eq.1 ...." from within the
c                  L1 IF-ELSE block - since idrain must be 1 to reach
c                  this statement.
c               i) removed calls to DECOMP and SOIL - these have been
c                  moved to the beginning of the simulation day in
c                  subroutine CONTIN.
c               j) changed unit numbers on write statements. Added
c                  YEAR to write statements and changed formats
c               k) added in section of commented out code which can
c                  be used to check the water balance
c               l) added changes for new winter routines from Savabi
c                  dcf  5/20/94
c
c     Version: This module recoded from WEPP Version 91.50.
c     Date recoded: 01/21/93 - 01/22/93.
c     Recoded by: Charles R. Meyer.
c
c     + + + PARAMETERS + + +
      include 'pmxelm.inc'
      include 'pmxnsl.inc'
      include 'pmxpln.inc'
      include 'pmxpnd.inc'
      include 'pmxprt.inc'
      include 'pmxres.inc'
      include 'pmxsrg.inc'
      include 'pmxtil.inc'
      include 'pmxtls.inc'
      include 'pntype.inc'
      include 'pmxhil.inc'
      include 'pmxcrp.inc'
      include 'pmxcut.inc'
      include 'pmxgrz.inc'
      include 'pxstep.inc'
      include 'pmxchr.inc'
c
c     + + + ARGUMENT DECLARATIONS + + +
      integer lunp,luns,lunw,nowcrp
      real elevm
c
c     + + + ARGUMENT DEFINITIONS + + +
c     lunp   - Flag for plant output to be written to files
c     luns   - Flag for soil output to be written to files
c     lunw   - Flag for water output to be written to files
c     nowcrp - current crop
c     elevm - passed value of weather station elevation (meters)
c
c     + + + COMMON BLOCKS + + +
      include 'cangie.inc'
c
      include 'ccdrain.inc'
c        read: idrain,ddrain,drainc,sdrain,drdiam
c      modify: satdep
c       write: drainq
c
      include 'cclim.inc'
c        read: tmnavg
c
      include 'ccons.inc'
c      read coca
c
      include 'ccover.inc'
c        read: lanuse, canhgt, cancov
c
      include 'ccrpgro.inc'
c
      include 'ccrpout.inc'
c        read: lai
c
      include 'ccrpprm.inc'
c        read: itype
c
      include 'ccrpvr1.inc'
c        read: smrm,rtm,rmogt,rmagt
c
      include 'ccrpvr2.inc'
c        read: vdmt
c
      include 'cflags.inc'
c        read: iflag
c
      include 'chydrol.inc'
c        read: runoff, rain(mxplan)
c
      include 'cirfurr.inc'
c        read: irapld(mxplan)
c
      include 'cirriga.inc'
c        read: irdept
c
      include 'cparame.inc'
c        read: ks(mxplan), sm(mxplan), por(mxnsl,mxplan)
c
      include 'cperen.inc'
c        read: imngmt(mxcrop,mxplan)
c
      include 'cstore.inc'
c     modify: roffon, rvolon
c
      include 'cstruc.inc'
c        read: iplane
c
      include 'cstruct.inc'
c       read: ielmt
c
      include 'ctillge.inc'
c        read: tillay(2,mxplan)
c
      include 'cupdate.inc'
c        read: sdate
c
      include 'cwater.inc'
c        read: thetdr(mxnsl,mxplan),thetfc(mxnsl,mxplan),
c              solthk(mxnsl,mxplan),dg(mxnsl,mxplan)
c      modify: soilw(mxnsl,mxplan), sep(mxplan), ul(mxnsl,mxplan), fc(mxnsl),
c              fin, ep, es, cv
c       write: s1(mxplan),s2(mxplan),hk(mxnsl)
c
      include 'cwint.inc'
c        read: wmelt(mxplan)
c
      include 'cprams.inc'
c     modify: norun(mxplan),watblf(mxplan)
c
      include 'cdist2.inc'
      include 'cslpopt.inc'
      include 'cefflen.inc'
      include 'ccntfg.inc'
      include 'ctemp.inc'
      
      include 'ccntour.inc'
      include 'wathour.inc'
      include 'cchrt.inc'
c
c     + + + LOCAL VARIABLES + + +
c
      real watcon(mxplan), xfin, soldep, sd, ch, h, tmpvr1,
     1    drfc(mxnsl), latqcc, latk, fcdep, avcoca, avfca, avhk, avpora,
     1    avstt, avul, fffx, fslope, rm, subq, totdg, totk,
     1    totlqc, watyld,runoffin(mxplan),frozwt,fzul,fzdrfc,
     1    etplcp, subrin, ui_LFtstpF, deepSeep, watbl, tileDrainage
      integer i, mn, jj, lflag, ii, ictop, icleft, icrght, uzone
c
      real hrfin, tdvv
c
cd    Variable added by S. Dun. May 26, 2007
c    A flag to indicate a if a layer meets subsurface lateral flow criteria 
c   from Erin Brooks.
      integer meblfc
c
c     + + + LOCAL DEFINITIONS + + +
c     watcon - water content of the root zone
c     xfin   - water available to infiltrate into the current soil layer
c     soldep - soil profile depth
c     surdra - surface drainage water
c     sd     - sun's declination angle
c     ch     -
c     h      -
c     tmpvr1 -
c     drawat -
c     drfc   -
c     latqc  -
c     latqcc -
c     latk   -
c     fcdep  -
c     runoffin - runoff flow into the segment
c     frozwt - soil water in ice form
c     fcdfz - frozen portion in the saturated layers. 
c
c     + + + SAVES + + +
      save watcon, fcdep, totlqc
c
c     + + + SUBROUTINES CALLED + + +
c     PURK
c     DRAIN
c     EVAP
c     PTGRA
c     PTGRP
c     DECOMP
c     RANGE
c     SWU
c     SOIL
c
c     + + + OUTPUT FORMATS + + +
c
c     + + + END SPECIFICATIONS + + +

c      If this an initialization call, initialize constants.
      if (iflag.eq.0) then
        watcon(iplane) = 0.0
        s1(iplane) = 0.0
        s2(iplane) = 0.0
c
c       SURDRA assigned value but not used  12-20-93 10:53am  sjl
c
        surdra(iplane) = 0.0
        resint(iplane) = 0.0
        plaint(iplane) = 0.0
        totlqc = 0.0
c
c       LATQC assigned value but not used   12-20-93 10:53am  sjl
c
c       latqc = 0.0
        latqcc = 0.0
        subq = 0.0
        sbrunf(iplane)=0.0
c
c       TDR assigned value but not used   12-20-93 10:54am  sjl
c
c       tdr = 0.0
c
c       Initialize soil water limits -- compute potential available water.
c
c       totwat=0.0
        do 10 i = 1, nsl(iplane)
c         ------ upper limit of water content for current layer
          ul(i,iplane) = (por(i,iplane)-thetdr(i,iplane)) * dg(i,iplane)
c         ------ field capacity for current layer   (ISN'T THIS CONSTANT ? dcf)
          fc(i) = dg(i,iplane) * (thetfc(i,iplane)-thetdr(i,iplane))
c         ------ Used in PERC to adjust sat. hyd. cond. on non-saturated soils.
c         (WEPP Equation 7.4.4)
          hk(i) = -2.655 / alog10(fc(i)/ul(i,iplane))
c         ------ calculate total soil water in the root zone (m)
          soilw(i,iplane) = st(i,iplane) + (thetdr(i,iplane)*
     1        dg(i,iplane))

   10   continue
c
      end if
c
      ui_LFtstpF = ui_LFtstp
      sep(iplane) = 0.0
      deepSeep = 0.0
      tileDrainage = 0.0
      soldep = solthk(nsl(iplane),iplane)
c
      surdra(iplane) = 0.0
      etplcp = 0.0
c
c     *** L0 IF ***
c     (If this is NOT an initialization call, proceed; otherwise, RETURN)
      if (iflag.ne.0) then
cd    Added by S. Dun. Jan 10, 2010 for checking water balace of the channel section
c     Input water from upland subsurface flow
      subrin = 0.0
cd    endadding      
c       Note: Intercepted rainfall is subtracted from rainfall Reza 9/93
c       ------ Calculate infiltration.
cd    Modified by S. Dun Nov 11, 2003 and Jan 28,2004
      if((plaint(iplane).lt.1.0E-8).and.(pintlv(iplane).gt.1.0e-8)) then
        if((rtd(iplane).gt.0.0).and.(lai(iplane).gt.0.0)) then
            plaint(iplane) = pintlv(iplane)
        else
            resint(iplane) = resint(iplane) + pintlv(iplane)
        endif
      endif
cd        fin = rain(iplane) - (plaint(iplane)+resint(iplane)) +
cd    1  wmelt(iplane) + irdept(iplane) + irapld(iplane) - runoff(iplane)
      fin = rain(iplane)-(plaint(iplane)-pintlv(iplane)+resint(iplane))+
     1  wmelt(iplane) + irdept(iplane) + iraplo(iplane) 
c
      pintlv(iplane) = 0.0
cd    End Modifying
c
      ui_Hcrunf = runoff(iplane)
      if (iplane.eq.1) ui_Hurunf = 0.0

cd    Added by S. Dun July 08,2003, Modified Jan 28, 2004
c    For channel
c???    Check impondment part later
      if ((ivers.eq.3).or.(contrs(nowcrp,iplane).ne.0)) then
        fin = fin + roffon(ielmt) - runoff(iplane)
        runoffin(iplane) = roffon(ielmt)
      else
        if (iplane.ne.1) then 
          fin = fin  + (ui_HUrunf*efflen(iplane-1)
     1            - ui_Hcrunf*efflen(iplane))/slplen(iplane)

          runoffin(iplane) = runoff(iplane-1)
     1            *efflen(iplane-1)/slplen(iplane)     
          subrin = sbrunf(iplane-1)
     1            *(fwidth(iplane-1)*slplen(iplane-1))
     1              /(fwidth(iplane)*slplen(iplane))
        else
          fin = fin - runoff(iplane)
          runoffin(iplane) = 0.0
        endif
      endif
cd    End adding
c
cd    Modified by S. Dun Jan 24, 2004
c
      if (fin.lt.0.0) then
        if ((ivers.eq.3).or.(contrs(nowcrp,iplane).ne.0)) then
           fin = roffon(ielmt) - runoff(iplane)
         else
           if (iplane.gt.1) fin = (runoff(iplane-1)*efflen(iplane-1)
     1             - runoff(iplane)*efflen(iplane))/slplen(iplane)
        endif
      endif
c       ------ Add in check if FIN is negative which will happen on a
c       case 3 hydrologic plane on a multiple OFE hillslope - dcf
cd        if (fin.lt.0.0.and.ivers.ne.3) then
cd          if (iplane.gt.1) fin = runoff(iplane-1) - runoff(iplane)
cd        end if
c       in case of channel water balance (ivers.eq.3) runoff(iplane-1)
c       is not relevant. Use rvolon(ielmt) calculated in wshirs. Also
c       we do not need something equivalent to if(iplane.gt.1) since a
c       channel has always something draining into it - CB 3/95
cd        if (fin.lt.0.0.and.ivers.eq.3)
cd    rvolon is variable for volume instead of rate.    
cd     1                     fin = rvolon(ielmt) - runoff(iplane)
c
cd    End modifying
c
cd      Added by S. Dun, September 23, 2008
c       add in the water from subsurface flow of upland channel segements
c       Modified by S. Dun, May 05, 2009
c       Since I used sbrunv in WSHCQI.for for a different purpose. 
c       We need change the variable used here
        if (ivers.eq.3) then
          sbrunv(0) = 0. 
          fwidth(0) = 0.
          slplen(0) = 0.    
cd          fin = fin + (sbrunv(ncleft(ielmt)) + sbrunv(ncrght(ielmt)) 
cd     1                + sbrunv(nctop(ielmt)) + sbrunv(nitop(ielmt))
cd     2                + sbrunv(nileft(ielmt)) + sbrunv(nirght(ielmt)))
cd     3                /(fwidth(iplane)*slplen(iplane)) 
          ictop = 0
          icleft = 0
          icrght = 0
          if(nctop(ielmt).gt.0) ictop = nctop(ielmt)-nhill
          if(ncleft(ielmt).gt.0) icleft= ncleft(ielmt)-nhill
          if(ncrght(ielmt).gt.0) icrght= ncrght(ielmt)-nhill
c    
          subrin =  (sbrunf(ictop)*fwidth(ictop)*slplen(ictop) 
     1              + sbrunf(icleft)*fwidth(icleft)*slplen(icleft) 
     2              + sbrunf(icrght)*fwidth(icrght)*slplen(icrght))
     3                /(fwidth(iplane)*slplen(iplane))
          fin = fin + subrin 
        endif
cd      end adding
cd      Added by S. Dun, March 28, 2008
c       initiate infiltration into frozen soil flag
        nwfzfg(iplane) = 0
cd      end adding
        
  
          ui_LFtstp = 24
          
          ui_LFtstpF = 24.0
          
          sbrunf(iplane) = 0.0
          surdra(iplane) = 0.0 
        if(iplane.eq.1) then
          do 73 ii = 1, ui_LFtstp    
              ui_SUrunf(ii) =0.0 
              ui_SCrunf(ii) = 0.0
              ui_LfUrf(ii) = 0.0
              ui_LfCrf(ii) = 0.0
   73     continue
      else
          do 74 ii = 1, ui_LFtstp    
              ui_SCrunf(ii) = 0.0
              ui_LfCrf(ii) = 0.0
   74     continue


      endif

c
c     This is the hourly timestep loop
c
      do 75 ii = 1, ui_LFtstp

c
c       *** L1 IF ***
c       If there is infiltration, prorate water into the plow layer.
c       Commented by S. Dun, Jan. 18, 2011
cd        if (fin.gt.0.0) then
c         -------- available water      
          if ((ivers.ne.3).and.(contrs(nowcrp,iplane).ne.1)) then
           if(iplane.gt.1) then
           
            xfin = fin/ui_LFtstpF + (ui_LfUrf(ii) + ui_SUrunf(ii))
     1                 *(fwidth(iplane-1)*slplen(iplane-1))
     1                 /(fwidth(iplane)*slplen(iplane))
           else
              xfin = fin/ui_LFtstpF
           endif
         else
             xfin = fin/ui_LFtstpF
         endif
cd            hrfin = xfin

          hrfin = xfin
c
cd        Added by S. Dun, March 28, 2008
c         infiltration into frozen soil flag activated
          if (frdp(iplane).gt. 0.001) then
              nwfzfg(iplane) = 1
          endif
cd        end adding
c
cd        Modified by S. Dun, March 12,2008
c         All infiltrated water stays in the first layer if it is the only layer  
c           
          if (nsl(iplane).eq.1)  then
              st(1,iplane) = st(1,iplane) + xfin
              xfin = 0.0
          else
c
c         *** Begin L2-Loop ***
c         -------- Starting at top, infiltrate water into each tilled layer.
          i = 0
   20     continue
          i = i + 1
c         ---------- If plow layer does not end in current soil layer, add water          
          if (solthk(i,iplane).lt.tillay(2,iplane)) then
            tmpvr1 = xfin * dg(i,iplane) / tillay(2,iplane)
          else
            tmpvr1 = xfin
          endif
c
          if(hrfin.lt.-0.00001) then
            if(st(i,iplane).lt. (-tmpvr1)) tmpvr1 = -st(i,iplane)
        endif
c
          st(i,iplane) = st(i,iplane) + tmpvr1
          xfin = xfin - tmpvr1
c       
c         *** End L2-Loop ***
c
      if (hrfin.ge.0.0) then
          if ((i.lt.nsl(iplane)).and.xfin.gt.0.00001) go to 20
      else
        if ((i.lt.nsl(iplane)).and.xfin.lt.-0.00001) go to 20
        endif
         endif
c
c       Commented by S. Dun, Jan. 18, 2011
c       *** L1 ENDIF ***
cd        end if

c       ------ combined standing & fallen residue (used in EVAP to compute % bare soil)
c       only do this on the first hour, so that it is done once per day
        if (ii.eq.1) then
             cv = rmagt(iplane)
             do 30 i = 1, mxres
               cv = rmogt(i,iplane) + cv
   30        continue
         endif
c
c       ------ percolation of water through soil layers
        call purk
 
c       Accumulate the amount of water leaving the profile for this hour. 
        deepSeep = deepSeep + sep(iplane)
        
c
c       Only compute the evapotranspiration on the last hour,
c       so that it is only done once per day
        if (ii.eq.ui_LFtstp) then          
          ep(iplane) = 0.0
          es(iplane) = 0.0
          eres(iplane) = 0.0
c
c       ------ compute evapotranspiration (ET).
cd    S. Dun switched the evportranspiration method to Penman-Monteith 
          if (iflget.eq.1) then
             call evap(elevm)
          else
             call evappm(elevm,nowcrp)
          endif
        endif
        
c       ------ prevent the soil water content of any layer from exceeding the
c       upper limit for that layer.  Add water to next higher layer.
c       Moved to after lateral flow calculations and et -  reza 7/25/93
c
        do 40 i = nsl(iplane), 2, -1
cd        Added by S. Dun, March 13, 2008
          fzul = ul(i,iplane) - frzw(i,iplane)
          if (fzul .lt. 0.0) fzul = 0.0
cd        end adding
c
          if (fin.gt.1.0e-6) then
c         There is water from outside
            if (st(i,iplane).gt.fzul) then
                st(i-1,iplane) = st(i-1,iplane) + (st(i,iplane)-fzul)
                st(i,iplane) = fzul
             end if
          else
c         When there is no water from outside, water would not go upward due to frost melt
             if (st(i,iplane).gt.ul(i,iplane)) then
                 st(i-1,iplane) = st(i-1,iplane) + 
     1                           (st(i,iplane)-ul(i,iplane))
                 st(i,iplane) = ul(i,iplane)
             end if
          endif
   40   continue
  
c       
c       start drainage computations
c        
        drainq(iplane) = 0.0
        watbl = 0.0
        uzone = -1
        do 100 i = nsl(iplane), 1, -1
          drfc(i) = fc(i) + ((1-coca(i,iplane))*dg(i,iplane))
cd        Added by S. Dun, March 13, 2008
          fzdrfc = drfc(i) - frzw(i,iplane)
          if (fzdrfc .lt. 0.) fzdrfc = 0.
          if (st(i,iplane).ge.fzdrfc) then
            if (uzone.lt.0) then
               watbl = watbl + dg(i,iplane)
            endif
          else
c           hit unsaturated zone, stop
            uzone = i            
          endif
  100   continue
        
        unsdep(iplane) = soldep-watbl       
        satdep(iplane) = watbl

        if (idrain(iplane).eq.1.and.(unsdep(iplane).le.ddrain(iplane)))
     1  then
            call drain(solthk(nsl(iplane),iplane),nowcrp,watbl,1.0)
            tileDrainage = tileDrainage + drainq(iplane)
        endif
            
c
c     end drainage computations
c   

c%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
cCCCCCCCCCCCCCCCCC subsurface lateral flow calculation CCCCCCCCCCCC
cCCCCCCCCCCCCCCCCCCCCCCC  Reza Savabi, 7/93 CCCCCCCCCCCCCCCCCCCCCCC
c%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
c

        fcdep = 0.0
c        fcdfz = 0.0
        tdvv = 0.0
        unsdep(iplane) = 0.0
        do 50 i = 1, nsl(iplane)
          drfc(i) = fc(i) + ((1-coca(i,iplane))*dg(i,iplane))
c
cd        Added by S. Dun, March 13, 2008
      fzdrfc = drfc(i) - frzw(i,iplane)
      if (fzdrfc .lt. 0.) fzdrfc = 0.
cd        end adding
         
cd     -------------------------------------------------
cd    Modified by S. Dun May 26, 2007
c    This is a big change based on Erin Brooks
c    We are assuming that only saturated lateral occurs.  
c    There is no unsaturated lateral flow because we assume the hydraulic gradient of
c     a wetting front is mostly vertical.
c
c    We define whether a layer has a saturated layer with the following criteria: 
c    either the layer below is saturated or the layer below is the restrictive layer 
c    at the bottom of the soil profile. 
        if (i .eq. nsl(iplane)) then
             meblfc = 1
        elseif ((st(i+1,iplane)/ul(i+1,iplane)).ge.1.0) then
           meblfc = 1
        else
             meblfc = 0
        endif
c
          if ((st(i,iplane).ge.fzdrfc).and. meblfc.eq.1) then
             fcdep = fcdep + dg(i,iplane)
           tdvv = tdvv +(st(i,iplane) - fzdrfc)
          else
             unsdep(iplane) = unsdep(iplane) + dg(i,iplane)
          end if
   50   continue
c
        latqcc = 0.0
        subq = 0.0
        
c
c       ****M1 if, the big subsurface lateral flow M1 if
c
        if (fcdep.gt.0.0) then
c
c         radinc = average slope in degree
c         Calculate average saturated soil hydraulic conductivity in
c         saturated zone
c         (below water table).
c
          avpora = 0.0
          avfca = 0.0
          avcoca = 0.0
          totk = 0.0
          totdg = 0.0
          avstt = 0.0
          avul = 0.0
          avhk = 0.0
          fffx = 1.0
          lflag = 1
c
cd        Added in by S. Dun, Jan 19, 2011
cd        For merging Erin's lateral flow version
          
cd        For Erin's lateral flow version
          do 66 mn = 1, nsl(iplane)

            if (mn .eq. nsl(iplane)) then
               meblfc = 1
            elseif ((st(mn+1,iplane)/ul(mn+1,iplane)).ge.1.0) then
               meblfc = 1
            else
               meblfc = 0
            endif
c
            if ((st(mn,iplane).ge.drfc(mn)).and. meblfc.eq.1) then

              totdg = totdg + dg(mn,iplane)
              avpora = avpora + (por(mn,iplane)*(dg(mn,iplane)/fcdep))
              avfca = avfca + (thetfc(mn,iplane)*(dg(mn,iplane)/fcdep))
              avcoca = avcoca + (coca(mn,iplane)*(dg(mn,iplane)/fcdep))

              fffx = (st(mn,iplane)-drfc(mn))/(ul(mn,iplane)-drfc(mn))
              if (fffx.gt.1) fffx = 1
              totK = totK + (ui_ssh(mn,iplane)*fffx*dg(mn,iplane))
            end if
            
   66     continue

c
c         SLOPED assigned a value but not used  12-20-93 10:55am  sjl
c
c         sloped = radinc * 180. / 3.14159
          fslope = sin(radinc(iplane))
c         Use hour time in seconds to be clear.          
          if (totdg.gt.0.0) then
            if (solwpv.ge.2006) then
c              latk = 86400. * (totk/totdg)
               latk = 3600. * (totk/totdg)
            else
c              latk = 86400. * (totk/totdg) * fffx
               latk = 3600. * (totk/totdg) * fffx
            endif
          else
              latk = 0.0
          endif
   
cx    Added by Arthur. Modified by S. Dun Dec. 05, 2003
cd          latqcc = fcdep * latk * fslope
cd          subq = latqcc
c          subq = fcdep * 1 * latk * fslope
          if (solwpv.ne.7778) then
             subq = fcdep  * anisrt(iplane) * latk * fslope
          else
             subq = fcdep  *  latk * fslope
          endif

c         Amount of lateral flowfor this hour
          latqcc = subq /slplen(iplane)
          if (latqcc.gt.tdvv) latqcc = tdvv


cx    End adding. May,2000
          if (latqcc.lt.0.0) latqcc = 0.0
cd    Modified by S. Dun Jan 09, 2004
cd          totlqc = totlqc + latqcc
cd    End Modifying.
c
c         calculate new hoo2 (depth of saturated depth at the bottom of hillslope)
c         for next day (m)
c
          watyld = avpora - (avfca+(1.0-avcoca))
          
          if (solwpv.lt.2006) then
             fcdep = fcdep - (latqcc/watyld)
             if (fcdep.lt.0.0) fcdep = 0.0
          end if          
         
          unsdep(iplane) = soldep - fcdep
c
c         Convert subsurface lateral flux to soil water depth using average
c         drainable porosity (water yield).
c
c         If there is lateral flow, latqcc,  update the
c         available water content (ST) in each soil layer to reflect
c         the lateral flow from each layer, starting at the top layer.
c
c         ****M2 if loop***
          if (latqcc.gt.0.0) then
c           Accumulate lateral flow for the current day
            sbrunf(iplane) = latqcc + sbrunf(iplane)
c           save lateral flow amount for this timestep hour
            ui_lfcrf(ii) = latqcc
c
c           *** Begin M2 DO-LOOP ***
c
            do 70 jj = 1, nsl(iplane)
c
cd             Added by S. Dun, March 13, 2008
               fzdrfc = drfc(jj) - frzw(jj,iplane)
               if (fzdrfc .lt. 0.) fzdrfc = 0.
cd             end adding
c
c********M3 IF ***
c             - If layer is above field capacity, drain it.
              if (st(jj,iplane).gt.fzdrfc.and.latqcc.ge.0.0) then
c               ---------- potential water which can be flow laterally from this layer
                drawat(jj) = st(jj,iplane) - fzdrfc
c
c***********M4 IF ***
                if (latqcc.gt.0.0) then
c
c                 ------------ If water excess in this layer exceeds or equals what has
c                 run from latqcc.
c*************** M5 IF ***
                  if (drawat(jj).ge.latqcc) then
c                   ------- subtract amount that has run out the drain from this layer.
                    st(jj,iplane) = st(jj,iplane) - latqcc
                    if (st(jj,iplane).lt.1e-10) st(jj,iplane) = 1e-10
                    latqcc = 0.0
c                 ------- If water excess in this layer is less than what has run
c                 from profile ...
                  else
c                   ------- subtract from latqcc what this layer can contribute.
                    latqcc = latqcc - drawat(jj)
c                   ------- adjust soil layer water content by same amount of water
cd    Modified by S.Dun July 08,2003
cd                    st(jj,iplane) = fc(jj)
                    st(jj,iplane) = fzdrfc
cd    End modifying
c
c                 *************** M5 ENDIF ***
                  end if
c               ********* M4 ENDIF ***
                end if
c             ****** M3 ENDIF ***
              end if
c           **** M2 DO-LOOP END ***
   70       continue
c         Added by S. Dun 12/15/2005
c         Soil profile could not drain out that much water could potentially flow
          if (latqcc.gt.0.0) then
            sbrunf(iplane) = sbrunf(iplane) - latqcc
            ui_lfcrf(ii) = ui_lfcrf(ii) - latqcc
          endif
c         *** M2 ENDIF ***
          end if
c       ** M1 ENDIF ***
        end if
c
cCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
cCCCCCCCCCCCCCCCC end subsurface flow calculations CCCCCCCCCCCCCCCCC
c%%%%%%%%%%%%%%%%%%%%%%%%%% 7/93 %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

c
c       Compute surface drainage water (SURDRA).
c
        fzul =ul(1,iplane) - frzw(1,iplane)
        if (fzul .lt. 0.) fzul = 0.
        if  ((st(1,iplane)-fzul).gt.1e-6) then
c
c         -- XXX -- Variable SURDRA is never used! -- CRM -- 5/14/93.
c
c         -- NOTE -- Problem currently exists of how to handle this surface
c         drainage water computed - it should really be added back
c         into the runoff for the current day - HOWEVER - this
c         runoff has already been routed and erosion computations
c         made at this point in the model.  POSSIBLE SOLUTION:
c         move the call to WATBAL to within SR IRS or CONTIN -
c         check to see if SURDRA(iplane) > 0.0 for any OFE - if it
c         is then somehow add this water as an input and go back
c         and redo the IRS-GRNA computations. ANOTHER SOLUTION -
c         discard this water amount as done currently.
c         DCF - 5/21/93
c
c
c         SURDRA assigned a value but not used  12-20-93 10:56am  sjl
c
c         surdra = st(1,iplane) - ul(1)
cd Added by S. Dun. May 22, 2003, Modified Jan 28, 2004
          ui_Scrunf(ii) = st(1,iplane) - fzul
          norun(iplane) = 1

          st(1,iplane) = fzul
cd          unsdep(iplane) = 0.0
c          unsdep(iplane) = unsdep(iplane)-dg(1,iplane)
        else
           ui_scrunf(ii) = 0.0
        end if
        surdra(iplane) = surdra(iplane) + ui_scrunf(ii)
c   
   75   continue
   
      drainq(iplane) = tileDrainage

      sep(iplane) = deepSeep
      
      ui_HUrunf = ui_HCrunf
      do 76 ii = 1, ui_LFtstp
         ui_SUrunf(ii) = ui_SCrunf(ii)
         ui_LfUrf(ii) = ui_LfCrf(ii)
   76    continue
c
          if ((ivers.eq.3).or.(contrs(nowcrp,iplane).ne.0)) then
c     runoff is from subsurface flow only

              if (runoff(iplane).eq.0.0) then 
                    chkflg = 2 
              end if
              runoff(iplane) = runoff(iplane) + surdra(iplane)
          else
              if (efflen(iplane).eq.0.0) then 
                    efflen(iplane) = slplen(iplane)
              endif
              runoff(iplane) = runoff(iplane) + surdra(iplane)
     1                * slplen(iplane)/efflen(iplane)
          endif
c
               if (surdra(iplane).gt. 1.0e-6) norun(iplane) = 1        
c         end if
cd    End adding.
c
c       QUESTION??  Is the following equation applicable to all
c       world hemispheres????? (will equation work in
c       Brazil or Australia???)     dcf  5/21/93
c
c       ------ Sun's declination angle
c       (EPIC Equation 2.195)
        sd = 0.4102 * sin((sdate-80.25)/58.09)
c
c       Code changed because of bug in Lahey compiler using tangent
c       function on AT&T 6300 machine.   dcf -- 10/1/91
c       Original code:
c       ch = -ytn * tan(sd)
        ch = -ytn * sin(sd) / cos(sd)
c
        if (ch.ge.1.0) then
          h = 0.0
        else if (ch.le.-1.0) then
          h = 3.1416
        else
          h = acos(ch)
        end if
c
c       ------ day length
c       (EPIC Equation 2.194)
        daylen = 7.72 * h
c
c
c       *****************************************************************
c       *  Compute canopy cover, canopy height, root mass by soil     *
c       * layer, root depth, leaf area index, and plant basal area, *
c       *  and plant residue for CROPLAND plants.                     *
c       *****************************************************************
c
        if (lanuse(iplane).eq.1) then
c         -------- (PERENNIALS)
          if (imngmt(nowcrp,iplane).eq.2) then
            call ptgrp(nowcrp)
c         -------- (ANNUALS)
          else if (imngmt(nowcrp,iplane).eq.1) then
            call ptgra(nowcrp)
          end if
c
c       NOTE --- call to DECOMP moved to SR CONTIN at beginning of
c       simulation day so that residue managements for a given
c       day will impact that day's cover values.   dcf  5/21/93
c       -------- residue decomposition
c       call decomp(nowcrp)
c
c       *****************************************************************
c       *  Compute canopy cover, canopy height, root mass by soil     *
c       * layer, root depth, leaf area index, and plant basal area, *
c       *  plant residue, and residue decomposition for RANGELAND.    *
c       *****************************************************************
c
        else
cWarning from ftnchek, changed nsl to nsl(iplane) in call to range
c         Dummy arg is scalar in module RANGE line 1 file range.f
c         Actual arg is whole array in module WATBAL line 576 file watbal.f
          call range(watstr(iplane),nsl(iplane),nowcrp)
        end if
c
c       -------- Write output to Plant File.
        if (lunp.gt.0) write (36,1000) iplane, sdate, year, 
     1      canhgt(iplane),
     1      cancov(iplane), lai(iplane), rilcov(iplane),
     1      inrcov(iplane), itype(nowcrp,iplane), vdmt(iplane),
     1      rmagt(iplane), (iresd(i,iplane),rmogt(i,iplane),i = 1,3), (
     1      smrm(i,iplane),i = 1,3), (iroot(i,iplane),rtm(i,iplane),i =
     1      1,3), tmnavg
c
c       ------ If evapotranspiration and root depth are positive....
        if (ep(iplane).gt.0.0.and.rtd(iplane).gt.0.0) then
c         -------- estimate evaporation and plant water use
          call swu(nowcrp)
c
cd    Added by S. Dun July 10,2003 for the havest day's water balance. 
c    Probably we should have a better way to solve this problem. 
c        
        elseif(plaint(iplane).gt.0.0)    then
          if (plaint(iplane).gt.ep(iplane)) then
            pintlv(iplane) = plaint(iplane)-ep(iplane)
          else
            ep(iplane) = plaint(iplane)
            pintlv(iplane) = 0.0
          endif
c          plaint(iplane) = 0.0
cd    End adding
        else
c         -------- no evapotranspiration
          ep(iplane) = 0.0
c         -------- no water stress   QUESTION - do we want to do this ? dcf
          watstr(iplane) = 1.0
        end if
c
cd      Added by S. Dun, April 25, 2008 
c       for output ET from plant interception (etplcp in meter here)
        if(plaint(iplane).gt.0.0) then
          if(pintlv(iplane).gt.0.0) then
             etplcp = plaint(iplane) - pintlv(iplane)
          else
             etplcp = plaint(iplane)
          endif
        endif
        plaint(iplane) = 0.0
c       end adding
c
c       NOTE - variable waty is used below in water balance checking
c       code which is currently commented out      dcf  5/21/93
c       waty=watcon(iplane)
c
        watcon(iplane) = 0.0
        do 90 i = 1, nsl(iplane)
c         --------- soil water content by layer
          soilw(i,iplane) = st(i,iplane) + (thetdr(i,iplane)*
     1                     (dg(i,iplane) - frozen(i,iplane)))
cd     1        dg(i,iplane))
c         --------- water content of the root zone
          watcon(iplane) = watcon(iplane) + soilw(i,iplane)
   90   continue
cd
cd      if (ihill.le.nhill) then
cd               write(60,1500) sdate,year,ihill,iplane,((soilw(i,iplane)
cd     1              + frzw(i,iplane))/dg(i,iplane), i = 1, nsl(iplane))
cd               write(60,1500) sdate,year,ihill,iplane, (thetfc(i,iplane)
cd     1               , i = 1, nsl(iplane))
cd      endif 
cd 1500            format(1x,4i6, 10f6.2)
c
c       check the water balance (equation 7.1)
c
c       watsm=abs(rain+wmelt(iplane)+irdept(iplane)+irapld(iplane) -
c       1      (ep(iplane) + es(iplane) + sep(iplane) + runoff(iplane)))
c
c       watdel=watcon(iplane)-waty
c
c       if(watdel.gt.0.0)then
c       watdif=watdel-watsm
c       else
c       watdif=watdel+watsm
c       endif
c       write (6,*)'watdif',watdif
c       if(abs(watdif).ge.0.001.and.sdate.gt.1)then
c       write (6,*)'   '
c       write (6,*)'IN SR WATBAL - watdif = ',watdif
c       write (6,*)'SDATE = ',sdate,' rain= ',rain
c       write (6,*)'iplane=',iplane,' wmelt(iplane)=',wmelt(iplane)
c       write (6,*)'irdept,irapld=',irdept(iplane),irapld(iplane)
c       write (6,*)'ep(iplane)= ',ep(iplane),'es(iplane)=',es(iplane)
c       write (6,*)'sep(iplane)=',sep(iplane),'runoff=',runoff(iplane)
c       write (6,*)'  '
c       endif
c
c
c       -------- Write output to Soil File.
        if(luns.gt.0)
     1    write (39,1100) iplane, sdate, year, por(1,iplane)*100.,
     1      ks(iplane) * 3.6e6, sm(iplane) * 1000., thetfc(1,iplane),
     1      thetdr(1,iplane), rrc(iplane)*1000., kiadjf(iplane),
     1      kradjf(iplane), tcadjf(iplane)
c
        rm=(rain(iplane)+wmelt(iplane)+irdept(iplane)+iraplo(iplane))
     1       *1000.
c
cd    Added by S. Dun, March 12, 2008
c     print out the water in soil form when frost exists
      frozwt = 0.0
      if(frdp(iplane).gt.0.001) then
          do 95 i = 1, nsl(iplane)
              soilf(i,iplane) = frzw(i,iplane)+ 
     1                 thetdr(i,iplane)* frozen(i,iplane)
              frozwt = frozwt + soilf(i,iplane)
95        continue
      else 
          do 96 i = 1, nsl(iplane)
             soilf(i,iplane) = 0.0
96        continue             
      endif
      
cd    end adding
cd
cd      if (ihill.le.nhill) then
cd             write(60,1500) sdate,year,ihill,iplane,((soilw(i,iplane)
cd     1              + frzw(i,iplane) 
cd     1              + thetdr(i,iplane)* frozen(i,iplane))
cd     1                /dg(i,iplane), i = 1, nsl(iplane))
cd             write(60,1500) sdate,year,ihill,iplane,(soilw(i,iplane)
cd     1               , i = 1, nsl(iplane))
cd             write(61,1500) sdate,year,ihill,iplane,(frzw(i,iplane) 
cd     1               , i = 1, nsl(iplane))
cd             write(62,1550) sdate,year,ihill,iplane,surdra(iplane)*1000.
cd     1              ,runoff(iplane)*1000.* efflen(iplane)/slplen(iplane)
cd      endif 
cd  1500         format(1x,4i6, 10f6.2)
cd1550         format(1x,4i6, 2f8.3)   
c
c
c       -------- Write output to Water Balance File.
        if ((lunw.eq.1).and.(ivers.ne.3)) then    
cd    Modified by S.Dun Jan 28, 2004
          if ((contrs(nowcrp,iplane).ne.0)) then
            write (35,1300) iplane, sdate, year, prcp*1000., rm,
     1      runoff(iplane)*1000., ep(iplane)*1000., es(iplane)*1000.,
     1      eres(iplane)*1000.,
     1      sep(iplane)*1000,runoffin(iplane)*1000,subrin*1000.,
     1      sbrunf(iplane)*1000.,watcon(iplane)*1000.,frozwt*1000.,
     1      snodpy(iplane)*densg(iplane),
     1      runoff(iplane)*1000.,drainq(iplane)*1000,
     1      (irdept(iplane)+iraplo(iplane))*1000,
     1      slplen(iplane)*fwidth(iplane)    
          else
c           changed runoff value to use cumulative length (totlen)
c           because efflen may span OFE's. Matches event output code
c           in sedout.for 6-13-2008 dcf,jrf          
            write (35,1300) iplane, sdate, year, prcp*1000., rm,
     1      runoff(iplane)*1000.* efflen(iplane)/totlen(iplane), 
     1      ep(iplane)*1000., es(iplane)*1000.,eres(iplane)*1000.,
     1      sep(iplane)*1000,runoffin(iplane)*1000,subrin*1000.,
     1      sbrunf(iplane)*1000.,watcon(iplane)*1000.,frozwt*1000.,
     1      snodpy(iplane)*densg(iplane),
     1      runoff(iplane)*1000.*efflen(iplane)/slplen(iplane),
     1      drainq(iplane)*1000,
     1      (irdept(iplane)+iraplo(iplane))*1000,
     1      slplen(iplane)*fwidth(iplane)     
          endif
        endif 
c
c     ------ initialize soil parameters like bulk density, porosity, etc.
c     -- XXX -- IMODEL is undefined. -- CRM -- 5/14/93.
c
c     NOTE - call to SOIL has been moved to beginning of simulation day
c     in SR CONTIN so that tillage impacts on roughness and
c     residue and infiltration will occur before storm event
c     dcf  5/21/93
c     call soil(nowcrp,imodel)
c
c
c     *** L0 ENDIF ***
      end if
c
      return
 1000 format (i2,1x,i3,1x,i5,1x,f4.2,1x,f5.3,1x,f4.2,2(1x,f5.3),1x,i1,
     1    1x,f6.3,
     1    1x,f6.4,3(1x,i1,1x,f6.4),3(1x,f6.4),1x,i1,1x,f6
     1    .4,2(1x,i1,1x,f6.4),1x,f5.1)
 1100 format (1x,i2,2x,i3,2x,i5,1x,9f7.2)
c     1200 format (1x,i3,1x,i3,1x,i3,1x,6(f6.2,1x),1x,f4.2,2x,f6.2,3x,f7.2)
 1300 format (1x,3(1x,I4),2(1x,f7.2),1x,e15.7,4(1x,f7.2),
     1        1x,e15.7,5(1x,f7.2),2x,e15.7,2(1x,f7.2),1x,f10.2)
c    2300 format (1x,3(1x,I4),11(1x,f9.2))
      end




