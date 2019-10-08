Timing of Tillage Work
======================

Covered by [GH 67](https://github.com/dailyerosion/dep/issues/67).

The request was to pick 3 random HUC12s within Iowa's 10 MLRAs.  Here's the SQL query that picked those out.  This totaled 3,707 flowpaths.  For the constant climate file runs, random climate file in central Iowa of `/i/0/cli/093x042/093.91x042.11.cli` was picked.

    with data as (select mlra_id, huc_12, random() from huc12 where scenario = 0 and states = 'IA'), agg as (select mlra_id, huc_12, rank() OVER (PARTITION by mlra_id ORDER by random DESC) from data) select huc_12 from agg WHERe rank < 4 ORDER by mlra_id, huc_12;

DEP Scenarios Allocated
-----------------------

ID | Name | Status
-- | -- | --
59 | April 10 Tillage, Constant Climate | done
60 | April 15 Tillage, Constant Climate | done
61 | April 20 Tillage, Constant Climate | done
62 | April 25 Tillage, Constant Climate | done
63 | April 30 Tillage, Constant Climate | done
64 | May 5 Tillage, Constant Climate | done
65 | May 10 Tillage, Constant Climate | done
66 | May 15 Tillage, Constant Climate | done
67 | May 20 Tillage, Constant Climate | done
68 | May 25 Tillage, Constant Climate | done
69 | May 30 Tillage, Constant Climate | done
70 | April 10 Tillage, Local Climate | done
71 | April 15 Tillage, Local Climate | done
72 | April 20 Tillage, Local Climate | done
73 | April 25 Tillage, Local Climate | done
74 | April 30 Tillage, Local Climate | done
75 | May 5 Tillage, Local Climate | done
76 | May 10 Tillage, Local Climate | done
77 | May 15 Tillage, Local Climate | done
78 | May 20 Tillage, Local Climate | done
79 | May 25 Tillage, Local Climate | done
80 | May 30 Tillage, Local Climate | done
81 | Dynamic Tillage April 15 after 45% | done
82 | Dynamic Tillage April 15 after 40% | done
83 | Dynamic Tillage April 15 after 35% | done
84 | Dynamic Tillage April 15 after 30% | done
85 | Dynamic Tillage April 15 after 25% | done
86 | Dynamic Tillage April 15 after 20% | done
87 | Dynamic Tillage April 15 after 15% | done
88 | Dynamic Tillage April 15 after Plastic Limit 1.0 | done
89 | Dynamic Tillage April 15 after Plastic Limit 0.9 | done
90 | Dynamic Tillage April 15 after Plastic Limit Fx | done
