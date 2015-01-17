var map, tms;
var iaextent;
var scenario = 0;
var MRMS_FLOOR = new Date("2013/08/20");
var appstate = {
		lat: 42.22,
		lon: -95.489,
		date: null,
		ltype: 'loss2'
};

/**
 * Define a namespace for the application.
 */
window.app = {};
var app = window.app;



/**
 * @constructor
 * @extends {ol.interaction.Pointer}
 */
app.Drag = function() {

  ol.interaction.Pointer.call(this, {
    handleDownEvent: app.Drag.prototype.handleDownEvent,
    handleDragEvent: app.Drag.prototype.handleDragEvent,
    handleMoveEvent: app.Drag.prototype.handleMoveEvent,
    handleUpEvent: app.Drag.prototype.handleUpEvent
  });

  /**
   * @type {ol.Pixel}
   * @private
   */
  this.coordinate_ = null;

  /**
   * @type {string|undefined}
   * @private
   */
  this.cursor_ = 'pointer';

  /**
   * @type {ol.Feature}
   * @private
   */
  this.feature_ = null;

  /**
   * @type {string|undefined}
   * @private
   */
  this.previousCursor_ = undefined;

};
ol.inherits(app.Drag, ol.interaction.Pointer);


/**
 * @param {ol.MapBrowserEvent} evt Map browser event.
 * @return {boolean} `true` to start the drag sequence.
 */
app.Drag.prototype.handleDownEvent = function(evt) {
  var map = evt.map;

  var feature = map.forEachFeatureAtPixel(evt.pixel,
      function(feature, layer) {
        return feature;
      });

  if (feature) {
    this.coordinate_ = evt.coordinate;
    this.feature_ = feature;
  }

  return !!feature;
};


/**
 * @param {ol.MapBrowserEvent} evt Map browser event.
 */
app.Drag.prototype.handleDragEvent = function(evt) {
  var map = evt.map;

  var feature = map.forEachFeatureAtPixel(evt.pixel,
      function(feature, layer) {
        return feature;
      });

  var deltaX = evt.coordinate[0] - this.coordinate_[0];
  var deltaY = evt.coordinate[1] - this.coordinate_[1];

  var geometry = /** @type {ol.geom.SimpleGeometry} */
      (this.feature_.getGeometry());
  geometry.translate(deltaX, deltaY);

  this.coordinate_[0] = evt.coordinate[0];
  this.coordinate_[1] = evt.coordinate[1];
};


/**
 * @param {ol.MapBrowserEvent} evt Event.
 */
app.Drag.prototype.handleMoveEvent = function(evt) {
  if (this.cursor_) {
    var map = evt.map;
    var feature = map.forEachFeatureAtPixel(evt.pixel,
        function(feature, layer) {
          return feature;
        });
    var element = evt.map.getTargetElement();
    if (feature) {
      if (element.style.cursor != this.cursor_) {
        this.previousCursor_ = element.style.cursor;
        element.style.cursor = this.cursor_;
      }
    } else if (this.previousCursor_ !== undefined) {
      element.style.cursor = this.previousCursor_;
      this.previousCursor_ = undefined;
    }
  }
};


/**
 * @param {ol.MapBrowserEvent} evt Map browser event.
 * @return {boolean} `false` to stop the drag sequence.
 */
app.Drag.prototype.handleUpEvent = function(evt) {
	var c = ol.proj.transform(this.coordinate_, 'EPSG:3857', 'EPSG:4326')
	appstate.lat = c[1];
    appstate.lon = c[0];
    updateDetails();
	this.coordinate_ = null;
  this.feature_ = null;
  return false;
};

function setType(t){
	$('#'+ t +'_opt').click();
}

function hideDetails(){
	$('#details_hidden').css('display', 'block');
	$('#details_details').css('display', 'none');
	$('#details_loading').css('display', 'none');
}

function updateDetails(){
	$('#details_hidden').css('display', 'none');
	$('#details_details').css('display', 'none');
	$('#details_loading').css('display', 'block');
    $.get('nextgen-details.php', {lat: appstate.lat, lon: appstate.lon,
		date: $.datepicker.formatDate("yy-mm-dd", appstate.date)},
		function(data){
			$('#details_details').css('display', 'block');
			$('#details_loading').css('display', 'none');
			$('#details_details').html(data);
	});

}

function showConvergence(huc_12){
	var $dialog = $('<div></div>')
    .html('Image will appear here shortly!')
    .dialog({
        height: 500,
        width: 600,
        title: 'Convergence Plot'});

	$dialog.dialog('open');
	$dialog.html('<img src="/plots/convergence.py?huc_12='+huc_12+'" style="width: 100%;"/>');
}

