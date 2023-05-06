      subroutine ptgra(nowcrp)
c
c     + + + PURPOSE + + +
c     This is the plant growth subroutine for annual crops.
c     This subroutine predicts canopy cover, canopy height, and
c     root mass at different soil zones, root depth, leaf area
c     index and plant basal area.
c
c     Called from WATBAL
c     Author(s): Alberts, Ghiddey, Arnold
c     Reference in User Guide:
c
c     Changes:
c           1) Parameter MXGRAZ not used, so PMAXGRZ.INC
c              was dereferenced.
c           2) Common blocks RINPT1, CLIYR, CLIM, RIDGE, & WATER were
c              not used, so they were dereferenced.
c           3) Imbedded RETURN's were converted to IF's.
c           4) ISENES changed to ISENES(MXPLAN). -- CRM -- 5/29/92
c           5) Since ISENES is now stored in common block SENES,
c              DATA statement which set it to zero was removed.
c              This is statement is now included in BLKDATA.
c              CRM -- 6/9/92.
c           6) Variables IDECOM[p], ISTART, TMPVAR, IFLAG, X5, and
c              X6 are not needed for the call to GROW, since in
c              PTGRA they are always zero.  ISTART & IFLAG were
c              the only ones that were even initialized.  All these
c              variables were deleted.  6/09/92 -- CRM
c           7) VDMT set to zero at planting.  6/26/92 -- CRM.
c           8) In order to conform to the WEPP Coding Convention, the
c              5th - 8th arguments to GROW moved after the 2nd one,
c              and the last argument moved after the 3rd one.  Cor-
c              responding changes made in the call to GROW from this
c              routine.
c           9) Deleted dummy parameters TMPFLG, ISTART, & TRTMAS from
c              GROW, and its calls from PTGRA, PTGRP, and RANGE
c          10) Adding setting back of TLIVE to 0.0 whenever VDMT was
c              set back to zero.  TLIVE is used by new interception
c              code from Savabi.  Also  XXX  Arnold needs to review
c              the meaning, computation, and use of variables VDMT,
c              TLIVE, RMOGT, RMAGT, CANCOV, CANHGT - as there appear
c              to be inconsistencies between CROPLAND and RANGELAND
c              usage - and RANGELAND usage seems to match variable
c              descriptions better.   dcf   7/30/93
c
c
c     Version: This module recoded from WEPP version 91.40.
c     Date recoded: 10/02/91.
c     Note: This module is current with WEPP release version 91.50.
c     Date checked: 12/5/91.
c     Note: This module is current with WEPP release version 92.25.
c     Date checked: 5/29/92 - 6/09/92.
c     Recoded by: Charles R. Meyer.
c     Note: This module is current with WEPP version 93.05  dcf 5/19/93
c
c     + + + KEYWORDS + + +
c
c     + + + PARAMETERS + + +
      include 'pntype.inc'
      include 'pmxnsl.inc'
      include 'ptilty.inc'
      include 'pmxpln.inc'
      include 'pmxres.inc'
      include 'pmxcrp.inc'
      include 'pmxcut.inc'
      include 'pmxtls.inc'
      include 'pmxtil.inc'
      include 'pmxhil.inc'
c
c     + + + ARGUMENT DECLARATIONS + + +
      integer nowcrp
c
c     + + + ARGUMENT DEFINITIONS + + +
c     nowcrp - index of current crop
c
c     + + + COMMON BLOCKS + + +
      include 'ccrpvr1.inc'
c     modify: rmagt(mxplan),rtm(mxres,iplane)
c
      include 'ccrpvr2.inc'
c     modify: vdmt(mxplan)
c
      include 'ccrpvr3.inc'
c       read: fgs,dlai,gssen
c      write: sumgdd(mxplan)
c
      include 'ccrpvr5.inc'
c       read: ncount(mxplan)
c
      include 'ccover.inc'
c      write: canhgt(mxplan), cancov(mxplan), gcover(mxplan)
c
      include 'ccrpout.inc'
c      write: rtd(mxplan), rtmass(mxplan), lai(mxplan)
c
      include 'ccrpprm.inc'
c       read: jdharv(mxcrop,mxplan), jdplt(mxcrop,mxplan)
c
      include 'ccrpgro.inc'
