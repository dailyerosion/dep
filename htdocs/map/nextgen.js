var map;
var vectorLayer;
var iaextent;
var scenario = 0;
var MRMS_FLOOR = new Date("2013/08/20");
var geojsonFormat = new ol.format.GeoJSON();

var varunits = {
	avg_runoff: 'inches',
	avg_loss: 'tons per acre',
	qc_precip: 'inches',
	avg_delivery: 'tons per acre'
};
var vartitle = {
	avg_runoff: 'Water Runoff',
	avg_loss: 'Soil Detachment',
	qc_precip: 'Daily Precipitation',
	avg_delivery: 'Soil Delivery'
};

// Sets the title shown on the page for what is being viewed
function setTitle(){
	dt = $.datepicker.formatDate("yy-mm-dd", appstate.date);
	dtextra = (appstate.date2 === null) ? '': ' to '+$.datepicker.formatDate("yy-mm-dd", appstate.date2);
	$('#maptitle').html("<h4>Displaying "+ eval('vartitle.'+appstate.ltype) +" ["+
			eval('varunits.'+appstate.ltype) +"] for "+ dt +" "+ dtextra +"</h4>");
}

// When user clicks the "Get Shapefile" Button
function get_shapefile(){
	dt = $.datepicker.formatDate("yy-mm-dd", appstate.date);
	window.location.href = 'http://mesonet.agron.iastate.edu/cgi-bin/request/idep2.py?dt='+dt;
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
    $.get('nextgen-details.php', {huc12: huc12,
		date: $.datepicker.formatDate("yy-mm-dd", appstate.date)},
		function(data){
			$('#details_details').css('display', 'block');
			$('#details_loading').css('display', 'none');
			$('#details_details').html(data);
	});

}

