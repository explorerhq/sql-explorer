/*global _ */

function Utils() {}

Utils.log10Floor = function (val) {
  return Math.floor(Math.log(val) / Math.LN10, 0)
}

Utils.getUrlParameters = function () {
  var string = window.location.search.slice(1)
  return string ? JSON.parse(decodeURIComponent(string)) : []
}

Utils.addParamToUrl = function (url, paramName, paramValue) {
  if (url.indexOf(paramName + '=') >= 0) {
    var prefix = url.substring(0, url.indexOf(paramName))
    var suffix = url.substring(url.indexOf(paramName));
    suffix = suffix.substring(suffix.indexOf('=') + 1);
    suffix = (suffix.indexOf('&') >= 0) ? suffix.substring(suffix.indexOf('&')) : '';
    return prefix + paramName + '=' + paramValue + suffix;
  }
  var separator = url.indexOf('?') < 0 ? '?' : '&'
  return url + separator + paramName + '=' + paramValue
}

Utils.camelToHyphen = function (string) {
  return string.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase()
}

Utils.stringToNumber = function (string) {
  return  +String(string).replace(/[^0-9\.\-]/g, '') || 0
}

Utils.addCommaSeparator = function (val) {
  return val.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

Utils.getRoundedValue = function (string, extent) {
  var val = Utils.stringToNumber(string)

  // round to the same decimal if all values are within 2 orders of magnitude (e.g., 10-1,000)
  var maxOrdersDiff = 2

  // always show 3 digits
  var digitsVisible = 3

  // find how many orders apart the max/min are to determine how much to round
  var ordersLow = Utils.log10Floor(Math.abs(extent[1]))
  var ordersHigh = Utils.log10Floor(Math.abs(extent[0]))
  var ordersDiff = Math.abs(ordersLow - ordersHigh)
  var ordersMax = Math.max(ordersLow, ordersHigh)
  var ordersToUse = ordersDiff <= maxOrdersDiff ? ordersMax : Utils.log10Floor(Math.abs(val))

  return this.roundToDecimalOrder(val, ordersToUse, digitsVisible)
}

Utils.roundToDecimalOrder = function (val, decimalOrder, digitsVisible) {
  if (decimalOrder < -3) {
    // when the val is below 0.001, just show the full value
    return val
  } else if (decimalOrder < 3) {
    // when the val is from 0.001 to 99, don't show extra decimals
    var roundToDigits = Math.max(digitsVisible - decimalOrder - 1, 0)
    return val.toFixed(roundToDigits)
  }
  var units = ['K', 'M', 'B', 'T']
  var commasToUse = Math.min(Math.floor(decimalOrder / 3), units.length)
  var divisor = Math.pow(1000, commasToUse)
  var decimals = Math.max(0, (commasToUse * 3) - decimalOrder + digitsVisible - 1)
  var thisUnit = units[commasToUse - 1]
  var thisVal = Utils.addCommaSeparator((val / divisor).toFixed(decimals))
  return thisVal + thisUnit
}

Utils.getNiceIntervals = function (range, height) {
  var rangeWithZero = [Math.min(0, range[0]), Math.max(0, range[1])]
  var fullRange = Math.max(rangeWithZero[1] - rangeWithZero[0])

  // include no more than 5 ticks spaced at least 50px apart
  var minDistance = 40
  var maxTicks = 5
  var maxPotentialTicks = Math.floor(Math.min(height / minDistance, maxTicks))

  // get the smallest nice interval value that produces no more than the max potential ticks
  var minInterval = fullRange/maxPotentialTicks
  var minMultipleOf10 = Math.pow(10, Utils.log10Floor(minInterval) + 1)
  var interval = minMultipleOf10
  _.each([2, 4, 5, 10], function (divisor) {
    var thisInterval = minMultipleOf10 / divisor
    interval = thisInterval >= minInterval ? thisInterval : interval
  })

  // get the appropriate digits to round the labels
  var intervalOrders = Utils.log10Floor(Math.abs(interval))
  var maxOrders = Utils.log10Floor(Math.max(Math.abs(rangeWithZero[0]), Math.abs(rangeWithZero[1])))
  var extraDigit = interval / Math.pow(10, intervalOrders) === 2.5 ? 1 : 0 // need extra digit if it's a quarter interval
  var digitsToUse = 1 + maxOrders - intervalOrders + extraDigit

  // get the intervals
  var niceIntervals = []
  var firstInterval = Math.ceil(rangeWithZero[0] / interval) * interval
  var currentInterval = firstInterval
  while (currentInterval < (range[1] + interval)) {
    var intervalObject = {
      value: currentInterval,
      displayString: currentInterval === 0 ? '0' : Utils.roundToDecimalOrder(currentInterval, maxOrders, digitsToUse),
      rawString: currentInterval === 0 ? '0' : Utils.roundToDecimalOrder(currentInterval, Math.min(0, maxOrders), 0)
    }
    currentInterval += interval
    niceIntervals.push(intervalObject)
  }

  return niceIntervals
}

Utils.getTrimmedExtent = function (array) {
  var firstNonEmptyItem = 0
  var lastNonEmptyItem = 0

  array.forEach(function (value, i) {
    if (value === '' && i === firstNonEmptyItem) {
      firstNonEmptyItem = i + 1
    } else if (value !== '') {
      lastNonEmptyItem = i
    }
  })

  return [firstNonEmptyItem, lastNonEmptyItem]
}
