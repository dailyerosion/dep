
c     begin include file cupdate.inc

c     + + + COMMON BLOCK DESCRIPTION + + +
c     + + + INSERT DESCRIPTION HERE  + + +

      common /update/   day,mon,year,sdate,mdate(mxtill,mxtlsq),
     1                  indxy(mxplan),
     1                  opday(366,mxtlsq),opcnt

c     + + + VARIABLE DECLARATIONS + + +

      integer           day,mon,year,sdate,mdate,indxy,opday,
     1                  opcnt

c     + + + VARIABLE DEFINITIONS + + +

c     day                  : day of year
c     mon                  : month of year
c     year                 : year of simulation
c     sdate                : date of year in Julian date
c     mdate(mxtill,mxtlsq) : Julian date on which tillage occurs
c     indxy(mxplan)        : management operation index
c     opday                : Max. operations in a day
c     opcnt                : Operation progressing counter

c     end include file cupdate.inc

