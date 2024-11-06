#
#
# makefile for solaris 8 wepp executable.
#
FC_IF	  = ifort
FC_G95        = g95
FC_GNU        = gfortran
FC_2      = f2c
#FFLAGS_IFORT    = -c -autodouble -O -align dcommons 
#FFLAGS_IFORT    = -c -autodouble -O -traceback -align dcommons -diag-disable 8291
FFLAGS_IFORT    = -c -autodouble -O1 -traceback -align dcommons -diag-disable 8291

FFLAGS_G95    = -c -Wall -malign-double -O3 -march=pentium4 
FFLAGS_G95    = -c -Wall -malign-double -r8 -O3 -i4 
FFLAGS_GNU     = -c -fdefault-real-8 -Wall -malign-double -O2 -fimplicit-none -Wno-align-commons -Wsurprising -Wextra -Wcompare-reals
FFLAGS_2 = -c -r
LINK_IF    = ifort 
LINK_G95    = g++
LINK_GNU     = gfortran
LINK_2    = g++
PROGRAM   = wepp

ifeq ($(FC),gfortran)
  FFLAGS = $(FFLAGS_GNU)
  FC = $(FC_GNU)
  LINKER = $(LINK_GNU)
else
  FFLAGS = $(FFLAGS_IFORT)
  FC = $(FC_IF)
  LINKER = $(LINK_IF)
endif

#FFLAGS = $(FFLAGS_G95)
#FC = $(FC_G95)
#LINKER = $(LINK_G95)

DEST      = .
#LDFLAGS   = -static /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc_eh.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libf95.a 

#LDFLAGS   = -static /usr/local/lib/gcc-lib/x86_64-unknown-linux-gnu/4.0.3/libgcc.a /usr/local/lib/gcc-lib/x86_64-unknown-linux-gnu/4.0.3/libgcc_eh.a /usr/local/lib/gcc-lib/x86_64-unknown-linux-gnu/4.0.3/libf95.a

#LDFLAGS   = -static /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc_eh.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libf95.a 

LDFLAGS = -static

.SUFFIXES: .for .o

MAKEFILE  = Makefile
OBJS            = annchn.o annout.o appmth.o aspect.o bgnrnd.o \
                  bighdr.o bigout.o brkpt.o \
                  case12.o case34.o chncon.o chnero.o chnpar.o \
                  chnrt.o chnvar.o close.o conrun.o \
                  const.o contin.o convrt.o covcal.o crit.o \
                  cross.o cutgrz.o dblex.o dcap.o decomp.o \
                  depc.o depend.o depeqs.o depirr.o deplet.o \
                  depos.o depsto.o detach.o disag.o drain.o \
                  eatcom.o endchn.o enddet.o endout.o enrcmp.o \
                  enrich.o enrprt.o eplane.o eqroot.o erod.o \
                  evap.o falvel.o frcfac.o frichn.o \
                  fslpar.o fslq.o furadv.o furgps.o furlea.o \
                  furrec.o furrow.o furrun.o gcurve.o gdmax.o \
                  getdat.o grna.o grow.o growop.o hdepth.o \
                  hdrive.o hr_tmp.o hrtmp.o hydchn.o hydout.o \
                  idat.o impday.o impeo.o impeos.o impflo.o \
                  imphnw.o impint.o impmai.o impmon.o imppol.o \
                  imppow.o imppro.o impreg.o impris.o impsvb.o \
                  impsvd.o impyr.o infile.o infpar.o inidat.o \
                  init1.o initd.o initgr.o input.o intrpl.o \
                  irflow.o irinpt.o irprnt.o irrig.o irs.o \
                  kostia.o main.o melt.o monchn.o \
                  monout.o mxint.o mxreal.o newrap.o newtil.o \
                  newton.o nowup.o open.o outfil.o param.o \
                  patrib.o peak.o perc.o phi.o print.o profil.o \
                  prtcmp.o psiinv.o psis.o ptgra.o ptgrp.o \
                  purk.o qinf.o radcur.o rand.o range.o rburn.o \
                  rdat.o readin.o reid.o res_dp.o resup.o \
                  rgraze.o rgrcur.o rherb.o rngint.o rochek.o \
                  root.o route.o rtpart.o runge.o runout.o \
                  scenhd.o scon.o scurv.o seddia.o sedia.o \
                  sedist.o sedmax.o sedout.o sedseg.o sedsta.o \
                  shdist.o shear.o shears.o shield.o \
                  sint.o sintdp.o sloss.o sndrft.o snowd.o \
                  soil.o spread.o stmget.o stmtim.o strip.o \
                  strout.o sumfrc.o sumrnf.o sumrun.o sunmap.o \
                  swu.o table.o tfail.o tilage.o \
                  tmpadj.o trcoef.o trncap.o trnlos.o undflo.o \
                  unifor.o useout.o verchk.o watbal.o winit.o \
                  winter.o winthd.o wshcqi.o wshdrv.o \
                  wshimp.o wshini.o wshinp.o wshiqi.o wshirs.o \
                  wshout.o wshpas.o wshpek.o wshred.o wshrun.o \
                  wshscs.o wshtc.o xcrit.o xinflo.o xmonth.o \
                  yalin.o yldopt.o pmetcoef.o evappm.o outeng.o hdreng.o \
                  frsoil.o psolr.o tmpcft.o saxpar.o frostn.o \
                  saxfun.o tmpfun.o locate.o frwatc.o frzng.o mltbtm.o watdst.o mlttp.o \
                  frznw.o sheart.o wshchr.o mann.o chrqin.o \
		  watbal_hourly.o watbalprint.o writeyearlylossbypoint.o getfreezecond.o \
		  sciomadd.o scireport.o initgrrcc.o getdat2.o resup2.o readin2.o

