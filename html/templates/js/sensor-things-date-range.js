/**
 * SensorThings API Plugin
 *
 *  Date utility functions.
 *
 */

/**
 * Utility class to manage date range
 */
class SensorThingsDateRange {
	constructor(dtStart, dtEnd, locale) {
		this.dayElapse = 86400000; //60 * 60 * 24 * 1000 ms
		this.dateStart = null;
		this.dateEnd = null;
		this.setDates(dtStart, dtEnd);
	}
	
	get Start() {
		return new Date(this.dateStart);
	}
	
	get End() {
		return new Date(this.dateEnd);
	}
	
	isValid() {
		return !(this.dateStart.getTime() > this.dateEnd.getTime());
	}
	
	normalize() {
		var dtStart = this.correctUtcDate(this.dateStart, 0, 0, 0, 0);
		var dtEnd = this.correctUtcDate(this.dateEnd, 23, 59, 59, 999);
		this.setDates(dtStart, dtEnd);
		return this;
	}
	
    incrementInputDate(date, numDays) {
		try {
			date.setTime(date.getTime()+(numDays*86400000)); //60 * 60 * 24 * 1000 ms
		} catch (error) {
			console.error(error);
		}
		return date;
	}
	
	setDates(dtStart, dtEnd) {
		try {
			this.dateStart = new Date(dtStart);
		} catch (error) {
			console.error(error);
			this.dateStart = new Date();
		}
		
		try {
			this.dateEnd = new Date(dtEnd);
		} catch (error) {
			console.error(error);
			this.dateEnd = new Date();
		}
	}
	
	parsePhenomenonTime(value) {
		var dates = String(value).split("/");
		dates.push(dates[0]);
		this.setDates(dates[0], dates[1]);
		return this;
	}
	
	correctUtcDate(date, hh, mm, ss, ms) {
		try {
			var date = new Date(date);
			var day = date.toLocaleString('it', { day: "2-digit" });
			var month = date.toLocaleString('it', { month: "2-digit" });
			var year = date.toLocaleString('it', { year: "numeric" });
			return new Date( parseInt(year), parseInt(month)-1, parseInt(day), hh, mm, ss, ms );
			
		} catch (error) {
			console.error(error);
			return new Date();
		}
	}
	
	
	getFilterRange(dtStart, dtEnd) {
		var dtRange = new SensorThingsDateRange(dtStart, dtEnd);
		dtRange.normalize();
		return dtRange;
	}
	
	getFilterRangeByDelta(dtFirst, numDays) {
		try {
			var dtSecond = new Date(dtFirst);
			dtSecond.setTime(dtSecond.getTime()+(numDays*this.dayElapse));
			if (numDays < 0) {
				return this.getFilterRange(dtSecond, dtFirst);
			}
			return this.getFilterRange(dtFirst, dtSecond);	
					
		} catch (error) {
			console.error(error);
			return new SensorThingsDateRange(this.dateStart, this.dateEnd);
		}
	}
	
	getQueryParams() {
		
		var filter = encodeURIComponent([
			
			"phenomenonTime ge",
			this.dateStart.toISOString(),
			"and phenomenonTime le",
			this.dateEnd.toISOString()
			
		].join(" "));
		
		return [
			"$top=2147483647",
			"$orderby=phenomenonTime+desc",
			["$filter", filter].join("=")
		].join("&")
	}
	
	toString() {
		
		return [
			this.dateStart.toISOString(),
			this.dateEnd.toISOString()
		].join('/');
	}
}
