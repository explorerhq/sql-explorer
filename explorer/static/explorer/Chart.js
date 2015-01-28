/*global $, d3, _, ChartData, ChartLegend, Utils */

function Chart(pageController, chartIndex, $wrapper, params, data) {
  this.pageController = pageController
  this.$wrapper = $wrapper

  // create initial HTML
  this.$wrapper.html(this.chartHTML())

  // cache elements
  this.$container = $wrapper.find('.chart').first()
  this.$plot = this.$container.find('.chart-plot').first()
  this.$xBeg = this.$container.find('.x-beginning')
  this.$xEnd = this.$container.find('.x-end')
  this.$selectionElem = this.$container.find('.selection')
  this.$selectionXLabel = this.$container.find('.selection-xlabel')
  this.$selectionYLabel = this.$container.find('.selection-ylabel')
  this.$yAxis = this.$container.find('.y-axis')
  this.$zeroLine = this.$container.find('.zero-line')
  this.$selectionValue = this.$container.find('.selection-value')
  this.$optionsElem = this.$container.find('.chart-options')
  this.$chartDescription = this.$container.find('.chart-description')

  // refresh chart and bind interactions
  this.refresh(chartIndex, params, data)
  this.bindInteractions()
}

Chart.prototype.refresh = function (chartIndex, params, data) {
  this.chartIndex = chartIndex
  this.params = params
  this.data = new ChartData(data, this.params.series)
  this.legend = new ChartLegend(this.pageController, this.data, this)

  this.setupChart()
  this.render()
}

Chart.prototype.setupChart = function () {
  // Clear any existing plot
  this.$plot.empty()

  // Update chart UI
  this.pageController.EDITABLES.forEach(function (item) {
    this.$container.find('.' + Utils.camelToHyphen(item)).text(this.params[item])
    this.updateEditablePlaceholder(item)
  }.bind(this))
  this.$xBeg.html(this.data.getIndexExtent()[0])
  this.$xEnd.html(this.data.getIndexExtent()[1])

  this.setScales()
  this.createChartElements()
}

Chart.prototype.setScales = function () {
  // set x- and y-axis scales and position functions
  this.xScale = d3.scale.linear().domain([0, this.data.getIndexCount()])
  this.xPosition = function (d) {
    return Math.floor(this.xScale(d.x), 0)
  }.bind(this)
  this.xBarWidth = function (d) {
    // have a pixel space when columns are at least 8px wide
    var space = this.plotWidth / this.data.getIndexCount() >= 8 ? 1 : 0
    var nextXScale = d.x + 1 < this.data.getIndexCount() ? this.xScale(d.x + 1) : this.plotWidth
    return Math.floor(nextXScale, 0) - this.xPosition(d) - space
  }.bind(this)
  this.xPositionLine = function (d) {
    return this.xPosition(d) + 0.5 * this.xBarWidth(this.data.getDatum(0, d.x))
  }

  this.yScale = d3.scale.linear()
  this.yPosition = function (d) {
    return this.yScale(d.y)
  }.bind(this)
  this.yPositionStacked = function (d) {
    return this.yScale(d.y1)
  }.bind(this)
  this.yHeightStacked = function(d) {
    return d.y === 0 ? 0 : this.yScale(d.y0) - this.yScale(d.y1) + 1
  }.bind(this)

  // set stacked and unstacked y ranges
  this.yRangeStacked = this.data.getStackedExtent()
  this.yRangeUnstacked = this.data.getUnstackedExtent()

  // set color scales
  this.colorLight = ['#333333']
  this.colorDark = ['#FFFFFF']
  this.colorRange = ['#6DCC73', '#1D7775', '#4FCFD5', '#FCE651', '#FF7050', '#FFC050', '#999999']
  this.color = d3.scale.ordinal().domain(this.data.getSeriesLabels())
  this.colorFn = function (yLabel) {
    return this.color(yLabel)
  }.bind(this)
}

