# this script extractS data from WEPP files in order to prepare it for WEPS input
# currently set up to read data for one WEPP site and:
# 1) update WEPS file -> 2) run WEPS -> 3) collect WEPP data for next day and -> 4) repeat

# updated: Dec 2019
# currently: not updating the wind speed/direction data - that will happen at IA State
# for testing purposes, the WEPS file has high wind speed for every day of the year
  #June 2024: Is this still true regarding the wind speed, or is it using measured wind speed values now?

# required input files: grph_0 (WEPP daily output file - obtained from Darryl H. at IA State)
# required input files: p0 (WEPP soil properties file - obtained from Darryl H. at IA State)
# required input file: "Mgmt.txt" (WEPP management information)

args = commandArgs(trailingOnly = TRUE)

# if we are running in interactive mode
if (length(args) == 0) {
  print('length(args) == 0')  
  generic_template_in <- 'WEPStest';
  weppgraphfile <- 'grph_0.txt';
  weppsoilfile <- 'p0.sol';
  weppmgmt<-"Mgmt.txt";
  Year <- 2019;
  DayofYear <- 365;
  CropCode <- 'C';
} else {
  # get arguments from the command line
  generic_template_in=args[1];
  weppgraphfile=args[2];
  weppsoilfile=args[3];
  Year=as.numeric(args[4]);
  weppmgmt=args[5]
  DayofYear=as.numeric(args[6]);
  CropCode=args[7];
}
generic_template_in.in<-paste(generic_template_in, ".in", sep="")
print(paste('Template File In: ', generic_template_in.in, sep=""))
print(paste('WEPP graph file: ', weppgraphfile, sep=""))
print(paste('WEPP soil file: ', weppsoilfile, sep = ""))
print(paste('Year: ', Year, sep = ""))
print(paste('Day of Year: ', DayofYear, sep = ""))
print(paste('WEPP mgmt file: ', weppmgmt, sep = ""))

require(readr)
require(dplyr)
#require(readtext)

# directory/file information here (shouldn't need to change script anywhere else)

#Set working directory 
#####*****working.dir<-"G:/SOIL/ESTIMATORS/Projects/BWSR_TillageStudy/WEPSstandalone/WorkSpace/DailyUpdate_Sept2019"
######working.dir<-"G:/SOIL/ESTIMATORS/Projects/BWSR_TillageStudy/WEPSstandalone/WorkSpace/DailyUpdate_Sept2019"
######setwd(working.dir)

######dir<- working.dir

#*******************shouldn't be any user input required down here*************
# colnames from commented portion of grph_0.txt
colnames<-c("year","Day","Precip_in","AvDet_t-a","MxDet_t-a","DetPt_ft","AvDepo_t-a","MxDepo_t-a","DepoPt_ft","SedLving_lb-ft",
            "5d_avMntmp_F","5d_avMxtmp_F","dlyMntmp_F","dlyMxtmp_F","IrrDpth_in","IrrVol_in","Runoff_in","IntRillNetLoss_t-a","CnpyHt_ft","CnpyCov",
            "LAI","IntRillCover","RillCover","AbvGrndliveBiom_t-a","LiveRootMass_t-a","LRM_0-15cm_t-a","LRM_15-30cm_t-a","LRM_30-60cm_t-a","Rtdepth_in","StndngDeadBiom_t-a",
            "Rsd_t-a","PrevRsd_t-a","OldRsd_t-a","SbmRsd_t-a","PrevSbmRsu_t-a","OldSbmRsd_t-a","DeadRoot_t-a","PrevRoot_t-a","OldRoot_t-a","Porosity%",
            "BlkDens_lbs-ft3","EffHydCond_in-h","Suct_in","ET_in","Drnge_in-day","DpthDrain_ft","EfInt_in-hr","PkRunoff_in-hr","EffRunoffDur_hr","EnrichRatio",
            "AdjKi","AdjKr","AdjTauc","RillWidth_in","PlntTransp_in","SoilEvap_in","Seepage_in","WaterStress","TempStress","TotSoilWater_in",
            "SoilWaterLyr1","SoilWaterLyr2","SoilWaterLyr3","SoilWaterLyr4","SoilWaterLyr5","SoilWaterLyr6","SoilWaterLyr7","SoilWaterLyr8","SoilWaterLyr9","SoilWaterLyr10",
            "RndRough_in","RdgHeight_in","FrstDepth_in","ThwDepth_in","SnwDepth_in","SnwMeltWater_in","SnwDensity_lb-ft3","RillCovFricFac","FricFracLivePlant","RillTotalFricFrac",
            "CompFricFactor","RillCoverRnge","LiveBasalAreaFricFac","LivePlantCanopyFricFac","DaysSinceDisturb","CropType","RsdType","PrevRsdType","OldRsdType","DeadRootType",
            "PrevDeadRootType","OldDeadRootType","SedLeavingOFE_lb-ft","EvapfromRsd","TotFrozSoilWater_in","FrzH2OLyr1","FrzH2OLyr2","FrzH2OLyr3","FrzH2OLyr4","FrzH2OLyr5",
            "FrzH2OLyr6","FrzH2OLyr7","FrzH2OLyr8","FrzH2OLyr9","FrzH2OLyr10")