function get_tms_url(){
	// Generate the TMS URL given the current settings
	return tilecache +'/cache/tile.py/1.0.0/idep0::'+appstate.ltype+'::'+$.datepicker.formatDate("yy-mm-dd", appstate.date)+'/{z}/{x}/{y}.png';
}
function remap(){
	tms.getSource().setUrl(get_tms_url());
	tms.setVisible(false);
	tms.setVisible(true);
}
function setDate(year, month, date){
	appstate.date = new Date(year+"/"+ month +"/"+ date);
	$('#datepicker').datepicker("setDate", appstate.date);
	remap();
	updateDetails();
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

	// Vector Layer to hold the query marker that allows us to interogate the
	// data layer
	var pointFeature = new ol.Feature(new ol.geom.Point(
			ol.proj.transform([-95.489, 42.22], 'EPSG:4326', 'EPSG:3857')));
	markers = new ol.layer.Vector({
	      source: new ol.source.Vector({
	    	  projection: ol.proj.get('EPSG:3857'),
	          features: [pointFeature]
	        }),
	        style: new ol.style.Style({
	          image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
	            anchor: [0.5, 0.5],
	            anchorXUnits: 'fraction',
	            anchorYUnits: 'fraction',
	            opacity: 0.95,
	            src: '/images/zoom-best-fit.png'
	          })),
	          stroke: new ol.style.Stroke({
	            width: 3,
	            color: [255, 0, 0, 1]
	          }),
	          fill: new ol.style.Fill({
	            color: [0, 0, 255, 0.6]
	          })
	        })
	      });
	
	// Our base tile map service layer, which we adjust to include the data
	// the user wants
	tms = new ol.layer.Tile({
		title : 'IDEP Data Layer',
		source : new ol.source.XYZ({
			url : get_tms_url()
		})
	});
	
	// Create map instance
    map = new ol.Map({
        target: 'map',
        interactions: ol.interaction.defaults().extend([new app.Drag()]),
        controls: [new ol.control.Zoom(),
            new ol.control.ZoomToExtent()
        ],
        layers: [new ol.layer.Tile({
            	title: 'OpenStreetMap',
            	visible: false,
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
        	make_iem_tms('Iowa GLU 0813', 'iaglu-900913', false),
        	tms,
        	make_iem_tms('Iowa Counties', 'iac-900913', false),
        	make_iem_tms('US States', 's-900913', true),
        	make_iem_tms('Hydrology', 'iahydrology-900913', false),
        	make_iem_tms('HUC 12', 'iahuc12-900913', true),
        	make_iem_tms('HUC 8', 'iahuc8-900913', false),
        	make_iem_tms('Flow Paths', 'flowpaths-900913', false),
        	markers
        ],
        view: new ol.View({
                projection: 'EPSG:3857',
                center: ol.proj.transform([-95.489, 42.22], 'EPSG:4326', 'EPSG:3857'),
                zoom: 7
        })
    });

    // Create a LayerSwitcher instance and add it to the map
    var layerSwitcher = new ol.control.LayerSwitcher();
    map.addControl(layerSwitcher);
    
    $("#datepicker").datepicker({
  	  dateFormat: 'M d, yy',
  	  minDate: new Date(2002, 1, 1),
  	  maxDate: lastdate,
  	   onSelect: function(dateText, inst) {
  		   appstate.date = $("#datepicker").datepicker("getDate");
  		   if ((appstate.ltype == 'mrms-calday') && (appstate.date < MRMS_FLOOR)){
  			   appstate.ltype = 'precip-in2';
  		    	  $('#rampimg').attr('src',"/images/"+ appstate.ltype +"-ramp.png");
  	       }
  		   if ((appstate.ltype == 'precip-in2') && (appstate.date > MRMS_FLOOR)){
  			   appstate.ltype = 'mrms-calday';
  		    	  $('#rampimg').attr('src',"/images/"+ appstate.ltype +"-ramp.png");
  	       }
  		   remap(); 
  		   updateDetails();
  	   }
    });

    $("#datepicker").datepicker('setDate', lastdate);
    
    $( "#radio" ).buttonset();
    $( '#radio input[type=radio]').change(function(){
    	if ((this.value == 'mrms-calday') && (appstate.date < MRMS_FLOOR)){
    		appstate.ltype = 'precip-in2';
  	  	} else {
  	  		appstate.ltype = this.value;
  	  	}
    	remap();
  	  	$('#rampimg').attr('src',"/images/"+ appstate.ltype +"-ramp.png");
    });
    updateDetails();
      
}); // End of document.ready()
