let STATUS_BUTTON_BACKGROUND_ID = "#status-button";
let STATUS_BUTTON_ICON_ID = "#status-button-icon";

let EDITORS_ID = "#editors";
let MODULAR_EDITORS_ID = "#editors #modular-editor";

let CSS_BACKGROUND_UNSAVED = "alert-danger";
let CSS_BACKGROUND_SAVED = "alert-success";

let CSS_ICON_SAVED = "glyphicon-floppy-saved";
let CSS_ICON_UNSAVED = "glyphicon-floppy-remove";


class StatusButton {
    constructor(
        {
            appearsAsSaved = false,
        } = {}
    ) {
        this.background = $(STATUS_BUTTON_BACKGROUND_ID);
        this.icon = $(STATUS_BUTTON_ICON_ID);
        this.appearsAsSaved = appearsAsSaved;
        this.changeAppearance(appearsAsSaved);
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

    changeAppearance(saved) {
        if (saved) {
            this.appearAsSaved();
        } else {
            this.appearAsUnsaved();
        }
    }

    toggleAppearance() {
        this.appearsAsSaved = !this.appearsAsSaved;
        this.changeAppearance(this.appearsAsSaved);
    }
}


class Editor {
    constructor(
        {
            csrfToken,
            modularEditorUrl,
            solutionsEditorUrl,
            solutionsListUrl,
        } = {}
    ) {
        this.csrfToken = csrfToken;
        this.modularEditorUrl = modularEditorUrl;
        this.solutionsEditorUrl = solutionsEditorUrl;
        this.solutionsListUrl = solutionsListUrl;
        this.button = new StatusButton();
        this.rusha = new Rusha();
        this.editors = [];
        this.id = 0;

        // Prevent CTRL+S (CMD+S on Mac) and add
        // our custom event handler
        let self = this;
        document.addEventListener("keydown", function(e) {
            if (e.keyCode === 83) {
                if (navigator.platform.match("Mac") ? e.metaKey : e.ctrlKey) {
                    e.preventDefault();
                    self.save();
                }
            }
        }, false);
    }

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

    load() {
        // Get last fetched state
        this.data = JSON.parse(`
        {
          "last_submission": "bc0f8d45bdcde5f4dd2ae181c52581e78ad0d5cb",
          "saved_files": {
            "test.java": "public class test {}",
            "test2.java": "",
            "test3.java": "",
            "test4.java": "",
            "test5.java": "",
            "test6.java": "",
            "test7.java": "",
            "test8.java": "",
            "test9.java": "",
            "test10.java": "",
            "test11.java": ""
          }
        }
        `);

        for (let key of Object.keys(this.data.saved_files)) {
            this.createNewEditor(key, this.data.saved_files[key]);
        }
    }

    computeHash() {
        let concatenatedContents = "";

        for (let e of this.editors) {
            concatenatedContents += e.getValue();
        }

        return this.rusha.digest(concatenatedContents);
    }

    dequeueEditorId() {
        this.id += 1;
        return "editor" + this.id;
    }

    fileNameForEditor(editor) {
        return $("#file-name-"+editor.container.id).val()
    }

    fileNameExists(fileName) {
        for (let editor of this.editors) {
            if (this.fileNameForEditor(editor) === fileName) {
                return true;
            }
        }
        return false;
    }

    createNewEditor(fileName, content) {
        if (this.fileNameExists(fileName)) {
            // TODO: Notify user, that this file exists already
            return;
        }
        let id = this.dequeueEditorId();
        let self = this;
        $.get(this.modularEditorUrl, {file_name: fileName, editor_id: id}, function(html) {
            $(EDITORS_ID).append(html);
            let editor = ace.edit(id);
            editor.setOptions(Editor.config());
            editor.setValue(content);
            editor.clearSelection();
            editor.on("change", _ => self.didChange());
            self.editors.push(editor);
            self.sortEditorsById();
            self.didChange();
        })
    }

    createNewEmptyEditor() {
        this.createNewEditor(".java", "\n");
    }

    removeEditor(editorId, completion) {
        let editor = ace.edit(editorId);
        $("#" + editor.container.id).parent().remove();
        this.editors = this.editors.filter(editor => editor.container.id !== editorId);
        this.didChange();
    }

    sortEditorsById() {
        $(MODULAR_EDITORS_ID).sort(function(a, b) {
            let idA = $(a).attr("data-id");
            let idB = $(b).attr("data-id");
            if(idA < idB) { return -1; }
            if(idA > idB) { return 1; }
            return 0;
        }).each(function() {
            let elem = $(this);
            elem.remove();
            $(elem).appendTo(EDITORS_ID);
        });
        this.editors.sort(function(a, b) {
            if(a.container.id < b.container.id) { return -1; }
            if(a.container.id > b.container.id) { return 1; }
            return 0;
        })
    }

    save(completion) {
        // TODO: Perform actual save action
        console.log("TODO: Save not implemented yet!");

        // Update data
        this.data.last_submission = this.computeHash();
        this.data.saved_files = {};
        for (let editor of this.editors) {
            let fileName = this.fileNameForEditor(editor);
            this.data.saved_files[fileName] = editor.getValue();
        }

        let success = true;
        this.button.changeAppearance(success);

        if (typeof completion !== "undefined") {
            completion(success);
        }
    }

    upload() {
        // Upload our solution, but save it first
        // to ensure that our user will find it
        // when he gets back
        let self = this;
        this.save(function(success) {
            if (!success) {
                return;
            }
            let postData = {uploads: {}};
            for (let editor of self.editors) {
                let fileName = $("#file-name-"+editor.container.id).val();
                postData.uploads[fileName] = editor.getValue();
            }
            $.ajax({
                url: self.solutionsEditorUrl,
                type: "post",
                data: JSON.stringify(postData),
                headers: {"X-CSRFToken": self.csrfToken},
                datatype: "json",
                success: function( successResponse ) {
                    if (successResponse.success) {
                        window.location.replace(self.solutionsListUrl);
                    } else {
                        window.location.replace(self.solutionsEditorUrl);
                    }
                }
            });
        });
    }

    didChange() {
        let isSaved = this.computeHash() === this.data.last_submission;
        this.button.changeAppearance(isSaved);
    }
}