# set colwidths vector to read "grph_0.txt" as a fixed width file
colwidths<-c(4,6,rep(11,83),rep(3,7),rep(11,13))
colwidths<-as.integer(colwidths) #changes from numeric to integer
WEPPoutAll<- read_fwf(
    weppgraphfile,
    comment = "#",
    skip = 121,
    col_positions = fwf_widths(colwidths, col_names = colnames),
    col_types = "iidddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddiiiiiiiddddddddddddd")
WEPPout <- dplyr::filter(WEPPoutAll, year == Year)
WEPPout$Precip_mm<-WEPPout$Precip_in*25.4
WEPPout$IrrDpth_mm<-WEPPout$IrrDpth_in*25.4
WEPPout$SnwMeltWater_mm<-WEPPout$SnwMeltWater_in*25.4

#****DEP management information
m_colnames<-c("year","day","mgmt_flag","operation","details1","op2","details2")
# set m_colwidths vector to read in management file ("Mgmt_0.txt") as a fixed width file
widths<-c(4,4,2,21,14,17,11) #4 columns for year, 4 day, 2 mgmt flag, 21 mgmt file name, 14 mgmt file specifics, 17 2nd op, 11 2nd specifics
widths<-as.integer(widths) #changes from numeric to integer
WEPProt<- read_fwf(weppmgmt, col_positions = fwf_widths(widths, col_names = m_colnames),
                   col_types = "iiicccc")

#***************WEPP soil variables
WEPPsoil<- read.table(weppsoilfile, skip = 4, nrows = 1, sep = " ")
Depthmm<-round(as.numeric(WEPPsoil[1,4]),digits=2)
Sandpct<-round(as.numeric(WEPPsoil[1,5]),digits=2)
Sandpct<-Sandpct/100 #needs to be in decimal percent for calculations

# determine very fine sand based on equation 7.2 from Foster et all., 2004 and USDA-ARS (2013) RUSLE2 documentation.
VFSandpct <- 0.74*Sandpct - 0.62*Sandpct^2

Claypct<-round(as.numeric(WEPPsoil[1,6]),digits=2)
Claypct<-Claypct/100 #needs to be in decimal percent for calculations
Organicpct<-round(as.numeric(WEPPsoil[1,7]),digits=2)
Organicpct<-Organicpct/100 #needs to be in decimal percent for calculations
CECmeq<-round(as.numeric(WEPPsoil[1,8]),digits=2)
Rockpct<-round(as.numeric(WEPPsoil[1,9]),digits=2)
Rockpct<-Rockpct/100 #don't think I need this, but including here for consistency
#compute silt by difference
Siltpct<-round((1-(Sandpct+Claypct)),digits=2)

#wilting point & saturation calculations using pedotransfer functions from Saxton and Rawls 2006
wilting_point1<-(-0.024*Sandpct+0.487*Claypct+0.006*Organicpct+(0.005*Sandpct*Organicpct)-(0.013*Claypct*Organicpct)+(0.068*Sandpct*Claypct)+0.031)
wilting_point<-(wilting_point1+(0.14*wilting_point1-0.02))
theta_s1<-0.278*Sandpct+0.034*Claypct+0.022*Organicpct-(0.018*Sandpct*Organicpct)-(0.027*Claypct*Organicpct)-(0.584*Sandpct*Claypct)+0.078
theta_s2<-theta_s1+(0.636*theta_s1-0.107)
field_capacity1<-(-0.251*Sandpct+0.195*Claypct+0.011*Organicpct+(0.006*Sandpct*Organicpct)-(0.027*Claypct*Organicpct)+(0.452*Sandpct*Claypct)+0.299)
field_capacity<-field_capacity1+(1.283*field_capacity1^2)-0.374*field_capacity1-0.015
theta_s<-field_capacity+theta_s2-0.097*Sandpct+0.043

