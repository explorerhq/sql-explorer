/*global _, d3, Utils */

function ChartData(pageData, seriesIndicesToUse) {
  this._data = pageData._data.filter(function (series, i) {
    return seriesIndicesToUse.indexOf(i) > -1
  })

  this._serieses = pageData._serieses.filter(function (series, i) {
    return seriesIndicesToUse.indexOf(i) > -1
  })

  this._indices = pageData._indices

  this.formatData()
}

ChartData.prototype.formatData = function () {
  // add stackedPosition
  this._data[0].forEach(function (row, i) {
    var negY0 = 0
    var posY0 = 0

    this._data.forEach(function (series, j) {
      var datum = this._data[j][i]
      datum.ySeries = j

      if (datum.y < 0) {
        negY0 = negY0 + datum.y
        datum.y0 = negY0
        datum.y1 = datum.y0 - datum.y
      } else {
        datum.y0 = posY0
        datum.y1 = datum.y0 + datum.y
        posY0 = posY0 + datum.y
      }
    }.bind(this))
  }.bind(this))
}

ChartData.prototype.getFlattenedData = function () {
  return _.flatten(this._data)
}

ChartData.prototype.getSerieses = function () {
  return this._serieses
}

ChartData.prototype.getSeries = function (i) {
  return this._serieses[i]
}

ChartData.prototype.getDatum = function (seriesIndex, index) {
  return this._data[seriesIndex][index]
}

ChartData.prototype.getSeriesLabels = function () {
  return this._serieses.map(function (series) { return series.label })
}

ChartData.prototype.getSeriesCount = function () {
  return this._serieses.length
}

ChartData.prototype.getUnstackedValuesAtIndex = function (i) {
  return this._data.map(function (series) {
    return series[i].y
  })
}

ChartData.prototype.getValuesForSeries = function (seriesIndex) {
  var seriesExtent = this.getSeriesExtent(seriesIndex)
  return this._data[seriesIndex].slice(seriesExtent[0], seriesExtent[1] + 1)
}

ChartData.prototype.getFirstDatum = function (seriesIndex) {
  var firstPointIndex = this.getSeriesExtent(seriesIndex)[0]
  return this._data[seriesIndex][firstPointIndex]
}

ChartData.prototype.getLastDatum = function (seriesIndex) {
  var lastPointIndex = this.getSeriesExtent(seriesIndex)[1]
  return this._data[seriesIndex][lastPointIndex]
}

ChartData.prototype.getSeriesExtent = function (seriesIndex) {
  var yRawValues = _.pluck(this._data[seriesIndex], 'yRaw')
  return Utils.getTrimmedExtent(yRawValues)
}

ChartData.prototype.getIndices = function () {
  return this._indices
}

ChartData.prototype.getIndexCount = function () {
  return this._indices.length
}

ChartData.prototype.getStackedExtent = function () {
  return d3.extent(this.getFlattenedData(), function (datum) {
    return datum.y < 0 ? datum.y0 : datum.y1
  })
}

ChartData.prototype.getStackedExtentForIndex = function (index) {
  var extent = [0, 0]
  this._data.forEach(function (series) {
    var minOrMax = series[index].y < 0 ? 0 : 1
    extent[minOrMax] += series[index].y
  })

  return extent
}

ChartData.prototype.getUnstackedExtent = function () {
  return d3.extent(this.getFlattenedData(), function (datum) {
    return datum.y
  })
}

ChartData.prototype.getIndexExtent = function () {
  return [this._indices[0], this._indices[this._indices.length - 1]]
}
