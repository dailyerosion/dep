#
# Watershed project file modified: Wed Mar 14 12:07:51 AM 2001
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
      Head = (2158.414,1534.079)
      Tail = (1320.022,1774.894)
      Direction = -163.974
      Length = 868.680
      Width = 1.000
      Definition = "Dit_6695"
      Soil = "Or\bacona.sol"
      Profile = {
	73.9741  1.0000
	2  868.6800
	0, 0.05 1, 0.05 
	Segments = 1 20.000000 1 0.000000 1 0.000000
	1  868.679993 5.000000
      }
      Outlet = false
   }
   C2 {
      Head = (3219.783,1141.640)
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
      Head = (3014.644,410.277)
      Tail = (3219.783,1141.640)
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
      File = "Rome OR with Cattle Grazing_H1"  {
Landuse = 1
Length = 182.880
Profile {
   Data {
	343.9741  868.6800
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
   bacona       {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR cattle grazing.rot"
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
      Head = (1765.975,1739.218)
      Direction = -73.974
      Angle = 90.000
      Base = 868.680
      Height = 182.880
      Polygon =   5 {
            (2185.171143,1623.269897) (1346.778931,1855.165649) (1400.293335,2033.546875) (2229.766357,1792.732178) (2185.171143,1623.269897)
      }
   }
   H2 {
      File = "Rome OR with Cattle Grazing_H2"  {
Landuse = 1
Length = 182.880
Profile {
   Data {
	163.9741  868.6800
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
   bacona        {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR cattle grazing.rot"
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
      Head = (1712.461,1560.836)
      Direction = -253.974
      Angle = 90.000
      Base = 868.680
      Height = 182.880
      Polygon =   5 {
            (1293.264526,1676.784302) (2131.656738,1444.888550) (2078.142334,1266.507324) (1248.669189,1507.322021) (1293.264526,1676.784302)
      }
   }
   H3 {
      File = "Rome OR with Cattle Grazing_H3"  {
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
   bacona           {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR cattle grazing.rot"
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
      Head = (2657.882,1257.588)
      Direction = -249.708
      Angle = 90.000
      Base = 1127.760
      Height = 182.880
      Polygon =   5 {
            (2131.656738,1453.807617) (3184.106445,1061.368774) (3121.672852,891.906555) (2069.223145,1284.345459) (2131.656738,1453.807617)
      }
   }
   H4 {
      File = "Rome OR with Cattle Grazing_H4"  {
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
   bacona          {
      Distance = 182.880
      File = "Or\bacona.sol"
   }
}
Management {
   Breaks = 0
   Big Sacaton Grassland-Rome OR {
      Distance = 182.880
      File = "OR\Rome OR cattle grazing.rot"
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
      Head = (2711.396,1418.131)
      Direction = -69.708
      Angle = 90.000
      Base = 1127.760
      Height = 182.880
      Polygon =   5 {
            (3237.620850,1221.911987) (2185.171143,1614.350830) (2247.604492,1783.813110) (3300.054199,1391.374268) (3237.620850,1221.911987)
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