Chart.prototype.createChartElements = function () {
  this.svg = d3.select(this.$plot.get(0)).append('svg')
  this.line = d3.svg.line()
    .interpolate('cardinal')
    .tension(0.96)
    .x(this.xPositionLine)
    .y(this.yPosition)
  this.layerGroup = this.svg.append('g')
    .attr('class', 'layers')
  this.layers = this.layerGroup.selectAll('g')
    .data(this.data.getSeriesLabels())
    .enter().append('g')
    .attr('class', 'layer')

  var _this = this
  this.layers.each(function (yLabel, i) {
    var layer = d3.select(this)
    layer.append('path')
      .attr('class', 'line')
      .each(function () {
        _this.data.getSeries(i).lineEl = this
      })
    layer.selectAll('rect')
      .data(_this.data.getValuesForSeries(i))
      .enter().append('rect')
      .attr('class', 'column')
      .each(function (d) {
        _this.data.getDatum(i, d.x).columnEl = this
      })
    layer.append('circle')
      .attr('class', 'end-dot last-dot')
      .attr('r', 3)
    layer.append('circle')
      .attr('class', 'end-dot first-dot')
      .attr('r', 3)
    layer.append('circle')
      .attr('class', 'selected-dot')
      .attr('r', 4)
  })
}

Chart.prototype.updateSizes = function () {
  this.margin = {top: 4, right: 4, bottom: 0, left: 0}
  this.width = this.$plot.width()
  this.plotWidth = this.width - this.margin.right - this.margin.left
  this.height = this.$plot.height()
  this.svg.attr('width', this.width).attr('height', this.height)
  this.xScale.range([this.margin.left, (this.width - this.margin.right - this.margin.left)])
  this.yScale.range([this.height - this.margin.bottom, this.margin.top])
  this.xEndEdge = this.$xEnd.offset().left - this.$plot.offset().left
  this.xBegEdge = this.$xBeg.offset().left - this.$plot.offset().left + this.$xBeg.width()
}

Chart.prototype.render = function () {
  this.updateSizes()

  // apply general rounding and background color
  if (this.params.rounding === 'off') {
    this.$container.addClass('rounding-off')
  } else {
    this.$container.removeClass('rounding-off')
  }

  // go to last point and refresh chart
  this.selectedX = this.data.getIndexCount() - 1
  this.applyChartColors()
  this.applyChartType()
  this.updateYAxis()
  this.plotAll()
  this.updateSelectedX()
  this.legend.update()
}

Chart.prototype.applyChartColors = function () {
  this.colorBase = this.pageController.getPageColor() === 'dark' ? this.colorDark : this.colorLight
  var colorsToUse = this.data.getSeriesCount() === 1 ? this.colorBase : this.colorRange
  this.color.range(colorsToUse)

  var _this = this
  this.layers.each(function (yLabel) {
    var layer = d3.select(this)
    layer.selectAll('.line')
      .attr('stroke', _this.colorFn(yLabel))
    layer.selectAll('.column, .selected-column, .selected-dot, .end-dot')
      .attr('fill', _this.colorFn(yLabel))
  })
}

Chart.prototype.applyChartType = function () {
  if (this.params.type === 'column') {
    this.$container.addClass('show-columns')
    this.yRange = this.yRangeStacked
    this.focusedSeriesIndex = this.data.getSeriesCount()
  } else {
    this.$container.removeClass('show-columns')
    this.yRange = this.yRangeUnstacked

    // focus the series with the max value at the selected point
    var dataAtLastIndex = this.data.getUnstackedValuesAtIndex(this.selectedX)
    this.focusedSeriesIndex = dataAtLastIndex.indexOf(d3.max(dataAtLastIndex)) // TODO
  }

  // yScale range should always include 0, abd add 10% margin for negatives; TODO: make margin pixel based
  var adjustExtent = function (extent) {
    var min = extent[0] < 0 ? extent[0] * 1.1 : 0
    return [min, Math.max(0, extent[1])]
  }
  this.yScale.domain(adjustExtent(this.yRange))
}

