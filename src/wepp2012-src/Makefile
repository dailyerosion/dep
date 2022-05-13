#
#
# makefile for solaris 8 wepp executable.
#

FC_IF	  = ifort
FC_G95        = g95
FC_GNU        = gfortran
FC_2      = f2c
FFLAGS_IFORT    = -c -autodouble -O1 -align dcommons 
FFLAGS_G95    = -c -Wall -malign-double -O3 -march=pentium4 
FFLAGS_G95    = -c -Wall -malign-double -O3 -i4 
FFLAGS_GNU     = -c -fdefault-real-8 -Wall -malign-double -O2 
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


DEST      = .
#LDFLAGS   = -static /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc_eh.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libf95.a 

#LDFLAGS   = -static /usr/local/lib/gcc-lib/x86_64-unknown-linux-gnu/4.0.3/libgcc.a /usr/local/lib/gcc-lib/x86_64-unknown-linux-gnu/4.0.3/libgcc_eh.a /usr/local/lib/gcc-lib/x86_64-unknown-linux-gnu/4.0.3/libf95.a

#LDFLAGS   = -static /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libgcc_eh.a /usr/lib/gcc-lib/i686-pc-linux-gnu/4.1.1/libf95.a 

LDFLAGS =

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
		    watbal_hourly.o watbalprint.o writeyearlylossbypoint.o getfreezecond.o


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
		    watbal_hourly.for watbalprint.for writeyearlylossbypoint.for getfreezecond.for

.for.o:
	$(FC) $(FFLAGS) $<

$(PROGRAM):     $(OBJS) $(LIBS)
	$(LINKER) $(OBJS) $(LDFLAGS) -o $(PROGRAM)

all: $(PROGRAM)
 
clean:
	@rm -f $(OBJS)

### OPUS MKMF:  Do not remove this line!  Automatic dependencies follow.

annchn.o: cchcon.inc cchpar.inc cchpek.inc cchprt.inc cchsed.inc \
         cenrpa1.inc cimeos.inc cimyrs.inc coutchn.inc cpart2.inc \
         cseddet.inc cslpopt.inc cstore.inc cstore1.inc cstore2.inc \
         cstruc.inc cstruct.inc csumirr.inc pmxcsg.inc pmxelm.inc \
         pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc

annout.o: cavloss.inc ccliyr.inc ciravlo.inc cstruc.inc csumirr.inc \
         csumout.inc cupdate.inc pmxhil.inc pmxpln.inc pmxtil.inc \
         pmxtls.inc

aspect.o: cangie.inc

bgnrnd.o: crndm.inc

bigout.o: cavepar.inc cavloss.inc ccdrain.inc cclim.inc ccliyr.inc \
         ccons.inc ccover.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc cefflen.inc cends4.inc cenrpa2.inc cffact.inc \
         cflags.inc chydrol.inc cirfur1.inc cirfur2.inc cirfurr.inc \
         cirriga.inc cparame.inc cparva2.inc cseddet.inc cslpopt.inc \
         csolva2.inc cstruc.inc cupdate.inc cwater.inc cwint.inc pmxcrp.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc \
         pmxsrg.inc pmxtil.inc pmxtls.inc pntype.inc pxstep.inc

brkpt.o: cdiss1.inc cdiss11.inc cdiss12.inc cdiss3.inc chydrol.inc \
         cupdate.inc pmxelm.inc pmxpln.inc pmxtil.inc pmxtls.inc

calchc.o: cstruc.inc cwater.inc cwint.inc pmxcrp.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxtil.inc pmxtls.inc

caqout.o: cstruc.inc cwint.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxtil.inc pmxtls.inc

case12.o: cchcas.inc cchero.inc cchvar.inc cgully.inc pmxcsg.inc \
         pmxpln.inc pmxprt.inc

case34.o: cchcas.inc cchero.inc cchvar.inc pmxcsg.inc pmxpln.inc \
         pmxprt.inc

chncon.o: cchcon.inc cchpar.inc cchpek.inc cchprt.inc cchtrl.inc \
         cchvar.inc cgully.inc cpart1.inc cstore.inc cstore1.inc \
         cstore2.inc cstruct.inc pmxcsg.inc pmxelm.inc pmxhil.inc \
         pmxpln.inc pmxprt.inc pmxtim.inc

chnero.o: cchpar.inc cchpek.inc cchvar.inc cpart1.inc cstore.inc \
         cstore1.inc cstore2.inc cstruct.inc pmxcrp.inc pmxcsg.inc \
         pmxelm.inc pmxhil.inc pmxpln.inc pmxprt.inc pmxtil.inc pmxtls.inc

chnpar.o: cchcon.inc cchflo.inc cchpar.inc cchpek.inc cchprt.inc \
         cchtrl.inc cchvar.inc cpart.inc cpart1.inc cpart2.inc cpart3.inc \
         cstore.inc cstore1.inc cstore2.inc cstruct.inc pmxcsg.inc \
         pmxelm.inc pmxhil.inc pmxpln.inc pmxprt.inc

chnrt.o: cchcas.inc cchcon.inc cchero.inc cchflo.inc cchpar.inc \
         cchpek.inc cchprt.inc cchsed.inc cchtrl.inc cchvar.inc cenrpa1.inc \
         cgully.inc chydrol.inc coutchn.inc cpart.inc cpart1.inc cpart2.inc \
         cpart3.inc cstore.inc cstore1.inc cstore2.inc cstruc.inc \
         cstruct.inc pmxcsg.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxprt.inc

chnvar.o: cchvar.inc pmxcsg.inc pmxpln.inc

cldfrz.o: cstruc.inc cupdate.inc cwint.inc pmxhil.inc pmxnsl.inc \
         pmxpln.inc pmxtil.inc pmxtls.inc

close.o: ccrpprm.inc cerrid.inc cflags.inc ciplot.inc cirriga.inc \
         cstruc.inc pmxcrp.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc \
         pmxtls.inc pntype.inc

conrun.o: cavepar.inc ccntour.inc cconsts.inc cdata2.inc cefflen.inc \
         chydrol.inc cparame.inc cpass.inc cpass1.inc cpass2.inc cpass3.inc \
         cpass4.inc cprams.inc cprams1.inc cprams2.inc cstruc.inc \
         pmxcrp.inc pmxelm.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxtim.inc

const.o: cdiss11.inc cdiss2.inc cdiss3.inc cstruc.inc pmxpln.inc

