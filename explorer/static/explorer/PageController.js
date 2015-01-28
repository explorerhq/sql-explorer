/*global $, _, PageData, Chart, Utils */

function PageController () {
  this.DARK = 'dark'
  this.LIGHT = 'light'
  this.chartObjects = []

  // default values are first
  this.OPTIONS = {
    type: ['column', 'line'],
    rounding: ['on', 'off']
  }
  this.EDITABLES = ['title',]

  this.$body = $('body')
  this.$charts = $('.charts')

  // re-render charts on window resize
  $(window).resize(function () {
    clearTimeout(this.resizeTimer)
    this.resizeTimer = setTimeout(function () {
      this.setDimensions()
    }.bind(this), 30)
  }.bind(this))
}


PageController.prototype.setupPage = function (urlParameters) {
  this.$body.addClass('loading')
  this.parameters = urlParameters
  this.parameters.charts = this.parameters.charts || [{}]
  this.clearExisting()
  this.resetCharts()
}


PageController.prototype.clearExisting = function () {
  $('.chart-wrapper').remove()
  this.chartObjects = []
  $('body').unbind()
}


PageController.prototype.resetCharts = function () {
  this.fetchData(this.parameters.dataUrl, function (data) {
    this.data = data

    // set first title
    if (!this.parameters.charts[0].title) {
      this.parameters.charts[0].title = data.getSeriesCount() > 1 ? 'Chart' : data.getSeries(0).label
    }

    this.$body.removeClass('pre-load loading error')

    // update charts
    this.parameters.charts.forEach(function (chart, i) {
      this.updateChart(i)
    }.bind(this))

    this.setDimensions()
  }.bind(this))
}


PageController.prototype.fetchData = function (dataUrl, callback) {
  new PageData(dataUrl, function (error, data) {
    if (error) {
      return this.errorNotify(error)
    }

    callback(data)
  }.bind(this))
}


PageController.prototype.updateChart = function (chartIndex) {
  var chartParams = this.getFullParams(chartIndex)

  // determine what to do with chart
  if (chartParams.series.length === 0) {
    // if there are no series, remove it
    this.removeChart(chartIndex)
  } else if (chartIndex <= this.chartObjects.length - 1) {
    // if it already exists, refresh it
    this.chartObjects[chartIndex].refresh(chartIndex, chartParams, this.data)
  } else {
    // if it doesn't exist yet, create it
    this.createNewChart(chartIndex, this.getFullParams(chartIndex))
  }
}


PageController.prototype.getFirstChartSeries = function () {
  var otherChartSeries = []
  var firstChartSeries = []

  for (var i = 1; i < this.parameters.charts.length; i++) {
    otherChartSeries = otherChartSeries.concat(this.parameters.charts[i].series)
  }

  for (var j = 0; j < this.data.getSeriesCount(); j++) {
    if (otherChartSeries.indexOf(j) > -1) continue
    firstChartSeries.push(j)
  }

  return firstChartSeries
}


PageController.prototype.createNewChart = function (thisChartIndex, initialChartParams) {
  var $el = $('<div class="chart-wrapper"></div>')
  var dimensions = this.getChartDimensions()
  $el.outerHeight(dimensions.height).outerWidth(dimensions.width)
  this.$charts.append($el)
  this.chartObjects.push(new Chart(this, thisChartIndex, $el, initialChartParams, this.data))
}


PageController.prototype.moveToChart = function (series, fromChartIndex, toChartIndex) {
  var fromChart = this.parameters.charts[fromChartIndex]
  var toChart = this.parameters.charts[toChartIndex]

  // remove default titles
  this.parameters.charts.forEach(function (chart, i) {
    if (chart.title && chart.title == this.getDefaultTitle(i)) {
      delete chart.title
    }
  }.bind(this))

  // add series to intended chart
  if (toChartIndex > this.parameters.charts.length - 1) {
    this.parameters.charts.push({series: [series]})
  } else if (toChartIndex > 0) {
    toChart.series.push(series)
    toChart.series.sort(function(a, b) {
      return a - b
    })
  }

  // remove series from initial chart
  if (fromChartIndex > 0) {
    fromChart.series = fromChart.series.filter(function (listedSeries) {
      return listedSeries !== series
    })
  }

  this.updateChart(toChartIndex)

  $('html, body').animate({
      scrollTop: this.chartObjects[toChartIndex].$wrapper.offset().top
  }, 300)

  this.updateChart(fromChartIndex)

  // update all charts that come after, since default titles may have changed
  for (var j = fromChartIndex; j < this.chartObjects.length; j++) {
    if (j === toChartIndex) continue
    this.updateChart(j)
  }

  this.setDimensions()
}


PageController.prototype.removeChart = function (chartIndex) {
  // need to increment down the chartIndex for every chart that comes after
  for (var i = chartIndex + 1; i < this.chartObjects.length; i++) {
    this.chartObjects[i].chartIndex--
  }

  // remove the parameters, html element, and overall chart object
  this.parameters.charts.splice(chartIndex, 1)
  this.chartObjects[chartIndex].$wrapper.remove()
  this.chartObjects.splice(chartIndex, 1)
}


PageController.prototype.getFullParams = function (chartIndex) {
  var params = this.parameters.charts[chartIndex]
  Object.keys(this.OPTIONS).forEach(function (option) {
    params[option] = params[option] || this.OPTIONS[option][0]
  }.bind(this))

  if (chartIndex === 0) {
    params.series = this.getFirstChartSeries()
  }

  params.title = params.title || this.getDefaultTitle(chartIndex)

  return params
}


