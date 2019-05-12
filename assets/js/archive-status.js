// Load data attributes
let script = document.getElementById("archive-status-script");
let CSRF_TOKEN = document.getElementById("data-csrf-token");
let DOWNLOAD_BAR_ID = script.getAttribute("data-download-bar-id");
let DOWNLOAD_URL = script.getAttribute("data-download-url");
let CREATE_ARCHIVE_URL = script.getAttribute("data-create-archive-url");
let ARCHIVE_AVAILABILITY_URL = script.getAttribute("data-archive-availability-url");

let spinner = $(".spinner");

function changeDownloadBarText(text) {
    // Only override the parent's text, so that our
    // loading indicator stays untouched
    $(DOWNLOAD_BAR_ID).contents().filter(function(){
        return this.nodeType === 3;
    })[0].nodeValue = text
}

function archiveIsAvailableCallback() {
    let elem = $(DOWNLOAD_BAR_ID);
    elem.attr("class", "list-group-item list-group-item-success");
    changeDownloadBarText("Click here to download your solution as zip archive.");
    elem.attr("href", DOWNLOAD_URL);
    elem.attr("onClick", "");
    spinner.hide();
}

function createArchive() {
    let elem = $(DOWNLOAD_BAR_ID);
    spinner.show();
    $.ajax({
        url: CREATE_ARCHIVE_URL,
        type: "get",
        headers: {"X-CSRFToken": CSRF_TOKEN},
        datatype: "json",
        success: function(data) {
            if (data.status === "available") {
                archiveIsAvailableCallback();
                return;
            }
            if (data.status === "already running") {
                elem.attr("class", "list-group-item list-group-item-warning");
                changeDownloadBarText("There is already an archive being created in the background.");
            } else if (data.status === "initiated") {
                elem.attr("class", "list-group-item list-group-item-info");
                changeDownloadBarText("Your archive is being created.");
            } else {
                return;
            }
            // Listen for archive status changes
            $(this).refreshJSON("activate", {
                url: ARCHIVE_AVAILABILITY_URL,
                interval: 5000,
                success: function(data) {
                    if (data.status !== "available") return;
                    $(this).refreshJSON("deactivate");
                    archiveIsAvailableCallback();
                }
            })
        }
    });
}
