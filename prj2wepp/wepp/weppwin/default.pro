#
#  Modified:  Thu Sep 26 10:11:49 AM 2002
#
model = 98.4
project  =  "default.prj"
template = "default.prj"
set = none
units = english
grid = yes
weppdos = no
cligendos = no
wepsview = no
erosion = yes
startScreen = yes
limitred = no
limitgreen = no
3D = yes
graphics = {
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y,Y,Y
   Y,Y,Y,Y,Y,Y,Y,Y
}
shading = {{
   watershed_soil_loss = {
       ff,0,0
    }
   watershed_sediment = {
       ff,0,0
    }
   watershed_runoff = {
       ff,0,0
    }
}}
watershed_option_ask_keep_length = yes
watershed_option_keep_length = yes
watershed_option_warn_hillshape_change = yes
zoomlevel = 1.2500
hillborderthickness = 1
channelborderthickness = 3
layout_slope_use_normalized_scale = no