contin.o: cavloss.inc cchpar.inc cchvar.inc cclim.inc ccliyr.inc \
         ccntour.inc ccons.inc cconsta.inc ccontcv.inc ccover.inc \
         ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc ccrpvr2.inc \
         ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc cdecvar1.inc \
         cdiss11.inc cdist.inc cdist1.inc cdist2.inc cdist3.inc cefflen.inc \
         cends.inc cends1.inc cends2.inc cends3.inc cends4.inc cenrpa1.inc \
         cenrpa2.inc cenrpa3.inc cenrpas.inc cerrid.inc cffact.inc \
         cflags.inc cgully.inc chydrol.inc cincon.inc cinpman1.inc \
         cinpman2.inc ciplot.inc cirfur1.inc cirfur2.inc cirfurr.inc \
         cirriga.inc cke.inc cnew.inc cnew1.inc coutchn.inc cparame.inc \
         cpart.inc cpart1.inc cpart2.inc cpart3.inc cparva2.inc cperen.inc \
         cperen1.inc cprams.inc cprams1.inc cprams2.inc crinpt1.inc \
         crinpt1a.inc crinpt2.inc crinpt3.inc crinpt3a.inc crinpt5.inc \
         crinpt6.inc cseddet.inc csedld.inc cslinit.inc cslope2.inc \
         cslpopt.inc csolva2.inc cstmflg.inc cstore.inc cstore1.inc \
         cstore2.inc cstruc.inc cstruct.inc csumirr.inc csumout.inc \
         ctillge.inc cunicon.inc cupdate.inc cver.inc cwater.inc cwint.inc \
         cyield.inc pmxcrp.inc pmxcsg.inc pmxcut.inc pmxelm.inc pmxgrz.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxprt.inc pmxpts.inc \
         pmxres.inc pmxseg.inc pmxslp.inc pmxsrg.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc pxstep.inc

convrt.o: cchflo.inc cchpar.inc cchpek.inc cchprt.inc cchsed.inc \
         cchtrl.inc cchvar.inc cgully.inc cpart.inc cpart1.inc cpart2.inc \
         cpart3.inc csolva1.inc cstore.inc cstore1.inc cstore2.inc \
         cstruct.inc pmxcsg.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxprt.inc

covcal.o: ccover.inc ccrpout.inc ccrpvr1.inc ccrpvr2.inc ccrpvr5.inc \
         ccrpvr5a.inc cends4.inc cperen.inc cperen1.inc cridge.inc \
         pmxcrp.inc pmxcut.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc \
         pmxtls.inc pntype.inc

crit.o: cchcon.inc

cutgrz.o: ccrpprm.inc ccrpvr3.inc ccrpvr3a.inc cperen.inc cperen1.inc \
         crinpt1.inc crinpt1a.inc pmxcrp.inc pmxcut.inc pmxgrz.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

dblex.o: cdiss11.inc cdiss2.inc cdiss3.inc cstruc.inc cupdate.inc \
         pmxpln.inc pmxtil.inc pmxtls.inc

dcap.o: cchcon.inc cchprt.inc cchvar.inc pmxcsg.inc pmxelm.inc pmxpln.inc \
         pmxprt.inc

decomp.o: cclim.inc ccons.inc ccontcv.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc cdecvar.inc cdecvar1.inc cends4.inc cerrid.inc \
         chydrol.inc cnew.inc cperen.inc cperen1.inc cridge.inc csenes.inc \
         cstruc.inc ctillge.inc cupdate.inc cwater.inc pmxcrp.inc \
         pmxcut.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc \
         pmxtil.inc pmxtls.inc pntype.inc

depeqs.o: cends1.inc cinfco1.inc

depirr.o: cavepar.inc cdist2.inc cirdepl.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cirinfl.inc cirriga.inc cstruc.inc pmxhil.inc \
         pmxpln.inc pmxsrg.inc pxstep.inc

deplet.o: ccrpout.inc chydrol.inc cirdepl.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cirriga.inc cirspri.inc cstruc.inc cwater.inc \
         cwint.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxsrg.inc \
         pxstep.inc

depos.o: cdist1.inc cends1.inc cerdva1.inc cerdva2.inc cinfco1.inc \
         cstruc.inc pmxhil.inc pmxpln.inc

depsto.o: pmxtim.inc

detach.o: cchcas.inc cchero.inc cchvar.inc cgully.inc pmxcsg.inc \
         pmxpln.inc pmxprt.inc

disag.o: cdiss1.inc cdiss11.inc cdiss12.inc cdiss2.inc cdiss3.inc \
         chydrol.inc cirriga.inc cirspri.inc cstruc.inc cupdate.inc \
         cwint.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxtil.inc \
         pmxtls.inc

drain.o: ccdrain.inc ccons.inc cparame.inc cstruc.inc cwater.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pntype.inc

endchn.o: cchcon.inc cchpar.inc cchpek.inc cchprt.inc cchsed.inc \
         cenrpa1.inc cimacl.inc cimeos.inc coutchn.inc cpart2.inc \
         cseddet.inc cslpopt.inc cstore.inc cstore1.inc cstore2.inc \
         cstruc.inc cstruct.inc csumirr.inc pmxcsg.inc pmxelm.inc \
         pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc

enddet.o: cchcas.inc cchero.inc cchvar.inc pmxcsg.inc pmxpln.inc \
         pmxprt.inc

endout.o: ccliyr.inc cstmflg.inc cstruc.inc csumirr.inc csumout.inc \
         cunicon.inc cupdate.inc pmxhil.inc pmxpln.inc pmxtil.inc \
         pmxtls.inc

enrcmp.o: cchpar.inc cchprt.inc cchsed.inc cpart.inc cpart1.inc \
         cpart2.inc cpart3.inc pmxcsg.inc pmxelm.inc pmxpln.inc pmxprt.inc

enrich.o: cdist2.inc cends1.inc cends2.inc cenrpa1.inc cenrpa2.inc \
         chydrol.inc cinfco1.inc cinfco2.inc cirriga.inc cpart1.inc \
         cpart2.inc cpart4.inc csolva1.inc cstruc.inc ctcfrac.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxprt.inc pmxslp.inc \
         pmxtil.inc pmxtls.inc

enrprt.o: cavloss.inc ccliyr.inc ccntour.inc cenrpa1.inc cenrpa2.inc \
         cenrpa3.inc cenrpas.inc cpart.inc cpart1.inc cpart2.inc cpart3.inc \
         cstruc.inc cupdate.inc pmxcrp.inc pmxelm.inc pmxhil.inc pmxpln.inc \
         pmxprt.inc pmxtil.inc pmxtls.inc

eplane.o: pmxpln.inc

eqroot.o: ceqrot.inc

erod.o: cdetcom.inc cdist1.inc cends1.inc cerdva1.inc cerdva2.inc \
         cinfco1.inc cstruc.inc pmxhil.inc pmxpln.inc

evap.o: cangie.inc cclim.inc ccover.inc ccrpout.inc cobclim.inc \
         cstruc.inc cupdate.inc cwater.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxtil.inc pmxtls.inc

falvel.o: cconsta.inc cfall.inc

frcfac.o: ccontcv.inc ccover.inc ccrpout.inc ccrpprm.inc ccrpvr2.inc \
         ccrpvr3.inc ccrpvr3a.inc cends.inc cends1.inc cends2.inc \
         cends3.inc cends4.inc cffact.inc cfripas.inc crinpt1.inc \
         crinpt1a.inc crinpt6.inc cslinit.inc csolva1.inc csolva2.inc \
         csolvar.inc cstruc.inc ctillge.inc cupdate.inc pmxcrp.inc \
         pmxelm.inc pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc \
         pmxtil.inc pmxtls.inc pntype.inc ptilty.inc

frichn.o: cchcon.inc

frost.o: cclim.inc cstruc.inc cwater.inc cwint.inc pmxhil.inc pmxnsl.inc \
         pmxpln.inc

fslpar.o: cchcon.inc cchflo.inc cchtrl.inc pmxpln.inc

