// Load data attributes
let script = document.getElementById("editor-script");
let MODULAR_TAB_URL = script.getAttribute("data-modular-tab-url");
let MODULAR_NOTIFICATION_URL = script.getAttribute("data-modular-notification-url");
let MODULAR_INPUT_FORM_URL = script.getAttribute("data-modular-input-form-url");
let CSRF_TOKEN = script.getAttribute("data-csrf-token");
let SOLUTIONS_EDITOR_URL = script.getAttribute("data-solutions-editor-url");
let SOLUTIONS_LIST_URL = script.getAttribute("data-solutions-list-url");
let MODAL_CONTAINER_ID = script.getAttribute("data-modal-container-id");
let TAB_CONTAINER_ID = script.getAttribute("data-tab-container-id");
let EDITOR_ID = script.getAttribute("data-editor-id");
let STATUS_BUTTON_BACKGROUND_ID = script.getAttribute("data-status-button-background-id");
let STATUS_BUTTON_ICON_ID = script.getAttribute("data-status-button-icon-id");
let STATUS_BUTTON_HINT_ID = script.getAttribute("data-status-button-hint-id");
let CSS_BACKGROUND_UNSAVED = script.getAttribute("data-css-background-unsaved");
let CSS_BACKGROUND_SAVED = script.getAttribute("data-css-background-saved");
let CSS_ICON_UNSAVED = script.getAttribute("data-css-icon-unsaved");
let CSS_ICON_SAVED = script.getAttribute("data-css-icon-saved");


jQuery.fn.textNodes = function() {
    return this.contents().filter(function() {
        return (this.nodeType === Node.TEXT_NODE && this.nodeValue.trim() !== "");
    });
};


class ModalNotification {
    constructor(title, body) {
        let hook = "modal-notification-hook";
        $.get(MODULAR_NOTIFICATION_URL, {hook: hook, title: title, body: body}, function(html) {
            let container = $(MODAL_CONTAINER_ID);
            if (container === undefined || html === undefined) {
                return;
            }
            container.html(html);
            let modalContainer = $("#" + hook);
            modalContainer.modal("show");
        })
    }
}


class ModalInputForm {
    constructor(title, placeholder, callback) {
        let hook = "modal-input-form-hook";
        let inputHook = "modal-input-form-input-hook";
        $.get(MODULAR_INPUT_FORM_URL, {
            hook: hook,
            title: title,
            input_hook: inputHook,
            placeholder: placeholder
        }, function(html) {
            let container = $(MODAL_CONTAINER_ID);
            if (container === undefined || html === undefined) {
                return;
            }
            container.html(html);
            let modalContainer = $("#" + hook);
            modalContainer.modal("show");
            let inputElem = $("#" + inputHook);
            modalContainer.on('shown.bs.modal', function () {
                inputElem.focus();
            });
            modalContainer.on('hidden.bs.modal', function () {
                if (callback === undefined) return;
                let input = inputElem.val();
                callback(input);
            });
        })
    }
}


class StatusButton {

    constructor(isSaved) {
        this.background = $(STATUS_BUTTON_BACKGROUND_ID);
        this.icon = $(STATUS_BUTTON_ICON_ID);
        this.hint = $(STATUS_BUTTON_HINT_ID);
        this.changeAppearance(isSaved);
    }

    appearAsSaved() {
        this.background.removeClass(CSS_BACKGROUND_UNSAVED);
        this.background.addClass(CSS_BACKGROUND_SAVED);
        this.icon.removeClass(CSS_ICON_UNSAVED);
        this.icon.addClass(CSS_ICON_SAVED);
        this.hint.prop("title", "No changes detected.");
    }

    appearAsUnsaved() {
        this.background.removeClass(CSS_BACKGROUND_SAVED);
        this.background.addClass(CSS_BACKGROUND_UNSAVED);
        this.icon.removeClass(CSS_ICON_SAVED);
        this.icon.addClass(CSS_ICON_UNSAVED);
        this.hint.prop("title", "Changes detected. Save your solution.");
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

    updateHash(files) {
        this.hash = this.computeHash(files);
        statusButton.appearAsSaved();
    }

    computeHash(files) {
        let concatenatedContents = "";
        for (let f of files) {
            concatenatedContents += f.fileContent;
            concatenatedContents += f.fileName;
            console.log(f.fileContent);
        }
        let hash = this.rusha.digest(concatenatedContents);
        console.log(hash);
        return hash;
    }

    compareToFiles(files) {
        return this.computeHash(files) === this.hash;
    }
}


class Tab {
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
            if (self.onCreateClosure !== undefined) self.onCreateClosure(true);
        })
    }

    destroy() {
        let container = $(TAB_CONTAINER_ID);
        container.find("#" + this.tabId).first().remove();
        container.find("#edit-" + this.tabId).first().remove();
        container.find("#remove-" + this.tabId).first().remove();
        fileBuilder.destroy(this.file);
    }

    setName(name) {
        $("#label-" + this.tabId).textNodes().first().replaceWith(name);
    }

    appearAsActive() {
        $("#" + this.tabId).addClass("active");
        let editElement = $("#edit-" + this.tabId);
        editElement.css("display", "inherit");
        editElement.addClass("active");
        let removeElement = $("#remove-" + this.tabId);
        removeElement.css("display", "inherit");
        removeElement.addClass("active");
    }

    appearAsInactive() {
        $("#" + this.tabId).removeClass("active");
        let editElement = $("#edit-" + this.tabId);
        editElement.css("display", "none");
        editElement.removeClass("active");
        let removeElement = $("#remove-" + this.tabId);
        removeElement.css("display", "none");
        removeElement.removeClass("active");
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

    addSetFileNameListener(completion) {
        this.setFileNameListener = completion;
    }

    setFileName(name) {
        this.fileName = name;
        if (this.setFileNameListener !== undefined) this.setFileNameListener(name);
    }
}