c      write: hia(mxplan)
      include 'cdecvar1.inc'
c       read: cuthgt(ntype)
c
      include 'cflags.inc'
c       read: yldflg
      include 'cgcovr.inc'
c     modify: gcvplt(mxplan)
c
      include 'cperen.inc'
c       read: jdherb(mxcrop, mxplan),jdburn(mxcrop, mxplan),
c             jdslge(mxcrop, mxplan)
c
      include 'crout.inc'
c     modify: tlive(mxplan)
c
      include 'cstruc.inc'
c       read: iplane, ivers
c
      include 'cupdate.inc'
c       read: sdate
c
      include 'csenes.inc'
c     modify: isenes(mxplan)
CASnew
      include 'cyield.inc'
      include 'cnew.inc'
CASnew
c
c
c     + + + LOCAL VARIABLES + + +
      integer intcrp, idecom, nowres, iadflg
      real silamt,vdmact,pyld,vdmttmp
CASnew
      character*50 ystr
      real newhgt,laic,gddc
      integer cutflg
CASnew
c
c     + + + LOCAL DEFINITIONS + + +
c     intcrp - flag set at harvest, planting, burning, silage or
c              herbicide date. Vegetative dry matter, canopy cover,
c              canopy height, root mass, and root depth are set to
c              zero while the canopy cover decays.
c     idecom - dummy variable required by GROW. IDECOM is a flag used
c              to indicate whether residue updating needs to be done
c              at the first freezing of a perennial crop (call to RESUP)
c              setting of IDECOM is done in PTGRP
c     isenes - flag used in resup to indicate type of update for residue
c               1 - harvest after senescence
c               0 - harvest before senescence
c              -1 - stop/kill date of perennial
c              -2 - senescence (annual) or 1st freeze of perennial
c     silamt - silage harvest amount kg/m^2
c
c
c     + + + SUBROUTINES CALLED + + +
c     initpl
c     resup
c     grow
c
c     + + + END SPECIFICATIONS + + +
c
      intcrp = 0
c
c     Planting Date
c
      if (sdate.eq.jdplt(nowcrp,iplane)) then
        if (ivers.ne.3) write (6,*) 'PLANTING CROP #',nowcrp,
     1      ' on OFE #',iplane,' on DAY',sdate
        if (ivers.eq.3) write (6,*) 'PLANTING CROP #',nowcrp,
     1      ' on CHANNEL #',iplane,' on DAY',sdate
        isenes(iplane) = 0
        intcrp = 1
c
        vdmt(iplane) = 0.0
c
c       XXX - Variable TLIVE is never reset to 0.0 - this probably should
c       be done here when plant date is reached and other variables
c       set back to zero.   dcf   7/30/93
c
        tlive(iplane) = 0.0
c
        hia(iplane) = 0.0
c
c       Need to save the ground cover on the day of planting value -
c       this value will then be passed to subroutine INFPAR to compute
c       the macroporosity adjustment factor.  dcf  1/6/93
c
        gcvplt(iplane) = gcover(iplane)
CASnew On planting date resetting cutflg equal to zero for annuals.
        cutflg = 0
CASnew
      end if
c
c
CAS Commented L0 if else by A. Srivastava 7/10/2018. To fix crop growth when killing with herbicide application in NRCS WEPP.
CAS Also to fix growth of previous crop.
c     TRAPS: If simulation date is greater than date of silage,
c     burning or herbicide application, then RETURN.
c
c     *** L0 IF ***
Commented by A. Srivastava
!!      if ((sdate.gt.jdslge(nowcrp,iplane)).and.(jdslge(nowcrp,iplane)
!!     1    .ne.0)) then
!!        continue
!!c
!!c     *** L0 ELSE-IF ***
!!      else if ((sdate.gt.jdburn(nowcrp,iplane)).and.(
!!     1    jdburn(nowcrp,iplane).ne.0).and.(jdburn(nowcrp,iplane).gt.
!!     1    jdplt(nowcrp,iplane))) then
!!        continue
!!c
!!c     *** L0 ELSE-IF ***
!!      else if ((sdate.gt.jdherb(nowcrp,iplane)).and.(
!!     1    jdherb(nowcrp,iplane).ne.0)) then
!!        continue
!!c
!!c     *** L0 ELSE ***
!!      else
Comments ends
c
c       *** L1 IF ***
c
c       silage modifications 3/24/98
c
CAS Added silage date = harvest date condition. A. Srivastava 7/13/2018
        if (sdate.eq.jdslge(nowcrp,iplane).and.jdslge(nowcrp,iplane)
     1     .eq.jdharv(nowcrp,iplane)) then