furadv.o: cdist2.inc chydrol.inc ciraflo.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cirinfl.inc cirriga.inc cprams2.inc cstruc.inc \
         pmxelm.inc pmxhil.inc pmxpln.inc pmxsrg.inc pxstep.inc

furgps.o: ccrpout.inc ccrpprm.inc cends4.inc ciraflo.inc cirfur2.inc \
         cirriga.inc cstruc.inc pmxcrp.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxres.inc pmxsrg.inc pmxtil.inc pmxtls.inc pntype.inc pxstep.inc

furlea.o: ciraflo.inc cirfur1.inc cirfur2.inc cirfurr.inc cirinfl.inc \
         pmxpln.inc pmxsrg.inc pxstep.inc

furrec.o: ciraflo.inc cirfur1.inc cirfur2.inc cirfurr.inc cirinfl.inc \
         pmxnsl.inc pmxpln.inc pmxsrg.inc pxstep.inc

furrow.o: cconsta.inc ccrpout.inc ccrpprm.inc cdist2.inc cefflen.inc \
         cends4.inc cffact.inc chydrol.inc ciraflo.inc cirfur1.inc \
         cirfur2.inc cirfurr.inc cirriga.inc cprams2.inc cslope2.inc \
         cstmflg.inc cstruc.inc csumirr.inc pmxcrp.inc pmxelm.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxsrg.inc pmxtil.inc \
         pmxtls.inc pntype.inc pxstep.inc

furrun.o: cdist2.inc cefflen.inc chydrol.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cirriga.inc cstruc.inc pmxelm.inc pmxhil.inc \
         pmxpln.inc pmxsrg.inc pxstep.inc

gcurve.o: cclim.inc crinpt2.inc pmxcrp.inc pmxhil.inc pmxpln.inc \
         pntype.inc

gdmax.o: ccrpprm.inc cobclim.inc pmxcrp.inc pmxpln.inc pmxres.inc \
         pmxtil.inc pmxtls.inc pntype.inc

grna.o: cavepar.inc cdata.inc cdata1.inc cdata2.inc cdata3.inc cdata4.inc \
         cdiss1.inc cdiss11.inc cdiss12.inc chydrol.inc cparame.inc \
         cstruc.inc cwater.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxpnd.inc pmxtim.inc

grow.o: cclim.inc ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc \
         ccrpvr1.inc ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc cends4.inc \
         cgcovr.inc cperen.inc cperen1.inc cridge.inc crout.inc csenes.inc \
         cupdate.inc cwater.inc pmxcrp.inc pmxcut.inc pmxhil.inc pmxnsl.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

growop.o: ccrpgro.inc ccrpprm.inc ccrpvr3.inc ccrpvr3a.inc cobclim.inc \
         pmxcrp.inc pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

hdepth.o: cconsts.inc

hdrive.o: cdata3.inc chydrol.inc cintgrl.inc cpass2.inc cpass3.inc \
         cpass4.inc pmxelm.inc pmxpln.inc pmxtim.inc

hrtmp.o: cclim.inc pmxhil.inc pmxpln.inc

hydchn.o: cchcon.inc

hydout.o: ccliyr.inc cefflen.inc chydrol.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cirriga.inc cirspri.inc cstruc.inc csumirr.inc \
         cupdate.inc pmxelm.inc pmxhil.inc pmxpln.inc pmxsrg.inc pmxtil.inc \
         pmxtls.inc pxstep.inc

idat.o: ccover.inc ccrpout.inc ccrpvr1.inc ccrpvr2.inc cdata1.inc \
         cdata3.inc cdata4.inc cdiss1.inc cdiss11.inc cdiss12.inc cke.inc \
         crout.inc cstruc.inc cwater.inc pmxcrp.inc pmxhil.inc pmxnsl.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtim.inc pmxtls.inc pntype.inc

impday.o: cflags.inc cimday.inc cimeos.inc cimitf.inc cimmon.inc \
         cimpnd.inc cimsed.inc cimyrs.inc pmximp.inc

impeo.o: cangie.inc cclim.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxtil.inc \
         pmxtls.inc

impeos.o: cflags.inc cimday.inc cimeos.inc cimitf.inc cimpnd.inc \
         cimsed.inc pmximp.inc

impflo.o: cimflg.inc cimitf.inc cimpnd.inc cimqot.inc cimsed.inc \
         pmximp.inc

imphnw.o: cimitf.inc cimpnd.inc pmximp.inc

impint.o: cflags.inc cimacl.inc cimcv1.inc cimcv2.inc cimday.inc \
         cimds.inc cimeos.inc cimff.inc cimflg.inc cimitf.inc cimmon.inc \
         cimpnd.inc cimpr.inc cimqot.inc cimreg.inc cimrf.inc cimrou.inc \
         cimsed.inc cimsre.inc cimyrs.inc pmximp.inc

impmai.o: cflags.inc cimacl.inc cimcln.inc cimdate.inc cimday.inc \
         cimeos.inc cimflg.inc cimitf.inc cimmon.inc cimpnd.inc cimqot.inc \
         cimsed.inc cimyrs.inc cstruct.inc pmxelm.inc pmximp.inc pmxpln.inc

impmon.o: cflags.inc cimday.inc cimitf.inc cimmon.inc cimpnd.inc \
         cimsed.inc pmximp.inc

imppro.o: cimrou.inc

impreg.o: cimcln.inc cimcv1.inc cimcv2.inc cimds.inc cimff.inc cimflg.inc \
         cimitf.inc cimpnd.inc cimpr.inc cimqot.inc cimreg.inc cimrf.inc \
         cimsed.inc cimsre.inc pmximp.inc

impyr.o: cflags.inc cimday.inc cimitf.inc cimpnd.inc cimsed.inc \
         cimyrs.inc pmximp.inc

infile.o: ccdrain.inc cclig.inc cclim.inc ccliyr.inc ccntour.inc \
         ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr3a.inc ccrpvr5a.inc cdat.inc cdecvar1.inc \
         cends4.inc cerrid.inc cflags.inc cimpnd.inc cinpman1.inc \
         cinpman2.inc cinpop.inc cinpsur.inc cirriga.inc cke.inc cnew.inc \
         cnew1.inc cobclim.inc cparame.inc cperen1.inc crinpt1a.inc \
         crinpt2.inc crinpt3a.inc crinpt5.inc crinpt6.inc cslinit.inc \
         cstruc.inc ctemp.inc ctillge.inc cupdate.inc cver.inc cwint.inc \
         cwshed.inc pmxcrp.inc pmxelm.inc pmxhil.inc pmximp.inc pmxnsl.inc \
         pmxpln.inc pmxpnd.inc pmxprt.inc pmxres.inc pmxtil.inc pmxtls.inc \
         pntype.inc

infpar.o: cavepar.inc cclim.inc ccons.inc ccover.inc ccrpout.inc \
         ccrpvr1.inc cgcovr.inc chydrol.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cke.inc cparame.inc cperen1.inc cstmflg.inc cstruc.inc \
         ctemp.inc ctillge.inc cwater.inc pmxcrp.inc pmxelm.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc pmxsrg.inc pmxtil.inc \
         pmxtls.inc pntype.inc ptilty.inc pxstep.inc

