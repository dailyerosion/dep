<?php 
require_once "../../config/settings.inc.php";
require_once "../../include/myview.php";
$dbconn = pg_connect("dbname=idep host=iemdb user=nobody");
$rs = pg_query($dbconn, "SELECT value from properties where key = 'last_date'");
$row = pg_fetch_assoc($rs, 0);
$last_date = $row['value'];

$lat = 42.22;
$lon = -95.489;
if (isset($_GET["huc_12"])){
	$huc12 = substr($_GET["huc_12"],0,12);
	$rs = pg_query($dbconn, "with d as "
		."(select ST_transform(st_centroid(geom),4326) as g from ia_huc12 "
		."where huc_12 = '$huc12') select st_x(d.g), st_y(d.g) from d");
	if (pg_num_rows($rs) == 1){
		$row = pg_fetch_assoc($rs,0);
		$lat = $row["st_y"];
		$lon = $row["st_x"];
	}
}

$t = new MyView();
$t->title = "Map Interface";
$t->headextra = <<<EOF
 <link type="text/css" href="/vendor/openlayers/3.5.0/ol.css" rel="stylesheet" />
 <link type="text/css" href="/vendor/openlayers/3.5.0/ol3-layerswitcher.css" rel="stylesheet" />
 <link type="text/css" href="/vendor/jquery-ui/1.11.4/jquery-ui.min.css" rel="stylesheet" />
 <link rel='stylesheet' href='/css/default/style.css' type='text/css'>
          <style type="text/css">
     .dp {
     border: 0px;
background: black;
color: white;
font-weight: bolder;
font-size: 1.3em;
width: 149px;
float: left;
     }
           #map {
                height: 100%;
            }
        </style>
EOF;
$ddd = str_replace("-","/", $last_date);
$TMS_SERVER = TMS_SERVER;
$t->jsextra = <<<EOF
 <script type="text/javascript" src="/vendor/jquery/1.11.3/jquery-1.11.3.min.js"></script>
 <script type="text/javascript" src="/vendor/jquery-ui/1.11.4/jquery-ui.min.js"></script>
 <script src='/vendor/openlayers/3.5.0/ol.js'></script>
 <script src='/vendor/openlayers/3.5.0/ol3-layerswitcher.js'></script>
        <script type="text/javascript">
var tilecache = "{$TMS_SERVER}";
var lastdate = new Date("{$ddd}");
var appstate = {
		lat: {$lat},
		lon: {$lon},
		date: null,
		ltype: 'avg_loss'
};
        </script>
 <script src='nextgen.js?v=8'></script>
EOF;

$t->content = <<<EOF
<form>


<h3>Daily Erosion Project Map Interface</h3>
		
	<div class="row">
		<div class="col-md-4">Displaying: <span id="mapdate"><b>Single Daily Event Output for </b></span>
		<br />Map Display Units: <span id="mapunits"><b>tons per acre</b></span></div>
		<div class="col-md-8"><h4 class="pull-right">Select IDEP Variable to View:</h4></div>
	</div>
<div class="row">
	<div class="col-md-4">
		<img src="/images/map-ramp.png" class="img img-responsive" />
	</div>
	<div class="col-md-8">
		<div id="radio" class="pull-right">
		<input type="radio" id="precip-in2_opt" name="whichlayer" value="qc_precip"><label for="precip-in2_opt">Precip</label>
	    <input type="radio" id="delivery2_opt" name="whichlayer" value="avg_delivery"><label for="delivery2_opt">Delivery</label>
		<input type="radio" id="loss2_opt" name="whichlayer" value="avg_loss" checked="checked"><label for="loss2_opt">Detachment</label>
		<input type="radio" id="runoff2_opt" name="whichlayer" value="avg_runoff"><label for="runoff2_opt">Runoff</label>
		</div>
	</div>
</div>
<div class="row">
<div id="detailsContainer" class="col-md-3 well">
		<p><strong>Mouseover Quick Data</strong></p>
		<table class="table table-condensed table-bordered">
		<tr><th>HUC12</th><td><div id="info-huc12"></div></td></tr>
		<tr><th>Delivery</th><td><div id="info-delivery"></div></td></tr>
		<tr><th>Detachment</th><td><div id="info-loss"></div></td></tr>
		<tr><th>Precipitation</th><td><div id="info-precip"></div></td></tr>
		<tr><th>Runoff</th><td><div id="info-runoff"></div></td></tr>
		</table>
		<p><strong>More Detailed Data</strong></p>
		<div id="details_loading" class="hidden"><img src="/images/wait24trans.gif" /> Loading...</div>
		<div id="details_details"></div>
		<div id="details_hidden">Click on HUC12 to load detailed data.</div>
</div>
<div class="col-md-9">
	<div id="map"></div>
	<div id="controller">
	<input type="text" name="date" id="datepicker" class="dp" />
	<input type="text" name="date2" id="datepicker2" class="dp" />
	<input type="button" id="enablerange" value="Enable Date Range" >
	<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() - 0.1);" value="-"/>
	<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() + 0.1);" value="+"/>
	<input type="button" onclick="javascript: get_shapefile();" value="Get Shapefile"/>	
</div>
		</div>
</div>

</form>

EOF;
$t->render('single.phtml');
?>