c         set residue mass above ground to ratio of
c         vegetative dry matter-
c         (harvest cut height/canopy height)*vegetative dry matter
          intcrp = 1
          if(canhgt(iplane).le.0.0.or.vdmt(iplane).le.0.0)then
            write(6,1400)
          else
            if(canhgt(iplane).le.cuthgt(nowcrp))then
              silamt=((canhgt(iplane)-(canhgt(iplane)*0.05))/
     1           canhgt(iplane))*vdmt(iplane)
              write(6,1300)canhgt(iplane)*0.05
            else
            silamt=((canhgt(iplane)-cuthgt(nowcrp))/
     1         canhgt(iplane))*vdmt(iplane)
            end if
            rmagt(iplane)=rmagt(iplane)+vdmt(iplane)-silamt
c           Kill annual crop
            vdmt(iplane)=0.0
            if (ivers.ne.3) write (6,1000) sdate, iplane, silamt
            if (ivers.eq.3) write (6,1200) sdate, iplane, silamt
c
            if (yldflg.eq.1)
     1         write (46,1100)itype(nowcrp,iplane),sdate,iplane,silamt
CASnew !! For silage yield
                sumyld(itype(nowcrp,iplane),iplane) =
     1              sumyld(itype(nowcrp,iplane),iplane) + silamt
                iyldct(itype(nowcrp,iplane),iplane) =
     1              iyldct(itype(nowcrp,iplane),iplane) + 1
CASnew
            nowres = 1
            rtm(3,iplane) = rtm(2,iplane)
            rtm(2,iplane) = rtm(nowres,iplane)
            rtm(nowres,iplane) = rtm15(iplane)
          end if

c
c       Herbicide Application Date
c
c       *** L1 ELSE-IF ***
CAS Added herbicide date = harvest date condition. A. Srivastava 7/13/2018
     !!     else if (sdate.eq.jdherb(nowcrp,iplane).and.
     !!1      jdherb(nowcrp,iplane).ne.0.and.jdherb(nowcrp,iplane)
     !!1      .eq.jdharv(nowcrp,iplane)) then
        else if (sdate.eq.jdherb(nowcrp,iplane).and.
     1      jdherb(nowcrp,iplane).ne.0) then
          !rmagt(iplane) = rmagt(iplane) + vdmt(iplane)
          !nowres = 1
          !rtm(3,iplane) = rtm(2,iplane)
          !rtm(2,iplane) = rtm(nowres,iplane)
          !rtm(nowres,iplane) = rtm15(iplane)
CAS
CAS          call resup(nowcrp,isenes(iplane))
CAS
          intcrp = 1
c
c       Harvest Date
c
c       *** L1 ELSE-IF ***
      else if (sdate.eq.jdharv(nowcrp,iplane)) then
c
CASnew A. Srivastava
CAS          isenes(iplane) = 1 !! This was causing dead roots not to decompose. 
CAS								!! isenes = 1 was not shifting residue pools at harvest or senescence.		  
CASnew
          call resup(nowcrp,isenes(iplane))
          intcrp = 1
c
c       Burning Date
c
c       *** L1 ELSE-IF ***
        else if (sdate.eq.jdburn(nowcrp,iplane).and.
     1      jdburn(nowcrp,iplane).ne.0) then
          !rmagt(iplane) = (rmagt(iplane)+vdmt(iplane))
          !nowres = 1
          !rtm(3,iplane) = rtm(2,iplane)
          !rtm(2,iplane) = rtm(nowres,iplane)
          !rtm(nowres,iplane) = rtm15(iplane)
CAS
CAS          call resup(nowcrp,isenes(iplane))
CAS
          intcrp = 1
          