inidat.o: cavloss.inc cbgout.inc ccdrain.inc cchcas.inc cchpar.inc \
         cchpek.inc cchprt.inc cchsed.inc cchtrl.inc cchvar.inc cclim.inc \
         ccntour.inc cconsta.inc ccontcv.inc ccover.inc ccrpgro.inc \
         ccrpout.inc ccrpprm.inc ccrpvr1.inc ccrpvr2.inc ccrpvr3.inc \
         ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc cdat.inc cdata.inc \
         cdata1.inc cdata2.inc cdata3.inc cdata4.inc cdecvar.inc \
         cdecvar1.inc cdetcom.inc cdiss2.inc cefflen.inc cends.inc \
         cends1.inc cends2.inc cends3.inc cends4.inc cenrpa1.inc \
         cenrpa2.inc cenrpa3.inc cenrpas.inc ceqrot.inc cerrid.inc \
         cfall.inc cffact.inc cflags.inc cgully.inc chydrol.inc cifpar.inc \
         cimpnd.inc cincon.inc ciplot.inc ciravlo.inc cirdepl.inc \
         cirfur1.inc cirriga.inc cirspri.inc cke.inc ckrcon.inc coutchn.inc \
         cpart.inc cpart1.inc cpart2.inc cpart3.inc cpass.inc cpass1.inc \
         cpass2.inc cpass3.inc cpass4.inc cperen.inc cperen1.inc \
         cprams2.inc cpsis1.inc cptgrow.inc cridge.inc crinpt1.inc \
         crinpt1a.inc crinpt2.inc crinpt3.inc crinpt3a.inc crinpt5.inc \
         crinpt6.inc crndm.inc crout.inc cseddet.inc csedld.inc csenes.inc \
         cslinit.inc cslope.inc cslope1.inc cslope2.inc cslope3.inc \
         cslpopt.inc cstmgt.inc cstore.inc cstore1.inc cstore2.inc \
         cstruc.inc cstruct.inc csumirr.inc csumout.inc ctemp.inc \
         ctillge.inc cupdate.inc cver.inc cwater.inc cwint.inc cyield.inc \
         pmxcrp.inc pmxcsg.inc pmxcut.inc pmxelm.inc pmxgrz.inc pmxhil.inc \
         pmximp.inc pmxnsl.inc pmxpln.inc pmxprt.inc pmxpts.inc pmxres.inc \
         pmxseg.inc pmxslp.inc pmxsrg.inc pmxtil.inc pmxtim.inc pmxtls.inc \
         pntype.inc ptilty.inc pxstep.inc

init1.o: cclim.inc ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc \
         ccrpvr1.inc ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc \
         ccrpvr5a.inc cends4.inc cgcovr.inc cperen.inc cperen1.inc \
         cridge.inc cstruc.inc cwater.inc cwint.inc pmxcrp.inc pmxcut.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc

initd.o: ccover.inc cdecvar.inc cdecvar1.inc cobclim.inc cwater.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtls.inc pntype.inc

initgr.o: ccover.inc ccrpout.inc ccrpprm.inc ccrpvr2.inc ccrpvr3.inc \
         ccrpvr3a.inc cperen.inc cperen1.inc cstruc.inc pmxcrp.inc \
         pmxcut.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc \
         pmxtls.inc pntype.inc

input.o: ccdrain.inc cchpar.inc cchtrl.inc ccntour.inc ccover.inc \
         ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc ccrpvr2.inc \
         ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc cdecvar.inc \
         cdecvar1.inc cdist.inc cdist1.inc cdist2.inc cdist3.inc cends4.inc \
         cerrid.inc cflags.inc cinpop.inc cinpsur.inc cirriga.inc cnew.inc \
         cnew1.inc cparame.inc cparva1.inc cparva2.inc cparval.inc \
         cperen.inc cperen1.inc cridge.inc crinpt1.inc crinpt1a.inc \
         crinpt2.inc crinpt3.inc crinpt3a.inc crinpt5.inc crinpt6.inc \
         cslinit.inc cslope.inc cslope1.inc cslope2.inc cslope3.inc \
         cslpopt.inc csolva1.inc csolva2.inc csolvar.inc cstruc.inc \
         cstruct.inc ctemp.inc ctillge.inc cupdate.inc cwater.inc cwint.inc \
         pmxcrp.inc pmxcsg.inc pmxcut.inc pmxelm.inc pmxgrz.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc pmxslp.inc pmxtil.inc \
         pmxtls.inc pntype.inc ptilty.inc

irflow.o: ciraflo.inc

irinpt.o: ccliyr.inc ccntour.inc cdat.inc cirdepl.inc cirfixd.inc \
         cirfur1.inc cirfur2.inc cirfurr.inc cirriga.inc cirspri.inc \
         cstruc.inc cstruct.inc pmxcrp.inc pmxelm.inc pmxhil.inc pmxpln.inc \
         pmxsrg.inc pxstep.inc

irprnt.o: cavepar.inc ccons.inc cconsta.inc ccover.inc cdist2.inc \
         cffact.inc cirfur1.inc cirfur2.inc cirfurr.inc cirinfl.inc \
         cirriga.inc cparame.inc cslope2.inc cstruc.inc cwater.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxsrg.inc pmxtls.inc \
         pxstep.inc

irrig.o: cavloss.inc cdat.inc cdata1.inc cdata3.inc cdiss11.inc \
         cdiss3.inc cdist2.inc chydrol.inc cirdepl.inc cirfixd.inc \
         cirfur1.inc cirfur2.inc cirfurr.inc cirriga.inc cirspri.inc \
         cparame.inc cstmflg.inc cstruc.inc csumirr.inc csumout.inc \
         cupdate.inc pmxcrp.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxpnd.inc pmxsrg.inc pmxtil.inc pmxtim.inc pmxtls.inc pxstep.inc

irs.o: cavepar.inc ccntour.inc cconsts.inc ccrpout.inc cdata1.inc \
         cdata2.inc cdata3.inc cdiss3.inc cdist2.inc cefflen.inc \
         chydrol.inc cirriga.inc cirspri.inc cparame.inc cpass1.inc \
         cpass2.inc cpass3.inc cprams.inc cprams1.inc cprams2.inc \
         cslope2.inc cslpopt.inc cstmflg.inc cstruc.inc csumirr.inc \
         pmxcrp.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc \
         pmxslp.inc pmxtim.inc

kostia.o: cavepar.inc ccrpout.inc cdist2.inc ciraflo.inc cirfur2.inc \
         cirinfl.inc cirriga.inc cparame.inc cstruc.inc pmxcrp.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc pmxsrg.inc \
         pmxtil.inc pmxtls.inc pntype.inc pxstep.inc

main.o: cerrid.inc cimpnd.inc cstruc.inc cunicon.inc cver.inc cwshed.inc \
         pmxhil.inc pmximp.inc pntype.inc

melt.o: cclim.inc ccover.inc ccrpout.inc cdecvar.inc cdecvar1.inc \
         crinpt6.inc cstruc.inc cupdate.inc cwint.inc pmxhil.inc pmxnsl.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

mltfdp.o: cstruc.inc cupdate.inc cwint.inc pmxhil.inc pmxnsl.inc \
         pmxpln.inc pmxtil.inc pmxtls.inc