Chart.prototype.plotAll = function () {
  var _this = this
  this.layers.each(function (yLabel, i) {
    var layer = d3.select(this)
    layer.selectAll('.column')
      .attr('x', _this.xPosition)
      .attr('y', _this.yPositionStacked)
      .attr('height', _this.yHeightStacked)
      .attr('width', _this.xBarWidth)
    layer.selectAll('.line')
      .attr('d', _this.line(_this.data.getValuesForSeries(i)))

    // plot the dot at the last point
    var firstPoint = _this.data.getFirstDatum(i)
    var lastPoint = _this.data.getLastDatum(i)
    layer.selectAll('.last-dot')
      .attr('cx', _this.xPositionLine(lastPoint))
      .attr('cy', _this.yPosition(lastPoint))
    layer.selectAll('.first-dot')
      .attr('cx', _this.xPositionLine(firstPoint))
      .attr('cy', _this.yPosition(firstPoint))
  })
}

Chart.prototype.updateYAxis = function () {
  // apply Y axis labels
  var HTML = ''
  var intervals = Utils.getNiceIntervals(this.yRange, this.height)
  var maxTop = this.$yAxis.height() - this.$container.height() + 60 // must be 60px below the top
  intervals.forEach(function (interval) {
    interval.top = this.yScale(interval.value)
    if (interval.top >= maxTop) {
      interval.display = this.params.rounding === 'on' ? interval.displayString : interval.rawString
      HTML += this.yAxisLabelHTML(interval)
    }
  }.bind(this))
  this.$yAxis.html(HTML)

  // update zero line position
  this.$zeroLine.removeClass('hidden').css('top', this.yScale(0))
}

Chart.prototype.updateSelectedX = function (index) {
  if (index !== undefined) {
    this.selectedX = index
  }

  var thisXPosition = this.xPosition(this.data.getDatum(0, this.selectedX))
  var adjust = 0.5 * this.xBarWidth(this.data.getDatum(0, this.selectedX))
  var selectionLeft = thisXPosition + adjust

  // move selection
  this.$selectionElem.css('left', selectionLeft)

  var beg = selectionLeft
  var end = selectionLeft + this.$selectionXLabel.width()

  if (selectionLeft < (this.width / 2)) {
    this.$selectionElem.addClass('on-right')
  } else {
    this.$selectionElem.removeClass('on-right')
    beg = selectionLeft - this.$selectionXLabel.width()
    end = selectionLeft
  }

  // hide x-axis labels if necessary
  if (beg <= this.xBegEdge) {
    this.$xBeg.addClass('hidden')
  } else {
    this.$xBeg.removeClass('hidden')
  }

  if (end >= this.xEndEdge) {
    this.$xEnd.addClass('hidden')
  } else {
    this.$xEnd.removeClass('hidden')
  }

  // move selected dots
  var _this = this
  this.layers.each(function (yLabel, i) {
    var seriesExtent = _this.data.getSeriesExtent(i)
    if (_this.selectedX >= seriesExtent[0] && _this.selectedX <= seriesExtent[1]) {
      d3.select(this).selectAll('.selected-dot')
        .attr('cx', _this.xPositionLine(_this.data.getDatum(i, _this.selectedX)))
        .attr('cy', _this.yPosition(_this.data.getDatum(i, _this.selectedX)))
        .style({'opacity': '1'})
    } else {
      d3.select(this).selectAll('.selected-dot').style({'opacity': '0'})
    }
  })

  // add selected class to the appropriate columns
  var columns = this.data.getIndexCount()
  for (var i = 0; i < columns; i++) {
    var columnClass = 'column'
    if (_this.selectedX === i) {
      columnClass = 'column selected'
    }

    for (var j = 0; j < _this.data.getSeriesCount(); j++) {
      d3.select(_this.data.getDatum(j, i).columnEl).attr('class', columnClass)
    }
  }

  this.updateSelectionText()
}