# Compute soil CaCO3 based on pedotransfer function found in:
# Wang, Q., Y. Li, and W. Klassen. 2005. Determination of Cation Exchange Capacity on Low to Highly
# Calcareous Soils. Communications in Soil Science and Pland Anlaysis, 36: 1479-1498.
# DOI: 10.1081/CSS-200058493 
OrgCgkg<-Organicpct*1000 #to get into proper units (g/kg) for pedotransfer function
Claygkg<-Claypct*1000 #to get into proper units (g/kg) for pedotransfer function
CaCO3gkg<- (CECmeq - 1.909 - 0.0199*OrgCgkg - 0.0199*Claygkg) / 0.0076
CaCO3pct<-CaCO3gkg/1000 #to get back into proper units for WEPS calculations

#################temp CaCO3pct value for comparison to WEPS outputs###################Sept24_2019
CaCO3pct<-0.00 #based on soils data for WAUKON FSL in WEPS model for comparison here
#################remove this later####################################################Sept24_2019

##****Soil aggregate calculation parameters (Added June 2024)
k4f <- 1.4 #water migration & freezing expansion coef for agg stab
k4fs <- 4.25 #freezing solidification coef. for agg. stability
k4fd <-5.08 # drying while frozen coef. for agg. stabilityu
k4w<-1.0 # wetting process coef. modified by current dry stability
c4p<-0.6
c4f<-0

#initialize soil aggregate calc. parameters
HRwc0 <- 0
#se0 <-0.5 #what would be a good initial value here?
soil_temp_prior <-1

#average aggregate stability
SEag_mean <- 0.83 + 15.7*Claypct - 23.8*Claypct^2
#adjustments for absolute range allowed in SWEEP document page 17
if (SEag_mean < 0.1){
  SEag_mean <- 0.1
} else if (SEag_mean > 7.0){
  SEag_mean <- 7.0
}

#Set se0 initial
#cseagmx and cseagmn (maximum and minimum aggregate stability) from eq 27 and 28 in WEPS documentation
cseagmx<-SEag_mean+2*0.16*SEag_mean
cseagmn<-SEag_mean-2*0.16*SEag_mean
cseags=SEag_mean #2 #cseags=SEag_mean; setting to a specific value for testing purposes 
se0 <- (cseags - cseagmn)/(cseagmx - cseagmn)

#NEW 2/5/24: set abnormal lognormal aggregate size distribution (ASD) representation
#set average and stdev aggregate size fraction less than 0.84mm (eq 50 WEPS)
if(Sandpct<0.15){
  SF84_m<-0.2909+0.31*Sandpct+0.17*Siltpct+0.00333*(Sandpct/Claypct)-4.66*Organicpct-0.95*CaCO3pct
} else{
  SF84_m<-0.2909+0.31*Sandpct+0.17*Siltpct+0.01*(Sandpct/Claypct)-4.66*Organicpct-0.95*CaCO3pct
}
SF84_std<-(0.41-0.22*Sandpct)*SF84_m #standard deviation of aggregate size fraction less than 0.84mm
#max and min values for geometric mean diameter:
cslmin<-exp(3.44-7.21*(SF84_m+2*SF84_std)) #min value for geometric mean aggregate diamter (WEPS eq 53)
cslmax<-exp(3.44-7.21*(SF84_m-2*SF84_std)) #max value for geometric mean aggregate diameter (WEPS eq 54)
#initial geometric mean diameter (WEPS eq 52)
cslagm_0<-exp(3.44-7.21*SF84_m) 
#non-dimensional aggregate geometric mean diameter
gmd0<-(cslagm_0-cslmin)/(cslmax-cslmin) 

#Extract daily data from "grph_0.txt", write WEPS.in file and run SWEEP 

