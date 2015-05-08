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
 <link type="text/css" href="/css/ui-lightness/jquery-ui-1.8.22.custom.css" rel="stylesheet" />
 <link rel='stylesheet' href='/css/default/style.css' type='text/css'>
          <style type="text/css">
		#iem-footer { display: none; }
     .dp {
     border: 0px;
background: black;
color: white;
font-weight: bolder;
font-size: 1.3em;
width: 149px;
float: left;
     }
            html, body, #map {
                margin: 0;
                width: 100%;
                height: 100%;
            }
            #detailsContainer {
                position: absolute;
                bottom: 1em;
                right: 1em;
                width: 240px;
                z-index: 20001;
                background-color: #53675A;
                padding: 0.1em;
            }
            #details {
                background-color: #FFF;
                padding: 0.1em;
            }
            #controller {
                position: absolute;
                bottom: 0.5em;
                left: 0.5em;
                padding-right: 0.5em;
                background-color: #000;
                z-index: 20001;
                padding-left: 0.5em;
            }
            #ramp {
                position: absolute;
                bottom: 50px;
                left: 0.5em;
                background-color: #000;
                z-index: 20000;
                padding-left: 0.5em;
            }
        </style>
EOF;
$ddd = str_replace("-","/", $last_date);
$TMS_SERVER = TMS_SERVER;
$t->jsextra = <<<EOF
 <script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
 <script type="text/javascript" src="/js/jquery-ui-1.8.22.custom.min.js"></script>
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
<div id="detailsContainer">
	<div style="float: right; border: 1px solid #000;"><a href="javascript:hideDetails();">X</a></div>
	<div id="details">
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
</div>
<div id="controller">
	<form>
	<input type="text" name="date" id="datepicker" class="dp" />
	<a href="/">
	<span class="glyphicon glyphicon-home"></span>
	<span style="font-size: 1.3em; color:#FFF; font-weight:bolder;">Daily Erosion Project </span>
	</a>
	<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() - 0.1);" value="-"/>
	<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() + 0.1);" value="+"/>
	<input type="button" onclick="javascript: get_shapefile();" value="Get Shapefile"/>
	
	<br clear="both"/>&nbsp;<br />
	<div id="radio">
	<input type="radio" id="precip-in2_opt" name="radio" value="qc_precip" /><label for="precip-in2_opt">Precip</label>
		<!-- <input type="radio" id="precip-in_opt" name="radio" value="precip-in" /><label for="precip-in_opt">P.v1</label> -->
	    <input type="radio" id="delivery2_opt" name="radio" value="avg_delivery" checked="checked" /><label for="delivery2_opt">Delivery</label>
		<input type="radio" id="loss2_opt" name="radio" value="avg_loss" checked="checked" /><label for="loss2_opt">Detachment</label>
		<!-- <input type="radio" id="loss_opt" name="radio" value="avg_loss" /><label for="loss_opt">E.v1</label> -->
		<input type="radio" id="runoff2_opt" name="radio" value="avg_runoff" /><label for="runoff2_opt">Runoff</label>
		<!-- <input type="radio" id="runoff_opt" name="radio" value="avg_runoff" /><label for="runoff_opt">R.v1</label> -->
		<!--  <input type="radio" id="vsm_opt" name="radio" value="vsm2" /><label for="vsm_opt">Root Zone Soil Moisture</label>
		<input type="radio" id="sm10_opt" name="radio" value="sm102" /><label for="sm10_opt">0-4in Soil Moisture</label> 
		-->
	</div>
	</form>
</div>
<div id="ramp">
<img src="/images/avg_loss-ramp.png" id="rampimg" />
<br /> &nbsp; 
<br /> &nbsp; 
<br /> &nbsp; 
<br /> &nbsp; 
</div>
<div id="map"></div>
EOF;
$t->render('app.phtml');
?>
