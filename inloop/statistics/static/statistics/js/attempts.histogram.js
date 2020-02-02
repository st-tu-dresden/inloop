
document.addEventListener("DOMContentLoaded", function() {
  window.attemptsHistogram = {};

  window.attemptsHistogram.configure = function(
    templateEndpoint, apiEndpoint, csrfToken, querysetLimit
  ) {
    window.attemptsHistogram.templateEndpoint = templateEndpoint;
    window.attemptsHistogram.apiEndpoint = apiEndpoint;
    window.attemptsHistogram.csrfToken = csrfToken;
    window.attemptsHistogram.querysetLimit = querysetLimit;
  };

  window.attemptsHistogram.load = function() {
    if (window.attemptsHistogram.templateEndpoint === undefined ||
        window.attemptsHistogram.apiEndpoint === undefined ||
        window.attemptsHistogram.csrfToken === undefined) {
      throw Error("Attempts histogram is not configured yet.")
    }

    fetch(window.attemptsHistogram.templateEndpoint)
        .then(function(response) {
          return response.text();
        })
        .then(function(html) {
          document.getElementById("main-window").innerHTML = html;

          let chart;

          function showHistogram(chartData) {
            const data = Object.keys(chartData)
              .map((k, ) => ({
                x: parseInt(k),
                y: chartData[k]
              }))
              .sort((a, b) => {
                if (a.x > b.x) return 1;
                if (a.x < b.x) return -1;
                return 0;
              });

            const labels = data.map((e) => (e.x));

            const config = {
              data: {
                datasets: [{
                  label: "Quantity",
                  data: data,
                  borderColor: "#007bff",
                  backgroundColor: "rgba(56, 103, 214, 0.5)",
                }],
                labels: labels
              },
              type: "bar",
              options: {}
            };

            if (chart !== undefined) {
              chart.destroy();
            }

            chart = new Chart("chart", config);
          }

          function reloadAttemptsHistogram(querysetLimit) {
            const taskSelect = document.getElementById("task-select");
            const selectedTaskId = taskSelect
              .options[taskSelect.selectedIndex]
              .value;

            const url = new URL(
              window.location.protocol
              + "//"
              + window.location.host
              + window.attemptsHistogram.apiEndpoint
            );
            const params = {
              queryset_limit: querysetLimit,
              task_id: selectedTaskId
            };
            Object.keys(params)
              .filter(key => params[key] !== undefined)
              .forEach(key => url.searchParams.append(key, params[key]));
            const request = new Request(url, {
              method: "GET",
              headers: new Headers({
                "Content-type": "application/json",
                "X-CSRFToken": window.attemptsHistogram.csrfToken
              })
            });

            fetch(request)
              .then(response => {
                response.json().then(json => {
                  if (response.status === 200) {
                    showHistogram(json["histogram"]);
                  }
                  if (response.status === 409) {
                    const querysetCount = json["queryset_count"];
                    const actionWasConfirmed = confirm(
                      `This action will process ${querysetCount} objects, ` +
                      `which exceeds the limit of ${querysetLimit} objects ` +
                      `and can be very slow. Do you wish to proceed anyways?`
                    );
                    if (actionWasConfirmed) {
                      reloadAttemptsHistogram(undefined);
                    }
                  }
                });
              });
          }

          document.getElementById("task-select").onchange = function() {
            reloadAttemptsHistogram(window.attemptsHistogram.querysetLimit);
          };

          reloadAttemptsHistogram(window.attemptsHistogram.querysetLimit);
        });

  };
});


