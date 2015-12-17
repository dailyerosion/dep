 3 Dec 2015 - DEP Update
  Cruse, Gelder, Tim, James, Claudette
  - Union of Concerned Scientists has an interest in us running a scenario
    - They have a 4 year rotation to implement on the Des Moines lobe.
  - Tim is curious about EPIC and WEPP together, but I am unsure of coupling
  - UI Sediment folks has a new postdoc we can collaborate with
  - There's a NSF proposal being worked on with some folks from Engineering
  - Mario is coming 18 Jan till end of Feb
  - Further discussion on potential funding from Minnesota and logistics there
    - They have a wind erosion requirement
  - Reviewed Tim's significance testing and it appeared to check out
  - Claudette gave a processing update and things are moving along
  - James lead a DEM discussion and his happiness with recent usage of 2m data
  
19 Oct 2015 - DEP Update
  Cruse, Gelder, Tim, James
  - Tim noted that some subcatchments have more than 10 hillslopes contained
    within.  TODO: daryl check on this
  - TODO: something looks wrong with the output for 24 Jun 2011
  - Two of the 30 convergence test HUC12s had only a handful of subcatchments
  - Discussion on usage of Confidence Interval for showing convergence
  - Tim noted about a 33% coverage of daily data when erosion happened, which
    is about what daryl has noticed as well, I think
  - Discussion about paper progression and how to present the convergence work
  - Mario may be coming to visit us in Jan/Feb timeframe

17 Sep 2015 - Phosphorus Call
  Cruse, Gelder, Tim, Dennis, Jim, Mario
  - Having one flowpath per subcatchment is insufficient for WEPP watershed,
    will need to have many more and each subcatchment is likely one watershed
  - Discussion on if terraces are important for this project work.  Yes.
  - Jim noted that the input data structures (files) are complex to wepp
    watershed, daryl needs to email for the code.
  - Mario's work was only on P bound to sediment and not soluable
  - But there is a way to estimate this value if you make some assumptions
    about concentrations
  - Could use average soil test per county to provide these estimates for each
    soil used
  - Mario's code is on the postprocessing end of the WEPP watershed output
  - Q asked to Jim+Dennis: Does WEPP include all events of either runoff or
    erosion, A: Yes
  - Q: Does WEPP have a way to predict where gulleys start, A: No

 3 Sep 2015 - Stats meeting with Opsmer
  Cruse, Gelder, James, Tim
  - Emphasize that our estimates are daily at the HUC12 level, so that is
    what we need to evaluate
  - Look at the confidence interval when increasing the sample size, he
    suggested a simple variance devided by n^2
  - When adding sequential samples, it is best to random pick
  - We should present website users with some range of values instead of just
    a single value to give some confidence into our estimates
  - TODO: Should produce a map of samples per HUC12
  - TODO: Produce a map of where the yearly zeros are happening

