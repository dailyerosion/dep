var map;
var vectorLayer;
var iaextent;
var scenario = 0;
var myDateFormat = 'M d, yy';
var geojsonFormat = new ol.format.GeoJSON();
var quickFeature;
var detailedFeature;
var detailedFeatureIn;
var hoverOverlayLayer;
var clickOverlayLayer;
var defaultCenter = ol.proj.transform([-94.5, 40.1], 'EPSG:4326', 'EPSG:3857');
var defaultZoom = 6;
var popup;
var IDLE = "Idle";

var levels = [];
var colors = {
  'qc_precip': ['#ffffa6', '#9cf26d', '#76cc94', '#6399ba', '#5558a1', '#c34dee'],     
  'avg_runoff': ['#ffffa6', '#9cf26d', '#76cc94', '#6399ba', '#5558a1', '#c34dee'],
  'avg_loss': ['#cbe3bb', '#c4ff4d', '#ffff4d', '#ffc44d', '#ff4d4d', '#c34dee'],
  'avg_delivery': ['#ffffd2', '#ffff4d', '#ffe0a5', '#eeb74d', '#ba7c57', '#96504d']
};

/*
var colors = ['rgba(0, 0, 255, 1)',

			  'rgba(0, 212, 255, 1)',

			  'rgba(102, 255, 153, 1)',

			  'rgba(204, 255, 0, 1)',

			  'rgba(255, 232, 0, 1)',

			  'rgba(255, 153, 0, 1)'];
*/

var vardesc = {
	avg_runoff: 'Runoff is the average amount of water that left the hillslopes via above ground transport.',
	avg_loss: 'Soil Detachment is the average amount of soil disturbed on the modelled hillslopes.',
	qc_precip: 'Precipitation is the average amount of rainfall and melted snow received on the hillslopes.',
	avg_delivery: 'Delivery is the average amount of soil transported to the bottom of the modelled hillslopes.',
}

var varunits = {
	avg_runoff: 'inches',
	avg_loss: 'tons per acre',
	qc_precip: 'inches',
	avg_delivery: 'tons per acre'
};
var vartitle = {
	avg_runoff: 'Water Runoff',
	avg_loss: 'Soil Detachment',
	qc_precip: 'Total Precipitation',
	avg_delivery: 'Soil Delivery'
};
function formatDate(fmt, dt){
	return $.datepicker.formatDate(fmt, dt)
}

function makeDate(year, month, day){
	var s = month+"/"+day+"/"+year;
	return (new Date(s));
}
// Update the status box on the page with the given text
function setStatus(text){
	$('#status').html(text);
}

// Check the server for updated run information
function checkDates(){
	setStatus("Checking for new data.");
	$.ajax({
		url: '/geojson/timedomain.py?scenario=0',
		fail: function(jqXHR, textStatus){
			setStatus("New data check failed "+ textStatus);
		},
		success: function(data){
			setStatus(IDLE);
			if (data['last_date']){
				// Avoid ISO -> Badness
				var s = data['last_date'];
				var newdate = makeDate(s.substr(0,4), s.substr(5,2),
								s.substr(8,2))
				if (newdate > appstate.lastdate){
					appstate.lastdate = newdate;
					$('#datepicker').datepicker("change",
						{maxDate: formatDate(myDateFormat, newdate)});
					$('#datepicker2').datepicker("change",
							{maxDate: formatDate(myDateFormat, newdate)});
					$('#newdate-thedate').html(formatDate(myDateFormat,
														newdate));
				    $( "#newdate-message" ).dialog({
				        modal: true,
				        buttons: [{
				        	text: 'Show Data!',
				        	icons: {
				            	primary: "ui-icon-heart"
				          	},
				          	click: function() {
				          		setDate(appstate.lastdate.getFullYear(),
				          				appstate.lastdate.getMonth()+1,
				          				appstate.lastdate.getDate());
				                $( this ).dialog( "close" );
				              }
				        }, {
				        	text: 'Ok',
				          	click: function() {
				                $( this ).dialog( "close" );
				              }
				        }]
				      });
				}				
			}
			
		}
	});
}