function get_tms_url(){
	// Generate the TMS URL given the current settings
	var uri = '/geojson/huc12.py?date='+$.datepicker.formatDate("yy-mm-dd", appstate.date);
	if (appstate.date2 !== null){
		uri = uri + "&date2="+ $.datepicker.formatDate("yy-mm-dd", appstate.date2);
	}
	return uri;
}
function rerender_vectors(){
	//console.log("rerender_vectors() called");
	vectorLayer.changed();
}
function remap(){
	vectorLayer.setSource(new ol.source.Vector({
		url: get_tms_url(),
		format: geojsonFormat
	}));
	setTitle();
}
function setDate(year, month, date){
	appstate.date = new Date(year+"/"+ month +"/"+ date);
	$('#datepicker').datepicker("setDate", appstate.date);
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

$(document).ready(function(){

	appstate.date = lastdate;
	appstate.date2 = null;

	var style = new ol.style.Style({
		  fill: new ol.style.Fill({
		    color: 'rgba(255, 255, 255, 0.6)'
		  }),
		  stroke: new ol.style.Stroke({
		    color: '#319FD3',
		    width: 1
		  }),
		  text: new ol.style.Text({
		    font: '12px Calibri,sans-serif',
		    fill: new ol.style.Fill({
		      color: '#000'
		    }),
		    stroke: new ol.style.Stroke({
		      color: '#fff',
		      width: 3
		    })
		  })
		});

	vectorLayer = new ol.layer.Vector({
		title : 'IDEPv2 Data Layer',
		  source: new ol.source.Vector({
		    url: get_tms_url(),
		    format: geojsonFormat
		  }),
		  style: function(feature, resolution) {
			  val = feature.get(appstate.ltype);
			  var c;
			  if (val >= 7){
				  c = 'rgba(255, 102, 0, 1)';
			  } else if (val >= 5){
				  c = 'rgba(255, 153, 0, 1)';
			  } else if (val >= 3){
				  c = 'rgba(255, 153, 0, 1)';
			  } else if (val >= 2){
				  c = 'rgba(255, 204, 0, 1)';
			  } else if (val >= 1.5){
				  c = 'rgba(255, 232, 0, 1)';
			  } else if (val >= 1){
				  c = 'rgba(255, 255, 0, 1)';
			  } else if (val >= 0.75){
				  c = 'rgba(204, 255, 0, 1)';
			  } else if (val >= 0.5){
				  c = 'rgba(51, 255, 0, 1)';
			  } else if (val >= 0.25){
				  c = 'rgba(102, 255, 153, 1)';
			  } else if (val >= 0.1){
				  c = 'rgba(24, 255, 255, 1)';
			  } else if (val >= 0.05){
				  c = 'rgba(0, 212, 255, 1)';
			  } else if (val > 0.001){
				  c = 'rgba(0, 0, 255, 1)';
			  } else {
				  c = 'rgba(255, 255, 255, 0.6)';				  
			  }
			  style.getFill().setColor(c); 
		    // style.getText().setText(resolution < 5000 ? feature.get('avg_loss') : '');
		    return [style];
		  }
		});
	
	// Create map instance
    map = new ol.Map({
        target: 'map',
        controls: [new ol.control.Zoom(),
            new ol.control.ZoomToExtent()
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
                center: ol.proj.transform([-93.5, 42.1], 'EPSG:4326', 'EPSG:3857'),
                zoom: 7
        })
    });

    var highlightStyleCache = {};

    var featureOverlay = new ol.FeatureOverlay({
      map: map,
      style: function(feature, resolution) {
        var text = resolution < 5000 ? feature.get('name') : '';
        if (!highlightStyleCache[text]) {
          highlightStyleCache[text] = [new ol.style.Style({
            stroke: new ol.style.Stroke({
              color: '#f00',
              width: 1
            }),
            fill: new ol.style.Fill({
              color: 'rgba(255,0,0,0.1)'
            }),
            text: new ol.style.Text({
              font: '12px Calibri,sans-serif',
              text: text,
              fill: new ol.style.Fill({
                color: '#000'
              }),
              stroke: new ol.style.Stroke({
                color: '#f00',
                width: 3
              })
            })
          })];
        }
        return highlightStyleCache[text];
      }
    });

    var highlight;
    var displayFeatureInfo = function(pixel) {

      var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
      });

      var info = document.getElementById('info');
      if (feature) {
    	  $('#info-huc12').html( feature.getId() );
    	  $('#info-loss').html( feature.get('avg_loss').toFixed(3) + " T/a" );
    	  $('#info-runoff').html( feature.get('avg_runoff').toFixed(2) + " in" );
    	  $('#info-delivery').html( feature.get('avg_delivery').toFixed(3) + " T/a" );
    	  $('#info-precip').html( feature.get('qc_precip').toFixed(2) + " in");
      } else {
          $('#info-huc12').html('&nbsp;');
          $('#info-loss').html('&nbsp;');
          $('#info-runoff').html('&nbsp;');
          $('#info-delivery').html('&nbsp;');
          $('#info-precip').html('&nbsp;');
      }

      if (feature !== highlight) {
        if (highlight) {
          featureOverlay.removeFeature(highlight);
        }
        if (feature) {
          featureOverlay.addFeature(feature);
        }
        highlight = feature;
      }

    };

    map.on('pointermove', function(evt) {
      if (evt.dragging) {
        return;
      }
      var pixel = map.getEventPixel(evt.originalEvent);
      displayFeatureInfo(pixel);
    });

    map.on('click', function(evt) {
    	var pixel = map.getEventPixel(evt.originalEvent);
    	var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
            return feature;
        });
    	updateDetails(feature.getId());
    	
    });
    
    // Create a LayerSwitcher instance and add it to the map
    var layerSwitcher = new ol.control.LayerSwitcher();
    map.addControl(layerSwitcher);
    
    $("#datepicker").datepicker({
  	  dateFormat: 'M d, yy',
  	  minDate: new Date(2007, 1, 1),
  	  maxDate: lastdate,
  	   onSelect: function(dateText, inst) {
  		   appstate.date = $("#datepicker").datepicker("getDate");
  		   remap(); 
  	   }
    });

    $("#datepicker").datepicker('setDate', lastdate);

    $("#datepicker2").datepicker({
    	disable: true,
    	  dateFormat: 'M d, yy',
    	  minDate: new Date(2007, 1, 1),
    	  maxDate: lastdate,
    	   onSelect: function(dateText, inst) {
    		   appstate.date2 = $("#datepicker2").datepicker("getDate");
    		   remap(); 
    	   }
      });

      $("#datepicker2").datepicker('setDate', lastdate);
    
    $("#radio").buttonset();
    $( '#radio input[type=radio]').change(function(){
  	  	appstate.ltype = this.value;
    	rerender_vectors();
    	setTitle();
    });
    $("#t").buttonset();
    $( '#t input[type=radio]').change(function(){
    	if (this.value == 'single'){
        	$("#dp2").css('visibility', 'hidden');    		
    		
    	} else {
        	$("#dp2").css('visibility', 'visible');
    	}
    });
        
    setTitle();
      
}); // End of document.ready()