monchn.o: cchcon.inc cchpar.inc cchpek.inc cchprt.inc cchsed.inc \
         cdist2.inc cenrpa1.inc cimeos.inc cimmon.inc coutchn.inc \
         cpart2.inc cseddet.inc cslpopt.inc cstore.inc cstore1.inc \
         cstore2.inc cstruc.inc cstruct.inc csumirr.inc pmxcsg.inc \
         pmxelm.inc pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc

monout.o: ccliyr.inc ciravlo.inc cstruc.inc csumirr.inc csumout.inc \
         cupdate.inc pmxhil.inc pmxpln.inc pmxtil.inc pmxtls.inc

newtil.o: cupdate.inc pmxpln.inc pmxtil.inc pmxtls.inc

nowup.o: cupdate.inc pmxpln.inc pmxtil.inc pmxtls.inc

open.o: cerrid.inc cstruc.inc pntype.inc

outfil.o: cavloss.inc cchpar.inc cerrid.inc cflags.inc cimpnd.inc \
         ciplot.inc cprams.inc cprams1.inc cprams2.inc cstruc.inc \
         cunicon.inc pmxcsg.inc pmxhil.inc pmximp.inc pmxnsl.inc pmxpln.inc \
         pntype.inc

param.o: ccntour.inc cconsta.inc ccover.inc ccrpout.inc cdist.inc \
         cdist1.inc cdist2.inc cdist3.inc cefflen.inc cends.inc cends1.inc \
         cends2.inc cends3.inc cends4.inc cffact.inc chydrol.inc \
         cinfco1.inc cinfco2.inc cinfcof.inc cirriga.inc cirspri.inc \
         cpart.inc cpart1.inc cpart2.inc cpart3.inc cpart4.inc cparva1.inc \
         cparva2.inc cparval.inc crinpt3.inc crinpt3a.inc crinpt5.inc \
         cslope.inc cslope1.inc cslope2.inc cslope3.inc csolva1.inc \
         csolva2.inc csolvar.inc cstruc.inc cwint.inc pmxcrp.inc pmxelm.inc \
         pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxprt.inc pmxslp.inc \
         pmxtls.inc pntype.inc

patrib.o: ccover.inc ccrpout.inc ccrpvr1.inc ccrpvr2.inc ccrpvr3.inc \
         ccrpvr3a.inc crinpt1.inc crinpt1a.inc crinpt3.inc crinpt3a.inc \
         crinpt5.inc crinpt6.inc pmxcrp.inc pmxgrz.inc pmxnsl.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

perc.o: cstruc.inc cwater.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxtil.inc \
         pmxtls.inc

phi.o: cintgrl.inc cpass1.inc cpass3.inc cprams1.inc pmxhil.inc \
         pmxpln.inc pmxtim.inc

print.o: cavepar.inc cclim.inc ccons.inc ccover.inc cdata.inc cdata1.inc \
         cdata2.inc cdata3.inc cdata4.inc cdiss1.inc cdiss11.inc \
         cdiss12.inc cdiss3.inc cdist.inc cdist1.inc cdist2.inc cdist3.inc \
         cefflen.inc chydrol.inc cirriga.inc cirspri.inc cparame.inc \
         cpass.inc cpass1.inc cpass2.inc cpass3.inc cpass4.inc cprams.inc \
         cprams1.inc cprams2.inc cslope.inc cslope1.inc cslope2.inc \
         cslope3.inc cstruc.inc cupdate.inc cwater.inc cwint.inc pmxelm.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxslp.inc pmxtil.inc \
         pmxtim.inc pmxtls.inc

profil.o: cdist.inc cdist1.inc cdist2.inc cdist3.inc cslope.inc \
         cslope1.inc cslope2.inc cslope3.inc pmxnsl.inc pmxpln.inc \
         pmxslp.inc

prtcmp.o: cpart.inc cpart1.inc cpart2.inc cpart3.inc csolva1.inc \
         csolva2.inc csolvar.inc cstruc.inc pmxelm.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxprt.inc

psiinv.o: cprams1.inc cpsis1.inc pmxpln.inc pmxtim.inc

psis.o: cconsts.inc cintgrl.inc cpass1.inc cpass3.inc cprams1.inc \
         cpsis1.inc pmxpln.inc pmxtim.inc

ptgra.o: ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc \
         cdecvar1.inc cflags.inc cgcovr.inc cperen.inc cperen1.inc \
         crout.inc csenes.inc cstruc.inc cupdate.inc pmxcrp.inc pmxcut.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc

ptgrp.o: cclim.inc ccover.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc \
         cdecvar.inc cdecvar1.inc cflags.inc cnew1.inc cperen.inc \
         cperen1.inc cptgrow.inc crinpt1.inc crinpt1a.inc crout.inc \
         cstruc.inc cupdate.inc cyield.inc pmxcrp.inc pmxcut.inc pmxgrz.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc

purk.o: cstruc.inc cwater.inc pmxhil.inc pmxnsl.inc pmxpln.inc

qinf.o: ctemp.inc pmxnsl.inc pmxpln.inc

rand.o: crndm.inc

range.o: cclim.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc \
         chydrol.inc crinpt1.inc crinpt1a.inc crinpt2.inc crinpt3.inc \
         crinpt3a.inc crinpt4.inc crinpt6.inc crout.inc cstmflg.inc \
         cstruc.inc cupdate.inc pmxcrp.inc pmxelm.inc pmxgrz.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc

rburn.o: cclim.inc ccrpvr1.inc ccrpvr2.inc chydrol.inc crinpt1.inc \
         crinpt1a.inc crinpt3.inc crinpt3a.inc crinpt4.inc crinpt5.inc \
         crout.inc cstruc.inc pmxcrp.inc pmxelm.inc pmxgrz.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

rdat.o: ccntour.inc cconsta.inc cdist2.inc cffact.inc cintgrl.inc \
         cpass1.inc cpass2.inc cpass3.inc cprams.inc cprams1.inc \
         cprams2.inc cslope2.inc cstruc.inc pmxcrp.inc pmxhil.inc \
         pmxpln.inc pmxslp.inc pmxtim.inc

reid.o: cdata1.inc cdiss11.inc pmxpln.inc pmxtim.inc

res_dp.o: ccrpprm.inc ccrpvr1.inc ccrpvr5.inc ccrpvr5a.inc pmxcrp.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

resup.o: ccontcv.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr5.inc ccrpvr5a.inc cdecvar.inc cdecvar1.inc \
         cflags.inc cperen.inc cperen1.inc cptgrow.inc cridge.inc \
         cstruc.inc ctillge.inc cupdate.inc cyield.inc pmxcrp.inc \
         pmxcut.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc

rgraze.o: ccrpvr1.inc ccrpvr2.inc crinpt1.inc crinpt1a.inc crinpt2.inc \
         crinpt4.inc crinpt6.inc crout.inc cstruc.inc cupdate.inc \
         pmxcrp.inc pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc \
         pmxtil.inc pmxtls.inc pntype.inc

rherb.o: cclim.inc ccrpvr1.inc chydrol.inc crinpt1.inc crinpt1a.inc \
         crinpt4.inc crinpt6.inc crout.inc cstruc.inc cupdate.inc \
         pmxcrp.inc pmxelm.inc pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxres.inc pmxtil.inc pmxtls.inc pntype.inc