// Sets the permalink stuff
// date/date2/ltype/lon/lat/zoom
function setWindowHash(){
	var hash = "";
	if (appstate.date && appstate.date != 'Invalid Date'){
		hash += formatDate("yymmdd", appstate.date);
	}
	hash += "/";
	if (appstate.date2 && appstate.date2 != 'Invalid Date'){
		hash += formatDate("yymmdd", appstate.date2)
	}
	hash += "/"+ appstate.ltype+"/";
	var center = map.getView().getCenter();
	center = ol.proj.transform(center, 'EPSG:3857', 'EPSG:4326'),
	hash += center[0].toFixed(2)+"/"+ center[1].toFixed(2) +"/"+ map.getView().getZoom()+"/";
	if (detailedFeature){
		hash += detailedFeature.getId();
	}
	window.location.hash = hash;
}

// Reads the hash and away we go!
function readWindowHash(){
	var tokens = window.location.hash.split("/");
	// careful, we have the # char here to deal with
	if (tokens.length > 0 && tokens[0] != '' &&
		tokens[0] != '#' && tokens[0] != '#NaNNaNNaN'){
		appstate.date = makeDate(tokens[0].substr(1,4), tokens[0].substr(5,2),
									tokens[0].substr(7,2));
	}
	if (tokens.length > 1 && tokens[1] != '' && tokens[1] != 'NaNNaNNaN'){
		appstate.date2 = makeDate(tokens[1].substr(0,4), tokens[1].substr(4,2),
									tokens[1].substr(6,2));
	}
	if (tokens.length > 2 && tokens[2] != ''){
		appstate.ltype = tokens[2];
		$( '#radio input[value='+tokens[2]+']').prop('checked', true);
	}
	if (tokens.length > 5 && tokens[3] != '' && tokens[4] != '' &&
		tokens[5] != ''){
		defaultCenter = ol.proj.transform([parseFloat(tokens[3]), parseFloat(tokens[4])], 'EPSG:4326', 'EPSG:3857');
		defaultZoom = parseFloat(tokens[5]);
	}
	if (tokens.length > 6 && tokens[6].length == 12){
		detailedFeatureIn = tokens[6];
	}
	
}

// Sets the date back to today
function setToday(){
	setDate(appstate.lastdate.getFullYear(),
		appstate.lastdate.getMonth()+1,
		appstate.lastdate.getDate());
	$('#settoday').css('display', 'none');
}
// Sets the title shown on the page for what is being viewed
function setTitle(){
	dt = formatDate(myDateFormat, appstate.date);
	dtextra = (appstate.date2 === null) ? '': ' to '+formatDate(myDateFormat, appstate.date2);
	$('#maptitle').html(vartitle[appstate.ltype] +" ["+
			varunits[appstate.ltype] +"] for "+ dt +" "+ dtextra);
	$('#variable_desc').html(vardesc[appstate.ltype]);
}

// When user clicks the "Get Shapefile" Button
function get_shapefile(){
	dt = formatDate("yy-mm-dd", appstate.date);
	var uri = '/dl/shapefile.py?dt='+dt;
	if (appstate.date2 !== null){
		uri = uri + '&dt2='+ formatDate("yy-mm-dd", appstate.date2);
	}
	window.location.href = uri;
}

function setType(t){
	$('#'+ t +'_opt').click();
}

function hideDetails(){
	$('#details_hidden').css('display', 'block');
	$('#details_details').css('display', 'none');
	$('#details_loading').css('display', 'none');
}

function updateDetails(huc12){
	$('#details_hidden').css('display', 'none');
	$('#details_details').css('display', 'none');
	$('#details_loading').css('display', 'block');
	setStatus("Loading detailed information for HUC12: "+ huc12);
    $.get('nextgen-details.php', {
    	huc12: huc12,
		date: formatDate("yy-mm-dd", appstate.date),
		date2: formatDate("yy-mm-dd", appstate.date2)
		},
		function(data){
			$('#details_details').css('display', 'block');
			$('#details_loading').css('display', 'none');
			$('#details_details').html(data);
			setStatus(IDLE);
	});

}

function getGeoJSONURL(){
	// Generate the TMS URL given the current settings
	var uri = '/geojson/huc12.py?date='+formatDate("yy-mm-dd", appstate.date);
	if (appstate.date2 !== null){
		uri = uri + "&date2="+ formatDate("yy-mm-dd", appstate.date2);
	} 
	return uri;
}
function rerender_vectors(){
	levels = [];
	//console.log("rerender_vectors() called");
	vectorLayer.changed();
	setWindowHash();
	setTitle();
}

