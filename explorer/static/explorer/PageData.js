/*global d3, Utils */

function PageData(dataUrl, callback) {
  this.dataUrl = dataUrl
  this.callback = callback
  this._serieses = []
  this._indices = []
  this.fetchData()
}

PageData.prototype.fetchData = function () {
  var url = this.dataUrl;
  d3.text(url, function (error, fileString) {
    if (error) {
      return this.callback(error, null)
    }

    var fileRows = d3.csv.parseRows(fileString)
    var fileFieldNames = fileRows.shift()
    // create array of row objects with the field names as keys
    var fileData = fileRows.map(function (fileRow) {
      return fileFieldNames.reduce(function (memo, name, i) {
        memo[name] = fileRow[i]
        return memo
      }, {})
    })

    var indexFieldName

    if (fileFieldNames.length !== 1) {
      indexFieldName = fileFieldNames.shift()
      this._indices = fileData.map(function (fileRow) {
        return fileRow[indexFieldName]
      })
    } else {
      this._indices = d3.range(fileData.length).map(function (i) {
        return 'Row ' + (i + 1)
      })
    }

    this._serieses = fileFieldNames.map(function (label, i) {
      return {
        label: label,
        seriesIndex: i
      }
    })

    this._data = fileFieldNames.map(function (label) {
      return fileData.map(function (fileRow, i) {
        return {
          x: i,
          xLabel: this._indices[i],
          y: Utils.stringToNumber(fileRow[label]),
          yRaw: fileRow[label]
        }
      }.bind(this))
    }.bind(this))

    this.callback(null, this)
  }.bind(this))
}

PageData.prototype.getSerieses = function () {
  return this._serieses
}

PageData.prototype.getSeries = function (i) {
  return this._serieses[i]
}

PageData.prototype.getSeriesCount = function () {
  return this._serieses.length
}

PageData.prototype.getDatumCount = function () {
  return this._data[0].length
}
