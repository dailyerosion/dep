<?
//
// globals.php
// 
// These should be used in php code to make moving to other machines easier.
//
// September 2010
// Jim Frankenberger
// NSERL
//
//
// The following are _SESSION variables that are used at various places in the code:
// USE_ENG_UNITS -
// USE_FOREST_SOILS -
// USE_FOREST_LANDUSE -
// zone -
// verify -
// state -
// csa -
// mcl -
// xll -
// yll -
// xur -
// yur -
// imgext -
// width -
// height -
// zoom -
// outletX -
// outletY -
// user -
// year -
// SSURGO_QUERY_NEEDED -
// p_usesess -
// 
$myip = $_SERVER['REMOTE_ADDR'];
$globip = $_SERVER['SERVER_ADDR'];
if ($globip == "207.180.113.223")
   $website = "WSU";
else
   $website = "NSERL";

if (isset($_SESSION['USE_ENG_UNITS']))
   $globEngUnits = 1;
else
   $globEngUnits = 0;

if (isset($_SESSION['USE_FOREST_SOILS']))
   $globForestSoils = 1;
else
   $globForestSoils = 0;

if (isset($_SESSION['USE_FOREST_LANDUSE']))
   $globForestLanduse = 1;
else
   $globForestLanduse = 0;

if ($website == "NSERL") {
   $globtmpdir = "/var/www/localhost/tmp/";
   $globgisdir = "/var/www/localhost/ol/baer/data/";
   $globphpdir = "/var/www/localhost/ol/baer/";
   $globwebphp = "/ol/baer/";
   $mapserv = "http://milford.nserl.purdue.edu/cgi-bin/mapserv";
   $mapHeight = "700px";
   $mapWidth = "900px";
   $globConnectString = "host=localhost dbname=wepp user=postgres";
   $globStaticMap = "/var/www/localhost/ol/baer/ol_static_google.map";
   $globGoogleKey = "key=ABQIAAAAB4wr-mZMnUM4r9Uf8el7XBQvjeXz85W64rbjoFohwMVicFZJghSYzfVC13q6SpLST7XLXLOCgV6Aqg";
   $globPythonBin = "/usr/local/bin/";
   $globWorkRoot = "/home/wepp/";
   $globWebAlias = "/wepprun/";
   $globUnits = 0;
} else {
   $globtmpdir = "/var/www/weppwsu/tmp/";
   $globgisdir = "/var/www/weppwsu/baer/data/";
   $globphpdir = "/var/www/weppwsu/test-baer/";
   $globwebphp = "/test-baer/";
   $mapserv = "http://207.180.113.223/cgi-bin/mapserv";
   $mapHeight = "600px";
   $mapWidth = "800px";
   $globConnectString = "dbname=wepp user=wepp password=wepppw";
   $globStaticMap = "/var/www/weppwsu/test-baer/ol_static_google.map";
   $globGoogleKey = "key=ABQIAAAAA6j-9Ju6sVyjjDNgtinSFBRSIWSpeLtbSHhuUfQFx6oJXkbiQBSXVAPvBQb1tQL54XzS2MFyxwvAJQ";
   $globPythonBin = "/usr/bin/";
   if ($myip == "134.121.201.72") {
	  $globWorkRoot = "/home/wepp/"; 
   }else{
   //$globWorkRoot = "/dev/shm/";
   $globWorkRoot = "/home/wepp/";
   }
   //$globWebAlias = "/wepprunMem/";
   $globWebAlias = "/wepprun/";
   $globUnits = 0;
}
?>
