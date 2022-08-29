# SensorThingsAPI QGIS plugin
The SensorThings API plugin for QGIS has been developed by Deda Next (former Dedagroup Public Services, https://www.dedanext.it/) within the AIR-BREAK project (co-funded by UIA program, https://www.uia-initiative.eu/en/uia-cities/ferrara).

The plugin enables QGIS software (www.qgis.org) to access dynamic data from sensors, using SensorThings API protocol (https://www.ogc.org/standards/sensorthings)

The overall objective is to provide functionalities for accessing SensorThings API endpoints and interact with temporal data (timeseries).

Hereafter, you find "how-to" instructions for using the SensorThingsAPI plugin in QGIS. 

**To correctly download the plugin from this repository as zip file, please see Issue https://github.com/AirBreak-UIA/SensorThingsAPI_QGIS-plugin/issues/1**

1)	Once installed (as local zip file), the user interface shows a simple menu and a toolbar with two commands:
-	Upload 'SensorThingsAPI' layer from remote server
-	Show location information

Note: the following screenshots show the user interface in Italian.

<img width="208" alt="SensorThingsAPI menu" src="https://user-images.githubusercontent.com/110025591/181604383-cba059b8-89fc-4ae1-bac2-887287ba6aa2.png">

2)	The command Upload 'SensorThingsAPI' layer from remote server allows to add the Locations of a SensorThings endpoint as a geographical layer; in the popup window, select the button New and write the name and the URL of the endpoint to connect to: 
 
<img width="416" alt="New SensorThingsAPI endpoint" src="https://user-images.githubusercontent.com/110025591/181604880-6bef7010-a593-43cd-9f5d-c04313552baf.png">

To test the plugin, the following endpoints can be configured:
-	https://iot.comune.fe.it/FROST-Server/v1.1/Locations (data about air quality, bike transits, traffic by Municipality of Ferrara, Italy)
-	https://airquality-frost.k8s.ilt-dmz.iosb.fraunhofer.de/v1.1/Locations (data about air quality from AQ stations in Europe, by Fraunhofer Institute, Germany)
- https://demography.k8s.ilt-dmz.iosb.fraunhofer.de/v1.1/Locations (demographic statistics, by Fraunhofer Institute, Germany)
-	https://iot.hamburg.de/v1.1/Locations (by City of Hamburg)
-	https://ogc-demo.k8s.ilt-dmz.iosb.fraunhofer.de/v1.1/Locations (water data by OGC)
-	http://covidsta.hft-stuttgart.de/server/v1.1/Locations (COVID data by HFT Stuttgart, Germany)

... other public endpoints also available at https://github.com/opengeospatial/sensorthings/blob/master/PublicEndPoints.md


Click the Connect button to list all the locations available and optionally filter them using their own properties; select one or more items and clic the button Add (or double clic).

<img width="421" alt="List of Locations (grouped by properties)" src="https://user-images.githubusercontent.com/110025591/181605595-d32b7b29-b68a-4143-a2ab-1e66ab738a09.png">

... once selected the Locations to be added in the map, you will see something like this:

<img width="960" alt="Map with Locations from SensorThings server" src="https://user-images.githubusercontent.com/110025591/181605921-3ef9ed37-4948-4fc0-b659-dd290c7691c9.png">

3)	the command "Show location information" opens a new popup window to query a single location; when the location is clicked on the map, the popup appears with the list of Datastreams (measured parameter) available:

<img width="691" alt="Show location information" src="https://user-images.githubusercontent.com/110025591/181607537-35ed6065-6e95-4410-8061-627aa8092dae.png">

4) by clicking on the right-side button, user has the possibility to access timeseries (observations) for each parameter and get data in either tabular or chart formats, with the possibility to change temporal filter (dates from/to):

<img width="564" alt="Data table" src="https://user-images.githubusercontent.com/110025591/181607752-46ddd0fc-2bb9-41aa-99bb-4cd224021f23.png">

5) User can also download data (bottom-right icon) in CSV format and elaborate them in spreadsheets or other software:

<img width="565" alt="Data chart and download" src="https://user-images.githubusercontent.com/110025591/181607891-b8cb5a2c-0f2f-47a9-a78e-c14460bb8114.png">
