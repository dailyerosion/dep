#
# Watershed project file modified: Wed Mar 14 12:08:45 AM 2001
#
Version = 99.1
Name = example
Comments {
    Default watershed
}
Climate {
   File = "Oregon\Rome OR.cli"
}
Size = (1000,1000)
Units = Meters
Orientation = 0.000000
Scale = 8.919065
Image {
   File = "rome topo.jpg"
}
Channels {
   Number = 3
   C1 {
      Head = (2149.495,1534.079)
      Tail = (1320.022,1774.894)
      Direction = -163.811
      Length = 868.680
      Width = 1.000
      Definition = "Dit_6695"
      Soil = "Or\bacona.sol"
      Profile = {
	73.8108  1.0000
	2  868.6800
	0, 0.05 1, 0.05 
	Segments = 1 20.000000 1 0.000000 1 0.000000
	1  868.679993 5.000000
      }
      Outlet = false
   }
   C2 {
      Head = (3210.864,1141.640)
      Tail = (2167.333,1560.836)
      Direction = -159.708
      Length = 1127.760
      Width = 1.000
      Definition = "Dit_6695"
      Soil = "Or\bacona.sol"
      Profile = {
	69.7080  1.0000
	2  1127.7600
	0, 0.027 1, 0.027 
	Segments = 1 20.000000 1 0.000000 1 0.000000
	1  1127.760010 2.700000
      }
      Outlet = true
   }
   C3 {
      Head = (3005.725,410.277)
      Tail = (3210.864,1141.640)
      Direction = -74.389
      Length = 762.000
      Width = 1.000
      Definition = "Dit_6695"
      Soil = "Or\bacona.sol"
      Profile = {
	344.3890  1.0000
	2  762.0000
	0, 0.008 1, 0.008 
	Segments = 1 20.000000 1 0.000000 1 0.000000
	1  762.000000 0.800000
      }
      Outlet = true
   }
}
Impoundments {
   Number = 0
}
Hillslopes {
   Number = 4
   H1 {
      File = "Rome OR with Sheep Grazing_H1"  {
Landuse = 1
Length = 182.880
Profile {
   Data {
	343.8108  868.6800
	3  182.8800
	0, 0 0.1, 0.1 1, 0.1 
	Segments = 1 20.000000 0 0.000000 1 0.000000
	1  182.880005 10.000000
   }
}
Climate {
   File = "Oregon\Rome OR.cli"
}
Soil {
   Breaks = 0
   bacona         {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR sheep grazing.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   SoilFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (1757.056,1739.218)
      Direction = -73.811
      Angle = 90.000
      Base = 868.680
      Height = 182.880
      Polygon =   5 {
            (2176.251953,1614.350830) (1337.859863,1864.084717) (1391.374268,2033.546875) (2220.847412,1792.732178) (2176.251953,1614.350830)
      }
   }
   H2 {
      File = "Rome OR with Sheep Grazing_H2"  {
Landuse = 1
Length = 182.880
Profile {
   Data {
	163.8108  868.6800
	3  182.8800
	0, 0 0.1, 0.12 1, 0.12 
	Segments = 1 20.000000 0 0.000000 1 0.000000
	1  182.880005 12.000000
   }
}
Climate {
   File = "Oregon\Rome OR.cli"
}
Soil {
   Breaks = 0
   bacona          {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR sheep grazing.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   SoilFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (1703.542,1560.836)
      Direction = -253.811
      Angle = 90.000
      Base = 868.680
      Height = 182.880
      Polygon =   5 {
            (1284.345459,1685.703369) (2122.737549,1435.969482) (2069.223145,1266.507324) (1239.750122,1507.322021) (1284.345459,1685.703369)
      }
   }
   H3 {
      File = "Rome OR with Sheep Grazing_H3"  {
Landuse = 1
Length = 182.880
Profile {
   Data {
	159.7080  1127.7600
	3  182.8800
	0, 0 0.1, 0.03 1, 0.03 
	Segments = 1 20.000000 0 0.000000 1 0.000000
	1  182.880005 3.000000
   }
}
Climate {
   File = "Oregon\Rome OR.cli"
}
Soil {
   Breaks = 0
   bacona                    {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR sheep grazing.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   SoilFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (2648.962,1248.669)
      Direction = -249.708
      Angle = 90.000
      Base = 1127.760
      Height = 182.880
      Polygon =   5 {
            (2122.737549,1444.888550) (3175.187256,1052.449707) (3112.753906,882.987488) (2060.304199,1275.426392) (2122.737549,1444.888550)
      }
   }
   H4 {
      File = "Rome OR with Sheep Grazing_H4"  {
Landuse = 1
Length = 182.880
Profile {
   Data {
	339.7080  1127.7600
	3  182.8800
	0, 0 0.1, 0.04 1, 0.04 
	Segments = 1 20.000000 0 0.000000 1 0.000000
	1  182.880005 4.000000
   }
}
Climate {
   File = "Oregon\Rome OR.cli"
}
Soil {
   Breaks = 0
   bacona                      {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR sheep grazing.rot"
   }
}
RunOptions {
   Version = 1
   HillSlopePassFile = AutoName
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   SoilFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   SmallEventByPass = 1
}
      }
      Head = (2702.477,1409.212)
      Direction = -69.708
      Angle = 90.000
      Base = 1127.760
      Height = 182.880
      Polygon =   5 {
            (3228.701660,1212.992920) (2176.251953,1605.431763) (2238.685547,1774.894043) (3291.135254,1382.455200) (3228.701660,1212.992920)
      }
   }
}
Network {
   C1 (H1, H2, 0,   0, 0, 0,   0, 0, 0)
   C2 (H4, H3, 0,   0, 0, C1,   0, 0, 0)
   C3 (0, 0, 0,   0, 0, C2,   0, 0, 0)
}
RunOptions {
   SoilLossOutputType = 1
   SoilLossOutputFile = AutoName
   PlotFile = AutoName
   SimulationYears = 2
   CalcMethod = 2
   LenWidthRatio = 1.000000
}