#####*****old section for running the WEPPgraph file as a loop.  Should be able to delete this
for (i in 1:nrow(WEPPout)){

print(i)

WEPS<-readLines(generic_template_in, n=-1)
# substitute WEPS parameter values on a line-by-line basis

### Compute SWEEP soil crust and aggregate parameters based on equations from SWEEP technical documentation;
  ##gmd calculations from WEPS logic (regression for management effects and WEPS soil documentation for freeze/thaw and wet/dry)
### Comment numbers in brackets refer to [page number, equation number] from:
### WEPS technical documentation, BETA release 95-08 (downloaded pdf from WEPS website)
### OR SWEEP documentation; default is WEPS documentation. If SWEEP documentation, it'll be noted

#CUMP = cumulative depth of snowmelt, rainfall, and sprinkler irrigation (mm)
#CUMSR = cumulative depth of sprinkler irrigation and rainfall (mm)
#These cumulative values reset to zero when there has been soil disturbance WEPPout$DaysSinceDisturb < 1 ###########################Sept 27 2019

if (WEPPout$DaysSinceDisturb[i]<=2) {
  CUMP <- 0.0
  CUMSR <- 0.0
} 
  
if (i==1) {
  CUMP <- WEPPout$SnwMeltWater_mm[i]+WEPPout$Precip_mm[i]+WEPPout$IrrDpth_mm[i]
  CUMSR <- WEPPout$Precip_mm[i]+WEPPout$IrrDpth_mm[i]
} else {
  CUMP <- CUMP + WEPPout$SnwMeltWater_mm[i]+WEPPout$Precip_mm[i]+WEPPout$IrrDpth_mm[i]
  CUMSR <- CUMSR + WEPPout$Precip_mm[i]+WEPPout$IrrDpth_mm[i] 
}

#SDag = Soil Layer Aggregate Density [SWEEP document page 17]  Mg/m3
SDag <- 2.01*(0.72 + 0.00092 * Depthmm)
#adjustments for absolute range allowed in SWEEP document page 17
if (SDag < 0.6){
  SDag <- 0.6
} else if (SDag > 2.5){
  SDag <- 2.5
}

#SEag = Soil Layer Aggregate Stability [SWEEP document page 17]  ln(J/kg)
SEag <- 0.83 + 15.7*Claypct - 23.8*Claypct^2
#adjustments for absolute range allowed in SWEEP document page 17
if (SEag < 0.1){
  SEag <- 0.1
} else if (SEag > 7.0){
  SEag <- 7.0
}
  
#Obsolete as of 5/3/24 (using WEPS-based aggregate equations instead)
  #Slagm = Aggregate Geometric Mean Diameter [SWEEP document page 17]
  #Slagm <- exp(1.343-2.235*Sandpct-1.226*Siltpct-0.0238*(Sandpct/Claypct)^3 
  #           + 33.6*Organicpct+6.85*CaCO3pct)*(1+0.006*Depthmm)
  #adjustments for absolute range allowed in SWEEP document page 17
  #if (Slagm < 0.03){
  # Slagm <- 0.03
#  } else if (Slagm > 30.0){
#  Slagm <- 30.0
#}

  #S0ags = Aggregate Geometric Standard Deviation (that's a zero "0", not an "O") [SWEEP document page 17]
  #S0ags <- 1.0 / (0.0203 + 0.00193*Slagm + 0.074 / Slagm^0.5)
  #adjustments for absolute range allowed in SWEEP document page 17
  #if (S0ags < 1.0){
    #S0ags <- 1.0
  #} else if (S0ags > 20.0){
    #S0ags <- 20.0
  #}

#*****NEW AGGREGATE CALCULATIONS (From "WEPS_test2")
  #*****Management Decisions***** I believe matches the WEPS calculations (5/3/24)
  #*This currently only works for corn; need some kind of flag to determine what crop is growing?
  management <- WEPProt$mgmt_flag[i]
  operation<-WEPProt$operation[i]
  details1<-WEPProt$details1[i]
  
  if (management==1){
    #adjust nondimensional gmd based on the management occuring
    x<-log(cslagm_0)
    #chisel plow
    #if (operation<-"OpCropDef.CHISSTSP"){
    #y<-0.6924*x+0.1634
    if (operation=="OpCropDef.FCSTACDP") {#spring disk (avg corn and soy)
      y<-0.688*x-0.00665
      
    } else if (operation=="OpCropDef.PLDDO") { #field finisher (no field finisher for WEPS, assuming its the same as cultivate)
      y<-0.8097*x-0.11675
      
      #} else if (op2=="CropDef.Cor_0967"){ #plant corn
      #y<-0.8752*x-0.3286
      
      #}else if (op2=="CropDef.Soy_2194"){ #plant soybean
      #y<-0.8293*x-0.2664
    } else if (operation=="OpCropDef.CHISSTSP" && details1=="{0.203200, 2}") { #soybean fall chisel
      y<-0.7768*x-0.3976
    }else if (operation=="OpCropDef.CHISSTSP" && details1=="{0.203200, 1}"){ #corn fall chisel
      y<-0.6924*x+0.1634
    }else
      y<-log(cslagm_0)
    
    
    cslagm_0<-exp(y)
    gmd0<-(cslagm_0-cslmin)/(cslmax-cslmin)
    
    #management not occuring, nondimensional gmd does not need to be adjusted  
  }
 
  gmd00<-gmd0  
  #} #this bracket closes the gmd adjusted by management for testing purposes
  #testing
  #print(cslagm_0)
  #print(management) 
  #print(operation)
  #print(x)
  #print(gmd0)
  
  #******Soil Aggregate Decisions*******
  #NEW as of June 2024
  #*#set parameters
  #Soil_temp = 0 means no frost depth = UNFROZEN
  #Soil_temp>0 means frost depth = FROZEN
  #Hrwc1>Hrwc0 means wetting
  #Hrwc1<HRwc0 means drying
  #HRwc1=Hrwc0 means no soil moisture change
  
  #wet/dry freeze/thaw variables
  k4td <- 0.4*(1+0.00333*(Depthmm))
  k4td <- min(k4td,0.667)
  k4d  <- 0.6*(1+0.00333*(Depthmm))
  k4d  <- min(k4d, 1.0)  
  
  
  #Soil Temp and Moisture
  #!!!soil is frozen if frost depth is > 0 
  soil_temp<-WEPPout$FrstDepth_in[i] 
  bulkdensity<-round((WEPPout$`BlkDens_lbs-ft3`[i]*16018.47/1000000),digits=2) #g/cm3
  SoilWater<-WEPPout$SoilWaterLyr1[i]*2.54 #assume water density of 1g/cm3; gives water in cm
  Volwater<-SoilWater/10 #assumes top layer depth of Wepp output is 10cm
  Soilpb<-as.numeric(bulkdensity)
  SoilMass<-(Depthmm/10)*Soilpb  #soil mass in top layer from SSURGO file (not necessarily the same layer depth as WEPP output)
  GravWaterContent<-round((Volwater/Soilpb),digits=2) #assumes water densit of 1 g/cm3
  #GravWaterContent<-round((SoilWater/SoilMass),digits=2) #old calculation
  #7/3/24 turned off wilting_point<-0.22 #JOhnston soil=0.123 probably volumetric #bearden silt loam =0.22; crete 0.11
  #7/3/24 turned off field_capacity<-0.41 #Johnston=0.216 volumetric; 0.41 bearden silt loam? SSURGO value is 0.34; crete 0.24
  HRwcw<-(wilting_point)/Soilpb
  HRwcs<-(theta_s)/Soilpb
  #HRwcs<-(field_capacity)/Soilpb #needs to use saturated content not FC
  HRwc<-(GravWaterContent-HRwcw)/(HRwcs-HRwcw) #non-dimensional soil moisture content
  if (HRwc < 0){
    HRwc <- 0
  } else if (HRwc > 1){
    HRwc <- 1
  } else {
    HRwc<-HRwc
  }
  
  
  #***Calculate sEag1*:
  #*#*Variable definitions:                        
  #se1=current day relative aggregate stability
  #se0=prior day relative aggregate stability
  #se, se2, se3, se4, se5, se6=relative stability with partial update
  #se & se2 partial updates for unfrozen-frozen
  #se3 partial update to se0 value considering freezing (se0 then becomes se4 freezing-freezing)
  #se5 and se 6 are partial updates for frozen-unfrozen
  
  se00<-se0
  
  #If statements to calculate se1 based on soil temp and soil moisture
  
  if (soil_temp_prior<=0 && soil_temp<=0) { #unfrozen-unfrozen 
    if(HRwc<HRwc0){#drying
      se1 <- se0 + k4d*(HRwc0-HRwc)
    } else {#wetting
      se1<-se0*(1.0001-k4w*HRwc)/(1.0001-k4w*HRwc0) #should it be "se0+..." or "se0*..."?? (* is what was originally done)
    }
    se1<-min(se1,1) #for unfrozen, limit size so can't go above 1
    
  } else if (soil_temp_prior<=0 &&soil_temp>0){#unfrozen_frozen
    if(HRwc<=HRwc0){ #drying
      se2<-se0+k4d*(HRwc0-HRwc)
    }else {
      se2<-se0*(1.0001-k4w*HRwc)/(1.0001-k4w*HRwc) #wetting; calculating se2 correctly ##se0+ or se0*?
    }
    se<-se2*(1.0001-k4w*k4f*HRwc)/(1.0001-k4w*HRwc)  #se2* or se2+?
    se<-max(0,se)
    se1<-se+k4fs*k4f*HRwc+0.5 # seems to be calculating lines 269-279 correctly
    se1<-min(se1,10) #for frozen, limit ability to go above out of range value
    
    
    #Frozen-frozen
  } else if (soil_temp_prior>0 && soil_temp>0){#frozen_frozen
    se3<-se0*(1.0001-k4w*k4f*HRwc0)/(1.0001-k4w*HRwc0) #se0* or se0+?
    se3<-max(0,se3)
    se4<-se3+k4fs*k4f*HRwc0+0.5
    if(HRwc<HRwc0){ #drying
      se1<-se4+k4fd*k4f*(HRwc-HRwc0)
      se1<-max(se1,0)
    }else if (HRwc>HRwc0) { #setting (do I need to consider se1=max(se4,0)?)
      se1<-se4+k4fs*k4f*(HRwc-HRwc0)
    }else {
      se1<-se4
    }
    se1<-min(se1,10) #for frozen, limit ability to go above out of range value
    
  } else {#frozen-unfrozen #currently testing on 11/11/23
    pud<-HRwc0*k4f  
    if(pud>1){ #puddling
      se5<-max(0.01,(0.999-k4td*HRwc0))
    }else {
      se3<-se0*(1.0001-k4w*k4f*HRwc0)/(1.0001-k4w*HRwc0) #se0* or se0+?
      se3<-max(0,se3)
      se4<-se3+k4fs*k4f*HRwc0+0.5
      se6<-se4-k4fs*k4f*HRwc0-0.5
      se6=max(se6,0)
      se5<-se6+k4td*HRwc0*(k4f-1)
    }
    if(HRwc<HRwc0){#drying
      se1 <- se5 + k4d*(HRwc0-HRwc)
    } else {#wetting
      se1<-se5*(1.0001-k4w*HRwc)/(1.0001-k4w*HRwc0) #se5* or se5+
    }
    se1<-min(se1,1) #for unfrozen, limit ability to go above 1 (max se)
}  
  #add if statement so that se1 can not go below minimum value of 0.01
  if(se1<0.01){
    se1<-0.01
  } else {
    se1<-se1
  }
  
  #undimensioned gmd calculations (noted as gmd1 for current day, gmd0 for previous day)
  gmd1_avg <-1-exp(-((se1/c4p)^2))
  gmd0_avg<-(1-exp(-(se0/c4p)^2))*(1-c4f)+c4f
  
  if(se0<1 && se1>1){ #freeze drying
    gmd1<-gmd0+se1  
  }else if (se0>1 && se1<1){ #soil thaws
    gmd1<-gmd1_avg
  }else if(se0==1 && se1==1){#unfrozen dry soil
    gmd1 <-(gmd1_avg+gmd0)/2
  }else if (se0 == se1){
    gmd1<-gmd1_avg*0.2+gmd0*0.8
  }else{
    slp0<-(gmd1_avg-gmd0)/(se1-se0)
    slp_avg<-(gmd1_avg-gmd0_avg)/(se1-se0)
    slp<-(slp0+slp_avg)/2
    gmd1<-gmd0+slp*(se1-se0)
  }
  #dimensioned gmd--> VALUE USED FOR REST OF CALCULATIONS
  cslagm_2 <- ((cslmax-cslmin)*gmd1)+cslmin
  cslagm_1 <- max(cslmin,cslagm_2)
  
  #calculate gsd (cs0ags) based on value of gmd (cslagm) (WEPS eq 65)
  cs0ags_1 <- 1.0 + 1.0 / (0.012448 + 0.002463*cslagm_1 + 0.093467/(cslagm_1)^0.5)
  
  ##***Resumes calculations of other soil parameters (pre-June 2024 changes/not new WEPS calculations):  

#SDbko = Settled bulk density at 300mm depth [S-15, 51]
SDbko <- SDag

#SDcr = Soil Crust Density [S-15, 52]
SDcr <- 0.576 + 0.603 * SDbko 

#############this equation probably needs to be updated!!!
######look at WEPS tech document page S-9 equation 23 and 21
#SFlos = Fraction Loose Material on Surface [S-8, 21]
if (CUMSR < 10) {
  SFlos <- 0 #based on equation and SWEEP manual page 18
} else if (CUMSR >= 10) {
  SFlos <- 0.14 + 0.001*CUMSR
}
# range guidance from SWEEP documentation page 18
if (SFlos<0){
  SFlos <- 0.0
} else if (SFlos > 1.0){
  SFlos <- 1.0
}

#Slagn = Soil Layer Minimum Aggregate Size [SWEEP document page 17]
Slagn <- 0.01 

#SMXlos = Maximum Loose, Erodible Mass on Crust [S-8, 19]
SMXlos <- 0.1*exp(-0.57+0.22*(Sandpct/Claypct) + 7.0*CaCO3pct - Organicpct)

#SMlos = Mass of Loose Material on Crust [S-8, 20], see also SWEEP document page 18  (kg/m2)
if (CUMSR < 10) {
  SMlos <- 3
} else if (CUMSR < 180) {
  SMlos <- SMXlos*(1 - 0.005 * CUMSR)
} else if (CUMSR >= 180){
  SMlos <- 0.0
}
# range guidance from SWEEP documentation page 18
if (SMlos < 0){
  SMlos <- 0.0
} else if (SMlos > 3.0){
  SMlos <- 3.0
}

#Slagx = Soil Layer Maximum Aggregate Size [SWEEP document page 17]
p <- 1.52 * cs0ags_1^-0.449
Slagx <- cs0ags_1 * cslagm_1 + 0.84^p
#adjustments for absolute range allowed in SWEEP document page 17
if (Slagx < 1.0){
  Slagx <- 1.0
} else if (Slagx > 1000.0){
  Slagx <- 1000.0
}

#SEag = Aggregate Stability Crushing Energy [S-9, 24]
SEag <- 0.83 + 15.7*Claypct - 23.8*Claypct^2

#SFcr = Soil Fraction Crust Cover [S-7, 17]
if (CUMP < 10) {
  SFcr <- 0.0
} else if (CUMP >= 10) {
  SFcr <- 0.36 + 0.0024 * CUMP
}
# range guidance from SWEEP documentation page 18
if (SFcr < 0){
  SFcr <- 0.0
} else if (SFcr > 1.0){
  SFcr <- 1.0
}

#SEcr = Crust Stability Crushing Energy [S-7, 18]
SEcr <- SEag

#SZcr = Crust Thickness [S-6, 14]
Acr <- -0.072 * 0.2*Claypct
Bcr <- 1.56 - 2.9 * Claypct
if (CUMP < 200){
  SZcr <- Acr * CUMP + Bcr * CUMP^0.5 
} else if (CUMP >= 200){
  tempCUMP <- 200
  SZcr <- Acr * tempCUMP + Bcr * tempCUMP^0.5 
}
# range guidance from SWEEP documentation page 18
if (SZcr < 0){
  SZcr <- 0.0
} else if (SZcr > 23.0){
  SZcr <- 23.0
}

# Only need to update the file when we are actually going to write something
if (i < DayofYear){
    next
}

### WEPS.IN +++ BIOMASS +++ 
WEPS[86]<-paste(" ",(round((WEPPout$CnpyHt_ft[i]*0.3048),digits=2)),sep="") #biomass height on day i; converted to m
WEPS[89]<-paste(" ",(round((WEPPout$CnpyHt_ft[i]*0.3048),digits=2)),sep="") #crop height on day i;  converted to m


#***************estimate Stem Area Index**********
if (CropCode == 'S'){
    stem_dia <- 0.006 #m #6.0mm
    stem_pop<-(100000/4046.86)
} else {
    stem_dia <- 0.01 #m #10.0mm
    stem_pop<-(32000/4046.86)
}
#NEED TO ADD STATEMENT FOR OTHER CROP
CSAI<-stem_dia*stem_pop*(WEPPout$CnpyHt_ft[i]*0.3048)
WEPS[93]<-paste(" ",(round(CSAI, digits=2)),"", (round(WEPPout$LAI[i], digits=2)),collapse="") #crop StemAI and LAI

#WEPS[93]<-paste(" ",0.0,"", (round(WEPPout$LAI[i], digits=2)),collapse="") #crop StemAI and LAI
#   WEPS[120]<-paste(" ",(round(WEPPout$LAI[i], digits=2)),"", (round(WEPPout$LAI[i], digits=2)),collapse="") #crop StemAI and LAI
   
#line 141 is flat biomass cover m2/m2, Need to convert residue t/ac to biomass cover (m/m)
#Percent cover estimated from residue biomass after equtions provided in Gregory, 1982
#Currently using a single cover coefficient (corn), need to find a way to update this by crop
Residuelbac<-WEPPout$`Rsd_t-a`[i]*2000 #convert t/ac to lb/acre
if (CropCode == 'S'){
    covercoef<-0.0002
} else {
    covercoef<-0.00038
}

Cover<-(1-exp(-covercoef*Residuelbac))
WEPS[114]<-Cover

#Crop row spacing
  if (CropCode =='S' ){
  crop_spacing<-(20*0.0254) #20in soybean row spacing
} else if (CropCode == 'C'){
  crop_spacing<-(30*0.0254) #30in corn row spacing 
}else {
  crop_spacing<-(30*0.0254)
}
WEPS[101]<-paste(" ",(round(crop_spacing, digits=2)),"", 0,collapse="")

### WEPS.IN +++ SOIL +++ 
WEPS[119]<-paste(" ",1,sep="")  #number of soil layers (WEPS only needs info for the top layer)
WEPS[124]<-paste(" ",Depthmm,sep="") #thickness of soil layer in mm
   
bulkdensity<-round((WEPPout$`BlkDens_lbs-ft3`[i]*16018.47/1000000),digits=2)
WEPS[127]<-paste(" ",bulkdensity,sep="")
WEPS[130]<-paste(" ",(round((Sandpct),digits=2)),sep="")
WEPS[132]<-paste(" ",(round((VFSandpct),digits=2)),sep="") 
WEPS[134]<-paste(" ",(round((Siltpct),digits=2)),sep="")
WEPS[136]<-paste(" ",(round((Claypct),digits=2)),sep="")
WEPS[139]<-paste(" ",(round((Rockpct),digits=2)),sep="")

# new in spring/summer 2019 (this note is just to help with trouble shooting)
WEPS[142]<-paste(" ",(round((SDag), digits=2)),sep="") #Soil layer aggregate density (Mg/m^3)
WEPS[144]<-paste(" ",(round((SEag), digits=2)),sep="") #Soil layer aggregate stability (ln(K/kg))
WEPS[146]<-paste(" ",(round((cslagm_1), digits=2)),sep="") #Soil layer geometric mean diameter (mm)
WEPS[148]<-paste(" ",(round((Slagn), digits=2)),sep="") #Soil layer minimum aggregate size (mm)
WEPS[150]<-paste(" ",(round((Slagx), digits=2)),sep="") #Soil layer maximum aggregate size (mm)
WEPS[152]<-paste(" ",(round((cs0ags_1), digits=2)),sep="") #Soil layer geometric std deviation (mm/mm)

#next line contains: Surface Crust Fraction, Surface Crust Thickness, Fraction Loose Material on Surface,
#Mass of loose material on the crust, soil crust density, soil crust stability
WEPS[161]<-paste("",(round((SFcr), digits=2)),(round((SZcr), digits=2)),
                 (round((SFlos), digits=2)),(round((SMlos), digits=2)),
                 (round((SDcr), digits=2)),(round((SEcr), digits=2)),sep=" ") 

WEPS[166]<-paste(" ",(round((WEPPout$RndRough_in[i]*25.4),digits=2)),sep="") #Allmaras Random Roughness (convert to mm)


### WEPS.IN +++ HYDROLOGY +++   
      
WEPS[178]<-paste(" ",(round((WEPPout$SnwDepth_in[i]*25.4),digits=2)),sep="") #snow depth converted to mm

#convert soil water to proper units (Mg/Mg)
#SoilWatercm<-WEPPout$SoilWaterLyr1[i]*2.54 #assume water density of 1g/cc
SoilWatercm<-0 #assumes very top layer is dry for wind erosion calculations
#Soilpb<-as.numeric(bulkdensity)
#SoilMass<-Depthmm/10*Soilpb
    
Layer1WaterContent<-0 #assumes very top layer is dry for wind erosion estimates
#Layer1WaterContent<-round((SoilWatercm/SoilMass),digits=2)
#WEPS[184]<-paste(" ",Layer1WaterContent,sep="")
#Volwater_cm<-SoilWatercm/10 #assumes top layer depth of wepp output is 10cm
#  GravWaterContent_cm<-round((Volwater_cm/Soilpb),digits=2) #assumes water densit of 1 g/cm3
#  Layer1WaterContent<-GravWaterContent_cm
SurfaceLayerWaterContent<-(c(rep(Layer1WaterContent,12))) #top layer of soil (not WEPP top layer) is dry for wind erosion estimates
#WEPS[190]<-paste(" ",SurfaceLayerWaterContent,collapse="")
#WEPS[191]<-paste(" ",SurfaceLayerWaterContent,collapse="")

### WEPS.IN +++ WEATHER +++  
#this will be where wind data are input

if (i == DayofYear){
    write(WEPS, file=generic_template_in, append=FALSE)
    break
}

  #set current value as previous for next date in loop  
  gmd0<-gmd1
  soil_temp_prior<-soil_temp 
  HRwc0<-HRwc
  se0<-se1
  cslagm00<-cslagm_0
  cslagm_0<-cslagm_1    
    
} # End of loop