18 Aug 2015 - DEP Update
  Cruse, Gelder, Claudette, James, Tim, Karl
  - BUG clicking on the homepage map did not work for Tim (#21)
  - Add a refresher to check for updated 'last date' for map (#22)
  - Karl leaves for his new job soon with IA Soybeans
  - Discussion on the map and various proposals currently in the pipe
  - Admin page color ramps are AWOL (#23)
  - There is a million dollar grant in Minnesota dealing with DEP related
    issues, discussion on approaches to it.
  - Ye ole stability plots analyses comes back, need to do for a single
    HUC12 and not all lumped together (daryl TODO)
  - Tim thinks we need to randomly add samples and not sequentially do it
  - Fix the HUC12 precip sampling to be polygon based and not agg runs (#24)
  - There will be a 3 Sept seminar on DEP, daryl shall present / attend!
  - Need to discuss with Jim and Dennis about the phosphoros issues
  - Gelder showed a plot of yearly precip totals from DEPv2, erm, check this
  - Gelder showed some calendar input related bugs (#25)

 9 Jul 2015 - DEPv2 Big Meeting
  Cruse, Gelder, James, Tim, Karl, KS Folks, Online Folks, Laflen
  - Issue of the number of OFEs and the sensitivity of such
  - Are the slopes of each OFE simple? I am unsure as the raw files seem to
    indicate not
  - Report State Averages, report view averages
  - Desire for Full Screen Display
  - What did we do with the management codes for Kansas?
  - make the state only modes
  - Have a conference with Dennis and Jim on current capabilities
  
 2 Jul 2015 -
  Cruse, Gelder, James, Claudette, Karl
  - Unsure of who exactly is coming next week, Brian will investigate
  - Discussion about agenda items for the meeting, Karl will work on it
  - Laflen will present some of his crop work at the meeting
  - Found a room at the Brenton Center after 3022 Agronomy was commendeered
  - We are working on a HUD proposal that seems well received
  - daryl needs to make a powerpoint for the meeting, items include:
    - precipitation changes
    - timing of output
    - website changes
    - show summary results
  - Kansas DEMs are not in good shape, but we hope that local watersheds are
    consistent, so border issues will not impact us
  - A bug was noticed with legend appearing too high on brian's PC (#17)
  - Switching display from two dates back to one did not properly work (#18)
  - Dynamic ramps would be nice, but need to figure out server side hinting
  - Decrease map to two decimals shown (#19)
  - Add a left/right carrot to the date widget for easy moving in time (#20)
  - Add a calendar icon as well to the date widget (#20)
  - Cull the null HUCs from the database, those on the border without runs made
  - The above bug #18 likely causes issue with the map title widget
  - Discussion on future funding opportunities
  - Look into what WEPP watershed does and if I can run it from the command line
  - Date issue above causes 1969 to appear in data widget

20 May 2015 -
  Cruse(phone), Gelder, James, Tim, Claudette, Karl
  - ISU Big Data proposal was submitted and will hear back on Friday if we are
    asked to submit a full proposal
  - daryl needs to resolve the solar radiation data aspects for MN and KS
    expansion.  IEMRE is doing it, but is currently unused(?)
  - Some issues have been found with Minnesota's LIDAR data
  - There are some positive signs that we may be able to seek funding from MN
    to do more erosion work in that state
  - 26 out of the 48 counties we are expanding to in KS are now done
  - Gelder needs to work on getting the LANDSAT archive built for KS
  - Discussion that the ordering of map elements needs to change (#13)
  - Make the map wider (use bootstrap container-fluid)
  - Suggestion to add full-screen option
  - Make OSM default as an enabled layer
  - Correct the hacky layout of the top 10 events
  - USGS WBD was used for the HUC12 identifiers, this may not match some other
    sources, like DNR.  daryl needs to investigate this some more.  Our version
    is vintage Oct 2012
  - A SMAP soil moisture proposal was submitted to NASA
  - Discussion about data storage needs and what is currently available from
    CEAP share
  - We are going to proceed with Tim's dailyerosion.org URI
  - Karl will email out the current paper draft
  - Cruse discussion about having photos to show what numbers look like
  
 2 Apr 2015 -
  Cruse, Gelder, James, Tim, Karl, Claudette
  - Gelder reported on his South Korea trip, maybe invited back again
  - The Kansas work is hopefully done by the end of the semester
  - Are we using Laflen's new cropping parameters in IDEPv2?
  - Am I using the new 2014 soils file that James provided?
  - There is a need to archive the old extracted hillslopes, soils, managements
  - Wait to change anything until the new cropping dataset is produced
  - There is a need for summarized time slices on the website
  - Tim suggested being able to average over a period over the years to get
    an average for comparison
  - Carl is going to send out the convergence plots to the group for comment
  - There is a need to get started on two papers
    1) The IDEPv2 paper that resembles IDEPv1 paper
    2) A comparison of the yearly values against the current accepted values
  - Did I filter out the 30% slopes from the runs?
  - The 10m DEM will be providing thresholds to bound the 3m DEM values
  - Need to resurrect the soil moisture stuff for the website/ processing
  - How to properly average out the soil water content?
  - Does WEPP have soil temperatures?
  - Tim has purchased dailyerosion.org and would like to create a frontpage
    for it
  - Talk with Tim about how DNS mapping works
  - Invite Kansas to a virtual meeting to discuss our progress
  - I had better start expanding the rainfall product, so when the Kansas data
    is ready to go, I am ready also...

24 Feb 2015 -
  Cruse, Gelder, James, Tim, Carl
  - James noted that during a demo of the site yesterday, it was very slow to
    respond around 2 PM.  daryl investigated and am unsure what is up.
  - We settled on 3 HUC12s per MLRA for the convergence test
  - For each sub-catchment, we need to over-sample more than just 10 as we want
    10 good ones and some times some of the samples are invalid
  - It was noted that two of the small MLRAs in the state may not have any 
    valid hillslopes to make runs for
  - We should do randoming picking from the 10 samples and not just append onto
    each as we iterate up to 10.
  - [TODO] truncate any slopes that go over 30% steep
  - Perhaps for this test, we should use the same climate file for all run
  - Do we dare ever do a substanciative comparison of IDEPv1 vs IDEPv2?  No
    as the numbers are likely not comparable
  - Discussion of pursuits of future funding for the project...

27 Jan 2015 -
  Cruse, Gelder, Carl, Tim
  - The 2007 erosion number is important as it was used in the EWG paper, I had
    better look more closely into it for IDEPv2
  - Tim Sklenar is joining our group, or will potentially join us
  - Discussion on approach for Karl's sampling.  The resolution was to generate
    at least one HUC12 with 'all' flowpaths and see where that gets us. Gelder
    will teach Karl how to do this.
  - Gelder shared a paper by Dennis showing his characteristic hillslope
  - daryl needs to check out 102300031504 for 15 Jun 2014
  - improve yearly totals shown on summarize page
  - daryl should email the group his status in the coming days as per scheduling
    upcoming meeting with brass

13 Jan 2015 -
  Cruse, Gelder, James, Carl, Claudette
  - Introduced new team members Claudette and Carl
  - A long discussion ensued about Carl's potential convergence work. A TODO
    item was for daryl to email Jean Opsomer about potential paths forward.
    The issue is how to increase the number of samples within the HUC12 to
    test for convergence.
  - We really need to look into the time resolution issue of the precipitation
    and its impact on the erosion estimates.  Is two minute interval too fine?
  - Illinois LIDAR data is problematic, so expansion into that state is tough
  - An open question is how we will handle irrigation in WEPP
  - James noted that major effort in expansion is dealing with field boundaries
  - Discussed central IT storage and Robin's GIS Lab capabilities.  For 10
    cents per gig per month, we can probably take advantage of that
  - James discussed a vision for where ACPF could go and how perhaps it would
    eventually follow DEP's lead 

20 Sep 2014
  Sanity Check, Cruse, Gelder, James, Victoria
  - [action] daryl emails Jim and asks about units of Sediment Delivery
  - We should be harvesting more than just detachment, maybe harvest them all?
  - Does Avg Detachment - Avg Deposition = Delivery?
  - Can I output on a per OFE basis?
  - Can I harvest the OFE summary data for quicker comparisons / QC ?
  - [action] check out the code to see about enabling all output!
  - Gelder is going to send me the G4 dataset, but with full paths
  - daryl was confused about what this G4 dataset was.  They are new 
    paths that can't be directly compared to previous ones.
  - [action] send out how many OFEs my system generated
  - [action] send out how many bad soils I hit...
  
19 Sep 2014
  Update meeting, Cruse, Gelder, James
  - Iowa Flood Center has some project verifying runoff using their stream 
    gauges.  May be interesting to collaborate on this.
  - Discussion on my map of flowpaths per HUC12 and how many points is enough
  - [action] send a new map with the ratio of provided flowpaths and what my
    algo ended up with
  - We should consider removing some HUC12s that are mostly urban or have 
    little ag land.
  - James: maybe we should stop flowpaths when they hit a 'bad' soil, currently
    I skip them an use the previous soil along the path
  - Cruse would like to get a press release out the door soon, will do once
    we are comfortable and the website is in a bit better shape!
  - Discussion about how WEPP can deal with cover crops.  Perhaps it does 
    but can't handle two crops growing at once.
  - Can we generate a comparison with the other erosion models, like RUSLE2
  - Would be nice to do a grand comparison
  - A deadline for stuff could be 25 Sept when Gelder presents stuff to 
    extension
    
28 Aug 2014
  Update meeting, Cruse, Gelder, James, Hao
  - Gelder is running G4 now for all the HUC12s, the hope is to have data by
    sometime in the mid-week
  - Are we able to harvest individual OFE results to look at what is happening
    near these fake terracces.
  - Victoria may have a chapter in her dissertation on looking at sensitivity
    to grid order
  - Would like to have things working by Baker Council meeting, early Oct
  - Should hear about CIG proposal by 15 Sept
  - James will be presenting lots of our stuff to NRCS technical folks soon
  - [action] email Gelder about 72 hour precip
  - [action] look into how WEPP reports water balance for each OFE?

 6 Aug 2014
  Update meeting, Cruse, Gelder, James
  - A side project with Gelder was funded by Iowa Nutrient Reduction Strategy
  - Should find out this month about the main grant application needed for
    agronomy matching funds
  - Great deal of discussion on the grid ordering work and how this can be 
    used to find converging flow.  Gelder wants to rerun cutter, but this will
    take considerable time.
  - Lots of discussion about what we are going to do with terracess.  Initially,
    just need to quantify how many are there.
     
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
  
03 Feb 2014
 Progress meeting in conference room with KS folks and others
 - Our current project deadline is 1 June 2014
 - Gelder is geting closer to getting a big push of computing done on ISU GIS
   lab systems, meeting with Robin on 4th
 - James points out that fallow acres in 2013 will cause some grief as there
   was lots of acres.
 - IDEPv2 rotations may be based on 2008-2013
 - Laflen has most of the crops completed
 - There is a PhD student coming in March for six months, that may have interest
   in working with us on sensitivity stuff
 - Will want to have some "beta" notation on the website for our outputs until
   we resolve 'validation'
 - I need to look into the KS Mesonet website and see what all they are up 
   to these days.  Looks to have a number of locations now
 - Kansas State would like their logo on stuff, but codes/data can live at ISU
 - KS wants to have a powerpoint detailing what we are up to as they look for
   funding
 - Dr Cruse is interested in app development or some special way to showcase
   our data and get it out into the hands of those out in the field.