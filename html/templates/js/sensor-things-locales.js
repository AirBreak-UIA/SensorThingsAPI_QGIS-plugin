/**
 * SensorThings API Plugin
 *
 *  Localization utility functions.
 *
 */

/****************************************************************************
 * Sensor Things class to manage localization  
 ****************************************************************************/
function SensorThingsLocales(language) {
	// get language dictionary
	language = ''+language;
	var langSetting = jQuery.fn.sensorthings && jQuery.fn.sensorthings[language];
	// store loacale code
	this.locale = (!!langSetting) ? language : 'en';
	// cache
	this.cached = {
		"dateRangeValue": "",
		"dateRangeArray": ['','']
	}
}

/****************************************************************************
 * Static method to get a new Localilizer object
 ****************************************************************************/
SensorThingsLocales.getLocalizer = function(language) {
	return new SensorThingsLocales(language);
}

/****************************************************************************
 * Method to get Sensor Things locale dictionary defined as 
 * jQuery.fn.sensorthings[<language>].
 ****************************************************************************/
SensorThingsLocales.prototype.getCode = function () {
	return this.locale;
}

/****************************************************************************
 * Method to get Sensor Things locale dictionary defined as 
 * jQuery.fn.sensorthings[<language>].
 ****************************************************************************/
SensorThingsLocales.prototype.getLangDictionary = function () {
	return jQuery.fn.sensorthings && 
	       jQuery.fn.sensorthings[this.locale] && 
           jQuery.fn.sensorthings[this.locale]['Dictionary'];
}

/****************************************************************************
 * Method to get Date Picket format
 ****************************************************************************/
SensorThingsLocales.prototype.getDatePickerFormat = function (options) {
	options = options || {}
	var format = (jQuery.fn.sensorthings && 
	              jQuery.fn.sensorthings[this.locale] && 
                  jQuery.fn.sensorthings[this.locale]['DatePickerFormat']) || 
                 'mm-dd-yyyy';

    if (!!options.twoDigitYear) {
		format = format.replace('yyyy', 'yy');
	}
	return format;
}

/****************************************************************************
 * Method to replace element text from Sensor Things locale dictionary 
 * Element must have attribute:
 *     data-langkey       for text translation
 *     data-langtipkey    for tooltip translation
 ****************************************************************************/
SensorThingsLocales.prototype.processLangDocument = function () {
	// get language dictionary
	var langDict = this.getLangDictionary();
	if (!langDict) {
		return;
	}
	// loop tags for text
    var tags = document.querySelectorAll('span,img,a,label,li,option,h1,h2,h3,h4,h5,h6,button');
    Array.from(tags).forEach(function(elem, _){
	    // get language key attribute
        var key = elem.dataset.langkey;
        if (!!key) {
			// get translation
			var translation = langDict[key];
			if (!!translation) {
				elem.innerText = translation;
			}
		} 
    });
	// loop tags for tooltip
    var tags = document.querySelectorAll('button');
	Array.from(tags).forEach(function(value, index){
	    // get language key attribute
        var key = value.dataset.langtipkey;
        if (!!key) {
			// get translation
			var translation = langDict[key];
			if (!!translation) {
				value.title = translation;
			}
		} 
    });
}

/****************************************************************************
 * Method to translate a text from Sensor Things locale dictionary.
 ****************************************************************************/
SensorThingsLocales.prototype.translate = function (value) {
	// get language dictionary
	var langDict = this.getLangDictionary();
	if (!langDict) {
		return value;
	}
	// translate
	value = ''+value;
	var translation = langDict[value];
	if (!!translation) {
		return translation;
	}
	return value;
}

/****************************************************************************
 * Method to get the system time zone name; if language parameter is
 * defined, tries to translate.
 ****************************************************************************/
SensorThingsLocales.prototype.getTimezone = function () {
	var res = ''+Intl.DateTimeFormat().resolvedOptions().timeZone;
	return this.translate(res);
}

/****************************************************************************
 * Method to format a phenomenon time sting (date range) with localization.
 ****************************************************************************/
SensorThingsLocales.prototype.formatPhenomenonTime = function (value) {
	// init
	if (!value) {
		return this.translate("N.D.");
	}
	value = String(value);
	
	// format date range
	try {
		var arOut = []
		var dateArray = String(value).split("/");
		for (var i = 0; i < dateArray.length; i++) {
		    var d = new Date(dateArray[i]);
			var s = d.toLocaleString(this.locale, {
				day: "2-digit",    // numeric, 2-digit
				year: "numeric",   // numeric, 2-digit
				month: "short",    // numeric, 2-digit, long, short, narrow
			}).replace(",", "");
			arOut.push(s);
		}
		return arOut.join(" - ");
		
	} catch (error) {
		console.log(error);
		return value;
	}
}

/****************************************************************************
 * Method to format a phenomenon time string(date range) as an array of 
 * formatted date string with localization.
 * Return always an array of two string(start time, end time), at leat empty.  
 ****************************************************************************/
SensorThingsLocales.prototype.formatCompactPhenomenonTimeAsArray = function (value) {
	// init
	value = String(value || "");
	var arOut = [];
	
	// check if cached
	if (value == this.cached.dateRangeValue) {
		arOut = this.cached.dateRangeArray.map((x) => x);
		
	} else {
		try {
			// split date range
			var dateArray = String(value).split("/");
			// format date array
			for (var i = 0; i < dateArray.length; i++) {
			    var d = new Date(dateArray[i]);
				var s = d.toLocaleString(this.locale, {
					day: "2-digit",
					month: "2-digit",
					year: "numeric",
					hour: 'numeric', 
					minute: 'numeric', 
					second: 'numeric',
					hour12: false
				}).replace(",", "");
				arOut.push(s);
			}
			// cache result
			this.cached.dateRangeValue = value;
			this.cached.dateRangeArray = arOut.map((x) => x);
			
		} catch (error) {
			console.log(error);
		}
	}
	
	// check if arraay contains two values
	var len = arOut.length;
	if (len < 1) {
		arOut.push('');
	}
	if (len < 2) {
		arOut.push('');
	}
	
	// return formatted date array
	return arOut;
}


/****************************************************************************
 * Method to format a date(timestamp) as international date without 
 * separator:
 *              YEAR(4 chars) + MONTH(2 chars) + DAY(2 char)  
 ****************************************************************************/
SensorThingsLocales.prototype.formatCompactedInternationalDate = function (value) {
	try {
		var date = new Date(value);
		var day = date.toLocaleString(this.locale, { day: "2-digit" });
		var month = date.toLocaleString(this.locale, { month: "2-digit" });
		var year = date.toLocaleString(this.locale, { year: "numeric" });
		return year + month + day;			
	} catch (error) {
		console.error(error);
		return '';
	}
}


/****************************************************************************
 * Method to create an UTC date from a local date 
 ****************************************************************************/
SensorThingsLocales.prototype.getUtcDatefromLocal = function (aDate) {
	var date = new Date(aDate);
	var day = date.toLocaleString(this.locale, { day: "2-digit" });
	var month = date.toLocaleString(this.locale, { month: "2-digit" });
	var year = date.toLocaleString(this.locale, { year: "numeric" });
	return new Date( Date.UTC( parseInt(year), parseInt(month)-1, parseInt(day) ) );
}