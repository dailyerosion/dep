      subroutine chrqin(vol, qin, nt0, iq)
c
c     + + + PURPOSE + + +
c     SR CHRQIN calculates channel inflow (m^3/s) or lateral inflow (m^3/s) for each time step.
c
c     Called from: SR WSHCHR
c     Author(s): L. Wang
c     Reference in User Guide:
c
c     Version:
c     Date recoded:
c     Recoded by:
c
c     + + + KEYWORDS + + +
c
c     + + + PARAMETERS + + +
c
      include 'pmxelm.inc'
      include 'pmxhil.inc'
      include 'pmxpln.inc'
      include 'pmxprt.inc'
      include 'pmxslp.inc'
      include 'pmxtim.inc'
      include 'pmxseg.inc'
      include 'pmxcsg.inc'
      include 'pmxchr.inc'
      include 'pmxtil.inc'
      include 'pmxtls.inc'
c
c     + + + ARGUMENT DECLARATIONS + + +
c
c     + + + ARGUMENT DEFINITIONS + + +
c
c     + + + COMMON BLOCKS + + +
c
      include 'cchpek.inc'
      include 'cdata1.inc'
      include 'cdata3.inc'
      include 'chydrol.inc'
      include 'cslope.inc'
      include 'cstore.inc'
      include 'cstruc.inc'
      include 'cstruct.inc'
      include 'cchvar.inc'
      include 'cchpar.inc'
      include 'cchrt.inc'
      include 'cupdate.inc'
c
c     + + + LOCAL VARIABLES + + +
c
      real a1, b1, d1, u, vol, tc, td, ti, qp, eps, qin(0:mxtchr),
     1 tl, expap1, expap2, qin0(0:mxtchr),vsum,vf
      integer it, ierr, iq, nt0
c
c
c     + + + LOCAL DEFINITIONS + + +
c
c     a1    - constant in the equation:  1 - exp(-u) = a1 * u
c             in this subroutine, a = vol/(qp * td)
c     b1    - coefficient in double exponential
c     d     - coefficient in double exponential
c     ierr  - Flag. 0: equation solved
c                   1: no solution for given a
c     it    - current time step number
c     qin   - channel inflow rate, [m3/s]
c     qp    - peak runoff of overland flow, [m3/s]
c     tc    - time of concentration of overland flow, [s]
c     td    - runoff duration of a hillslope, [s]
c     u     - variable in the equation: 1 - exp(-u) = a1 * u
c     vol   - runoff volume of a hillslope, [m3]
c
c     + + + SUBROUTINES CALLED + + +
c     eqroot
c
c     + + + DATA INITIALIZATIONS + + +
c
c     + + + END SPECIFICATIONS + + +
c
c
      eps = 1.e-6
      vsum = 0.0
      if(vol > eps) then
c     
        if(iq == 1) then         ! lateral inflow from left hillslope
         td = watdur(nhleft(ielmt))
         qp = tmppkr(nhleft(ielmt))
        elseif(iq == 2) then     ! lateral inflow from right hillslope
         td = watdur(nhrght(ielmt))
         qp = tmppkr(nhrght(ielmt))
      else                     ! inflow from top hillslope
         td = watdur(nhtop(ielmt))
         qp = tmppkr(nhtop(ielmt))
      endif
c      tc = htcs(ielmt)*3600.
      tc = td / 2.67
c     
      if(vol >= qp*td-eps) then
          do it = nt0, ntchr
          ti = dtchr * it
          if(ti <= td) then
                 qin(it) = qin(it) + qp
          endif
        enddo
      else
        a1 = vol / (qp * td)
          call eqroot(a1, ierr, u)
        b1 = u / tc
        d1 = u / (td - tc)
c--------------------------------------------------
c using pointwise value
        if(mofapp==1) then
            do it = nt0, ntchr
            ti = dtchr * it
        if(ti <= tc) then
                  qin0(it) = qp * exp(b1*(ti-tc))
                  vsum = vsum + qin0(it)
                elseif(ti <= td) then
                  qin0(it) = qp * exp(d1*(tc-ti))
                  vsum = vsum + qin0(it)
            endif
          enddo
c checking mass balance in case time step too large
            vsum = (vsum - qin0(nt0)) * dtchr
            if (vsum.gt.1.0e-32) then
             vf = vol / vsum
               do it = nt0, int(td/dtchr)
                  qin(it) = qin(it) + qin0(it) * vf
               enddo
            endif
c--------------------------------------------------
c using cell average
        else
            do it = nt0, ntchr
              ti = dtchr * it
                if(u <= eps) then
              if(ti <= td) qin(it) = qin(it) + qp
                else
              tl = ti - dtchr
              if(ti <= tc) then
                     if(b1 <= eps) then
                   qin(it) = qin(it) + qp*(1.+(ti-tc-0.5*dtchr)*b1)
                     else
                   qin(it) = qin(it) + qp*((exp(b1*(ti-tc))
     1                         - exp(b1*(tl-tc)))/(b1*dtchr))
                 endif
              elseif(tl < tc) then
                 if(b1 <= eps) then
                   expap1 = tc-tl-0.5*b1*(tl-tc)**2
                 else
                   expap1 = (1.-exp(b1*(tl-tc)))/b1
                 endif
                 if(d1 <= eps) then
                   expap2 = tc-ti+0.5*d1*(ti-tc)**2
                 else
                   expap2 = (exp(-d1*(ti-tc))-1.)/d1
                     endif
                     qin(it) = qin(it) + qp*(expap1 - expap2)/dtchr
                   elseif(tl < td) then
                     if(d1 <= eps) then
                   qin(it) = qin(it) + qp*(1.-(ti-tc-0.5*dtchr)*d1)
                     else
                   qin(it) = qin(it) + qp*((exp(-d1*(tl-tc))
     1                         - exp(-d1*(ti-tc)))/(d1*dtchr))
                 endif
              endif
            endif
          enddo
c--------------------------------------------------
          endif
      endif
      endif
      return
      end