function remap(){
	// console.log("remap() called"+ detailedFeature);
	if (appstate.date2 != null && appstate.date2 <= appstate.date){
		setStatus("Please ensure that 'To Date' is later than 'Date'");
		return;
	}
	setStatus("Fetching new data to display...");
	levels = [];
	var newsource = new ol.source.Vector({
		url: getGeoJSONURL(),
		format: geojsonFormat
	});
	// We should replace the detailed feature with new information, so that
	// the mouseover does not encounter this old information
	newsource.on('change', function(){
		if (detailedFeature){
			clickOverlayLayer.getSource().removeFeature(detailedFeature);
			detailedFeature = vectorLayer.getSource().getFeatureById(detailedFeature.getId());
			clickOverlayLayer.getSource().addFeature(detailedFeature);
		}
		drawColorbar();
		setStatus(IDLE);
	});
	vectorLayer.setSource(newsource);
	setTitle();
	if (detailedFeature){
		updateDetails(detailedFeature.getId());
	}
	setWindowHash();
}
function setYearInterval(syear){
	$('#eventsModal').modal('hide');
	
	appstate.date = makeDate(syear, 1, 1);
	appstate.date2 = makeDate(syear, 12, 31);
	$('#datepicker').datepicker("setDate", formatDate(myDateFormat,
	appstate.date));
	$('#datepicker2').datepicker("setDate", formatDate(myDateFormat,
	appstate.date2));
	$('#multi').prop('checked', true).button('refresh');
	remap();
	$("#dp2").css('visibility', 'visible');
}

function setDateFromString(s){
	$('#eventsModal').modal('hide');
	var dt = (new Date(s));
	setDate(formatDate('yy', dt),
		formatDate('mm', dt),
		formatDate('dd', dt));
}

function setDate(year, month, day){
	appstate.date = makeDate(year, month, day);
	$('#datepicker').datepicker("setDate", formatDate(myDateFormat,
													appstate.date));
	// Called from top 10 listing, so disable the period
	$('#single').prop('checked', true).button('refresh');
	appstate.date2 = null;
	$("#dp2").css('visibility', 'hidden');
	remap();
}
function zoom_iowa(){
    map.zoomToExtent(iaextent);
}

function make_iem_tms(title, layername, visible){
	return new ol.layer.Tile({
		title : title,
		visible: visible,
		source : new ol.source.XYZ({
			url : tilecache +'/c/tile.py/1.0.0/'+layername+'/{z}/{x}/{y}.png'
		})
	})
}
function setHUC12(huc12){
	feature = vectorLayer.getSource().getFeatureById(huc12);
	makeDetailedFeature(feature);
	jQuery.noConflict();
	$('#myModal').modal('hide');
}

function makeDetailedFeature(feature){
	if (feature == null){
		return;
	}

	if (feature != detailedFeature){
		if (detailedFeature){
			detailedFeature.set('clicked', false);
			clickOverlayLayer.getSource().removeFeature(detailedFeature);
		}
		if (feature){
			clickOverlayLayer.getSource().addFeature(feature);
		}
		detailedFeature = feature;
	}
	updateDetails(feature.getId());
	setWindowHash();
}

// View daily or yearly output for a HUC12
function viewEvents(huc12, mode){
	function pprint(val, mode){
		if (val == null) return "0";
		return val.toFixed(2);
	}
	var lbl = ((mode == 'daily') ? 'Daily events': 'Yearly summary');
	$('#eventsModalLabel').html(lbl + " for " + huc12);
	$('#eventsres').html('<p><img src="/images/wait24trans.gif" /> Loading...</p>');
	$.ajax({
		method: 'GET',
		url: '/geojson/huc12_events.py',
		data: {huc12: huc12, mode: mode}
	}).done(function(res){
		var myfunc = ((mode == 'yearly')? 'setYearInterval(': 'setDateFromString(');
		var tbl = "<table class='table table-striped header-fixed'><thead><tr><th>Date</th><th>Precip [inch]</th><th>Runoff [inch]</th><th>Detach [t/a]</th><th>Delivery [t/a]</th></tr></thead>";
		$.each(res.results, function(idx, result){
			var dt = ((mode == 'daily')? result.date: result.date.substring(6,10));
			tbl += "<tr><td><a href=\"javascript: "+ myfunc +"'"+ dt +"');\">"+ dt +"</a></td><td>"+ pprint(result.qc_precip) +"</td><td>"+ pprint(result.avg_runoff) +"</td><td>"+ pprint(result.avg_loss) +"</td><td>"+ pprint(result.avg_delivery) +"</td></tr>";
		});
		tbl += "</table>";
		$('#eventsres').html(tbl);
	}).fail(function(res){
		$('#eventsres').html("<p>Something failed, sorry</p>");
	});
	
}