class FileBuilder {
    constructor(files) {
        this.files = files;
    }

    build(fileName, fileContent) {
        for (let file of this.files) {
            if (file.fileName === fileName) {
                new ModalNotification(
                    "Duplicate Filename",
                    "\"" + fileName +  "\" exists already. " +
                    "Please choose another filename or edit the " +
                    "name of the existing file."
                );
                return undefined;
            }
        }
        let f = new File(fileName, fileContent);
        this.files.push(f);
        return f;
    }

    destroy(file) {
        this.files = this.files.filter(f => f.name !== file.name);
    }
}


class TabBar {
    constructor() {
        this.tabs = [];
        this.editor = new Editor();
        this.editor.addOnChangeListener(function() {
            let equal = hashComparator.compareToFiles(fileBuilder.files);
            statusButton.changeAppearance(equal);
        });
        for (let file of fileBuilder.files) {
            this.createNewTab(file);
        }
        // Prevent CTRL+S (CMD+S on Mac) and add
        // our custom event handler
        document.addEventListener("keydown", function(e) {
            if (e.keyCode === 83) {
                if (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey) {
                    e.preventDefault();
                    communicator.save();
                }
            }
        }, false);
    }

    dequeueTabId() {
        if (this.tabId === undefined) {
            this.tabId = 0;
        }
        this.tabId += 1;
        return this.tabId;
    }

    createNewEmptyTab() {
        let self = this;
        let modalInputForm = new ModalInputForm(
            "Choose a name for your new File.",
            "New.java",
            function(fileName) {
                if (fileName === undefined) return;
                let file = fileBuilder.build(fileName, "\n");
                if (file === undefined) return;
                self.createNewTab(file);
            }
        );
    }

    createNewTab(file) {
        let tabId = this.dequeueTabId();
        let self = this;
        let tab = new Tab(tabId, file).onCreate(function(success) {
            if (success !== true) {
                // TODO: Handle failure
                return;
            }
            tab.setName(file.fileName);
            file.addSetFileNameListener(function(name) {
                tab.setName(name);
            });
            self.activate(tabId);
        });
        this.tabs.push(tab);
        tab.build();
        return tab;
    }

    activate(tabId) {
        if (this.activeTab !== undefined) {
            this.activeTab.appearAsInactive();
        }
        this.activeTab = this.tabs.find(function(element) {return element.tabId === tabId;});
        this.editor.bind(this.activeTab.file);
        this.activeTab.appearAsActive();
    }

    edit(tabId) {
        this.activeTab = this.tabs.find(function(element) {return element.tabId === tabId;});
        this.activeTab.appearAsActive();
        let self = this;
        new ModalInputForm(
            "Rename " + this.activeTab.file.fileName,
            "New.java",
            function(fileName) {
                self.activeTab.file.fileName = fileName;
                self.activeTab.setName(fileName);
            }
        )
    }

    destroy(tabId) {
        if (this.activeTab !== undefined) {
            this.activeTab.appearAsInactive();
        }
        this.editor.unbind(this.activeTab.file);
        this.activeTab.destroy();
        this.activeTab = undefined;
    }
}


class Editor {

    static config() {
        return {
            highlightActiveLine: true,
            highlightSelectedWord: true,
            readOnly: true,
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
            fontSize: "10.5pt",
            value: "// Select or create files to continue"
        };
    }

    constructor() {
        this.editor = ace.edit(EDITOR_ID);
        if (this.editor === undefined) {
            return;
        }
        this.editor.setOptions(Editor.config());
    }

    addOnChangeListener(closure) {
        this.onChangeClosure = closure;
    }

    bind(file) {
        if (this.editor === undefined) return;
        this.editor.setReadOnly(false);
        this.editor.removeAllListeners("change");
        let self = this;
        this.editor.setValue(file.fileContent);
        this.editor.clearSelection();
        this.editor.on("change", function() {
            file.fileContent = self.editor.getValue();
            if (self.onChangeClosure !== undefined) self.onChangeClosure();
        });
    }

    unbind(file) {
        if (this.editor === undefined) return;
        this.editor.removeAllListeners("change");
        this.editor.setValue("");
        this.editor.setReadOnly(true)
    }
}


class Communicator {

    constructor() {}

    load(completion) {
        // TODO: Actually load JSON data
        this.uploadedData = JSON.parse(`
        {
          "last_submission": "fdb8da1705ac435e669120369236a8f48fdf68bc",
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
        hashComparator.updateHash(fileBuilder.files);
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


let fileBuilder;
let statusButton;
let hashComparator;
let tabBar;
let communicator = new Communicator();

communicator.load(function(f, h) {
    fileBuilder = new FileBuilder(f);
    hashComparator = new HashComparator(h);
    let hashIsUpToDate = hashComparator.compareToFiles(fileBuilder.files);
    statusButton = new StatusButton(hashIsUpToDate);
    tabBar = new TabBar();
});
