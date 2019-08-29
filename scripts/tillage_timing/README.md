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
63 | April 30 Tillage, Constant Climate | -
64 | May 5 Tillage, Constant Climate | -
65 | May 10 Tillage, Constant Climate | -
66 | May 15 Tillage, Constant Climate | -
67 | May 20 Tillage, Constant Climate | -
68 | May 25 Tillage, Constant Climate | -
69 | May 30 Tillage, Constant Climate | -