PageController.prototype.getDefaultTitle = function (chartIndex) {
  var series = this.parameters.charts[chartIndex].series
  if (series.length === 1) {
    return this.getSeriesName(series[0])
  }
  var earlierCharts = this.parameters.charts.filter(function (chart, i) {
    return chart.series.length > 0 && i < chartIndex
  })
  return chartIndex === 0 ? 'Chart' : 'Chart ' + (1 + earlierCharts.length)
}


PageController.prototype.getSeriesNames = function () {
  if (! this.parameters.seriesNames) {
    this.parameters.seriesNames = {}
  }
  return this.parameters.seriesNames
}


PageController.prototype.getSeriesName = function (i) {
  if (! this.parameters.seriesNames || ! this.parameters.seriesNames[i]) {
    return this.data.getSerieses()[i].label
  } else {
    return this.parameters.seriesNames[i]
  }
}


PageController.prototype.getChartCount = function () {
  return this.parameters.charts.length
}


PageController.prototype.getOtherCharts = function (chartIndex) {
  return this.parameters.charts.map(function (chart, i) {
    return {
      title: chart.title || this.getDefaultTitle(i),
      chartIndex: i
    }
  }.bind(this)).filter(function (chart, i) {
    return i !== chartIndex
  })
}


PageController.prototype.updateSelectedX = function (index) {
  this.chartObjects.forEach(function (chart) {
    chart.updateSelectedX(index)
  })
}


PageController.prototype.toggleColor = function () {
  this.parameters.color = this.parameters.color === this.DARK ? this.LIGHT : this.DARK
  this.applyColor()
  this.chartObjects.forEach(function (chart) {
    chart.render()
  })
}


PageController.prototype.applyColor = function () {
  if (this.parameters.color == this.DARK) {
    this.$body.addClass(this.DARK)
  } else {
    this.$body.removeClass(this.DARK)
  }
}


PageController.prototype.getPageColor = function () {
  return this.parameters.color
}


PageController.prototype.getChartDimensions = function () {
  // get all values to use
  var minHeightForHalfHeight = 600
  var minWidthForHalfWidth = 1200
  var minWidthForFullHeight = 800
  var minPixelsPerDatum = 5
  var windowWidth = $(window).innerWidth()
  var windowHeight = 'innerHeight' in window ? window.innerHeight: document.documentElement.offsetHeight
  var approximateChartSpaceInGrid = (windowWidth / 2) - 200 //200px are taken up by the title/legend side pane
  var pixelsPerDatum = approximateChartSpaceInGrid / this.data.getDatumCount()
  var defaultHeight = windowWidth > minWidthForFullHeight ? windowHeight : 'auto'
  var chartCount = this.chartObjects ? this.chartObjects.length : 0

  // check conditions for adjusting dimensions
  var enoughWidthForHalfWidth = windowWidth > minWidthForHalfWidth && pixelsPerDatum >= minPixelsPerDatum
  var enoughHeightForHalfHeight = windowHeight > minHeightForHalfHeight && windowWidth > minWidthForFullHeight
  var enoughChartsForHalfWidth = chartCount >= 2
  var enoughChartsForHalfHeight = chartCount >= 3 || (chartCount === 2 && !enoughWidthForHalfWidth)

  // determine dimension types
  var useGrid = chartCount >= 3 && windowWidth > minWidthForHalfWidth && windowHeight > minHeightForHalfHeight
  var useHalfWidth = useGrid || (enoughWidthForHalfWidth && enoughChartsForHalfWidth)
  var useHalfHeight = useGrid || (enoughHeightForHalfHeight && enoughChartsForHalfHeight)

  /*return {
    width: useHalfWidth ? windowWidth / 2 : windowWidth,
    height: useHalfHeight ? windowHeight / 2 : defaultHeight,
    isHalfHeight: useHalfHeight,
    isGrid: useGrid || (enoughWidthForHalfWidth && enoughChartsForHalfWidth)
  }*/
  return {
    width: 1140,
    height: 500,
    isHalfHeight: useHalfHeight,
    isGrid: useGrid || (enoughWidthForHalfWidth && enoughChartsForHalfWidth)
  }
}


PageController.prototype.setDimensions = function () {
  var dimensions = this.getChartDimensions()
  if (dimensions.isGrid) {
    this.$body.addClass('chart-grid')
    this.$body.removeClass('half-height')
  } else if (dimensions.isHalfHeight) {
    this.$body.removeClass('chart-grid')
    this.$body.addClass('half-height')
  } else {
    this.$body.removeClass('chart-grid half-height')
  }
  $('.chart-wrapper').outerHeight(dimensions.height).outerWidth(dimensions.width)

  var bottomRowIndex = Math.floor((this.chartObjects.length - 1) / 2) * 2
  this.chartObjects.forEach(function (chart, i) {
    if (dimensions.isGrid && i >= bottomRowIndex) {
      chart.$wrapper.addClass('bottom-row')
    } else {
      chart.$wrapper.removeClass('bottom-row')
    }
    chart.render()
  })
}


PageController.prototype.errorNotify = function (error) {
  /*jshint devel:true */

  this.$body.addClass('error').removeClass('loading')
  var displayMessage = error.message || 'There’s been an error. Please check that you are using a valid .csv file. If you are using a Google Spreadsheet or Dropbox link, the privacy setting must be set to shareable.'
  $('.error-message').html(displayMessage)

  if(error && error.reponseText) {
    console.error(error.responseText)
  }
}


PageController.prototype.useUrl = function () {
  var urlParameters = Utils.getUrlParameters()

  // support prior csvUrl parameter
  urlParameters.dataUrl = urlParameters.csvUrl || urlParameters.dataUrl

  if (!urlParameters.dataUrl) return
  $('.data-input').val(urlParameters.dataUrl)
  this.setupPage(urlParameters)
}