Chart.prototype.updateSelectionText = function() {
  // a focusedSeriesIndex >= to the ySeries length means use the total
  var showTotal = this.focusedSeriesIndex >= this.data.getSeriesCount()
  var chartYSeries = showTotal ? this.data.getSeriesCount() - 1 : this.focusedSeriesIndex
  var thisPoint = this.data.getDatum(chartYSeries, this.selectedX)

  var thisYLabel = ''
  var thisYColor = showTotal ? this.colorBase : this.colorFn(this.data.getSeries(thisPoint.ySeries).label)
  if (this.data.getSeriesCount() > 1) {
    var pageYSeries = this.getChartSeries()[chartYSeries]
    thisYLabel = showTotal ? 'total' : this.pageController.getSeriesName(pageYSeries)
  }

  var seriesExtent = this.data.getStackedExtentForIndex(this.selectedX)
  var seriesTotal = seriesExtent[1] + seriesExtent[0]
  var thisValue = showTotal ? seriesTotal : thisPoint.yRaw
  var thisValueFormatted = this.params.rounding === 'on' ? Utils.getRoundedValue(thisValue, this.yRange) : thisValue

  // update selection
  this.$selectionYLabel.text(thisYLabel).css('color', thisYColor)
  this.$selectionXLabel.text(thisPoint.xLabel)
  this.$selectionValue.text(thisValueFormatted).css('color', thisYColor)
}

Chart.prototype.bindInteractions = function () {
  // chart option toggles
  Object.keys(this.pageController.OPTIONS).forEach(function (option) {
    this.$container.find('.toggle-' + option).click(function (event) {
      event.preventDefault()
      var options = this.pageController.OPTIONS[option]
      this.params[option] = this.params[option] === options[0] ? options[1] : options[0]
      this.render()
    }.bind(this))
  }.bind(this))

  // chart editables
  this.pageController.EDITABLES.forEach(function (item) {
    var $elem = this.$container.find('.' + Utils.camelToHyphen(item))
    $elem.on('focusout', function () {
      if ($elem.text() === '' && item === 'title') {
        this.params[item] = this.pageController.getDefaultTitle(this.chartIndex)
        $elem.text(this.params[item])
      } else {
        this.params[item] = $elem.text()
        this.updateEditablePlaceholder(item)
      }
    }.bind(this))
  }.bind(this))

  // handle mouseover
  this.$container.mousemove(function (e) {
    this.handleMouseover(e)
  }.bind(this))
}

Chart.prototype.handleMouseover = function(pixel) {
  // show the options
  this.$container.addClass('active')
  $('body').addClass('page-active')
  clearTimeout(this.mouseTimer)
  this.mouseTimer = setTimeout(function () {
    if (! this.$optionsElem.is(':hover') && ! this.$chartDescription.is(':hover')) {
      this.$container.removeClass('active')
      $('body').removeClass('page-active')
    }
  }.bind(this), 1000)

  // don't change the selection if mouseover is below the plot
  if (pixel.pageY - this.$plot.offset().top > this.$plot.height()) return

  // update everything if the selextedX or focusedSeriesIndex is different
  var closestPoint = this.getClosestPoint(pixel)
  if (closestPoint.selectedX !== this.selectedX || closestPoint.focusedSeriesIndex !== this.focusedSeriesIndex) {
    this.selectedX = closestPoint.selectedX
    this.focusedSeriesIndex = closestPoint.focusedSeriesIndex
    this.updatefocusedSeriesIndex()
    this.pageController.updateSelectedX(this.selectedX)
  }
}