rngint.o: ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc cends.inc cends1.inc \
         cends2.inc cends3.inc cends4.inc crinpt1.inc crinpt1a.inc \
         crinpt2.inc crinpt3.inc crinpt3a.inc crinpt4.inc crinpt5.inc \
         crinpt6.inc crout.inc cstruc.inc cwater.inc cwint.inc pmxcrp.inc \
         pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc pmxtil.inc \
         pmxtls.inc pntype.inc ptilty.inc

rochek.o: cdiss11.inc cdiss3.inc cdist2.inc cefflen.inc chydrol.inc \
         crozero.inc cstruc.inc pmxelm.inc pmxhil.inc pmxpln.inc

route.o: cends1.inc cends2.inc cends3.inc cenrpa1.inc cerdva1.inc \
         cinfco1.inc cinfco2.inc cirriga.inc cpart1.inc cparva1.inc \
         cslope1.inc cstruc.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxprt.inc pmxslp.inc pmxtls.inc

rtpart.o: ccrpout.inc pmxnsl.inc pmxpln.inc

runge.o: cdetcom.inc cends1.inc

runout.o: cchpek.inc cflags.inc chydrol.inc cstore.inc cstore1.inc \
         cstore2.inc cstruc.inc cstruct.inc cupdate.inc cwint.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxprt.inc pmxtil.inc \
         pmxtls.inc

scon.o: ccons.inc ccover.inc ccrpout.inc ccrpprm.inc cke.inc ckrcon.inc \
         cparame.inc cparva1.inc cparva2.inc cparval.inc crinpt1a.inc \
         crinpt6.inc crout.inc cslinit.inc csolva1.inc csolva2.inc \
         csolvar.inc cstruc.inc ctillge.inc cwater.inc pmxcrp.inc \
         pmxelm.inc pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc \
         pmxres.inc pmxtil.inc pmxtls.inc pntype.inc ptilty.inc

sedia.o: cconsta.inc cfall.inc

sedist.o: cdist.inc cdist1.inc cdist2.inc cdist3.inc csedld.inc \
         cslope.inc cslope1.inc cslope2.inc cslope3.inc cstruc.inc \
         pmxhil.inc pmxpln.inc pmxpts.inc pmxseg.inc pmxslp.inc

sedmax.o: csedld.inc pmxpln.inc pmxpts.inc pmxseg.inc

sedout.o: cavloss.inc ccliyr.inc ccntour.inc ccover.inc ccrpout.inc \
         ccrpvr1.inc ccrpvr2.inc cdist.inc cdist1.inc cdist2.inc cdist3.inc \
         cefflen.inc cends.inc cends1.inc cends2.inc cends3.inc cends4.inc \
         cenrpa1.inc cenrpa2.inc cenrpa3.inc cenrpas.inc chydrol.inc \
         ciravlo.inc cirriga.inc coutchn.inc cparame.inc cpart1.inc \
         cparva1.inc cparva2.inc cparval.inc cseddet.inc csedld.inc \
         cslope.inc cslope1.inc cslope2.inc cslope3.inc cslpopt.inc \
         csolva1.inc csolva2.inc csolvar.inc cstore1.inc cstruc.inc \
         cstruct.inc csumirr.inc cunicon.inc cupdate.inc cwater.inc \
         pmxcrp.inc pmxcsg.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxpnd.inc pmxprt.inc pmxpts.inc pmxres.inc pmxseg.inc pmxslp.inc \
         pmxtil.inc pmxtls.inc pntype.inc ptilty.inc

sedseg.o: cavloss.inc ccntour.inc cseddet.inc csedld.inc cslpopt.inc \
         cstmflg.inc cstruc.inc csumout.inc cunicon.inc pmxcrp.inc \
         pmxelm.inc pmxhil.inc pmxpln.inc pmxpts.inc pmxseg.inc

sedsta.o: csedld.inc pmxpln.inc pmxpts.inc pmxseg.inc

set_hc.o: cparame.inc cstruc.inc cwater.inc cwint.inc pmxcrp.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxtil.inc pmxtls.inc

shears.o: cclim.inc cconsta.inc cends.inc cends1.inc cends2.inc \
         cends3.inc cends4.inc cffact.inc cslpopt.inc csolva1.inc \
         csolva2.inc csolvar.inc cstruc.inc cupdate.inc pmxelm.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxtil.inc pmxtls.inc

sint.o: cintgrl.inc cpass1.inc cpass2.inc cpass3.inc cprams1.inc \
         pmxpln.inc pmxtim.inc

sintdp.o: cintgrl.inc cpass1.inc cpass2.inc cpass3.inc cprams1.inc \
         pmxpln.inc pmxtim.inc

sloss.o: cavloss.inc ccntour.inc cconsta.inc ccover.inc ccrpout.inc \
         cdist.inc cdist1.inc cdist2.inc cdist3.inc cefflen.inc cends.inc \
         cends1.inc cends2.inc cends3.inc cends4.inc cenrpa1.inc \
         cenrpa2.inc cenrpa3.inc cenrpas.inc cerdva1.inc cerdva2.inc \
         cerdval.inc chydrol.inc ciravlo.inc cirriga.inc cparame.inc \
         cpart.inc cpart1.inc cpart2.inc cpart3.inc cparva1.inc cparva2.inc \
         cparval.inc cseddet.inc cstore.inc cstore1.inc cstore2.inc \
         cstruc.inc cupdate.inc cwater.inc pmxcrp.inc pmxelm.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxpnd.inc pmxprt.inc pmxpts.inc pmxseg.inc \
         pmxtil.inc pmxtls.inc

sndrft.o: cclim.inc ccover.inc ccrpout.inc ccrpvr1.inc ccrpvr5.inc \
         ccrpvr5a.inc cdecvar.inc cdecvar1.inc cdist.inc cdist1.inc \
         cdist2.inc cdist3.inc cperen.inc cperen1.inc crinpt3.inc \
         crinpt3a.inc cslope2.inc cslpopt.inc cstruc.inc cwint.inc \
         pmxcrp.inc pmxcut.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc \
         pmxslp.inc pmxtil.inc pmxtls.inc pntype.inc ptilty.inc

snowd.o: cclim.inc cwint.inc pmxhil.inc pmxnsl.inc pmxpln.inc

soil.o: cclim.inc ccons.inc ccontcv.inc ccover.inc ccrpout.inc \
         ccrpprm.inc ccrpvr1.inc ccrpvr3.inc ccrpvr3a.inc cends4.inc \
         cflags.inc chydrol.inc cincon.inc cirriga.inc cke.inc ckrcon.inc \
         cparame.inc cridge.inc crinpt1a.inc crinpt3.inc crinpt3a.inc \
         crinpt5.inc crinpt6.inc crout.inc cslinit.inc cslope2.inc \
         csolva1.inc csolva2.inc csolvar.inc cstruc.inc ctemp.inc \
         ctillge.inc cupdate.inc cwater.inc cwint.inc pmxcrp.inc pmxelm.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc pmxtil.inc \
         pmxtls.inc pntype.inc

spread.o: pmxcsg.inc pmxpln.inc

