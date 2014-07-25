23 Jul 2014
  Update meeting, Cruse, Gelder, James, Victoria, Hao, Sarah
  - James would like to look into soil table differences
  - Gelder talked about differences between HS in WEPP and the explicit slopes
    we are feeding WEPP, perhaps this is not ideal and we should attempt to
    provide more generalized hill slopes for WEPP
  - Continued discussion about if WEPP can provide us guidance on when gullies
    start
  - daryl should email James about the upfact used in IDEPv1
  - Perhaps we could use Iowa Flood center data to validate the runoff output
  - Some of us probably should attend EGU in Vienna in April 2015

 2 Jul 2014
  Update meeting, Cruse, Gelder, Victoria, grad student, James
  - We should ask Dennis F if he has LS curve graphics to share
  - Can the WEPP code tell us when we should truncate flowpaths?  Perhaps it
    has some internal flag for when it things we have left sheet-rill
  - James is going to look more into 9999 soils, perhaps something else is
    up, these are when some soil property is missing
  - daryl should send some soil 9999 diagnostics
  - Are we reporting yield or detactment erosion!  gasp
  
17 Jun 2014
  Team project meetings, lots of attendees
  - The main issue was that our initial flow paths were too long and probably 
    the reason for the high erosion estimates
  - If we expand, the project name is just Daily Erosion Project at that point
  - Dennis Flanagan was also noting that our flow paths were way too long
  - Kansas is probably only interested in the area two counties west of ICT
    to the eastern border
  - Average irrigation in Kansas is 14.5 inches per year
  
11 Jun 2014
  Cruse, Gelder, James, daryl, grad student
  - First iteration had 211,414 flowpaths
  - Brian is producing 1-5 management codes, which equates to tillage c-fact
  - Desired products for Tuesday Meeting
    1) State map of outputs for some days or many days
    2) Have some sort of comparison engine for IDEPv1 and IDEPv2 outputs
    3) Provide some highlights in the management changes
    
16 May 2014
  Cruse, Gelder, James, daryl, grad student,Sarah
  - 16 HUC12s are currently missing cut-dems
  - Dave noted that some of the HUC12s have too many subcatchments
  - There is hope that the soil types have intrinsic slope characteristics, so
    they will break naturally
  - daryl should check the generalized slopes against individual cell to cell
    slopes
  - Brian would like to see the 1km precip displayed on the IDEPv2 map
  - The flowpaths are going to change as things are iterated, should I create
    some mechanism to account for these changes.  This could be ugly.
  - Will I need to version the output...
  - Dave's flow path computation takes 20 minutes per HUC12
  - There will be folks at the meeting on the 17th that are ignorant of the
    project, may have to rehash some things
  - Does the cutter code top terraces?
  - Need to ask the Kansas folks where their LIDAR data is!
   
23 April 2014 
  Cruse, Gelder, James, daryl, grad student
  - We have settled on 1616 HUC12s
  - Currently looking at a baseline rotation from 2008 to 2013 (6 yrs)
  - Discussion on handling the cropping data, daryl would like a simple code
    per field per year and then he'll build the rotations dynamically
  - Do we need to worry about difference between pasture and alfalfa ?
  - Grad student will do some tests to see if estimates statistically converge
    or not
  - Long discussion about how to do the breaks for the flow path, the initial
    break will be on slope, then soil, then management
  - daryl should email Laflen to see what he now has...
  - Need to get IDEPv2 running in realtime, even with the few watersheds