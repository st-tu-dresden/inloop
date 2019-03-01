// Load data attributes
let script = document.getElementById("editor-script");
let MODULAR_TAB_URL = script.getAttribute("data-modular-tab-url");
let MODAL_NOTIFICATION_URL = script.getAttribute("data-modal-notification-url");
let MODAL_INPUT_FORM_URL = script.getAttribute("data-modal-input-form-url");
let MODAL_CONFIRMATION_FORM_URL = script.getAttribute("data-modal-confirmation-form-url");
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


// Check for ECMAScript 6 support
var supportsES6 = function() {
    try {
        new Function("(a = 0) => a");
        return true;
    }
    catch (err) {
        return false;
    }
}();

if (!supportsES6) {
    alert(
      "Your browser does not support ECMAScript 6." +
      " Please update or change your browser to use the editor."
    );
}


// Add function to jQuery to parse
// all nodes containing text
jQuery.fn.textNodes = function() {
    return this.contents().filter(function() {
        return (this.nodeType === Node.TEXT_NODE && this.nodeValue.trim() !== "");
    });
};


class Modal {
    constructor(url, hook, params) {
        this.url = url;
        this.hook = hook;
        this.params = params;
        this.onHiddenCallbacks = [];
        this.onShownCallbacks = [];
    }

    addOnHiddenCallback(callback) {
        this.onHiddenCallbacks.push(callback);
    }

    addOnShownCallback(callback) {
        this.onShownCallbacks.push(callback);
    }

    load(completion) {
        let self = this;
        $.get(this.url, this.params, function(html) {
            let container = $(MODAL_CONTAINER_ID);
            if (container === undefined || html === undefined) {
                return;
            }
            container.html(html);
            let modal = $("#" + self.hook);
            modal.modal("show");
            modal.on('hidden.bs.modal', function () {
                for (let callback of self.onHiddenCallbacks) {
                    callback();
                }
            });
            modal.on('shown.bs.modal', function () {
                for (let callback of self.onShownCallbacks) {
                    callback();
                }
            });
            if (completion !== undefined) completion(html, container, modal);
        })
    }
}


class ModalNotification extends Modal {
    constructor(title, body) {
        super(MODAL_NOTIFICATION_URL, "modal-notification-hook", {
            hook: "modal-notification-hook",
            title: title,
            body: body
        });
    }
}


class TryAgainLaterModalNotification extends ModalNotification {
    constructor(title) {
        super(title, "Please try again later.");
    }
}


class DuplicateFileNameModalNotification extends ModalNotification {
    constructor(fileName) {
        super(
            "Duplicate Filename",
            "\"" + fileName +  "\" exists already. " +
            "Please choose another filename or edit the " +
            "name of the existing file."
        );
    }
}


class ModalInputForm extends Modal {
    constructor(title, placeholder) {
        super(MODAL_INPUT_FORM_URL, "modal-input-form-hook", {
            hook: "modal-input-form-hook",
            title: title,
            input_hook: "modal-input-form-input-hook",
            placeholder: placeholder
        });
        this.onInputCallbacks = [];
    }

    addOnInputCallback(callback) {
        this.onInputCallbacks.push(callback);
    }

    load(completion) {
        let self = this;
        this.addOnShownCallback(function() {
            $("#modal-input-form-input-hook").focus();
        });
        this.addOnHiddenCallback(function() {
            for (let callback of self.onInputCallbacks) {
                callback($("#modal-input-form-input-hook").val());
            }
        });
        super.load(completion);
    }
}


class ModalConfirmationForm extends Modal {
    constructor(title) {
        super(MODAL_CONFIRMATION_FORM_URL, "modal-confirmation-form-hook", {
            hook: "modal-confirmation-form-hook",
            title: title,
            confirm_button_hook: "modal-confirmation-form-confirm-button-hook",
            cancel_button_hook: "modal-confirmation-form-cancel-button-hook"
        });
        this.onConfirmCallbacks = [];
        this.onCancelCallbacks = [];
    }

    addOnConfirmCallback(callback) {
        this.onConfirmCallbacks.push(callback);
    }

    addOnCancelCallback(callback) {
        this.onCancelCallbacks.push(callback);
    }

    load(completion) {
        let self = this;
        super.load(function(html, container, modal) {
            $("#modal-confirmation-form-confirm-button-hook").click(function() {
                for (let callback of self.onConfirmCallbacks) {
                    callback();
                }
            });
            $("#modal-confirmation-form-cancel-button-hook").click(function() {
                for (let callback of self.onCancelCallbacks) {
                    callback();
                }
            });
            if (completion !== undefined) completion(html, container, modal);
        });
    }
}


class ToolTip {
    constructor(id) {
        this.elem = $(id);
        this.runningTimeout = undefined;
    }

    changeTitle(newTitle) {
        this.elem.title = newTitle;
        this.elem.attr("data-original-title", newTitle)
    }

    show(milliseconds) {
        if (this.runningTimeout !== undefined) {
            clearTimeout(this.runningTimeout);
            this.runningTimeout = undefined;
        }
        this.elem.tooltip("show");
        let self = this;
        if (milliseconds !== undefined) {
            self.runningTimeout = setTimeout(function() {
                self.hide();
            }, milliseconds);
        }
    }

    hide() {
        this.elem.tooltip("hide");
    }
}


class StatusButton {
    constructor(isSaved) {
        this.background = $(STATUS_BUTTON_BACKGROUND_ID);
        this.icon = $(STATUS_BUTTON_ICON_ID);
        this.hint = new ToolTip(STATUS_BUTTON_HINT_ID);
        if (isSaved === true) {
            this.appearAsSaved();
        } else {
            this.appearAsUnsaved();
        }
        this.isSaved = isSaved;
    }

