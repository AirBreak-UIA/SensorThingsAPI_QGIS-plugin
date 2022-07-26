/*!
 * SensorThings APIPlugin
 *
 *  observations.js
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
	
	/* Function to correct datapicker date */
	function correctDatePickerDate(datePickerObj) {
		var date = datePickerObj.datepicker('getDate');
		try {
			var dateFormat = datePickerObj.datepicker("getFormattedDate", 'yyyy-mm-dd');
			return new Date(dateFormat + 'T00:00:00.000Z')
		} catch (error) {
			return date;
		}
	}
	
	
	/* Get page data */
	var pageData = pyjsapi.getPageData() || {};
	var localizer = SensorThingsLocales.getLocalizer( pageData['locale'] );
	var propData = pageData['selectRow'] || {};
	var props = propData['observedProperty'] || [];
	var isMultidataStream = pageData['isMultidataStream'] || false;
	
	/* Get filter data range */
	var phenomenonRange = new SensorThingsDateRange().parsePhenomenonTime(propData['phenomenonTime']);
	var phenomenonRangeNorm = new SensorThingsDateRange().parsePhenomenonTime(propData['phenomenonTime']).normalize();
	//var filterRange = new SensorThingsDateRange().parsePhenomenonTime(pageData['filterTime']);
	
	var strPhenomenonStartDate = $.datepicker.formatDate(
		localizer.getDatePickerFormat({ twoDigitYear: true }), 
		localizer.getUtcDatefromLocal(phenomenonRange.Start)
	);
		
	var strPhenomenonEndDate = $.datepicker.formatDate(
		localizer.getDatePickerFormat({ twoDigitYear: true }), 
		localizer.getUtcDatefromLocal(phenomenonRange.End)
	);
	
	/* export CSV field definition */
	var exportFields = { 
		'Data osservazione': {
			'field': 'phenomenonTime'
		}
	};
	
	//phenomenonRange.normalize();
	//filterRange.normalize();
	///////////////////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////////////////
	
	/***********************************************
	 * Initial settings
     ***********************************************/
	
	/* localize document */
	localizer.processLangDocument();
	
	/* Format header phenomenon time */
	var el = $('#phenomenonTime')
	el.text( localizer.formatPhenomenonTime( el.text() ) );
	
	
	
	/***********************************************
	 * Chart creation 
     ***********************************************/

	/* Function to create chart */
	function polulateChart(oss_data, prop_data, isMultidataStream) {
		
		try {
			// Hide chart spinner
			$('#chart_processing').hide();
			
			// init
			oss_data = oss_data || [];
			prop_data = prop_data || [];
			
			var pageData = pyjsapi.getPageData() || {};
			var chartOptions = pageData['chart_opts'] || {};
			var line_color = chartOptions['line_color'] || '#32CD32';
			var line_colors = chartOptions['line_colors'] || [];
			var line_colors_len = line_colors.length;
			if (line_colors_len === 0) {
				line_colors.push('#32CD32');
			}
			
			var chart_data = {
				datasets: []
			};

			var chart_options = {
				responsive: true,
				maintainAspectRatio: false,
			    legend: { 
					display: false 
				},
				tooltips: {
			      callbacks: {
		                title: function(tooltipItem, data) {
							var tip = tooltipItem[0];
							var ds = data.datasets[tip.datasetIndex];
							var value = ''+ds.data[tip.index].x;
							var dates = localizer.formatCompactPhenomenonTimeAsArray(value);
							if (!dates[1]) {
								// puntual event
								return [
									dates[0], " (", localizer.getTimezone(), ")"
								].join('');
							}
							// duration event
							return [
								localizer.translate("Start: "), 
								dates[0], " (", localizer.getTimezone(), ")",
								"\n",
								localizer.translate("End  : "), 
								dates[1], " (", localizer.getTimezone(), ")"
							].join('');
		                }
		            }
			    },
				scales: {
					xAxes: [{
						type: 'time',
						
						time: {
							tooltipFormat: 'DD/MM/YYYY HH:mm:ss',
							displayFormats: {
								millisecond: 'DD/MM HH:mm',
								second: 'DD/MM HH:mm',
								minute: 'DD/MM HH:mm',
								hour: 'DD/MM HH:mm',
								day: 'DD/MM/YY',
								week: 'DD/MM/YY',
								month: 'DD/MM/YY',
								quarter: 'DD/MM/YY',
								year: 'DD/MM/YY',
							},
							parser: function(value) {
								if (typeof value === 'string') {
									return value.split('/')[0];
								}  	
								return value;
							}
						},
						
						ticks: {
							source: 'data',
							maxTicksLimit: 10,
							autoSkip: true,
							maxRotation: 0,
							minRotation: 0,
							beginAtZero: true,
							
							callback: function (value, index, values) {
								/*
								var l = values.length;
								if (l > 2 && (index == 0 || index == l-1)) {
									return undefined;
								}
								return value;
								*/
								var date = new Date(values[index].value);
								if (value.indexOf(':') > -1) {
									return date.toLocaleString(localizer.getCode(), {
										day: "2-digit",
										month: "2-digit",
										hour: 'numeric', 
										minute: 'numeric', 
										hour12: false
									}).replace(",", "");
								}
								return date.toLocaleString(localizer.getCode(), {
									day: "2-digit",
									month: "2-digit",
									year: "2-digit"
								});
							}
						}
					}],
					
					yAxes: [{
			            ticks: {
			                beginAtZero: true
			            }
			        }]
				},
				
				pan: {
					enabled: true,
					mode: 'x'
				},
				zoom: {
					enabled: true,
					mode: 'x',
				}
			};
			
			// categorize
			var categorize = false;
			var labels = [];
			if (!!isMultidataStream) {
				for (var i=0; i<prop_data.length; ++i) {
					for (var j=0; j<oss_data.length; ++j) {
						var res = oss_data[j].result[i];
						labels.push(res);
						if (isNaN(res)) {
							categorize = true;
						}
					}	
				}
			} else {
				for (var j=0; j<oss_data.length; ++j) {
					var res = oss_data[j].result;
					labels.push(res);
					if (isNaN(res)) {
						categorize = true;
					}
				}
			}
			if (categorize) {
				console.log("Categorized");
				labels = labels.filter((value, index, self) => {
					return self.indexOf(value) === index;
				});
				
				chart_options['scales']['yAxes']= [{
					type: 'category',
    				labels: labels,
		            ticks: {
		                beginAtZero: false
		            }
		        }];
				
				if (!!oss_chart) {
					var tp = oss_chart.options.scales.yAxes[0]['type'];
					if (tp != 'category') {
						oss_chart = null;
					}
				}
                
			}
			
			// load datasets
			if (!!isMultidataStream) {
				
				for (var i=0; i<prop_data.length; ++i) {
					
					var color = line_colors[i % line_colors_len];
				
					chart_data.datasets.push({
						
						label: prop_data[i].name,
						fill: true,
						//lineTension: 0.4,
						backgroundColor: color+'30',
						borderColor: color,
						borderWidth: 2,
						pointBorderColor: color,
						pointBackgroundColor: color,
						cubicInterpolationMode: 'default',
						tension: 0.4,
						//data: data.map(o => o.result[i])
						data: oss_data.map(o => ({ x: o.phenomenonTime, y: o.result[i] }))
						
					});
				}
				
				chart_options.legend = { display: true };
		
			} else {
			
				chart_data.datasets.push({
			      data: oss_data.map(o => ({ x: o.phenomenonTime, y: o.result })),
			      borderColor: line_color,
			      borderWidth: 1,
			      pointBorderColor: line_color,
			      pointBackgroundColor: line_color,
			      fill: false,
			      cubicInterpolationMode: 'default',
			      tension: 0.4
			    });
			}
			
			// check if crat already created
			if (!!oss_chart) {
				
				// update chart
				oss_chart.data.datasets = chart_data.datasets;
				oss_chart.update();
				oss_chart.resetZoom();
				
			} else {
				
				// create chart
				oss_chart = new Chart("observation-chart", {
					type: 'line',
					data: chart_data,
					options: chart_options
				});
			}
			
		} catch (error) {
			console.error(error);
		}
	}
	
	
	/* create chart */
	var oss_chart = null;
	polulateChart([], [], isMultidataStream);
	
	/* Chart height on page resizing */
	$( window ).resize(function() {
		var h = $('#oss-header').height() +
		        $('#oss-tabs').height() +
                $('#oss-footer').height() +
                20;
		
		$('#chart-container').height('calc(100vh - ' + h + 'px)');  
	});
	
	
	/***********************************************
	 * Datatable creation 
     ***********************************************/

	/* Define table columns */
	columns = [{ 
		title: localizer.translate("Start time") + 
		       " (" + localizer.getTimezone() + ")", 
		data: "phenomenonTime", 
		defaultContent: "",
		render: function(data, type, row) {
			return localizer.formatCompactPhenomenonTimeAsArray(row.phenomenonTime)[0];
		},
		className: "text-center"
	},{ 
		title: localizer.translate("End time") + 
		       " (" + localizer.getTimezone() + ")", 
		data: "phenomenonTime", 
		defaultContent: "",
		render: function(data, type, row) {
			return localizer.formatCompactPhenomenonTimeAsArray(row.phenomenonTime)[1];
		},
		className: "text-center"
	}];
	
	if (!!isMultidataStream) {
		
		// add columns multi values
		for (var i=0; i<props.length; ++i) {
			
			var propName = props[i].name;
			
			columns.push({ 
				title: '' + propName + '<br>(' + props[i].__unitSymbol + ')', 
				data: "result", 
				defaultContent: "", 
				className: "text-center",
				render: (function() {
					var index = i;
					return function (data, type, row) { 
						return data[index]; 
					}
				})()
			});
			
			// append export field definition
			exportFields[propName] = {
				'field': 'result',
				'index': i
			}
		}
		
	} else {
		
		//  add value column	
		var unit = propData['unitOfMeasurement'] || {}
		var unitSmb = unit['symbol'] || ''
		
		columns.push({ 
			title: localizer.translate("Value") + "(" + unitSmb + ")",
			data: "result", 
			defaultContent: "", 
			className: "text-center"
		});
		
		// collect column export definition
		exportFields['Valore'] = {
			'field': 'result'
		}
	}
	
	/* Create Valori tables */
	var table = $("#valori").DataTable({
		"info": false,
	    "pageLength": 10,
	    "paging": true,
        "searching": false,
        "ordering": false,
		"bLengthChange": false,
		"autoWidth": false,		
		"columns": columns,
		"processing": true,	
		"language": (jQuery.fn.datatables && jQuery.fn.datatables[localizer.getCode()]) || {
			"processing": '<i class="fa fa-spinner fa-spin" style="font-size:24px;color:rgb(75, 183, 245);"></i>&nbsp;&nbsp;&nbsp;&nbsp;Processing...'
		} ,
		
		"ajax": function (data, callback, settings) {
			
			/* get request url */		
			var url = propData['Observations@iot.navigationLink'] || ''; 
			var query = pageData['queryParams'] || ''; 
			url = [url, query].join('?');
			
			/* Show chart spinner */
			$('#chart_processing').show();
			
			/* Create a GET request promise */
			requestPromise(url, { "dataSrc": "value" })
				.then(d => { 
					callback({ data: d });
					polulateChart(d, props, isMultidataStream);
				})
				.catch(err => { 
					callback({ data: [] });
					polulateChart([], [], isMultidataStream); 
					console.log(err); 
				});
		},
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
	
	/* Make resizable columns */
    $("table th").resizable({
        handles: "e",
        stop: function(e, ui) {
          $(this).width(ui.size.width);
        }
    });

	/* clone datatable spinner content to chart */
	$('#chart_processing').html( $('#valori_processing').html() );
	

	/***********************************************
	 * Set date filter panel 
     ***********************************************/

    /* Create filter date picker */
    $('.date.input-group').datepicker({
		"format": localizer.getDatePickerFormat(),
		"assumeNearbyYear": true,
	    "calendarWeeks": false,
	    "todayHighlight": true,
	    "autoclose": true,
        "useCurrent": true,
        "showOnFocus": false,
	    "language": localizer.getCode(),

        "startDate": strPhenomenonStartDate,
        "endDate": strPhenomenonEndDate,
        
	});
	
	$('#datePickerStart').datepicker(
		"update", strPhenomenonEndDate);
	$('#datePickerEnd').datepicker(
		"update", strPhenomenonEndDate);
	$('#dateCsvPickerStart').datepicker(
		"update", strPhenomenonEndDate);
	$('#dateCsvPickerEnd').datepicker(
		"update", strPhenomenonEndDate);
	
		
	/* Set initial phenomenon time label */
    $('#labelDateFirst').text(
		localizer.formatPhenomenonTime(phenomenonRange.Start)
	 )
		
	/* Set final phenomenon time label */
	$('#labelDateLast').text(
		localizer.formatPhenomenonTime(phenomenonRange.End)
	 )	
	
    /* Set initial start filter date */
	$('#filterDateFirst').click(function() {
		
		$('#datePickerStart').datepicker(
			"update", strPhenomenonStartDate);
	}); 
	
	/* Decrease start filter date */
	$('#filterDateDown').click(function() {
		var date = $('#datePickerStart').datepicker('getDate');
		if (!!date && date instanceof Date) {
			phenomenonRangeNorm.incrementInputDate(date, -1);
			if (date.getTime() < phenomenonRangeNorm.Start.getTime()) {
				date = strPhenomenonStartDate
			}
			$('#datePickerStart').datepicker("update", date);
		}
	});
	
	/* Increase end filter date */
	$('#filterDateUp').click(function() {
		var date = $('#datePickerEnd').datepicker('getDate');
		if (!!date && date instanceof Date) {
			phenomenonRangeNorm.incrementInputDate(date, 1);
			if (date.getTime() > phenomenonRangeNorm.End.getTime()) {
				date = strPhenomenonEndDate
			}
			$('#datePickerEnd').datepicker("update", date);
		}
	});
	
	/* Set final end filter date */
	$('#filterDateLast').click(function() {
		$('#datePickerEnd').datepicker(
			"update", strPhenomenonEndDate);
	});
	
	/* Reload Observations data */
	$('#filterRefresh').click(function() {
		
		// compose filter date query
		var dtStart = correctDatePickerDate($("#datePickerStart"));
		var dtEnd = correctDatePickerDate( $("#datePickerEnd"));
		var dateRange = new SensorThingsDateRange().getFilterRange(dtStart, dtEnd);
		pageData['queryParams'] = dateRange.getQueryParams();
		
		// clear and reload data
		var table = $('#valori').DataTable();
		table.clear().draw();
		table.ajax.reload();
	});
	
	/* Download CSV */
	$('#downloadCsv').click(function() {
		
		// compose filter date query
		var dtFrmStart = $("#dateCsvPickerStart").datepicker("getFormattedDate");
		var dtFrmEnd = $("#dateCsvPickerEnd").datepicker("getFormattedDate");
		var dtStart = correctDatePickerDate($("#datePickerStart"));
		var dtEnd = correctDatePickerDate( $("#datePickerEnd"));
		var dateRange = new SensorThingsDateRange().getFilterRange(dtStart, dtEnd);
		var queryParams = dateRange.getQueryParams();
		var url = [
			
			(propData['Observations@iot.navigationLink'] || ''),
			queryParams 
		
		].join('?');
		
		// compose file name
		var propName = propData['name'] || 'Osservazioni';
		propName.replace(/\s/g, "-");
		
		var fileName = [			
			propName,
			localizer.formatCompactedInternationalDate(dateRange.Start),
		    localizer.formatCompactedInternationalDate(dateRange.End)
		].join('_');
		
		// close modal
		$('#exportModal').modal('toggle');
		//$('#exportModal').hide();
		
		// export CSV
		pyjsapi.exportCSV(url, {
			
			"fileName": fileName,
			"exportFields": exportFields,
			"dataSrc": "value",
			"openFile": $('#exportOpenFlag').is(":checked"),
			"dateRange": dtFrmStart + ' - ' + dtFrmEnd
		});
	});
	
	/* On show modal */
	$('#exportModal').on('show.bs.modal', function (event) {
		// set module filter date from search
		var strFilterStartDate = 
			$('#datePickerStart').datepicker('getFormattedDate');
		var strFilterEndDate = 
			$('#datePickerEnd').datepicker('getFormattedDate');
		$('#dateCsvPickerStart').datepicker(
			"update", strFilterStartDate);
		$('#dateCsvPickerEnd').datepicker(
			"update", strFilterEndDate);
	});
	
	/***********************************************
	 * Final settings 
     ***********************************************/
	
	/* adjust chart hight */
	$( window ).trigger('resize');
});