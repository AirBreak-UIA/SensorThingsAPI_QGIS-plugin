/**
 * SensorThings API Plugin
 *
 *  sensor-things.it.js
 *
 */

!function (a) {
	a.fn.sensorthings = a.fn.sensorthings || {};
    a.fn.sensorthings.it = {
		"Dictionary": {
			
			"DataStreamTitle": "Osservazioni disponibili",                        // Available observations
			"MultiDataStreamTitle": "Serie temporali complesse",                  // Complex time series
			
			"Name": "Nome",                                                       // Name
			"Description": "Descrizione",                                         // Description
			"Ref. dates": "Date rif.",                                            // Ref. dates
			"Observed property": "Proprietà misurata",                            // Observed property
			"Sensor": "Sensore",                                                  // Sensor
			"Observations":  "Osservazioni",                                      // Observations
			
			"Location": "Postazione",                                             // Location
	        "Station": "Stazione",                                                // Station
	        "ObsProperties": "Proprietà osservate",                               // Observed Properties
		
		    "Values": "Valori",                                                   // Values
	        "Chart": "Grafico",                                                   // Chart
	
	        "ExportDates": "Indica il periodo per l'esportazione del CSV",        // Indicates the period for CSV exporting
	        "FromDate": "Da:",                                                    // From:
	        "ToDate": "A:",                                                       // To:
	        "Download": "Scarica",                                                // Download
	        "Cancel": "Annulla",                                                  // Cancel
	        "Open": "Apri",                                                       // Open
	        
	        "NoDateBefore": "Non esistono osservazioni precedenti a questa data", // There are no observations prior to this date
	        "MoveToBegin": "Sposta all'inizio",                                   // Move to the beginning
	        "MoveBack": "Sposta indietro",                                        // Move back
			"MoveForward": "Sposta avanti",                                       // Move forward
	        "MoveToEnd": "Sposta alla fine",                                      // Move to the end
	        "LastObsDate":"Data ultima osservazione",                             // Last observation date
	        "Update": "Aggiorna",                                                 // Update
	        "DownloadCSV": "Scarica CSV",                                         // Download CSV
	
	        "Value": "Valore",                                                    // Value
	        "Start time": "Tempo Inizio",                                         // Start time
	        "End time": "Tempo Fine",                                             // End time
	        "Start: ": "Inizio: ",                                                // Start: 
	        "End  : ": "Fine  : ",                                                // End  :
	
	        "Europe/Rome": "Europa/Roma"                                          // Europe/Rome 
		},
		
		"DatePickerFormat": "dd-mm-yyyy"
    }
}
(jQuery);