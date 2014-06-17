#
# Watershed project file modified: Wed Nov 22 09:11:42 AM 2000
#
Version = 99.1
Name = example
Comments {
    Default watershed
}
Climate {
   File = "weppdemo.cli"
}
Size = (1000,1000)
Units = Meters
Orientation = 0.000000
Scale = 1.000000
Image {
   File = "sample.jpg"
}
Channels {
   Number = 1
   C1 {
      Head = (419.000,577.000)
      Tail = (416.000,371.000)
      Direction = 90.834
      Length = 206.022
      Width = 2.787
      Definition = "WATERWAY"
      Soil = "ATHENA.sol"
      Profile = {
	179.1660  2.7870
	2  206.0220
	0, 0.05 1, 0.05 
	Segments = 1 20.000000 1 0.000000 1 0.000000
	1  206.022003 5.000000
      }
      Outlet = true
   }
}
Impoundments {
   Number = 0
}
Hillslopes {
   Number = 3
   H1 {
      File = "grass strip_H1"  {
Landuse = 1
Length = 127.424
Profile {
   Data {
	179.1660  148.0130
	8  127.4240
	0, 0 0.02344, 0.02 0.211, 0.02 0.2688, 0.09 0.5438, 0.09 0.6203, 0.03 0.9578, 0.03 1, 0.015 
	Segments = 3 20.000000 0 0.000000 0 0.000000
	1  29.867243 2.000000
	2  43.801590 9.000000
	3  53.755173 3.000000
   }
}
Climate {
   File = "weppdemo.cli"
}
Soil {
   Breaks = 0
   belmore {
      Distance = 127.424
      File = "belmore.sol"
   }
}
Management {
   Breaks = 0
   grass (continuous) {
      Distance = 127.424
      File = "grass.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (416.000,371.000)
      Direction = 90.834
      Angle = 90.000
      Base = 148.013
      Height = 127.424
      Polygon =   6 {
            (286.000000,357.000000) (427.000000,368.000000) (488.000000,341.000000) (489.000000,266.000000) (291.000000,266.000000)
            (286.000000,357.000000) 
      }
   }
   H2 {
      File = "corn_H2"  {
Landuse = 1
Length = 118.647
Profile {
   Data {
	89.1660  206.0220
	5  118.6470
	0, 0 0.2, 0.08 0.47, 0.01 0.72, 0.15 1, 0.005 
   }
}
Climate {
   File = "weppdemo.cli"
}
Soil {
   Breaks = 0
   Duncanon {
      Distance = 118.647
      File = "DUNCANON.sol"
   }
}
Management {
   Breaks = 0
   continuous corn - fall moldboard plow {
      Distance = 118.647
      File = "corn-fall moldboard plow.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (407.000,474.000)
      Direction = 180.834
      Angle = 90.000
      Base = 206.022
      Height = 118.647
      Polygon =   5 {
            (408.000000,577.000000) (406.000000,371.000000) (287.000000,373.000000) (290.000000,579.000000) (408.000000,577.000000)
      }
   }
   H3 {
      File = "fallow tilled_H3"  {
Landuse = 1
Length = 96.347
Profile {
   Data {
	269.1660  206.0220
	8  96.3470
	0, 0 0.02344, 0.02 0.211, 0.02 0.2688, 0.09 0.5438, 0.09 0.6203, 0.03 0.9578, 0.03 1, 0.015 
	Segments = 3 20.000000 0 0.000000 0 0.000000
	1  22.583019 2.000000
	2  33.118965 9.000000
	3  40.645016 3.000000
   }
}
Climate {
   File = "weppdemo.cli"
}
Soil {
   Breaks = 0
   belmore {
      Distance = 96.347
      File = "belmore.sol"
   }
}
Management {
   Breaks = 0
   fallow - tilled {
      Distance = 96.347
      File = "fallow tilled.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (427.000,474.000)
      Direction = 0.834
      Angle = 90.000
      Base = 206.022
      Height = 96.347
      Polygon =   5 {
            (426.000000,371.000000) (428.000000,577.000000) (525.000000,576.000000) (522.000000,370.000000) (426.000000,371.000000)
      }
   }
}
Network {
   C1 (H2, H3, H1,   0, 0, 0,   0, 0, 0)
}
RunOptions {
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   CalcMethod = 2
   LenWidthRatio = 1.000000
}
