// Load data attributes
let script = document.getElementById("editor-script");
let MODULAR_TAB_URL = script.getAttribute("data-modular-tab-url");
let CSRF_TOKEN = script.getAttribute("data-csrf-token");
let SOLUTIONS_EDITOR_URL = script.getAttribute("data-solutions-editor-url");
let SOLUTIONS_LIST_URL = script.getAttribute("data-solutions-list-url");
let TAB_CONTAINER_ID = script.getAttribute("data-tab-container-id");
let EDITOR_ID = script.getAttribute("data-editor-id");
let STATUS_BUTTON_BACKGROUND_ID = script.getAttribute("data-status-button-background-id");
let STATUS_BUTTON_ICON_ID = script.getAttribute("data-status-button-icon-id");
let CSS_BACKGROUND_UNSAVED = script.getAttribute("data-css-background-unsaved");
let CSS_BACKGROUND_SAVED = script.getAttribute("data-css-background-saved");
let CSS_ICON_UNSAVED = script.getAttribute("data-css-icon-unsaved");
let CSS_ICON_SAVED = script.getAttribute("data-css-icon-saved");


jQuery.fn.textNodes = function() {
    return this.contents().filter(function() {
        return (this.nodeType === Node.TEXT_NODE && this.nodeValue.trim() !== "");
    });
};


class StatusButton {

    constructor(isSaved) {
        this.background = $(STATUS_BUTTON_BACKGROUND_ID);
        this.icon = $(STATUS_BUTTON_ICON_ID);
        this.changeAppearance(isSaved);
    }

    appearAsSaved() {
        this.background.removeClass(CSS_BACKGROUND_UNSAVED);
        this.background.addClass(CSS_BACKGROUND_SAVED);
        this.icon.removeClass(CSS_ICON_UNSAVED);
        this.icon.addClass(CSS_ICON_SAVED);
    }

    appearAsUnsaved() {
        this.background.removeClass(CSS_BACKGROUND_SAVED);
        this.background.addClass(CSS_BACKGROUND_UNSAVED);
        this.icon.removeClass(CSS_ICON_SAVED);
        this.icon.addClass(CSS_ICON_UNSAVED);
    }

    changeAppearance(isSaved) {
        if (isSaved) {
            this.appearAsSaved();
        } else {
            this.appearAsUnsaved();
        }
    }
}


class HashComparator {

    constructor(hash) {
        this.rusha = new Rusha();
        this.hash = hash;
    }

    computeHash(files) {
        let concatenatedContents = "";
        for (let f of files) {
            concatenatedContents += f.fileContent;
            concatenatedContents += f.fileName;
        }
        return this.rusha.digest(concatenatedContents);
    }

    compareToFiles(files) {
        let equal = this.computeHash(files) === this.hash;
        return equal;
    }
}


class Tab {
    static compare(a, b) {
        return File.compare(a.file, b.file);
    }

    constructor(tabId, file) {
        this.tabId = tabId;
        this.file = file;
    }

    onCreate(closure) {
        this.onCreateClosure = closure;
        return this;
    }

    build() {
        let self = this;
        $.get(MODULAR_TAB_URL, {tab_id: this.tabId}, function(html) {
            if (html === undefined) {
                if (self.onCreateClosure !== undefined) self.onCreateClosure(false);
                return;
            }
            let container = $(TAB_CONTAINER_ID);
            if (container === undefined) {
                if (self.onCreateClosure !== undefined) self.onCreateClosure(false);
                return;
            }
            container.append(html);
            self.showName(self.file.fileName);
            if (self.onCreateClosure !== undefined) self.onCreateClosure(true);
        })
    }

    destroy() {
        let container = $(TAB_CONTAINER_ID);
        let self = container.find("#" + this.tabId).first();
        self.remove();
    }

    reattach() {
        let container = $(TAB_CONTAINER_ID);
        let self = container.find("#" + this.tabId).first();
        self.remove();
        container.append(self);
    }

    showName(name) {
        $("#label-" + this.tabId).textNodes().first().replaceWith(name);
    }

    appearAsActive() {
        $("#" + this.tabId).addClass("active");
    }

    appearAsInactive() {
        $("#" + this.tabId).removeClass("active");
    }
}


class File {
    static compare(a, b) {
        if(a.fileName < b.fileName) return -1;
        if(a.fileName > b.fileName) return 1;
        return 0;
    }

    constructor(fileName, fileContent) {
        this.fileName = fileName;
        this.fileContent = fileContent;
    }
}


class Suite {
    constructor() {
        let self = this;
        this.communicator = new Communicator();
        this.editor = new Editor();
        this.statusButton = new StatusButton(true);
        this.communicator.load(function(files, hash) {
            if (files === undefined || hash === undefined) {
                // TODO: Handle failure
                return;
            }
            self.hashComparator = new HashComparator(hash);
            self.editor.addOnChangeListener(function() {
                let equal = self.hashComparator.compareToFiles(files);
                self.statusButton.changeAppearance(equal);
            });
            for (let file of files) {
                self.createNewTab(file);
            }
        });
        // Prevent CTRL+S (CMD+S on Mac) and add
        // our custom event handler
        document.addEventListener("keydown", function(e) {
            if (e.keyCode === 83) {
                if (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey) {
                    e.preventDefault();
                    self.save();
                }
            }
        }, false);
    }

