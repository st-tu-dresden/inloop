
document.addEventListener("DOMContentLoaded", function() {
  window.submissionsHistogram = {};

  window.submissionsHistogram.configure = function(
    templateEndpoint, apiEndpoint, csrfToken, querysetLimit
  ) {
    window.submissionsHistogram.templateEndpoint = templateEndpoint;
    window.submissionsHistogram.apiEndpoint = apiEndpoint;
    window.submissionsHistogram.csrfToken = csrfToken;
    window.submissionsHistogram.querysetLimit = querysetLimit;
  };

  window.submissionsHistogram.load = function() {
    if (window.submissionsHistogram.templateEndpoint === undefined ||
        window.submissionsHistogram.apiEndpoint === undefined ||
        window.submissionsHistogram.csrfToken === undefined) {
      throw Error("Submissions Histogram is not configured yet.");
    }

    fetch(window.submissionsHistogram.templateEndpoint)
        .then(function(response) {
          return response.text();
        })
        .then(function(html) {
          document.getElementById("main-window").innerHTML = html;

          let chart;

          function showHistogram(selectedGranularity, histogram, fromDate, toDate) {
            let data = {};

            if (histogram.length > 0) {
              const dateMappedHistogram = histogram.map((e) => ({
                date: new Date(e.date),
                count: e.count
              }));
              const sortedHistogram = dateMappedHistogram
                .sort((a, b) => {
                  if (a > b) return 1;
                  if (a < b) return -1;
                  return 0;
                });

              if (sortedHistogram[0].date > fromDate) {
                sortedHistogram.unshift({
                  date: fromDate,
                  count: 0
                });
              }

              if (sortedHistogram[sortedHistogram.length - 1].date < toDate) {
                sortedHistogram.push({
                  date: toDate,
                  count: 0
                });
              }

              data = sortedHistogram.map((e) => ({t: e.date, y: e.count}));
            }

            const config = {
              data: {
                datasets: [{
                  label: "Solution Submissions",
                  data: data,
                  borderColor: "#007bff",
                  backgroundColor: "rgba(56, 103, 214, 0.5)",
                }],
                labels: []
              },
              type: "bar",
              options: {
                scales: {
                  xAxes: [{
                    type: "time",
                    time: {
                      unit: selectedGranularity
                    },
                    distribution: "linear"
                  }],
                  yAxes: [{
                    gridLines: {
                      drawBorder: false
                    }
                  }]
                }
              }
            };

            if (chart !== undefined) {
              chart.destroy();
            }
            chart = new Chart("chart", config);
          }


          function reloadSubmissionsHistogram(querysetLimit) {
            const categorySelect = document.getElementById("category-select");
            const categorySelectValue = categorySelect
              .options[categorySelect.selectedIndex]
              .value;
            let selectedCategoryId;
            if (categorySelectValue === "undefined") {
              selectedCategoryId = undefined;
            } else {
              selectedCategoryId = categorySelectValue;
            }

            const passedSelect = document.getElementById("passed-select");
            const passedSelectValue = passedSelect
              .options[passedSelect.selectedIndex]
              .value;
            let selectedPassed;
            if (passedSelectValue === "undefined") {
              selectedPassed = undefined;
            } else {
              selectedPassed = passedSelectValue === "true";
            }

            const granularitySelect = document.getElementById("granularity-select");
            const granularitySelectValue = granularitySelect
              .options[granularitySelect.selectedIndex]
              .value;
            let selectedGranularity;
            if (granularitySelectValue === "undefined") {
              selectedGranularity = undefined;
            } else {
              selectedGranularity = granularitySelectValue;
            }

            const dateSpanSelect = document.getElementById("date-span-select");
            const dateSpanSelectValue = dateSpanSelect
              .options[dateSpanSelect.selectedIndex]
              .value;
            let selectedNumberOfHours;
            if (dateSpanSelectValue === "undefined") {
              selectedNumberOfHours = undefined;
            } else {
              selectedNumberOfHours = parseInt(dateSpanSelectValue);
            }

            let fromTimestamp, toTimestamp, fromDate, toDate;

            if (selectedNumberOfHours !== undefined) {
              fromDate = new Date()
                .startOfDay()
                .minusHours(selectedNumberOfHours);
              fromTimestamp = fromDate.toISOString();
              toDate = new Date()
                .endOfDay();
              toTimestamp = toDate.toISOString();
            }

            const url = new URL(
              window.location.protocol
              + "//"
              + window.location.host
              + window.submissionsHistogram.apiEndpoint
            );
            const params = {
              queryset_limit: querysetLimit,
              from_timestamp: fromTimestamp,
              to_timestamp: toTimestamp,
              granularity: selectedGranularity,
              category_id: selectedCategoryId,
              passed: selectedPassed,
            };
            Object.keys(params)
              .filter(key => params[key] !== undefined)
              .forEach(key => url.searchParams.append(key, params[key]));
            const request = new Request(url, {
              method: "GET",
              headers: new Headers({
                "Content-type": "application/json",
                "X-CSRFToken": window.submissionsHistogram.csrfToken
              })
            });

            fetch(request)
              .then(response => {
                response.json().then(json => {
                  if (response.status === 200) {
                    showHistogram(selectedGranularity, json["histogram"], fromDate, toDate);
                  }
                  if (response.status === 409) {
                    const querysetCount = json["queryset_count"];
                    const actionWasConfirmed = confirm(
                      `This action will process ${querysetCount} objects, ` +
                      `which exceeds the limit of ${querysetLimit} objects ` +
                      `and can be very slow. Do you wish to proceed anyways?`
                    );
                    if (actionWasConfirmed) {
                      reloadSubmissionsHistogram(undefined);
                    }
                  }
                });
              });
          }

          for(const selectId of [
            "passed-select",
            "category-select",
            "date-span-select",
            "granularity-select"
          ]) {
            document.getElementById(selectId).onchange = function() {
              reloadSubmissionsHistogram(window.submissionsHistogram.querysetLimit);
            };
          }

          reloadSubmissionsHistogram(window.submissionsHistogram.querysetLimit);

        });
  };
});


