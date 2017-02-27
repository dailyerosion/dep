As you likely remember, I was asked to lead an effort addressing the
question: Is corn production as we currently practice sustainable? And can
it be?

To that end, soil erosion is one of the metrics against which we are asking
this question and DEP has become a major player in generating evidence
related to these questions.

Could be have data/graphs generated similar to those for the UCS report for:
Continuous corn no-till
Corn/soybeans with current tillage management but with cover crops
(understand this might be a bit of a stretch currently, but can we do it?);
Corn/soybeans no-till
Corn/soybeans with some form of intensive tillage - likely moldboard plow to
give us the worst case scenario

I may have another scenario or two tomorrow after I review my laptop notes
that are on my computer at home.

Thanks much and happy to answer any questions.


Tillage
-------
 - OpCropDef.FIEL0001 Field Cultivator
 - OpCropDef.CHISSTSP Chisel plow 8-inch
 - OpCropDef.TAND0002 Tandem Disk
 - OpCropDef.MOPL Molboard Plow
 - OpCropDef.ANHYDROS Anhydros
 - OpCropDef.CULTMUSW Row crop cultivator

Planting
--------
 - OpCropDef.CRNTFRRI NT Drill
 - OpCropDef.PLNTFC NT Planting
 - OpCropDef.PLDDO Conventional Planting

1. CC Notill (scenario: 18)
  - NT Planting
  - Anhydros in fall (1 Nov)
2. CS w/ cover conv (scenario: 19)
  - Conv Plant Corn
  - Harvest Corn
  - NT Drill (next day)  (zero GDD emergence)
  - Harvest Operation on cover
  - Chisel (-6 days)
  - tandem disk (-4 days)
  - field cultivate (-2 days)
  - Conv Plant Soy
  - Harvest Soy
  - NT Drill cover crop
  - Harvest Operation on cover
  - Anhydros (-4 days)
  - Chisel (-4 days)
  - field cultivate (-2 days)
3. CS conv (scenario: 20)
  - Conv Plant Corn
  - Harvest Corn 
  - Chisel (-6 days)
  - tandem disk (-4 days)
  - field cultivate (-2 days)
  - Conv Plant Soy
  - Harvest Soy
  - Anhydros (-4 days)
  - Chisel (-4 days)
  - field cultivate (-2 days)
4. CS plow (scenario: 21)
  - Conv Plant Corn
  - Harvest Corn
  - Fall Plow (+5 days)
  - tandem disk (-4 days)
  - field cultivate (-2 days)
  - Conv Plant Soy
  - Harvest Soy
  - Fall Plow (+5 days)
  - tandem disk (-4 days)
  - field cultivate (-2 days)
  - Anhydros (-4 days)
5. CS Notill (scenario: 22)
  - NT Planting Corn
  - Corn Harvest
  - NT Planting Soybean
  - Soybean harvest
  - Anhydros in fall (1 Nov)
6. CS w/cover notill (scenario: 23)
  - NT Plant Corn
  - Harvest Corn
  - NT Drill (next day)  (zero GDD emergence)
  - Harvest Operation on cover (-2 days)
  - NT Plant Soy
  - Harvest Soy
  - NT Drill (next day)  (zero GDD emergence)
  - Harvest Operation on cover (-2 days)
  - Anhydros (-4 days)
  