stmget.o: cclig.inc cclim.inc cdiss1.inc cdiss11.inc cdiss12.inc \
         cdiss3.inc chydrol.inc cstmflg.inc cstmgt.inc cstruc.inc \
         cupdate.inc pmxelm.inc pmxhil.inc pmxpln.inc pmxtil.inc pmxtls.inc

strout.o: cchcon.inc cchflo.inc cchsed.inc coutchn.inc pmxcsg.inc \
         pmxelm.inc pmxprt.inc

sumfrc.o: cpart1.inc pmxelm.inc pmxhil.inc pmxpln.inc pmxprt.inc

sumrnf.o: cavloss.inc chydrol.inc cstmflg.inc cstruc.inc csumout.inc \
         pmxelm.inc pmxhil.inc pmxpln.inc

sumrun.o: cavloss.inc cclim.inc cefflen.inc chydrol.inc cirriga.inc \
         cslpopt.inc cstmflg.inc cstruc.inc csumirr.inc csumout.inc \
         pmxelm.inc pmxhil.inc pmxpln.inc pmxprt.inc

sunmap.o: cangie.inc cclim.inc pmxhil.inc pmxpln.inc

swu.o: cclim.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc cstruc.inc \
         cwater.inc pmxcrp.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxres.inc \
         pmxtil.inc pmxtls.inc pntype.inc ptilty.inc

tfail.o: ccntour.inc cconsta.inc cdist.inc cdist1.inc cdist2.inc \
         cdist3.inc cends.inc cends1.inc cends2.inc cends3.inc cends4.inc \
         cffact.inc chydrol.inc cslope.inc cslope1.inc cslope2.inc \
         cslope3.inc cstruc.inc pmxcrp.inc pmxelm.inc pmxhil.inc pmxpln.inc \
         pmxslp.inc

tfwmlt.o: cstruc.inc cwint.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxtil.inc pmxtls.inc

tilage.o: ccdrain.inc ccntour.inc ccontcv.inc ccover.inc ccrpout.inc \
         ccrpprm.inc ccrpvr5.inc ccrpvr5a.inc cinpman1.inc cinpman2.inc \
         cinpop.inc cnew.inc cparame.inc cperen.inc cperen1.inc crinpt1.inc \
         crinpt1a.inc crinpt3.inc crinpt3a.inc crinpt4.inc csolva1.inc \
         csolva2.inc csolvar.inc cstmflg.inc cstruc.inc ctemp.inc \
         ctillge.inc cwater.inc pmxcrp.inc pmxcut.inc pmxelm.inc pmxgrz.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc pmxtil.inc \
         pmxtls.inc pntype.inc

tmpadj.o: cclim.inc ccover.inc ccrpout.inc cstruc.inc cwater.inc \
         cwint.inc pmxcrp.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxtil.inc \
         pmxtls.inc

trncap.o: cchcon.inc cchprt.inc pmxelm.inc pmxprt.inc

trnlos.o: cchpar.inc cchpek.inc cdiss3.inc cefflen.inc chydrol.inc \
         cstore.inc cstore1.inc cstore2.inc cstruc.inc cstruct.inc \
         pmxcsg.inc pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc \
         pmxprt.inc

watbal.o: cangie.inc ccdrain.inc cclim.inc ccliyr.inc ccons.inc \
         ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc cflags.inc chydrol.inc cirfur1.inc cirfur2.inc \
         cirfurr.inc cirriga.inc cparame.inc cperen.inc cperen1.inc \
         cstore.inc cstore1.inc cstore2.inc cstruc.inc cstruct.inc \
         ctillge.inc cupdate.inc cwater.inc cwint.inc pmxcrp.inc pmxcut.inc \
         pmxelm.inc pmxgrz.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc \
         pmxprt.inc pmxres.inc pmxsrg.inc pmxtil.inc pmxtls.inc pntype.inc \
         pxstep.inc

winit.o: cclim.inc ccons.inc ccover.inc ccrpout.inc ccrpvr1.inc \
         ccrpvr5.inc ccrpvr5a.inc chydrol.inc cparame.inc cslope2.inc \
         cstruc.inc ctillge.inc cupdate.inc cwater.inc cwint.inc pmxcrp.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc \
         pmxslp.inc pmxtil.inc pmxtls.inc pntype.inc

winter.o: cangie.inc cclim.inc ccliyr.inc ccons.inc ccover.inc \
         ccrpout.inc ccrpprm.inc ccrpvr1.inc ccrpvr5.inc ccrpvr5a.inc \
         cdiss11.inc chydrol.inc cparame.inc cslope2.inc cstmflg.inc \
         cstruc.inc ctillge.inc cupdate.inc cwater.inc cwint.inc pmxcrp.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxres.inc \
         pmxslp.inc pmxtil.inc pmxtls.inc pntype.inc

winthd.o: cver.inc pmxpln.inc

wmlt.o: cstruc.inc cupdate.inc cwint.inc pmxhil.inc pmxnsl.inc pmxpln.inc \
         pmxtil.inc pmxtls.inc

wshcqi.o: cchpek.inc cdiss11.inc cdist2.inc cefflen.inc cirspri.inc \
         cstore.inc cstore1.inc cstore2.inc cstruc.inc cstruct.inc \
         pmxcsg.inc pmxelm.inc pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc

wshdrv.o: cavloss.inc cchpar.inc cchpek.inc cchvar.inc cclim.inc \
         ccliyr.inc ccntour.inc ccons.inc cconsta.inc ccontcv.inc \
         ccover.inc ccrpgro.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc ccrpvr3.inc ccrpvr3a.inc ccrpvr5.inc ccrpvr5a.inc \
         cdecvar1.inc cdiss11.inc cdist.inc cdist1.inc cdist2.inc \
         cdist3.inc cefflen.inc cends.inc cends1.inc cends2.inc cends3.inc \
         cends4.inc cenrpa1.inc cenrpa2.inc cenrpa3.inc cenrpas.inc \
         cerrid.inc cffact.inc cflags.inc cgully.inc chydrol.inc \
         cimdate.inc cimpnd.inc cincon.inc cinpman1.inc cinpman2.inc \
         ciplot.inc cirfur1.inc cirfur2.inc cirfurr.inc cirriga.inc cke.inc \
         cnew.inc cnew1.inc coutchn.inc cparame.inc cpart.inc cpart1.inc \
         cpart2.inc cpart3.inc cparva2.inc cperen.inc cperen1.inc \
         cprams.inc cprams1.inc cprams2.inc crinpt1.inc crinpt1a.inc \
         crinpt2.inc crinpt3.inc crinpt3a.inc crinpt5.inc crinpt6.inc \
         cseddet.inc csedld.inc cslinit.inc cslope2.inc cslpopt.inc \
         csolva2.inc cstmflg.inc cstore.inc cstore1.inc cstore2.inc \
         cstruc.inc cstruct.inc csumirr.inc csumout.inc ctillge.inc \
         cupdate.inc cver.inc cwater.inc cwint.inc cwshed.inc cyield.inc \
         pmxcrp.inc pmxcsg.inc pmxcut.inc pmxelm.inc pmxgrz.inc pmxhil.inc \
         pmximp.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxprt.inc pmxpts.inc \
         pmxres.inc pmxseg.inc pmxslp.inc pmxsrg.inc pmxtil.inc pmxtls.inc \
         pntype.inc ptilty.inc pxstep.inc