    appearAsSaved() {
        this.background.removeClass(CSS_BACKGROUND_UNSAVED);
        this.background.addClass(CSS_BACKGROUND_SAVED);
        this.icon.removeClass(CSS_ICON_UNSAVED);
        this.icon.addClass(CSS_ICON_SAVED);
        if (this.isSaved === false) {
            this.hint.changeTitle("Solution saved!");
            this.hint.show(2000);
        }
        this.isSaved = true;
    }

    appearAsUnsaved() {
        this.background.removeClass(CSS_BACKGROUND_SAVED);
        this.background.addClass(CSS_BACKGROUND_UNSAVED);
        this.icon.removeClass(CSS_ICON_SAVED);
        this.icon.addClass(CSS_ICON_UNSAVED);
        if (this.isSaved === true) {
            this.hint.changeTitle("Changes detected. Remember to save your solution!");
            this.hint.show(2000);
        }
        this.isSaved = false;
    }
}


class HashComparator {
    constructor(hash) {
        this.rusha = new Rusha();
        this.hash = hash;
        this.statusButton = new StatusButton(false);
    }

    updateHash(files) {
        this.hash = this.computeHash(files);
    }

    computeHash(files) {
        let concatenatedContents = "";
        for (let f of files) {
            concatenatedContents += f.fileContent;
            concatenatedContents += f.fileName;
        }
        return this.rusha.digest(concatenatedContents);
    }

    lookForChanges(files) {
        let equal = this.computeHash(files) === this.hash;
        if (equal === true) {
            this.statusButton.appearAsSaved();
        } else {
            this.statusButton.appearAsUnsaved();
        }
        return equal;
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

    rename(name) {
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
}


class FileBuilder {
    constructor(files) {
        this.files = files;
    }

    contains(fileName) {
        for (let file of this.files) {
            if (file.fileName.toLowerCase() === fileName.toLowerCase()) {
                return true;
            }
        }
        return false;
    }

    build(fileName, fileContent) {
        let f = new File(fileName, fileContent);
        this.files.push(f);
        return f;
    }

    destroy(file) {
        this.files = this.files.filter(f => f.fileName !== file.fileName);
    }
}


class TabBar {
    constructor(files) {
        this.tabs = [];
        this.editor = new Editor();
        this.editor.addOnChangeListener(function() {
            hashComparator.lookForChanges(fileBuilder.files);
        });
        for (let file of files) {
            this.createNewTab(file);
        }
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
        let inputForm = new ModalInputForm("Choose a name for your new File.", "New.java");
        inputForm.addOnInputCallback(function(fileName) {
            if (fileName === undefined || fileName === "") return;
            if (fileBuilder.contains(fileName)) {
                let modal = new DuplicateFileNameModalNotification(fileName);
                modal.addOnHiddenCallback(function() {
                    self.createNewEmptyTab();
                });
                modal.load();
                return;
            }
            let file = fileBuilder.build(fileName, "\n");
            hashComparator.lookForChanges(fileBuilder.files);
            if (file === undefined) return;
            self.createNewTab(file);
        });
        inputForm.load();
    }

    createNewTab(file) {
        let tabId = this.dequeueTabId();
        let self = this;
        let tab = new Tab(tabId, file).onCreate(function(success) {
            if (success !== true) {
                return;
            }
            tab.rename(file.fileName);
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
        let modalInputForm = new ModalInputForm("Rename " + this.activeTab.file.fileName, "New.java");
        modalInputForm.addOnInputCallback(function(fileName) {
            if (fileName === undefined || fileName === "") return;
            if (fileBuilder.contains(fileName)) {
                let notification = new DuplicateFileNameModalNotification(fileName);
                notification.addOnHiddenCallback(function() {
                    self.edit(tabId);
                });
                notification.load();
                return;
            }
            self.activeTab.file.fileName = fileName;
            self.activeTab.rename(fileName);
            hashComparator.lookForChanges(fileBuilder.files);
        });
        modalInputForm.load();
    }

    destroyActiveTab() {
        if (this.activeTab === undefined) return;
        let confirmation = new ModalConfirmationForm(
            "Are you sure that you want to delete \""
            + this.activeTab.file.fileName + "\"?"
        );
        let self = this;
        confirmation.addOnConfirmCallback(function() {
            self.activeTab.appearAsInactive();
            self.editor.unbind();
            self.activeTab.destroy();
            self.activeTab = undefined;
            hashComparator.lookForChanges(fileBuilder.files);
        });
        confirmation.load();
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

    unbind() {
        if (this.editor === undefined) return;
        this.editor.removeAllListeners("change");
        this.editor.setValue("");
        this.editor.setReadOnly(true);
        this.editor.off("change");
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
        for (let key of Object.keys(this.uploadedData["saved_files"])) {
            let file = new File(key, this.uploadedData["saved_files"][key]);
            files.push(file);
        }
        completion(files, this.uploadedData["last_submission"]);
    }

    save(completion) {
        // TODO: Implement save
        console.log("TODO: Save not implemented yet!");
        hashComparator.updateHash(fileBuilder.files);
        hashComparator.lookForChanges(fileBuilder.files);

        if (completion !== undefined) completion(true);
    }

    upload(files) {
        this.save(function(success) {
            if (success !== true) {
                let modal = new TryAgainLaterModalNotification("Upload failed.");
                modal.load();
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
                    if (successResponse.success === true) {
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
let hashComparator;
let tabBar;
let communicator = new Communicator();

communicator.load(function(files, hash) {
    fileBuilder = new FileBuilder(files);
    hashComparator = new HashComparator(hash);
    hashComparator.lookForChanges(files);
    tabBar = new TabBar(files);
});

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
