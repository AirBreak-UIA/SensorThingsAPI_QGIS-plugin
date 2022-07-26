/**
 * SensorThings API Plugin
 *
 *  Promise utility functions.
 *
 */


/**
 * Returns a promise about an asyncronous request
 * done by QGIS Api via Python injected object
 * (pyjsapi.getRequest)
 */
function requestPromise(url, options) {
	return new Promise((resolve, reject) => {
		var request = pyjsapi.getRequest();
		if (!request) {
			return reject("Impossibile istanziare una promessa di tipo Request.")
		}
		request.resolved.connect(resolve);
		request.rejected.connect(reject);
		request.get(url, options);
	});
}