SRCS            = annchn.for annout.for appmth.for aspect.for bgnrnd.for \
                  bighdr.for bigout.for brkpt.for \
                  case12.for case34.for chncon.for chnero.for chnpar.for \
                  chnrt.for chnvar.for close.for conrun.for \
                  const.for contin.for convrt.for covcal.for crit.for \
                  cross.for cutgrz.for dblex.for dcap.for decomp.for \
                  depc.for depend.for depeqs.for depirr.for deplet.for \
                  depos.for depsto.for detach.for disag.for drain.for \
                  eatcom.for endchn.for enddet.for endout.for enrcmp.for \
                  enrich.for enrprt.for eplane.for eqroot.for erod.for \
                  evap.for falvel.for frcfac.for frichn.for \
                  fslpar.for fslq.for furadv.for furgps.for furlea.for \
                  furrec.for furrow.for furrun.for gcurve.for gdmax.for \
                  getdat.for grna.for grow.for growop.for hdepth.for \
                  hdrive.for hr_tmp.for hrtmp.for hydchn.for hydout.for \
                  idat.for impday.for impeo.for impeos.for impflo.for \
                  imphnw.for impint.for impmai.for impmon.for imppol.for \
                  imppow.for imppro.for impreg.for impris.for impsvb.for \
                  impsvd.for impyr.for infile.for infpar.for inidat.for \
                  init1.for initd.for initgr.for input.for intrpl.for \
                  irflow.for irinpt.for irprnt.for irrig.for irs.for \
                  kostia.for main.for melt.for monchn.for \
                  monout.for mxint.for mxreal.for newrap.for newtil.for \
                  newton.for nowup.for open.for outfil.for param.for \
                  patrib.for peak.for perc.for phi.for print.for profil.for \
                  prtcmp.for psiinv.o psis.for ptgra.for ptgrp.for \
                  purk.for qinf.for radcur.for rand.for range.for rburn.for \
                  rdat.for readin.for reid.for res_dp.for resup.for \
                  rgraze.for rgrcur.for rherb.for rngint.for rochek.for \
                  root.for route.for rtpart.for runge.for runout.for \
                  scenhd.for scon.for scurv.for seddia.for sedia.for \
                  sedist.for sedmax.for sedout.for sedseg.for sedsta.for \
                  shdist.for shear.for shears.for shield.for \
                  sint.for sintdp.for sloss.for sndrft.for snowd.for \
                  soil.for spread.for stmget.for stmtim.for strip.for \
                  strout.for sumfrc.for sumrnf.for sumrun.for sunmap.for \
                  swu.for table.for tfail.for tilage.for \
                  tmpadj.for trcoef.for trncap.for trnlos.for undflo.for \
                  unifor.for useout.for verchk.for watbal.for winit.for \
                  winter.for winthd.for wshcqi.for wshdrv.for \
                  wshimp.for wshini.for wshinp.for wshiqi.for wshirs.for \
                  wshout.for wshpas.for wshpek.for wshred.for wshrun.for \
                  wshscs.for wshtc.for xcrit.for xinflo.for xmonth.for \
                  yalin.for yldopt.for pmetcoef.for evappm.for outeng.for hdreng.for \
                  frsoil.for psolr.for tmpcft.for saxpar.for frostn.for \
                  saxfun.for tmpfun.for locate.for frwatc.for frzng.for mltbtm.for watdst.for mlttp.for \
                  frznw.for sheart.for wshchr.for mann.for chrqin.for \
                  watbal_hourly.for watbalprint.for writeyearlylossbypoint.for getfreezecond.for \
		  sciomadd.for scireport.for initgrrcc.for getdat2.for resup2.for readin2.for

.for.o:
	$(FC) $(FFLAGS) $<

$(PROGRAM):     $(OBJS) $(LIBS)
	$(LINKER) $(OBJS) $(LDFLAGS) -o $(PROGRAM)

all: $(PROGRAM)
 
clean:
	@rm -f $(OBJS)
