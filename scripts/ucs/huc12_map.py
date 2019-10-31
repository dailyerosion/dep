"""Map."""
import sys

from pyiem.plot import MapPlot
from pyiem.util import get_dbconn
from shapely.wkb import loads
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.colors as mpcolors
import matplotlib.pyplot as plt

DBCONN = get_dbconn("idep")
cursor = DBCONN.cursor()

scenario = int(sys.argv[1])
titles2 = {10: "4", 11: "3", 7: "4", 9: "3"}
nt = {10: "(no-till)", 11: "(no-till)"}
threshold = 2
m = MapPlot(
    sector="iowa",
    axisbg="white",
    nologo=True,
    subtitle="1 Jan 2008 thru 31 Dec 2015",
    title=("UCS %s Year %s Scenario Change in Soil Delivery " "from Baseline")
    % (titles2[scenario], nt.get(scenario, "")),
)

cursor.execute(
    """
with baseline as (
    SELECT huc_12, sum(avg_delivery) * 4.463 as loss from results_by_huc12
    where valid between '2008-01-01' and '2016-01-01' and
    scenario = 0 GROUP by huc_12),
scenario as (
    SELECT huc_12, sum(avg_delivery) * 4.463 as loss from results_by_huc12
    where valid between '2008-01-01' and '2016-01-01' and
    scenario = %s GROUP by huc_12),
agg as (
    SELECT b.huc_12, b.loss as baseline_loss, s.loss as scenario_loss from
    baseline b LEFT JOIN scenario s on (b.huc_12 = s.huc_12))

 SELECT ST_Transform(simple_geom, 4326),
 (scenario_loss  - baseline_loss) / 8.0 as val, i.huc_12
 from huc12 i JOIN agg d on (d.huc_12 = i.huc_12)
 WHERE i.states ~* 'IA' ORDER by val DESC

""",
    (scenario,),
)

# bins = np.arange(0, 101, 10)
bins = [-25, -10, -5, -2, 0, 2, 5, 10, 25]
cmap = plt.get_cmap("BrBG_r")
cmap.set_under("purple")
cmap.set_over("black")
norm = mpcolors.BoundaryNorm(bins, cmap.N)
patches = []

for row in cursor:
    polygon = loads(row[0].decode("hex"))
    a = np.asarray(polygon.exterior)
    x, y = m.map(a[:, 0], a[:, 1])
    a = zip(x, y)
    c = cmap(norm([float(row[1])]))[0]
    p = Polygon(a, fc=c, ec="None", zorder=2, lw=0.1)
    patches.append(p)

m.ax.add_collection(PatchCollection(patches, match_original=True))
m.draw_colorbar(bins, cmap, norm, units="T/a")

m.drawcounties()
m.postprocess(filename="test.png")
