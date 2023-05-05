
c     begin include file cslinit.inc

c     + + + COMMON BLOCK DESCRIPTION + + +
c     + + + INSERT DESCRIPTION HERE  + + +

      common /slinit/   rrinit(mxplan),rhinit(mxplan),rfcum(mxplan),
     1                  bdtill(mxplan),riinit(mxplan)

c     + + + VARIABLE DECLARATIONS + + +

      real              rrinit,rhinit,rfcum,bdtill,riinit

c     + + + VARIABLE DEFINITIONS + + +

c     rrinit(mxplan) : initial ridge roughness (m)
c     rhinit(mxplan) : initial ridge height (m)
c     rfcum(mxplan)  : cumulative rainfall since last tillage (mm)
c     bdtill(mxplan) : bulk density after last tillage (g/cc)
c     riinit(mxplan) : initial ridge interval (m)

c     end include file cslinit.inc