wshimp.o: cchprt.inc cenrpa1.inc cflags.inc chydrol.inc cimday.inc \
         cimpnd.inc coutchn.inc cpart3.inc cstore.inc cstore1.inc \
         cstore2.inc cstruct.inc cwater.inc pmxcsg.inc pmxelm.inc \
         pmxhil.inc pmximp.inc pmxnsl.inc pmxpln.inc pmxprt.inc

wshini.o: cchpar.inc cchpek.inc cchtmp.inc cchvar.inc cimpnd.inc \
         cpart.inc cpart1.inc cpart2.inc cpart3.inc cslope2.inc cslpopt.inc \
         csolva1.inc cstore.inc cstore1.inc cstore2.inc cstruc.inc \
         cstruct.inc cwshed.inc pmxcsg.inc pmxelm.inc pmxhil.inc pmximp.inc \
         pmxnsl.inc pmxpln.inc pmxprt.inc

wshinp.o: cchpar.inc cchpek.inc cchtrl.inc cchvar.inc cdist2.inc \
         cimpnd.inc cparame.inc cslope1.inc cslpopt.inc csolva1.inc \
         cstruc.inc cstruct.inc pmxcsg.inc pmxelm.inc pmxhil.inc pmximp.inc \
         pmxnsl.inc pmxpln.inc pmxpnd.inc pmxprt.inc pmxslp.inc

wshiqi.o: cchpek.inc cflags.inc chydrol.inc cimpnd.inc cstore.inc \
         cstore1.inc cstore2.inc cstruct.inc pmxcsg.inc pmxelm.inc \
         pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc

wshirs.o: cavepar.inc ccntour.inc cconsts.inc ccrpout.inc cdata1.inc \
         cdata2.inc cdata3.inc cdiss3.inc cdist2.inc cefflen.inc cflags.inc \
         chydrol.inc cirriga.inc cirspri.inc cparame.inc cpass1.inc \
         cpass2.inc cpass3.inc cprams.inc cprams1.inc cprams2.inc \
         cslope2.inc cslpopt.inc cstmflg.inc cstore.inc cstore1.inc \
         cstore2.inc cstruc.inc cstruct.inc csumirr.inc pmxcrp.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxprt.inc \
         pmxslp.inc pmxtim.inc

wshout.o: cavepar.inc cavloss.inc ccdrain.inc cclim.inc ccliyr.inc \
         ccons.inc ccover.inc ccrpout.inc ccrpprm.inc ccrpvr1.inc \
         ccrpvr2.inc cefflen.inc cends4.inc cenrpa2.inc cffact.inc \
         cflags.inc chydrol.inc cirfur1.inc cirfur2.inc cirfurr.inc \
         cirriga.inc cparame.inc cparva2.inc cseddet.inc cslpopt.inc \
         csolva2.inc cstore.inc cstore1.inc cstore2.inc cstruc.inc \
         cstruct.inc cupdate.inc cwater.inc cwint.inc pmxcrp.inc pmxelm.inc \
         pmxhil.inc pmxnsl.inc pmxpln.inc pmxpnd.inc pmxprt.inc pmxres.inc \
         pmxsrg.inc pmxtil.inc pmxtls.inc pntype.inc pxstep.inc

wshpas.o: ccliyr.inc cdata1.inc cdata3.inc cdiss11.inc cdist.inc \
         cdist1.inc cdist2.inc cdist3.inc cefflen.inc cenrpa1.inc \
         cenrpa2.inc cenrpa3.inc cenrpas.inc chydrol.inc cpart.inc \
         cpart1.inc cpart2.inc cpart3.inc cseddet.inc csedld.inc cslope.inc \
         cslope1.inc cslope2.inc cslope3.inc cslpopt.inc cstore.inc \
         cstore1.inc cstore2.inc cstruc.inc cver.inc cwater.inc cwshed.inc \
         pmxelm.inc pmxhil.inc pmxnsl.inc pmxpln.inc pmxprt.inc pmxpts.inc \
         pmxseg.inc pmxslp.inc pmxtim.inc

wshpek.o: cchpek.inc cchtmp.inc cdata1.inc cdata3.inc cenrpa1.inc \
         cflags.inc chydrol.inc cimpnd.inc coutchn.inc cpart1.inc \
         cstore.inc cstore1.inc cstore2.inc cstruc.inc cstruct.inc \
         cupdate.inc pmxcsg.inc pmxelm.inc pmxhil.inc pmximp.inc pmxpln.inc \
         pmxprt.inc pmxtil.inc pmxtim.inc pmxtls.inc

wshred.o: cchprt.inc cenrpa1.inc chydrol.inc cpart1.inc cpart3.inc \
         cseddet.inc cstore.inc cstore1.inc cstore2.inc cstruc.inc \
         cupdate.inc pmxelm.inc pmxhil.inc pmxpln.inc pmxprt.inc pmxtil.inc \
         pmxtls.inc

wshrun.o: cdiss11.inc cirspri.inc coutchn.inc cstore1.inc cstruct.inc \
         pmxcsg.inc pmxelm.inc pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc

wshscs.o: chydrol.inc cstore.inc cstore1.inc cstore2.inc pmxelm.inc \
         pmxhil.inc pmxpln.inc pmxprt.inc

wshtc.o: cchpar.inc cchpek.inc cchtmp.inc cchvar.inc cflags.inc \
         chydrol.inc cimpnd.inc cslope2.inc cstore.inc cstore1.inc \
         cstore2.inc cstruc.inc cstruct.inc pmxcsg.inc pmxelm.inc \
         pmxhil.inc pmximp.inc pmxpln.inc pmxprt.inc pmxtim.inc

xinflo.o: ccntour.inc ccover.inc ccrpprm.inc ccrpvr3.inc ccrpvr3a.inc \
         ccrpvr5.inc ccrpvr5a.inc cdist.inc cdist1.inc cdist2.inc \
         cdist3.inc cefflen.inc cends.inc cends1.inc cends2.inc cends3.inc \
         cends4.inc cffact.inc chydrol.inc cinfco1.inc cinfco2.inc \
         cinfcof.inc cirfur1.inc cirfur2.inc cirfurr.inc cirriga.inc \
         crinpt1.inc crinpt1a.inc crinpt3.inc crinpt3a.inc crinpt5.inc \
         cslope.inc cslope1.inc cslope2.inc cslope3.inc cstruc.inc \
         cupdate.inc pmxcrp.inc pmxelm.inc pmxgrz.inc pmxhil.inc pmxpln.inc \
         pmxres.inc pmxslp.inc pmxsrg.inc pmxtil.inc pmxtls.inc pntype.inc \
         pxstep.inc

yalin.o: cconsta.inc cpart.inc cpart1.inc cpart2.inc cpart3.inc \
         csolva1.inc cstruc.inc ctcfrac.inc pmxelm.inc pmxhil.inc \
         pmxnsl.inc pmxpln.inc pmxprt.inc

yldopt.o: ccrpgro.inc ccrpprm.inc ccrpvr3.inc ccrpvr3a.inc pmxcrp.inc \
         pmxpln.inc pmxres.inc pmxtil.inc pmxtls.inc pntype.inc