    files() {
        let files = this.tabs.map(function(element) {return element.file});
        files.sort(File.compare);
        return files;
    }

    upload() {
        this.communicator.upload(this.files());
    }

    save() {
        this.communicator.save();
        let files = this.files();
        this.hashComparator.hash = this.hashComparator.computeHash(files);
        let equal = this.hashComparator.compareToFiles(files);
        this.statusButton.changeAppearance(equal);
    }

    dequeueTabId() {
        if (this.tabId === undefined) {
            this.tabId = 0;
        }
        this.tabId += 1;
        return this.tabId;
    }

    createNewTab(file) {
        if (this.tabs === undefined) {
            this.tabs = [];
        }
        if (file === undefined) {
            file = new File("New.java", "\n");
        }
        let tabId = this.dequeueTabId();
        let self = this;
        let tab = new Tab(tabId, file).onCreate(function(success) {
            if (success !== true) {
                // TODO: Handle failure
                return;
            }
            self.sortTabs();
        });
        this.tabs.push(tab);
        tab.build();
    }

    sortTabs() {
        this.tabs.sort(Tab.compare);
        for (let t of this.tabs) {
            t.reattach();
        }
    }

    activate(tabId) {
        if (this.activeTab !== undefined) {
            this.activeTab.appearAsInactive();
        }
        this.activeTab = this.tabs.find(function(element) {return element.tabId === tabId;});
        this.editor.bind(this.activeTab.file);
        this.activeTab.appearAsActive();
    }
}


class Editor {

    static config() {
        return {
            highlightActiveLine: true,
            highlightSelectedWord: true,
            readOnly: false,
            cursorStyle: "ace",
            mergeUndoDeltas: true,
            printMargin: 80,
            theme: "ace/theme/inloop",
            mode: "ace/mode/java",
            newLineMode: "auto",
            tabSize: 4,
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: true,
            maxLines: Infinity,
            fontFamily: "Menlo, Monaco, Consolas, \"Courier New\", monospace",
            fontSize: "10.5pt"
        };
    }

    constructor() {
        this.editor = ace.edit(EDITOR_ID);
        if (this.editor === undefined) {
            if (this.onCreateClosure !== undefined) this.onCreateClosure(false);
            return;
        }
        this.editor.setOptions(Editor.config());
        if (this.onCreateClosure !== undefined) this.onCreateClosure(true);
    }

    addOnChangeListener(closure) {
        this.onChangeClosure = closure;
    }

    bind(file) {
        if (this.editor === undefined) return;
        this.editor.removeAllListeners("change");
        let self = this;
        this.editor.on("change", function() {
            if (self.onChangeClosure !== undefined) self.onChangeClosure();
        });
        this.editor.setValue(file.fileContent);
        this.editor.clearSelection();
        this.editor.on("change", function() {
            file.fileContent = self.editor.getValue();
        });
    }
}


class Communicator {

    constructor() {}

    load(completion) {
        // TODO: Actually load JSON data
        this.uploadedData = JSON.parse(`
        {
          "last_submission": "bc0f8d45bdcde5f4dd2ae181c52581e78ad0d5cb",
          "saved_files": {
            "test.java": "public class test {}",
            "A.java": "public class A {}",
            "B.java": "public class B {}",
            "Z.java": "public class Z {}",
            "C.java": "public class C {}"
          }
        }
        `);
        let files = [];
        for (let key of Object.keys(this.uploadedData.saved_files)) {
            let file = new File(key, this.uploadedData.saved_files[key]);
            files.push(file);
        }
        completion(files, this.uploadedData.last_submission);
    }

    save(completion) {
        // TODO: Implement save
        console.log("TODO: Save not implemented yet!");
        if (completion !== undefined) completion(true);
    }

    upload(files) {
        let self = this;
        this.save(function(success) {
            if (!success) {
                // TODO: Handle failure
                return;
            }
            let postData = {uploads: {}};
            for (let file of files) {
                postData.uploads[file.fileName] = file.fileContent;
            }
            $.ajax({
                url: SOLUTIONS_EDITOR_URL,
                type: "post",
                data: JSON.stringify(postData),
                headers: {"X-CSRFToken": CSRF_TOKEN},
                datatype: "json",
                success: function( successResponse ) {
                    if (successResponse.success) {
                        window.location.replace(SOLUTIONS_LIST_URL);
                    } else {
                        window.location.replace(SOLUTIONS_EDITOR_URL);
                    }
                }
            });
        });
    }
}


let suite = new Suite();
