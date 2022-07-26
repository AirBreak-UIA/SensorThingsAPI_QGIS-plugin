/**
 * SensorThings API Plugin
 *
 *  location.js
 *
 */

/* Global function to show spinner */
window.sensorThingsShowSpinner = function(show) {
	if (!!show) {
		$("#spinner-div").show();
	} else {
		$("#spinner-div").hide();
	}
}


/* Setup document when full loaded */
$(document).ready(function() {
	
	var pageData = pyjsapi.getPageData() || {};
	var localizer = SensorThingsLocales.getLocalizer( pageData['locale'] );
	
	/***********************************************
	 * Initial settings
     ***********************************************/
    
    /* localize document */
	localizer.processLangDocument();
	
	/* Create datastream tables */
    $(".frost-stream").each(function(i) {
	
	    /* initial vars */
    	var thingId = $(this).attr("thing-id");
        var thingData = pyjsapi.getThingData(thingId);
        var isMultidataStream = $(this).hasClass("frost-multidatastream");

        /* hide mutidatastream table */
        if (isMultidataStream) {
			//$(this).parent().css('visibility', 'hidden');
		}
        
        /* cCreate datatable */
    	var table = $(this).DataTable( {
    		"info": false,
		    "pageLength": 10,
		    "paging": false,
	        "searching": false,
	        "ordering": false,
			"bLengthChange": false,
			"autoWidth": false,
			
			"processing": true,
			
			"language": (jQuery.fn.datatables && jQuery.fn.datatables[localizer.getCode()])|| {
				"processing": '<i class="fa fa-spinner fa-spin" style="font-size:24px;color:rgb(75, 183, 245);"></i>&nbsp;&nbsp;&nbsp;&nbsp;Processing...'
			} ,
			
			"ajax": function (data, callback, settings) {
				// create main promise to obtain stream data
				var url = isMultidataStream ? 
					thingData['MultiDatastreams@iot.navigationLink'] : 
					thingData['Datastreams@iot.navigationLink']; 
				
				// check if valid url
				if (!url) {
					callback({ data: [] });
					return;
				}
				
				// create main promise to get data
				requestPromise(url, { "dataSrc": "value" })
					.then(d => { 
						// create a promise chain to obtain
						// sensor and observerd property data
						var prop_url_fld = isMultidataStream ? 
							'ObservedProperties@iot.navigationLink' : 
							'ObservedProperty@iot.navigationLink'; 
					
						var promises = [];
						var rows = d || [];
						rows.forEach(row => {
							
							// sendsor promise
							var _url = row['Sensor@iot.navigationLink'];
							var _prom = requestPromise(_url)
								.then(data => { 
									row['sensorData'] = data;
								})
								.catch(reason => {
									console.error('Sendor load data error: '+reason);
									row['sensorData'] = { name: '???' };
								});
							promises.push(_prom);
							
							// observed property promise
							_url = row[prop_url_fld];
							_prom = requestPromise(_url, { "dataSrc": "value" })
								.then(data => { 
									row['observedProperty'] = data;
								})
								.catch(reason => {
									console.error('Observer property load data error: '+reason);
									row['observedProperty'] = (isMultidataStream) ? {} : [];
								});
							promises.push(_prom);
							
							// phenomenonTime for aggregation
							var aggregateFor = row.properties && row.properties.aggregateFor;
							if (!!aggregateFor) {
								aggregateFor = String(aggregateFor);
								
								if (!row.phenomenonTime) {
									// compose aggregation for url
									var aggr_url = '';
									if (aggregateFor.startsWith('http')) {
										aggr_url = aggregateFor;
									} else {
										var urlObj = new URL(url)
										var path_arr = urlObj.pathname.replace(/\/$/, '').split('/');
									    path_arr.pop();
									    urlObj.pathname = path_arr.join('/') + aggregateFor;
										aggr_url = urlObj.toString();
									}
									// create promise
									_prom = requestPromise(aggr_url)
										.then(data => { 
											row['phenomenonTime'] = data && data.phenomenonTime;
										})
										.catch(reason => {
											console.error('Aggregation for property load data error: '+reason);
										});
									promises.push(_prom);
								}
							}	
						});
						
						// esecute all promises
						Promise.all(promises).then((results) => { 
							callback({ data: d }); 
						});
					})
					.catch(err => { 
						callback({ data: [] }); 
						console.log(err); 
					});
			},
			
			"initComplete": function(settings, json) {
				// hide multistream table container if no data
				var o = $(this);
				if (o.hasClass("frost-multidatastream")) {
					var api = this.api();
					if (api.rows().count() > 0) {
						return;
					}
					var p = o.closest("#multistream-container");
					if (!!p) {
						//p.css('visibility', 'visible');
						p.hide();
					}
				}	
			},
			
			"columns": [
				{ title: localizer.translate("Name"), data: "name", defaultContent: "" },
				{ title: localizer.translate("Description"), data: "description", defaultContent: "" },
				{ 
					title: localizer.translate("Ref. dates"), 
					data: "phenomenonTime", 
					defaultContent: "",
					render: function(data, type, row) {
						return localizer.formatPhenomenonTime(row.phenomenonTime);
					},
				},
				{ 
					title: localizer.translate("Observed property"), 
					data: function (row) {
						return row['observedProperty'];
					},
					defaultContent: "",
					render: function(data, type, row) {
						if (isMultidataStream) {
							var ar = [];
							var units = row.unitOfMeasurements || [];
							var unitsLen = units.length;
							var props = row.observedProperty || [];
							for (var i=0; i<props.length && i<units.length; ++i) {
								var smb = (i<unitsLen) ? units[i].symbol : ''; 
								ar.push('- ' + props[i].name + ' (' + smb + ')');
								props[i]['__unitSymbol'] = smb;
							}
							return '<div style="white-space:pre-line">' + ar.join("\n") + '</div>';
						}
						return row.observedProperty.name + " - " + row.unitOfMeasurement.symbol;
					},
				},
				{ 
					title: localizer.translate("Sensor"), 
					data: function (row) {
						try { return row.sensorData.name; } catch(e){ return '<error>'; }
					},
					defaultContent: "",
					render: function (data, type) {
						return '<img class="sensor-img" src="./icons/sensor_icon.png" alt="Sensore"/> ' + data;
					}
				},
				{ 
					title: localizer.translate("Observations"), 
					data: null, 
					defaultContent: "",
					render: function (data, type, row) {
						// check if valid phenomenonTime
						if (!!row.phenomenonTime) {
							return '<button type="button" class="btn btn-default oss-img oss-button"></button>';
						}
						return '';
					}
				}
			]
		});
    	
    	/* Select\Deselect row */
    	table.on('click', 'tr', function () {
	        if ($(this).hasClass('selected')) {
	            $(this).removeClass('selected');
	        } else {
	            table.$('tr.selected').removeClass('selected');
	            $(this).addClass('selected');
	        }
	    });
    	
    	/* Handle Osservazioni buttun click */
    	table.on("click", ".oss-button", function () {
    		$(this).blur()
            var rowData = table.row($(this).parents('tr')).data();
    		if (!!rowData) {
	            // get data filter
				var dtFilterRange = new SensorThingsDateRange().parsePhenomenonTime(rowData['phenomenonTime']);
				dtFilterRange = dtFilterRange.getFilterRangeByDelta(dtFilterRange.End, 0);
				
				// show spinner
    			//$("#spinner-div").show();

				// show Observations data
    			pyjsapi.loadObservationsData(rowData, {
					"queryParams": dtFilterRange.getQueryParams(),
					"filterTime": dtFilterRange.toString(),
					"isMultidatastream": isMultidataStream
				});
    		}
        });
    });
	
	/* Make resizable columns */
    $("table th").resizable({
        handles: "e",
        stop: function(e, ui) {
          $(this).width(ui.size.width);
        }
    });
	
	/* Location selector */
	$('#location-selector').on('change', function() {
		pyjsapi.changeLocation(this.value);
	});
});