function doHUC12Search(){
	$('#huc12searchres').html('<p><img src="/images/wait24trans.gif" /> Searching...</p>');
	var txt = $('#huc12searchtext').val();
	$.ajax({
		method: 'GET',
		url: '/geojson/hsearch.py',
		data: {q: txt}
	}).done(function(res){
		var tbl = "<table class='table table-striped'><thead><tr><th>ID</th><th>Name</th></tr></thead>";
		$.each(res.results, function(idx, result){
			tbl += "<tr><td><a href=\"javascript: setHUC12('"+ result.huc_12 +"');\">"+ result.huc_12 +"</a></td><td>"+ result.name +"</td></tr>";
		});
		tbl += "</table>";
		$('#huc12searchres').html(tbl);
	}).fail(function(res){
		$('#huc12searchres').html("<p>Search failed, sorry</p>");
	});
}

function changeMapHeight(delta){
	var sz = map.getSize();
	map.setSize([sz[0], sz[1] + (sz[1] * delta)]);
}


function drawColorbar(){
	//console.log("drawColorbar called...");
    var canvas = document.getElementById('colorbar');
    var ctx = canvas.getContext('2d');
    
    canvas.height = colors[appstate.ltype].length * 20 + 50;
    
    // Clear out the canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.font = 'bold 12pt Calibri';
    ctx.fillStyle = 'white';
    var metrics = ctx.measureText('Legend');
    ctx.fillText('Legend', (canvas.width / 2) - (metrics.width / 2), 14);
    
    var pos = 20;
    $.each(levels, function(idx, level){
    	if (idx == (levels.length - 1)){
    	    var txt = "Max: "+ level.toFixed(2);
    	    ctx.font = 'bold 10pt Calibri';
    	    ctx.fillStyle = 'yellow';
    	    metrics = ctx.measureText(txt);
    	    ctx.fillText(txt, (canvas.width / 2) - (metrics.width / 2), 32);
    	
    	    // All zeros
    	    if (idx == 0){
        	    var txt = "All Zeros";
        	    ctx.font = 'bold 10pt Calibri';
        	    ctx.fillStyle = 'white';
        	    metrics = ctx.measureText(txt);
        	    ctx.fillText(txt, (canvas.width / 2) - (metrics.width / 2), 50);
    	    }
    	    
    		return;
    	}
    	
        ctx.beginPath();
        ctx.rect(5, canvas.height - pos - 10, 20, 20);
        ctx.fillStyle = colors[appstate.ltype][idx];
        ctx.fill();

        ctx.font = 'bold 12pt Calibri';
        ctx.fillStyle = 'white';
        var leveltxt = level.toFixed(2);
        if (level == 0.001){
        	leveltxt = 0.001;
        }
        metrics = ctx.measureText(leveltxt);
        ctx.fillText(leveltxt, 45 - (metrics.width/2), canvas.height - (pos-20) -4);

        pos = pos + 20;
    });

}

