"use strict";

/**
 * Provides an extensible wrapper for loading and showing
 * histograms with the chart.js framework.
 */
class Histogram {

  /**
   * Constructs a histogram.
   *
   * @param {string} elementId
   * The html element id under which the histogram will be inserted.
   * @param {Object} config
   * The configuration for the histogram.
   * @param {string} config.template
   * The url for the template endpoint, from which the histogram html is loaded.
   * @param {string} config.querysetLimit
   * The maximum number of database entries to be processed until a warning is shown.
   */
  constructor(elementId, config) {
    this.element = document.getElementById(elementId);
    if (!this.element) {
      throw Error("The defined element could not be found in the document tree.");
    }

    this.config = config;
    this.form = undefined;
    this.chart = undefined;
  }

  /**
   * Callback for the completion of a fetch event.
   *
   * @callback onCompletionCallback
   */

  /**
   * Shows the histogram.
   *
   * @param {undefined|onCompletionCallback} completion
   * The optional callback to be executed on completion.
   */
  show(completion) {
    fetch(this.config.template)
      .then(response => response.text().then(html => {
        this.element.innerHTML = html;

        // Link the parameter form to the histogram
        this.form = this.element.querySelector("form");
        this.form.addEventListener("submit", (event) => {
          event.preventDefault();
          this.reload();
        });

        if (completion !== undefined) completion();
      }));
  }

  /**
   * Generates the histogram data url to be fetched
   * together with its query parameters.
   *
   * @param {Boolean} isQuerysetLimitApplied
   * Specifies, whether the queryset limit should be applied or not.
   * If applied, url search parameters will communicate the
   * "queryset_limit" parameter to the server backend.
   *
   * @returns {URL}
   * The generated url.
   */
  url(isQuerysetLimitApplied) {
    const searchParams = new URLSearchParams(new FormData(this.form));
    if (isQuerysetLimitApplied) {
      searchParams.set("queryset_limit", this.config.querysetLimit);
    }
    const url = new URL(this.form.action);
    url.search = searchParams;
    return url;
  }

  /**
   * Reloads the chart data from the data endpoint.
   *
   * @param {Object} kwargs
   * The keyword arguments.
   * @param {Boolean} kwargs.isQuerysetLimitApplied
   * Specifies, whether the amount of objects to be handled by the backend
   * should be limited. If this parameter is set to false, the backend
   * will signal an exceeded queryset limit with the http response code 400.
   */
  reload({isQuerysetLimitApplied = true} = {}) {
    fetch(this.url(isQuerysetLimitApplied)).then(response => {
      response.json().then(json => {
        if (response.status === 200) {
          this.onSuccessfulReload(json);
        } else if (response.status === 400) {
          this.onQuerysetLimitReached(json);
        } else {
          this.onFailedReload(response);
        }
      });
    });
  }

  /**
   * Handles a successful reload of chart data.
   *
   * @param {Object} json
   * The json data the backend returned.
   * @param {Object} json.histogram
   * The computed histogram returned by the backend.
   */
  onSuccessfulReload(json) {
    const endpointData = json["histogram"];
    this.draw(endpointData);
  }

  /**
   * Handles a failed reload, which was caused by a reached queryset limit.
   *
   * @param {Object} json
   * The returned json data from the backend.
   * @param {Integer} json.queryset_count
   * The approximate count of objects, which would
   * be handled by the requested action.
   */
  onQuerysetLimitReached(json) {
    const querysetCount = json["queryset_count"];
    const actionWasConfirmed = confirm(
      `This action will process ${querysetCount} objects, ` +
      `which exceeds the limit of ${this.config.querysetLimit} objects ` +
      `and can be very slow. Do you wish to proceed anyways?`
    );
    if (actionWasConfirmed) {
      this.reload({isQuerysetLimitApplied: false});
    }
  }

  /**
   * Handles a reload, which failed due to an unspecified reason.
   *
   * @param {Response} response
   * The response, which was returned by the backend.
   */
  onFailedReload(response) {
    alert(`The histogram could not be loaded (HTTP Status Code ${response.status}).`);
  }

  /**
   * Draws the chart.
   *
   * @param {Object} config
   * The configuration for the chart.js chart.
   */
  draw(config) {
    // Remove the old chart from the view to avoid overlapping
    if (this.chart !== undefined) {
      this.chart.destroy();
    }
    this.chart = new Chart("chart", config);
  }
}


/**
 * Provides a specific histogram to show the attempts
 * it took users to successfully complete a particular task.
 */
class AttemptsHistogram extends Histogram {
  /**
   * Draws the attempts histogram.
   *
   * The endpoint data is mapped to a representation displayable
   * by chart.js before it is passed to the chart for drawing.
   *
   * @param {Object} endpointData
   * The data sent by the endpoint.
   */
  draw(endpointData) {
    // Map the data to displayable xy pairs
    const mappedData = Object.keys(endpointData)
      .map((k) => ({
        x: parseInt(k),
        y: endpointData[k]
      }));

    // Generate chart labels from the mapped data
    const labels = mappedData.map((e) => (e.x));

    const config = {
      data: {
        datasets: [{
          label: "Attempts Histogram",
          data: mappedData,
          borderColor: "#007bff",
          backgroundColor: "rgba(0, 123, 255, 0.5)",
        }],
        labels: labels
      },
      type: "bar",
      options: {
        scales: {
          xAxes: [{}],
          yAxes: [{}]
        },
        legend: {
          display: false
        }
      }
    };

    super.draw(config);
  }
}

/**
 * Provides a specific histogram to show the solution submissions over time.
 */
class SubmissionsHistogram extends Histogram {
  /**
   * Draws the submissions histogram.
   *
   * The endpoint data is mapped to a representation displayable
   * by chart.js before it is passed to the chart for drawing.
   *
   * @param {Object} endpointData
   * The data sent by the endpoint.
   */
  draw(endpointData) {
    // Map the data to displayable dated tuples
    const mappedData = endpointData
      .map((e) => ({
        t: new Date(e.date),
        y: e.count
      }));

    const config = {
      data: {
        datasets: [{
          label: "Submissions Histogram",
          data: mappedData,
          borderColor: "#007bff",
          backgroundColor: "rgba(0, 123, 255, 0.5)",
        }],
        // The time based x axis does automatedly generate labels
        labels: []
      },
      type: "bar",
      options: {
        scales: {
          xAxes: [{
            type: "time",
            distribution: "linear"
          }],
          yAxes: [{
            gridLines: {
              drawBorder: false
            }
          }]
        },
        legend: {
          display: false
        }
      }
    };

    super.draw(config);
  }
}