c
CCCCCCCCCCCCCC
c         Management Option 1 (cutting with removal) & 4  (without removal) - based on % biomass
CASnew1
      elseif ((mgtopt(nowcrp,iplane).eq.1 .or.
     1        mgtopt(nowcrp,iplane).eq.4).and.
     1        sdate.ne.jdharv(nowcrp,iplane)) then
c         Management Option 1 (cutting with removal)
            if (sdate.eq.jdancut(nowcrp,iplane)) then
                
                vdmttmp = 0.0
                vdmttmp = vdmt(iplane)
c
                vdmt(iplane) = vdmt(iplane)*
     1                            (1-ancutht(nowcrp,iplane))
c
c
                pyld = vdmttmp * (ancutht(nowcrp,iplane))
c
c               Calculate initial crop parameter values for simulation
c               of next cutting period
c
c
c               Update LAI and cumulative growing degree days
CASnew1
                laic = lai(iplane)
                gddc = sumgdd(iplane)
CASnew1
c
                lai(iplane) = (xmxlai(itype(nowcrp,iplane))*
     1              vdmt(iplane)) / (vdmt(iplane)+0.5512*
     1              exp(-6.8*vdmt(iplane)))
CAS Commented by A. Srivastava
     !!           sumgdd(iplane) = gddmax(itype(nowcrp,iplane)) *
     !!1              lai(iplane) / xmxlai(itype(nowcrp,iplane))
CASnew1 Not adjusting sumgdd for root and not root crops. A. Srivastava
      !!if (hitype(itype(nowcrp,iplane)).eq.1) then !! Do not adjust sumgdd when root crops are cut.
      !!          sumgdd(iplane) = gddc * (lai(iplane)/laic)
      !!endif
CASnew1
c
c               Equation 8.2.4
c               CANCOV = 1 - e ^ (BB * VDMT)
c
c               update canopy cover, based on vegetative dry matter (VDMT).
c
                cancov(iplane) = 1. -
     1              exp(-bb(itype(nowcrp,iplane))*vdmt(iplane))
c
                if (cancov(iplane).lt.0.0) cancov(iplane) = 0.0
                if (cancov(iplane).gt.0.999) cancov(iplane) = 0.999
c
c               update canopy height, based on vegetative dry matter (VDMT).
c
                canhgt(iplane) = (1.-
     1              exp(-bbb(itype(nowcrp,iplane))*vdmt(iplane))) *
     1                    hmax(itype(nowcrp,iplane))
c
              if (ivers.ne.3) write (6,1500) sdate, iplane, pyld
              if (ivers.eq.3) write (6,1700) sdate, iplane, pyld
              iadflg = 1
c
c
c             ADD a write statement to a file to store crop yields
c             for George Foster  3/25/93   dcf
c
c             if (mgtopt(nowcrp,iplane).eq.1. and. yldflg.eq.1) then
              if (yldflg.eq.1) then
CASnew
             if(mgtopt(nowcrp,iplane).eq.1) then
                ystr = '(Biomass removed from the field)';
                write (46,1600) itype(nowcrp,iplane), sdate, iplane,
     1              pyld,ystr
c
c               ADD summation variables to total up the yields of the
c               various crops on the various OFE's.  ADD variable to
c               ADD up the number of harvests of the various crops
c               on the various OFE's.
c
     !!!!           sumyld(itype(nowcrp,iplane),iplane) =
     !!!!1              sumyld(itype(nowcrp,iplane),iplane) + pyld
     !!!!           iyldct(itype(nowcrp,iplane),iplane) =
     !!!!1              iyldct(itype(nowcrp,iplane),iplane) + 1
             elseif(mgtopt(nowcrp,iplane).eq.4) then
                ystr = '(Biomass added to flat residue amount)';
                write (46,1150) itype(nowcrp,iplane), sdate, iplane,
     1              pyld,ystr
             endif
c
              end if
c
c             NEW CODE to put cut material on soil surface as residue
c             cover.   dcf  4/25/94
c
CASnew1
             if(mgtopt(nowcrp,iplane).eq.4) then
                 cutflg = 14
                 call resup2(nowcrp,cutflg,pyld)
!!				 isenes(iplane) = 0 !! resetting isenes(iplane) = 0; 
									!! Assuming after annual crop cutting isenes becomes zero.
									!! This could be discussed.
             endif
c
            end if
