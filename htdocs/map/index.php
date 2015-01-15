<?php 
require_once "../../config/settings.inc.php";
$dbconn = pg_connect("dbname=idep host=iemdb user=nobody");
$rs = pg_query($dbconn, "SELECT value from properties where key = 'last_date'");
$row = pg_fetch_assoc($rs, 0);
$last_date = $row['value'];
?>
<html>
<head>
 <link type="text/css" href="http://mesonet.agron.iastate.edu/assets/openlayers/3.1.1/css/ol.css" rel="stylesheet" />
 <link type="text/css" href="http://mesonet.agron.iastate.edu/assets/openlayers/3.1.1/css/ol3-layerswitcher.css" rel="stylesheet" />
 <link type="text/css" href="/css/ui-lightness/jquery-ui-1.8.22.custom.css" rel="stylesheet" />
 <script type="text/javascript" src="/js/jquery-1.7.2.min.js"></script>
 <script type="text/javascript" src="/js/jquery-ui-1.8.22.custom.min.js"></script>
 <script src="http://maps.google.com/maps/api/js?v=3&amp;sensor=false"></script>
 <script src='http://mesonet.agron.iastate.edu/assets/openlayers/3.1.1/build/ol.js'></script>
 <script src='http://mesonet.agron.iastate.edu/assets/openlayers/3.1.1/build/ol3-layerswitcher.js'></script>
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
        </script>
 <script src='nextgen.js?v=6'></script>
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
	<span style="font-size: 1.3em; color:#FFF; font-weight:bolder;">Iowa Daily Erosion Project</span>
	<input type="button" onclick="javascript: tms.setOpacity(tms.opacity - 0.1);" value="-"/>
	<input type="button" onclick="javascript: tms.setOpacity(tms.opacity + 0.1);" value="+"/>
	<input type="button" onclick="javascript: zoom_iowa();" value="View Iowa"/>
	
	<br clear="both"/>&nbsp;<br />
	<div id="radio">
		<input type="radio" id="precip-in2_opt" name="radio" value="mrms-calday" /><label for="precip-in2_opt">Precipitation</label>
		<!-- <input type="radio" id="precip-in_opt" name="radio" value="precip-in" /><label for="precip-in_opt">P.v1</label> -->
	    <input type="radio" id="delivery2_opt" name="radio" value="delivery2" checked="checked" /><label for="delivery2_opt">Delivery</label>
		<input type="radio" id="loss2_opt" name="radio" value="loss2" checked="checked" /><label for="loss2_opt">Erosion</label>
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
