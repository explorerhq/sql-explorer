/*global $, _ */

function ChartLegend(controller, data, chart) {
  this.chart = chart
  this.controller = controller
  this.data = data
  this.chartIndex = this.chart.getChartIndex()
  this.$container = this.chart.getChartContainer()
  this.series = this.chart.getChartSeries()
}

ChartLegend.prototype.update = function() {
  if (this.data.getSeriesCount() === 1 && this.controller.getOtherCharts(this.chartIndex).length === 0) {
    this.$container.find('.legend').html('')
    return
  }

  var $legend = $('')
  _(this.data.getSerieses()).eachRight(function (series, i) {
    var label = this.controller.getSeriesName(this.series[i])
    var thisLabel = {label: label, color: this.chart.colorFn(series.label)}
    var $legendEl = $(this.legendItemHTML(thisLabel))
    $legend = $legend.add($legendEl)
    series.legendEl = $legendEl
  }.bind(this))
  this.$container.find('.legend').html($legend).removeClass('hidden')
  this.bindLegendInteractions()
}

ChartLegend.prototype.bindLegendInteractions = function () {
  this.data.getSerieses().forEach(function (series, i) {
    // make series labels editable
    var $legendInput = series.legendEl.find('.legend-input')
    $legendInput.on('focusout', function () {
      var seriesNames = this.controller.getSeriesNames()

      if ($legendInput.text() === series.label || $legendInput.text() === '') {
        $legendInput.text(series.label)
        delete seriesNames[series.seriesIndex]
      } else {
        seriesNames[series.seriesIndex] = $legendInput.text()
      }
    }.bind(this))

    // open move-chart popover
    series.legendEl.find('.move-chart').click(function (event) {
      event.stopPropagation()
      this.$container.find('.move-chart-options').remove()
      this.$container.find('.legend-item').removeClass('active')
      var otherCharts = this.controller.getOtherCharts(this.chartIndex)

      // current number of charts = other charts + current chart
      var newChartIndex = otherCharts.length + 1

      if (otherCharts.length === 0) {
        // if no other charts, move series to a new chart
        this.controller.moveToChart(this.series[i], this.chartIndex, newChartIndex)

      } else if (otherCharts.length === 1 && this.series.length === 1) {
        // if only one series and only one other chart, move series back into that chart
        this.controller.moveToChart(this.series[i], this.chartIndex, otherCharts[0].chartIndex)

      } else {
        // else, show all the options in a popover
        series.legendEl.addClass('active')
        series.legendEl.append(this.moveChartHTML({otherCharts: otherCharts, series: this.series}))

        otherCharts.forEach(function (chart) {
          this.$container.find('.move-to-chart-' + chart.chartIndex).click(function (e) {
            e.preventDefault()
            this.controller.moveToChart(this.series[i], this.chartIndex, chart.chartIndex)
          }.bind(this))
        }.bind(this))

        this.$container.find('.move-to-new-chart').click(function () {
          this.controller.moveToChart(this.series[i], this.chartIndex, newChartIndex)
        }.bind(this))
      }
    }.bind(this))
  }.bind(this))

  // remove popovers
  $('body').click(function () {
    this.$container.find('.move-chart-options').remove()
    this.$container.find('.legend-item').removeClass('active')
  }.bind(this))
}

ChartLegend.prototype.legendItemHTML = function(label) {
  var template = ''
  template +='<li class="legend-item">'
  template +='  <div class="legend-label">'
  template +='    <span class="legend-input" contenteditable="true"><%- label %></span>'
  template +='    <span style="background-color:<%- color %>;" class="legend-box"></span>'
  template +='  </div>'
  template +='  <button class="move-chart"><span class="icon icon-move"></span></button>'
  template +='</li>'
  return _.template(template, label)
}

ChartLegend.prototype.moveChartHTML = function (otherCharts) {
  var template = ''
  template +='<div class="move-chart-options popover">'
  template +='  <p>Move to:</p>'
  template +='  <% _.forEach(otherCharts, function (chart) { %>'
  template +='    <a href= "#" class="move-chart-option move-to-chart-<%- chart.chartIndex %>"><%- chart.title %></a>'
  template +='  <% }) %>'
  template +='  <% if(series.length > 1) { %>'
  template +='    <a href= "#" class="move-chart-option move-to-new-chart">'
  template +='      <span class="icon icon-plus"></span>New chart'
  template +='    </a>'
  template +='  <% } %>'
  template +='  <span class="arrow-bottom-right"></span>'
  template +='</div>'
  return _.template(template, otherCharts)
}
