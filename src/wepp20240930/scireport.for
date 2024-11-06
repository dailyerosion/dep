c
c  
      subroutine scireport(jun)
c
c     + + + PURPOSE + + +
c     Uses SCI equations to write a report. SCI subfactors required by NRCS.
c
c     + + + KEYWORDS + + +
c        
c     + + + PARAMETERS + + +
      integer jun
c
c     + + + COMMON BLOCKS + + +           
      include 'pmxres.inc'
      include 'pmxtil.inc'
      include 'pmxpln.inc'
      include 'pmxtls.inc'
      include 'pmxnsl.inc'
      include 'pntype.inc'
      include 'cstruc.inc'
      include 'ccrpvr1.inc'
      include 'cdist2.inc'
      include 'ctemp.inc'
      
c     + + + LOCAL VARIABLES + +       
      real sand, clay
      real texmult, sci_om_factor
      real adjtotalrennerom
      real totseglen, avgtexmult
      real avgbiomass, avgallbiomass, seglen
      real totalRennerOM
      integer texclass,i

      parameter (totalRennerOM = 0.35155) ! 3136.5 pounds/acre base 
      
c Determines the usda textural class from the sand and clay fractions.
c Original code included for reference below, was modified to use
c fractions instead of percent and modified to return a class number,
c also defined below, instead of returning the string shown in the comment
c after the line where class number is set.
 
      write (jun,1950)
      totseglen = 0
      avgallbiomass = 0
      avgtexmult = 0
      texclass = 999
      do i = 1, nplane
        !!sand = sand1(1,i)
        !!clay = clay1(1,i)
CAS Using sand and silt content directly from top soil layer (without layer adjustment)
        sand = scisand1(1,i)
        clay = sciclay1(1,i)
        if (clay .gt. 0.40) then
        texclass = 12 !'c   '
        if (sand .gt. 0.45) texclass = 10 !'sc  '
        if ((sand+clay) .lt. 0.60) texclass = 11 !'sic '
        else
        if (clay .gt. 0.27) then
          texclass = 9 !'sicl'
          if (sand .gt. 0.20) texclass = 8 !'cl  '
          if (sand .gt. 0.45) then
            texclass = 7 !'scl '
            if (clay .gt. 0.35) texclass = 10 !'sc  '
          end if
        else
          if ((sand+clay) .lt. 0.50) texclass = 5 !'sil '
          if ((sand+clay) .lt. 0.20 .and.clay .lt. 0.12) texclass = 6 !'si  '
          if ((sand+clay) .ge. 0.50) texclass = 3 !'sl  '
          if (((sand+clay) .ge. 0.50) .and. ((sand+clay) .lt. 0.72)  
     &         .and. (clay .gt. 0.7) .and. (sand .lt. 0.52)) 
     &         texclass = 4    ! loam
          if (((sand+clay).ge. 0.72).and.(clay .gt. 0.20))
     &         texclass = 7 !scl
          if ((sand-clay) .gt. 0.70) texclass = 2 !'ls  '
          if ((sand-0.5*clay) .gt. 0.85) texclass = 1 !'s   '
        end if
        end if
        select case (texclass)
        case(1)  ! SAND
          texmult = 1.6
        case(2)  ! LOAMY SAND
          texmult = 1.6
        case(3)  ! SANDY LOAM
          texmult = 1.37
        case(4)  ! LOAM
          texmult = 1.37
        case(5)  ! SILT LOAM
          texmult = 1.37
        case(6)  ! SILT
          texmult = 1.37
        case(7)  ! S. CLAY LOAM
          texmult = 1.1
        case(8)  ! CLAY LOAM
          texmult = 1.1
        case(9)  ! SL. CLAY LOAM
          texmult = 1.1
       case(10) ! SANDY CLAY
          texmult = 1.0
       case(11) ! SILTY CLAY
          texmult = 1.0
       case(12) ! CLAY
          texmult = 1.0
       case default
          texmult = 1.4
        end select

        seglen = slplen(i)
        avgbiomass = allbiomass_sum(i) / days_sum
        avgallbiomass = avgallbiomass + avgbiomass * seglen
        avgtexmult = avgtexmult + texmult * seglen
        totseglen = totseglen + seglen
        write(jun,1975) i, avgbiomass, texclass, avgtexmult, seglen
      end do

      avgallbiomass = avgallbiomass / totseglen
      avgtexmult = avgtexmult / totseglen
      adjtotalRennerOM = totalRennerOM * avgtexmult
      sci_om_factor = (avgallbiomass-adjtotalRennerOM) /adjtotalRennerOM
      write(jun,1977)
      write(jun,1980) avgallbiomass, adjtotalRennerOM, sci_om_factor
      return
      
 1950 format(/2x,'D. SCI OM: ABOVE AND BELOW GROUND BIOMASS RETURNED',
     1       ' TO SOIL',/5x,'OFE    Amount    Texture ',
     1       '  Mult  Seg Len(m)')
 1975 format (3x,i4,4x,f8.4, 4x, i3, 4x, f6.2, 4x, f8.3)
 1977 format (/5x,'Avg all biomass  Adj Renner OM  SCI OM Factor',/5x,
     1            '---------------  -------------  -------------')
 1980 format (3x,f8.4,10x,f8.4,10x,f12.4)
      
      end


