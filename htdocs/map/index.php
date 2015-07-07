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
font-weight: bolder;
font-size: 1.3em;
width: 149px;
float: left;
     }
           #map {
		width: 100%;
            }
#colorbar {
	position: absolute;
	left: 1em;
	top: 8em;
	background: rgba(0,0,0,0.8);
	z-index: 3000;	
}
#maptitle {
	position: absolute;
	top: 0px;
	left: 5em;
	background: rgba(0,0,0,0.8);
	color: #FFF;
	font-weight: bold;
	font-size: 1.2em;
	padding-left: 20px;
	padding-right: 20px;
	z-index: 3000;
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
		date2: null,
		ltype: 'qc_precip'
};
        </script>
 <script src='nextgen.js?v=13'></script>
EOF;

$t->content = <<<EOF
<!-- Modal -->
<div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title" id="myModalLabel">Search for Watershed by Name</h4>
      </div>
      <div class="modal-body" onkeypress="return event.keyCode != 13;">
		<p>Enter some case-insensitive text to search for a watershed by name.</p>
      <form name="huc12search">
		<input type="text" name="q" id="huc12searchtext">
		<button type="button" class="btn btn-default" id="huc12searchbtn">
  <i class="glyphicon glyphicon-search"></i>
</button>
		</form>
		<hr />
		<div id="huc12searchres"></div>
		
	  </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>

<form>		
	<div class="row">
		<div class="col-md-6"></div>
		<div class="col-md-6"><h4 class="pull-right">Select IDEP Variable to View:</h4></div>
	</div>
<div class="row">
	<div class="col-md-6"><h3>DEP Interactive Map</h3></div>
	<div class="col-md-6">
		<div id="radio" class="pull-right">
		<input type="radio" id="precip-in2_opt" name="whichlayer" value="qc_precip" checked="checked"><label for="precip-in2_opt">Precipitation</label>
		<input type="radio" id="runoff2_opt" name="whichlayer" value="avg_runoff"><label for="runoff2_opt">Runoff</label>
		<input type="radio" id="loss2_opt" name="whichlayer" value="avg_loss"><label for="loss2_opt">Detachment</label>
		<input type="radio" id="delivery2_opt" name="whichlayer" value="avg_delivery"><label for="delivery2_opt">Delivery</label>
		</div>
		<br clear="all" />
		<div id="variable_desc" class="pull-right"></div>
	</div>
</div>
<div class="row">
<div class="col-md-9">
	<div id="map">
		<div id="maptitle">The Map Title</div>
		<canvas id="colorbar" width="75" height="300"></canvas>
	</div>
    <div clas="row">
		<div class="col-md-3">
			<h4>Days to Display</h4>
			<div id="t" class="pull-left">
			<input type="radio" id="single" name="t" value="single" checked="checked"><label for="single">Single</label>
			<input type="radio" id="multi" name="t" value="multi"><label for="multi">Multi</label>
			</div>
		</div>
		<div class="col-md-4">
			<h4>Date:</h4>
		<div class="input-group">
			<span class="input-group-btn"><button id="minus1d" class="btn btn-default" type="button"><i class="glyphicon glyphicon-arrow-left"></i></button></span>
		<input type="text" name="date" id="datepicker" class="form-control" style="font-weight: bolder;">
			<span class="input-group-btn"><button id="plus1d" class="btn btn-default" type="button"><i class="glyphicon glyphicon-arrow-right"></i></button></span>
		</div>
		<div style="display: none;" id="settoday"><a class="btn btn-default" role="button" href="javascript: setToday();"><i class="glyphicon glyphicon-chevron-left"></i> Back to Latest Date</a></div>
		</div>
		<div class="col-md-3" style="visibility: hidden;" id="dp2">
			<h4>To Date:</h4>
			<input type="text" name="date2" id="datepicker2" class="dp" />
		</div>
		<div class="col-md-2">
		<button type="button" class="btn btn-default" data-toggle="modal" data-target="#myModal">
  <i class="glyphicon glyphicon-search"></i>
</button>
		<!--
			<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() - 0.1);" value="-"/>
			<input type="button" onclick="javascript: tms.setOpacity(tms.getOpacity() + 0.1);" value="+"/>
		-->
			<input type="button" onclick="javascript: get_shapefile();" value="Get Shapefile"/>	
		</div>
	</div>
</div>
<div id="detailsContainer" class="col-md-3">
		<p><strong>Data for mouseover watershed</strong></p>
		<table class="table table-condensed table-bordered">
		<tr><th>HUC12</th><td><div id="info-huc12"></div></td></tr>
		<tr><th>Precipitation</th><td><div id="info-precip"></div></td></tr>
		<tr><th>Runoff</th><td><div id="info-runoff"></div></td></tr>
		<tr><th>Detachment</th><td><div id="info-loss"></div></td></tr>
		<tr><th>Delivery</th><td><div id="info-delivery"></div></td></tr>
		</table>
		<div id="clickDetails" class="well">
		<div id="details_loading" class="hidden"><img src="/images/wait24trans.gif" /> Loading...</div>
		<div id="details_details"></div>
		<div id="details_hidden">Click on a watershed to load detailed data</div>
		</div>
</div>
</div>

</form>

EOF;
$t->render('single.phtml');
?>
