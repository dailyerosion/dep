
c     begin include file ccntour.inc

c     + + + COMMON BLOCK DESCRIPTION + + +
c     + + + INSERT DESCRIPTION HERE  + + +

      common /cntour/   cntslp(mxplan),rowspc(mxplan),rowlen(mxplan),
     1                  rdghgt(mxplan),cntlen(mxplan),cnslp(mxplan),
     1                  conseq(mxcrop,mxplan),fail(3,mxplan),
     1                  totfal(mxplan),cntday(mxplan),cntend(mxplan),
     1                  contrs(mxcrop,mxplan)
     1                  ,cnfail(mxplan),condysflg(mxplan)
     1                  ,tildate(mxplan),failflg(mxplan),
     1                  contours_perm

c     + + + VARIABLE DECLARATIONS + + +

      real              cntslp,rowspc,rowlen,rdghgt,cntlen,cnslp
      integer           conseq,fail,totfal,cntday,cntend,contrs,cnfail
      integer           condysflg,tildate,failflg,contours_perm

c     + + + VARIABLE DEFINITIONS + + +
c     cntday(mxplan)        : beginning day contours in effect (julian)
c     cntend(mxplan)        : ending day contours in effect (julian)
c     cntslp(mxplan)        : contour slope (m/m)
c     rowspc(mxplan)        : contour row spacing (m)
c     rowlen(mxplan)        : contour row length (m)
c     rdghgt(mxplan)        : contour ridge height (m)
c     cntlen(mxplan)        : contour length
c     cnslp(mxplan)         : contour slope
c     conseq(mxcrop,mxplan) : contour sequence from management input
c     fail(3,mxplan)        : counter for contour failures
c                             1 - contour slope is the same as average slope
c                             2 - slope angle exceeds row angle
c                             3 - not currently set
c     totfal(mxplan)        :
c     condysflg(mxplan)     : flag for NRCS version (>= v2016.3) used to identify start and end dates of 
c                             contouring and to switch contours on/off for tillage within contours days
c     failflg(mxplan)       : counter used to switch off contours in a hillslope with multiple OFE's if 
c                             contours fails in the uppermost OFE's on a hillslope.
c     contours_perm         : flag to indicate if temporary contours (flag=0, NRCS version) or previous 
c                             permanent contouring (flag=1) should be used
c
c
c

c     end include file ccntour.inc