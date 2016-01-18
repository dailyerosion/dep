<?php 
require_once "../../config/settings.inc.php";
$dbconn = pg_connect("dbname=idep host=iemdb user=nobody");
$rs = pg_query($dbconn, "SELECT value from properties where key = 'last_date_0'");
$row = pg_fetch_assoc($rs, 0);
$last_date = $row['value'];
$OL = "3.11.1";
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

?>
<html>
<head>
 <title>Daily Erosion Project:: Map Interface</title>
 <link type="text/css" href="/vendor/openlayers/3.11.1/ol.css" rel="stylesheet" />
 <link type="text/css" href="/vendor/openlayers/3.11.1/ol3-layerswitcher.css" rel="stylesheet" />
 <link type="text/css" href="/css/ui-lightness/jquery-ui-1.8.22.custom.css" rel="stylesheet" />
 <script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
 <script type="text/javascript" src="/js/jquery-ui-1.8.22.custom.min.js"></script>
 <script src='/vendor/openlayers/3.11.1/ol.js'></script>
 <script src='/vendor/openlayers/3.11.1/ol3-layerswitcher.js'></script>
 <link rel='stylesheet' 
  href='/css/default/style.css' type='text/css'>
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
        <script type="text/javascript">
var tilecache = "<?php echo TMS_SERVER; ?>";
var lastdate = new Date("<?php echo str_replace("-","/", $last_date); ?>");
var appstate = {
		lat: <?php echo $lat; ?>,
		lon: <?php echo $lon; ?>,
		date: null,
		ltype: 'loss2'
};
        </script>
 <script src='nextgen.js?v=7'></script>
</head>
<body>
<div id="detailsContainer">
	<div id="details">
		<div id="details_loading"><img src="/images/wait24trans.gif" /> Loading...</div>
		<div id="details_details"></div>
		<div id="details_hidden">Move icon on map to load again</div>
	</div>
</div>
<div id="controller">
	<form>
	<input type="text" name="date" id="datepicker" class="dp" />
	<span style="font-size: 1.3em; color:#FFF; font-weight:bolder;">Daily Erosion Project</span>
	<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() - 0.1);" value="-"/>
	<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() + 0.1);" value="+"/>
	<input type="button" onclick="javascript: zoom_iowa();" value="View Iowa"/>
	
	<br clear="both"/>&nbsp;<br />
	<div id="radio">
		<input type="radio" id="mrms_opt" name="radio" value="mrms-calday" /><label for="mrms_opt">MRMS</label>
	<input type="radio" id="precip-in2_opt" name="radio" value="precip-in2" /><label for="precip-in2_opt">Precip</label>
		<!-- <input type="radio" id="precip-in_opt" name="radio" value="precip-in" /><label for="precip-in_opt">P.v1</label> -->
	    <input type="radio" id="delivery2_opt" name="radio" value="delivery2" checked="checked" /><label for="delivery2_opt">Delivery</label>
		<input type="radio" id="loss2_opt" name="radio" value="loss2" checked="checked" /><label for="loss2_opt">Detachment</label>
		<!-- <input type="radio" id="loss_opt" name="radio" value="loss" /><label for="loss_opt">E.v1</label> -->
		<input type="radio" id="runoff2_opt" name="radio" value="runoff2" /><label for="runoff2_opt">Runoff</label>
		<!-- <input type="radio" id="runoff_opt" name="radio" value="runoff" /><label for="runoff_opt">R.v1</label> -->
		<!--  <input type="radio" id="vsm_opt" name="radio" value="vsm2" /><label for="vsm_opt">Root Zone Soil Moisture</label>
		<input type="radio" id="sm10_opt" name="radio" value="sm102" /><label for="sm10_opt">0-4in Soil Moisture</label> 
		-->
	</div>
	</form>
</div>
<div id="ramp">
<img src="/images/loss2-ramp.png" id="rampimg" />
<br /> &nbsp; 
<br /> &nbsp; 
<br /> &nbsp; 
<br /> &nbsp; 
</div>
<div id="map"></div>
</body>
</html>