Chart.prototype.getClosestPoint = function(pixel) {
  var pixelX = (pixel.pageX - this.$plot.offset().left) * this.data.getIndexCount() / (this.width - this.margin.right)
  var pixelY = pixel.pageY - this.$plot.offset().top
  var currentX = Math.min(Math.floor(Math.max(pixelX, 0)), this.data.getIndexCount() - 1)
  var currentY = this.focusedSeriesIndex

  // determine the closest y series
  var diffs = d3.range(this.data.getSeriesCount()).map(function (i) {
    var thisDatum = this.data.getDatum(i, currentX)
    var indexPixelY = this.params.type === 'line' ? this.yPosition(thisDatum) : this.yPositionStacked(thisDatum)
    var diff = this.params.type === 'line' ? Math.abs(pixelY - indexPixelY) : pixelY - indexPixelY
    var isValid = (this.params.type === 'line' || diff > 0)
    return {diff: diff, series: i, isValid: isValid}
  }.bind(this))

  var validDiffs = diffs.filter(function (diff) {
    return diff.isValid
  })
  currentY = _.min(validDiffs, 'diff').series

  // use the total if it's a column chart and the mouse position it
  if (this.params.type === 'column') {
    // determine if position is over a y series stack, else show the total
    var yValueExtent = this.data.getStackedExtentForIndex(currentX)
    var yPixelExtent = [this.yScale(yValueExtent[0]), this.yScale(yValueExtent[1])]
    if (pixelY < yPixelExtent[1] || pixelY > yPixelExtent[0]) {
      currentY = this.data.getSeriesCount()
    }
  }

  return {selectedX: currentX, focusedSeriesIndex: currentY}
}

Chart.prototype.updatefocusedSeriesIndex = function () {
  if (this.params.type === 'line') {
    this.$container.find('.line').attr('class', 'line')
    var selectedLine = d3.select(this.data.getSeries(this.focusedSeriesIndex).lineEl)
    selectedLine.attr('class', 'line focused')
    d3.select(selectedLine.node().parentNode).each(function () {
      this.parentNode.appendChild(this)
    })
  }
}

Chart.prototype.updateEditablePlaceholder = function (item) {
  if (!this.params[item] || this.params[item] === '') {
    this.$container.find('.' + Utils.camelToHyphen(item)).addClass('empty')
  } else {
    this.$container.find('.' + Utils.camelToHyphen(item)).removeClass('empty')
  }
}

Chart.prototype.getChartIndex = function () {
  return this.chartIndex
}

Chart.prototype.getChartContainer = function () {
  return this.$container
}

Chart.prototype.getChartSeries = function () {
  return this.params.series
}

Chart.prototype.chartHTML = function (parameters) {
  var template = ''
  template +='<div class="chart show-columns">'
  template +='  <div class="chart-description">'
  template +='    <h1 class="title info-input"></h1>'
  template +='  </div>'
  template +='  <div class="chart-plot-outer-container">'
  template +='    <div class="chart-plot-inner-container">'
  template +='      <div class="y-axis-container"><div class="y-axis chart-height"></div></div>'
  template +='      <div class="zero-line-container chart-height"><div class="zero-line"></div></div>'
  template +='      <div class="x-axis"><span class="x-beginning"></span><span class="x-end"></span></div>'
  template +='      <div class="selection">'
  template +='        <div class="selection-info">'
  template +='          <div class="selection-value"></div>'
  template +='          <div class="selection-xlabel"></div>'
  template +='          <div class="selection-ylabel"></div>'
  template +='        </div>'
  template +='      </div>'
  template +='      <figure class="chart-plot chart-height"></figure>'
  template +='    </div>'
  template +='  </div>'
  template +='  <aside class="chart-info">'
  template +='    <ul class="legend hidden"></ul>'
  template +='    <div class="chart-options">'
  template +='      <a class="option-item toggle-type" href="#" title="Switch chart type">'
  template +='        <span class="icon icon-line"></span>'
  template +='        <span class="icon icon-column"></span>'
  template +='      </a>'
  template +='      <a class="option-item toggle-rounding" href="#" title="Turn rounding on/off">'
  template +='        <span class="icon icon-round-off"></span>'
  template +='        <span class="icon icon-round-on"></span>'
  template +='      </a>'
  template +='    </div>'
  template +='  </aside>'
  template +='</div>'
  return _.template(template, parameters)
}

Chart.prototype.yAxisLabelHTML = function (interval) {
  return _.template('<div class="y-axis-label" style="top:<%- top %>px"><%- display %></div>', interval)
}