CCCCCCCCCCCCCC
c         Management Option 5 (cutting with removal) & 6  (without removal) - based on cutting height
CASnew1
      elseif ((mgtopt(nowcrp,iplane).eq.5 .or.
     1        mgtopt(nowcrp,iplane).eq.6).and.
     1        sdate.ne.jdharv(nowcrp,iplane)) then
c         Management Option 1 (cutting with removal)
            if (sdate.eq.jdancut(nowcrp,iplane)) then
c
              if (canhgt(iplane).gt.cuthgt(itype(nowcrp,iplane))) then
                canhgt(iplane) = cuthgt(itype(nowcrp,iplane))
c
c               Update vegetative dry matter today
c
                vdmact = log(1.0-canhgt(iplane)/
     1              hmax(itype(nowcrp,iplane))) / (-
     1              bbb(itype(nowcrp,iplane)))
                pyld = vdmt(iplane) - vdmact
c
c               Calculate initial crop parameter values for simulation
c               of next cutting period
c
c               Update vegetative dry matter today
c
                vdmt(iplane) = vdmact
c
c               Update LAI and cumulative growing degree days
CASnew1
                laic = lai(iplane)
                gddc = sumgdd(iplane)
CASnew1
c
                lai(iplane) = (xmxlai(itype(nowcrp,iplane))*
     1              vdmt(iplane)) / (vdmt(iplane)+0.5512*
     1              exp(-6.8*vdmt(iplane)))
CAS Commented by A. Srivastava
     !!           sumgdd(iplane) = gddmax(itype(nowcrp,iplane)) *
     !!1              lai(iplane) / xmxlai(itype(nowcrp,iplane))
CASnew1 Not adjusting sumgdd for root and not root crops. A. Srivastava
      !!if (hitype(itype(nowcrp,iplane)).eq.1) then !! Do not adjust sumgdd when root crops are cut.
      !!          sumgdd(iplane) = gddc * (lai(iplane)/laic)
      !!endif
CASnew1
c
c               Equation 8.2.4
c               CANCOV = 1 - e ^ (BB * VDMT)
c
c               update canopy cover, based on vegetative dry matter (VDMT).
c
                cancov(iplane) = 1. -
     1              exp(-bb(itype(nowcrp,iplane))*vdmt(iplane))
c
                if (cancov(iplane).lt.0.0) cancov(iplane) = 0.0
                if (cancov(iplane).gt.0.999) cancov(iplane) = 0.999
c
              if (ivers.ne.3) write (6,1500) sdate, iplane, pyld
              if (ivers.eq.3) write (6,1700) sdate, iplane, pyld
              iadflg = 1
c
c
c             ADD a write statement to a file to store crop yields
c             for George Foster  3/25/93   dcf
c
c             if (mgtopt(nowcrp,iplane).eq.1. and. yldflg.eq.1) then
              if (yldflg.eq.1) then
CASnew
             if(mgtopt(nowcrp,iplane).eq.5) then
                ystr = '(Biomass removed from the field)';
                write (46,1600) itype(nowcrp,iplane), sdate, iplane,
     1              pyld,ystr
c
c               ADD summation variables to total up the yields of the
c               various crops on the various OFE's.  ADD variable to
c               ADD up the number of harvests of the various crops
c               on the various OFE's.
c
     !!!!           sumyld(itype(nowcrp,iplane),iplane) =
     !!!!1              sumyld(itype(nowcrp,iplane),iplane) + pyld
     !!!!           iyldct(itype(nowcrp,iplane),iplane) =
     !!!!1              iyldct(itype(nowcrp,iplane),iplane) + 1
             elseif(mgtopt(nowcrp,iplane).eq.6) then
                ystr = '(Biomass added to flat residue amount)';
                write (46,1150) itype(nowcrp,iplane), sdate, iplane,
     1              pyld,ystr
             endif
             endif
c
              else
                  pyld = 0.0
              end if
c
c             NEW CODE to put cut material on soil surface as residue
c             cover.   dcf  4/25/94
c
CASnew1
             if(mgtopt(nowcrp,iplane).eq.6) then
                 cutflg = 14
                 call resup2(nowcrp,cutflg,pyld)