function popupFeatureInfo(evt){
	
	  var feature = map.forEachFeatureAtPixel(map.getEventPixel(evt.originalEvent), function(feature, layer) {
        return feature;
      });
	
	  var element = popup.getElement();
	  if (feature){
		  popup.setPosition(evt.coordinate);
		  var h = '<table class="table table-condensed table-bordered">';
		  h += '<tr><th>HUC12</th><td>'+feature.getId()+'</td></tr>';
		  h += '<tr><th>Precipitation</th><td>'+ feature.get('qc_precip').toFixed(2) + ' in</td></tr>';
		  h += '<tr><th>Runoff</th><td>'+ feature.get('avg_runoff').toFixed(2) + ' in</td></tr>';
		  h += '<tr><th>Detachment</th><td>'+ feature.get('avg_loss').toFixed(2) + ' T/a</td></tr>';
		  h += '<tr><th>Delivery</th><td>'+ feature.get('avg_delivery').toFixed(2) + ' T/a</td></tr>';
		  h += '</table>';
		  popover = $(element).popover({
	    'placement': 'top',
	    'animation': false,
	    'html': true
		  });
		  popover.attr('data-content', h);
		  $(element).popover('show');
	  } else{
		  $(element).popover('hide');  
	  }
	  
	  // Keep only one selected
      if (feature !== quickFeature) {
        if (quickFeature) {
        	hoverOverlayLayer.getSource().removeFeature(quickFeature);
        }
        if (feature) {
        	hoverOverlayLayer.getSource().addFeature(feature);
        }
        quickFeature = feature;
      }
}

function displayFeatureInfo(evt) {

      var feature = map.forEachFeatureAtPixel(map.getEventPixel(evt.originalEvent), function(feature, layer) {
        return feature;
      });

      var info = document.getElementById('info');
      if (feature) {
    	  $('#info-huc12').html( feature.getId() );
    	  $('#info-loss').html( feature.get('avg_loss').toFixed(2) + " T/a" );
    	  $('#info-runoff').html( feature.get('avg_runoff').toFixed(2) + " in" );
    	  $('#info-delivery').html( feature.get('avg_delivery').toFixed(2) + " T/a" );
    	  $('#info-precip').html( feature.get('qc_precip').toFixed(2) + " in");
      } else {
          $('#info-huc12').html('&nbsp;');
          $('#info-loss').html('&nbsp;');
          $('#info-runoff').html('&nbsp;');
          $('#info-delivery').html('&nbsp;');
          $('#info-precip').html('&nbsp;');
      }

      // Keep only one selected
      if (feature){
      if (feature !== quickFeature) {
        if (quickFeature) {
          hoverOverlayLayer.getSource().removeFeature(quickFeature);
        }
        if (feature) {
          hoverOverlayLayer.getSource().addFeature(feature);
        }
        quickFeature = feature;
      }
      }

};
var featureDisplayFunc = displayFeatureInfo;

