$(document).ready(function() {
    // Load data attributes
    let script = document.getElementById("archive-status-script");
    let CSRF_TOKEN = document.getElementById("data-csrf-token");
    let DOWNLOAD_BAR_ID = script.getAttribute("data-download-bar-id");
    let SOLUTION_ARCHIVE_DOWNLOAD_URL = script.getAttribute("data-solution-archive-download-url");
    let SOLUTION_ARCHIVE_NEW_URL = script.getAttribute("data-solution-archive-new-url");
    let SOLUTION_ARCHIVE_STATUS_URL = script.getAttribute("data-solution-archive-status-url");

    class DownloadBar {
        get text() {
            return undefined;
        }

        get css() {
            return undefined;
        }

        get shouldShowSpinner() {
            return false;
        }

        get shouldHideSpinner() {
            return false;
        }

        constructor() {
            if (new.target === DownloadBar) {
                throw new TypeError("DownloadBar is abstract and cannot be instantiated!");
            }
            this.id = DOWNLOAD_BAR_ID;
            this.elem = $(DOWNLOAD_BAR_ID);
            this.prepare();
        }

        prepare() {
            this.prepareText();
            this.prepareCSS();
            this.prepareSpinner();
        }

        prepareText() {
            // Only override the parent's text, so that our
            // loading indicator stays untouched
            this.elem.contents().filter(function(){
                return this.nodeType === 3;
            })[0].nodeValue = this.text;
        }

        prepareCSS() {
            this.elem.attr("class", this.css);
        }

        prepareSpinner() {
            if (!(this.shouldShowSpinner || this.shouldHideSpinner)) return;
            let spinner = $(".spinner");
            if (this.shouldShowSpinner) {
                spinner.show();
            } else {
                spinner.hide();
            }
        }
    }


    class CreateArchiveDownloadBar extends DownloadBar {
        get text() {
            return "Click here to create a downloadable zip archive for this solution.";
        }

        get css() {
            return "list-group-item list-group-item-info";
        }

        get shouldHideSpinner() {
            return true;
        }
    }

    class PendingArchiveDownloadBar extends DownloadBar {
        get text() {
            return "The archive is being created.";
        }

        get css() {
            return "list-group-item list-group-item-info";
        }

        get shouldShowSpinner() {
            return true;
        }
    }


    class AlreadyRunningDownloadBar extends DownloadBar {
        get text() {
            return "There is already an archive being created in the background.";
        }

        get css() {
            return "list-group-item list-group-item-warning";
        }

        get shouldShowSpinner() {
            return true;
        }
    }


    class DownloadArchiveDownloadBar extends DownloadBar {
        get text() {
            return "Click here to download the solution as zip archive.";
        }

        get css() {
            return "list-group-item list-group-item-success";
        }

        get shouldHideSpinner() {
            return true;
        }

        prepare() {
            super.prepare();
            this.elem.attr("href", SOLUTION_ARCHIVE_DOWNLOAD_URL);
            this.elem.attr("onClick", "");
        }
    }


    class DownloadBarFactory {
        constructor() {
            this.state = undefined;
            this.downloadBar = undefined;
        }

        produce(state) {
            if (state === this.state) return this.downloadBar;
            if (state === "available") {
                this.downloadBar = new DownloadArchiveDownloadBar();
            } else if (state === "already running") {
                this.downloadBar = new AlreadyRunningDownloadBar();
            } else if (state === "initiated") {
                this.downloadBar = new PendingArchiveDownloadBar();
            } else {
                this.downloadBar = new CreateArchiveDownloadBar();
            }
            this.state = state;
            return this.downloadBar;
        }
    }


    class Endpoint {
        static get(url, callback) {
            $.ajax({
                url: url,
                type: "get",
                headers: {"X-CSRFToken": CSRF_TOKEN},
                datatype: "json",
                success: callback
            })
        }
    }

    createArchive = function () {
        let downloadBarFactory = new DownloadBarFactory();
        Endpoint.get(SOLUTION_ARCHIVE_NEW_URL, function(data) {
            downloadBarFactory.produce(data.status);

            // Listen for archive status changes
            $(this).refreshJSON("activate", {
                url: SOLUTION_ARCHIVE_STATUS_URL,
                interval: 5000,
                success: function(data) {
                    if (data.status !== "available") return;
                    $(this).refreshJSON("deactivate");

                    downloadBarFactory.produce(data.status);
                }
            });
        });
    }

    let createArchiveLink = document.getElementById("archive-download-bar");
    if (createArchiveLink !== null) {
        createArchiveLink.addEventListener("click", () => createArchive());
    }
});