!!				 isenes(iplane) = 0 !! resetting isenes(iplane) = 0; 
									!! Assuming after annual crop cutting isenes becomes zero.
									!! This could be discussed.
             endif
c
            end if
CCCCCCCCCCCCCC
c
        end if
c
c       Vegetative dry matter, canopy cover, canopy height, root mass,
c       and root depth values are set to zero when any of the following
c       times: at harvest, before planting, or at burning, silage, and
c       herbicide dates.
c
        if (intcrp.eq.1) then
c
          rtd(iplane) = 0.0
          rtmass(iplane) = 0.0
          rtm15(iplane) = 0.0
          rtm30(iplane) = 0.0
          rtm60(iplane) = 0.0
          sumgdd(iplane) = 0.0
          cancov(iplane) = 0.0
          canhgt(iplane) = 0.0
          if(jdslge(nowcrp,iplane).ne.sdate)vdmt(iplane) = 0.0
          lai(iplane) = 0.0
c
c         XXX  - Variable TLIVE is never reset to 0.0 - this probably should
c         be done here when stop date is reached and other variables
c         set back to zero.   dcf   7/30/93
c
          tlive(iplane) = 0.0
CASnew For release cover crop A. Srivastava 2/13/2017
      if (manver .ge. 2016.3) then
          if(sdate.eq.jdplt(nowcrp,iplane).and.
     1                    rcc(itype(nowcrp,iplane)).gt.0) then
              call initgrrcc(nowcrp)
          endif
      endif
CASnew End
        else if (intcrp.eq.0) then
c
c         Check whether simulation date is within the growing season.
c         -------- summer crop or winter crop
          if (((jdplt(nowcrp,iplane).lt.jdharv(nowcrp,iplane)).and.((
     1        sdate.ge.jdplt(nowcrp,iplane)).and.(sdate.le.
     1        jdharv(nowcrp,iplane)))).or.((jdplt(nowcrp,iplane).ge.
     1        jdharv(nowcrp,iplane)).and.((sdate.ge.
     1        jdplt(nowcrp,iplane)).or.(sdate.le.jdharv(nowcrp,iplane)))
     1        )) then
c
            call grow(nowcrp,iplane,0.0,0.0,ncount(iplane),idecom)
          end if
          end if
c
c     *** L0 ENDIF ***
Commented by A. Srivastava
      !!end if
Comment ends
c
      return
 1000 format(' SILAGE HARVEST DATE ',i3,' -- plane ',i2,
     1    ' yield ',f6.3,'(kg/m**2) '/)
 1100 format(' Crop Type # ',i2,' Date = ',i3,' OFE # ',i2,
     1    ' SILAGE= ',f8.3,'(kg/m**2)  ')
 1200 format(' SILAGE HARVEST DATE ',i3,' -- channel ',i2,
     1    ' yield ',f6.3,'(kg/m**2) '/)
 1300 format(//,' *** WARNING ***',/,' Cutting height greater than or',
     1    ' equal to canopy height!',/,' Cutting height set to 5% of',
     1    ' canopy height, cutting height for silage =',f5.2,' m',
     1    /,' *** WARNING ***',//)
 1400 format(//,' *** WARNING ***',/,' Canopy height or Vegetative dry',
     1    ' matter less than or equal to 0.0,',/,' No silage operation',
     1    ' performed!',/,' *** WARNING ***',//)
CASnew
 !!1500 format (' HARVEST date ',i3,' plane ',i4,' yield ',f8.3,
 !!    1    '(kg/m**2)')
 1500 format (' CUTTING date ',i3,' plane ',i4,' yield ',f8.3,
     1    '(kg/m**2)')
 1600 format (' Crop Type # ',i2,' Date = ',i3,' OFE # ',i2,' yield= ',
     1    f8.3,'(kg/m**2)',a50)
 !!1700 format (' HARVEST date ',i3,' channel ',i4,' yield ',f8.3,
 !!    1    ' (kg/m**2)')
 1700 format (' CUTTING date ',i3,' channel ',i4,' yield ',f8.3,
     1    ' (kg/m**2)')
CASnew
 1150 format (' Crop Type # ',i2,' Date = ',i3,' OFE # ',i2,' yield= ',
     1    f8.3,'(kg/m**2)',a50)
CASnew
      end