$(document).ready(function(){
	try{
		readWindowHash();
	} catch(e){
		setStatus("An error occurred reading the hash link...");
		//console.log(e);
	}
		
	var style = new ol.style.Style({
		  fill: new ol.style.Fill({
		    color: 'rgba(255, 255, 255, 0)'
		  }),
		  text: new ol.style.Text({
			  font: '14px Calibri,sans-serif',
			  stroke: new ol.style.Stroke({
	              color: '#fff',
	              width: 8
	            }),
			  fill: new ol.style.Fill({
	              color: '#000',
	              width: 3
	            })
		  }),
		  stroke: new ol.style.Stroke({
		    color: '#000000', //'#319FD3',
		    width: 0.5
		  })
		});

	var vs = new ol.source.Vector({
		  url: getGeoJSONURL(),
		  format: geojsonFormat
	});
	vs.on('change', function(){
		if (detailedFeatureIn){
			makeDetailedFeature(this.getFeatureById(detailedFeatureIn));
			detailedFeatureIn = null;
		}
		
	});
	vectorLayer = new ol.layer.Vector({
		title : 'DEP Data Layer',
		  source: vs,
		  style: function(feature, resolution) {
			if (levels.length == 0){
				levels = vectorLayer.getSource().getFeatureById('jenks').get(appstate.ltype);
				drawColorbar();
			}
			
			  val = feature.get(appstate.ltype);
			  var c = 'rgba(255, 255, 255, 0)'; //hallow
			  for (var i=(levels.length-2); i>=0; i--){
			      if (val >= levels[i]){
			    	 c = colors[appstate.ltype][i];
			    	 break;
			      }
			      
			  }			  
			  style.getFill().setColor(c); 
			  style.getStroke().setColor((resolution < 1250) ? '#000000' : c);
		      style.getText().setText(resolution < 160 ? val.toFixed(2) : '');
		    return [style];
		  }
		});
	
	// Create map instance
    map = new ol.Map({
        target: 'map',
        controls: [new ol.control.Zoom(),
            new ol.control.ZoomToExtent({
            	//map.getView().calculateExtent(map.getSize())
            	extent: [-10889524, 4833877, -9972280, 5488178]
            })
        ],
        layers: [new ol.layer.Tile({
            	title: 'OpenStreetMap',
            	visible: true,
        		source: new ol.source.OSM()
        	}),
        	new ol.layer.Tile({
                title: "Global Imagery",
                visible: false,
                source: new ol.source.TileWMS({
                        url: 'http://maps.opengeo.org/geowebcache/service/wms',
                        params: {LAYERS: 'bluemarble', VERSION: '1.1.1'}
                })
        	}),
        	make_iem_tms('Iowa 100m Hillshade', 'iahshd-900913', false),
        	vectorLayer,
        	make_iem_tms('Iowa Counties', 'iac-900913', false),
        	make_iem_tms('US States', 's-900913', true),
        	make_iem_tms('Hydrology', 'iahydrology-900913', false),
        	make_iem_tms('HUC 8', 'iahuc8-900913', false)
        ],
        view: new ol.View({
                projection: 'EPSG:3857',
                center: defaultCenter,
                zoom: defaultZoom
        })
    });
    
	 // Popup showing the position the user clicked
	 popup = new ol.Overlay({
	   element: document.getElementById('popup')
	 });
	 map.addOverlay(popup);

	 var highlightStyle = [new ol.style.Style({
            stroke: new ol.style.Stroke({
              color: '#f00',
              width: 1
            }),
            fill: new ol.style.Fill({
              color: 'rgba(255,0,0,0.1)'
            })
    })];
    var clickStyle = [new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '#000',
            width: 2
          })
    })];

    hoverOverlayLayer = new ol.layer.Vector({
    	source: new ol.source.Vector({
    	    features: new ol.Collection()
      }),
      style: function(feature, resolution) {
        return highlightStyle;
      }
    });
    map.addLayer(hoverOverlayLayer);  // makes unmanaged

    clickOverlayLayer = new ol.layer.Vector({
    	source: new ol.source.Vector({
    	    features: new ol.Collection()
      }),
      style: function(feature, resolution) {
        	return clickStyle;
      }
    });
    map.addLayer(clickOverlayLayer);  // makes unmanaged

    // fired when the map is done being moved around
    map.on('moveend', function(){
    	//set the hash
    	setWindowHash();
    });
    // fired as the pointer is moved over the map
    map.on('pointermove', function(evt) {
      if (evt.dragging) {
        return;
      }
      featureDisplayFunc(evt);
    });

    // fired as somebody clicks on the map
    map.on('click', function(evt) {
    	// console.log('map click() called');
    	var pixel = map.getEventPixel(evt.originalEvent);
    	var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
            return feature;
        });
    	if (feature){
        	makeDetailedFeature(feature);
    	} else {
    		alert("No features found for where you clicked on the map.");
    	}
    });
    
    // Create a LayerSwitcher instance and add it to the map
    var layerSwitcher = new ol.control.LayerSwitcher();
    map.addControl(layerSwitcher);
    
    $("#datepicker").datepicker({
    	changeMonth: true,
    	changeYear: true,
  	  	dateFormat: myDateFormat,
  	  	minDate: new Date(2007, 0, 1),
  	  	maxDate: formatDate(myDateFormat, appstate.lastdate),
  	  	onSelect: function(dateText, inst) {
    		var dt = $("#datepicker").datepicker("getDate");
  			appstate.date = makeDate(dt.getUTCFullYear(), dt.getUTCMonth()+1,
  								dt.getUTCDate());
  			remap();
  			if (appstate.date != appstate.lastdate){
  				$('#settoday').css('display', 'block');
  			}
  	   	}
    });
    $("#datepicker").on('change', function(e){
    		var dt = $("#datepicker").datepicker("getDate");
			appstate.date = makeDate(dt.getUTCFullYear(), dt.getUTCMonth()+1,
								dt.getUTCDate());
			remap();
  			if (appstate.date < appstate.lastdate){
  				$('#settoday').css('display', 'block');
  			}
    });
    // careful here, because of UTC dates
    $("#datepicker").datepicker('setDate',
    	formatDate(myDateFormat, appstate.date));

    $("#datepicker2").datepicker({
    	changeMonth: true,
    	changeYear: true,
    	disable: true,
    	dateFormat: myDateFormat,
    	minDate: new Date(2007, 0, 1),
    	maxDate: formatDate(myDateFormat, appstate.lastdate),
    	onSelect: function(dateText, inst) {
			var dt = $("#datepicker2").datepicker("getDate");
			appstate.date2 = makeDate(dt.getUTCFullYear(), dt.getUTCMonth()+1,
							dt.getUTCDate());
    		remap(); 
    	}
    });
    $("#datepicker2").on('change', function(e){
		var dt = $("#datepicker2").datepicker("getDate");
		appstate.date2 = makeDate(dt.getUTCFullYear(), dt.getUTCMonth()+1,
							dt.getUTCDate());
		remap(); 
    });

    $("#datepicker2").datepicker('setDate', (appstate.date2) ?
    		formatDate(myDateFormat, appstate.date2):
    		formatDate(myDateFormat, appstate.lastdate));
    
    $("#radio").buttonset();
    $( '#radio input[type=radio]').change(function(){
  	  	appstate.ltype = this.value;
    	rerender_vectors();

    });
    $("#t").buttonset();
    if (appstate.date2){
    	$( '#t input[value=multi]').prop('checked', true).button('refresh');	
    }
    $( '#t input[type=radio]').change(function(){
    	if (this.value == 'single'){
    		appstate.date2 = null;
        	$("#dp2").css('visibility', 'hidden');    		
        	remap();
    	} else {
    		var dt = $("#datepicker2").datepicker("getDate");
    		appstate.date2 = makeDate(dt.getUTCFullYear(), dt.getUTCMonth()+1,
    							dt.getUTCDate());
        	$("#dp2").css('visibility', 'visible');
    	}
    });
    $("#t2").buttonset();
    $( '#t2 input[type=radio]').change(function(){
    	if (this.value == 'side'){
        	$("#featureside_div").css('display', 'block');
        	featureDisplayFunc = displayFeatureInfo;
        	var element = popup.getElement();
        	$(element).popover('hide');
    	} else {
        	$("#featureside_div").css('display', 'none');
        	featureDisplayFunc = popupFeatureInfo;
    	}
    });

    if (appstate.date2){
    	$("#dp2").css('visibility', 'visible');	
    }
    
    $('#huc12searchtext').on('keypress', function (event) {
        if(event.which === 13){
        	doHUC12Search();
        }
    });
        
        
    $('#huc12searchbtn').on('click', function(){
    	doHUC12Search();
    });
    
    $('#minus1d').on('click', function(){
    	appstate.date.setDate(appstate.date.getDate() - 1);
    	$("#datepicker").datepicker("setDate",
    		formatDate(myDateFormat, appstate.date));
    	remap();
    	if (appstate.date < appstate.lastdate){
    		$("#plus1d").prop("disabled", false);
    	}
    	if (appstate.date != appstate.lastdate){
  		    $('#settoday').css('display', 'block');
  		}
    });

    $('#plus1d').on('click', function(){
    	appstate.date.setDate(appstate.date.getDate() + 1);
    	if (appstate.date > appstate.lastdate){
    		$("#plus1d").prop("disabled", true);
    		appstate.date.setDate(appstate.date.getDate() - 1);
    	} else{
	    	$("#datepicker").datepicker("setDate",
	    		formatDate(myDateFormat, appstate.date));
	    	remap();
    	}
    });

    $('#ia').on('click', function(){
    	map.getView().setCenter(ol.proj.transform([-93.5, 42.07], 'EPSG:4326', 'EPSG:3857'));
    	map.getView().setZoom(7);
    	$(this).blur();
    });
    $('#mn').on('click', function(){
    	map.getView().setCenter(ol.proj.transform([-94.31, 44.3], 'EPSG:4326', 'EPSG:3857'));
    	map.getView().setZoom(7);
    	$(this).blur();
    });
    $('#ks').on('click', function(){
    	map.getView().setCenter(ol.proj.transform([-98.38, 38.48], 'EPSG:4326', 'EPSG:3857'));
    	map.getView().setZoom(7);
    	$(this).blur();
    });
    
    
    setTitle();
    // Make the map 6x4
    sz = map.getSize();
    map.setSize([sz[0], sz[0] / 6. * 4.]);
    drawColorbar();
    
    checkDates();
    window.setInterval(checkDates, 600000);
    
}); // End of document.ready()
