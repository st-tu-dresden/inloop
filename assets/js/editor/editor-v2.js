import {getString, msgs} from './messages.js';

// Load data attributes, which are rendered into the script tag
const script = document.getElementById("editor-script");
const SAVE_CHECKPOINT_URL = script.getAttribute("data-save-checkpoint-url");
const GET_LAST_CHECKPOINT_URL = script.getAttribute("data-get-last-checkpoint-url");
const CSRF_TOKEN = script.getAttribute("data-csrf-token");
const SOLUTIONS_EDITOR_URL = script.getAttribute("data-solutions-editor-url");
const SOLUTIONS_LIST_URL = script.getAttribute("data-solutions-list-url");
const EDITOR_TABBAR_FILES_ID = 'editor-tabbar-files';
const EDITOR_ID = 'editor-content';
const BTN_SAVE_ID = 'toolbar-btn--save';
const BTN_ADD_FILE_ID = 'toolbar-btn--newfile';
const BTN_SUBMIT_ID = 'toolbar-btn--submit';
const BTN_RENAME_FILE_ID = 'editor-tabbar-btn--rename';
const BTN_DELETE_FILE_ID = 'editor-tabbar-btn--delete';

/**
 * Checks for ES6 support.
 *
 * ES6 support is needed for the editor.
 */
const supportsES6 = function() {
    try {
        new Function("(a = 0) => a");
        return true;
    }
    catch (err) {
        return false;
    }
}();


// Check for ES6 support and display an error
// message if ES6 is not supported.
if (!supportsES6) {
    showAlert(getString(msgs.missing_es6_support));
}


/**
 * Parses all non empty text subnodes of a jQuery node.
 *
 * jQuery nodes may contain other subnodes. Use this convenience function
 * to only parse non empty text subnodes (i.e. nodes, which already contain text).
 */
jQuery.fn.textNodes = function() {
    return this.contents().filter(function() {
        return (this.nodeType === Node.TEXT_NODE && this.nodeValue.trim() !== "");
    });
};

/**
 * Return true if the given name is a valid java filename, otherwise false.
 *
 * @param {string} filename - the filename to check.
 */
function isValidJavaFilename(filename) {
    return /^[A-Za-z0-9_]+\.java$/.test(filename);
}

/*
 * Represents an interactive button, which displays the current save status.
 */
class StatusButton {
    /**
     * Creates a status button.
     *
     * @constructor
     * @param {boolean} isSaved - Defines if the button appears as saved after instantiation.
     */
    constructor(isSaved) {
        this.button = $(`#${BTN_SAVE_ID}`);
        if (isSaved === true) {
            this.appearAsSaved();
        } else {
            this.appearAsUnsaved();
        }
        this.isSaved = isSaved;
    }

    /**
     * Changes the appearance of the status button, so that it appears as saved.
     */
    appearAsSaved() {
        this.button.attr('disabled', 'disabled');
        this.isSaved = true;
    }

    /**
     * Changes the appearance of the status button, so that it appears as unsaved.
     */
    appearAsUnsaved() {
        this.button.removeAttr('disabled');
        this.isSaved = false;
    }
}


/**
 * Represents a hash based comparator for files.
 */
class HashComparator {
    /**
     * Creates a hash comparator.
     *
     * @constructor
     * @param {string} hash - The MD5 hash of the files as an initial value.
     */
    constructor(hash) {
        this.rusha = new Rusha();
        this.hash = hash;
        this.statusButton = new StatusButton(false);
    }

    /**
     * Updates the MD5 hash.
     *
     * @param {string} hash - The new MD5 hash.
     */
    updateHash(hash) {
        this.hash = hash;
    }

    /**
     * Computes the MD5 hash of the given files by
     * file content and file name concatenation.
     *
     * @param {Array} files - The files on which the MD5 hash should be computed.
     * @returns {string} - The computed MD5 hash.
     */
    computeHash(files) {
        let concatenatedContents = "";
        for (let f of files) {
            concatenatedContents += f.fileContent;
            concatenatedContents += f.fileName;
        }
        return this.rusha.digest(concatenatedContents);
    }

    /**
     * Compute the MD5 hash of the given files and compare
     * it with the stored (class attribute) hash.
     *
     * @param {Array} files - The files on which the MD5 hash should be computed.
     * @returns {boolean} - Returns true if and only if the given files are unchanged.
     */
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


/**
 * Represents an editor tab for an editor file.
 */
class Tab {

    /**
     * Creates a tab.
     *
     * @constructor
     * @param {number} tabId - The unique id of the tab.
     * @param {File} file - The file to attach to this tab.
     */
    constructor(tabId, file) {
        this.tabId = tabId;
        this.file = file;
    }

    /**
     * Adds a closure function, which is executed when the tab was loaded.
     *
     * @param {function} closure - The closure function.
     */
    onCreate(closure) {
        this.onCreateClosure = closure;
        return this;
    }

    /**
     * Gets and inserts the rendered tab html.
     */
    build() {
        let self = this;
        const tabBarFileList = document.getElementById(EDITOR_TABBAR_FILES_ID);
        const newTab = document.createElement('li');
        newTab.innerText = this.file.fileName;
        newTab.id = this.tabId;
        newTab.addEventListener('click', () => tabBar.activate(this.tabId));
        tabBarFileList.appendChild(newTab);
    }

    /**
     * Removes the rendered tab html from the DOM.
     */
    destroy() {
        let container = $('#' + EDITOR_TABBAR_FILES_ID);
        container.find("#" + this.tabId).first().remove();
        container.find("#edit-" + this.tabId).first().remove();
        container.find("#remove-" + this.tabId).first().remove();
        fileBuilder.destroy(this.file);
    }

    /**
     * Changes the tab label to a given name.
     * Should be called on any filename changes
     * of the file coupled to the tab.
     *
     * @param {string} name - The new tab label.
     */
    rename(name) {
        document.getElementById(this.tabId).innerText = name;
    }

    /**
     * Changes the style of the tab, so that it appears as active.
     */
    appearAsActive() {
        $("#" + this.tabId).addClass("active");
        let editElement = $("#edit-" + this.tabId);
        editElement.css("display", "inherit");
        editElement.addClass("active");
        let removeElement = $("#remove-" + this.tabId);
        removeElement.css("display", "inherit");
        removeElement.addClass("active");
    }

    /**
     * Changes the style of the tab, so that it appears as inactive.
     */
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


/**
 * Represents an editor file.
 */
class File {
    /**
     * Compares two files by name. Provides a comparator function for alphabetic sorting.
     *
     * @param {File} a - The first file.
     * @param {File} b - The second file.
     * @returns {number} - The file name based comparator output.
     */
    static compare(a, b) {
        if(a.fileName < b.fileName) return -1;
        if(a.fileName > b.fileName) return 1;
        return 0;
    }

    /**
     * Creates an editor file with a given file name and given file contents.
     *
     * @constructor
     * @param {string} fileName - The file name.
     * @param {string} fileContent - The file content.
     */
    constructor(fileName, fileContent) {
        this.fileName = fileName;
        this.fileContent = fileContent;
    }
}


/**
 * Represents a builder for files.
 */
class FileBuilder {
    /**
     * Creates a file builder.
     *
     * @constructor
     * @param {Array} files - The initial files.
     */
    constructor(files) {
        this.files = files;
    }

    /**
     * Checks, if a given file name exists already.
     *
     * @param {string} fileName - The file name.
     * @returns {boolean} - Returns true if the file exists already.
     */
    contains(fileName) {
        for (let file of this.files) {
            if (file.fileName.toLowerCase() === fileName.toLowerCase()) {
                return true;
            }
        }
        return false;
    }

    /**
     * Builds a new file.
     *
     * @param {string} fileName - The file name.
     * @param {string} fileContent - The file contents.
     * @returns {File} - The built file.
     */
    build(fileName, fileContent) {
        let f = new File(fileName, fileContent);
        this.files.push(f);
        return f;
    }

    /**
     * Removes a given file.
     *
     * @param {File} file - The file to remove.
     */
    destroy(file) {
        this.files = this.files.filter(f => f.fileName !== file.fileName);
    }
}

/**
 * Represents a tab bar containing tabs.
 */
class TabBar {
    /**
     * Creates a new tab bar.
     *
     * @constructor
     * @param {Array} files - The initial files.
     */
    constructor(files) {
        this.tabs = [];
        this.editor = new InloopEditor();
        this.editor.addOnChangeListener(function() {
            hashComparator.lookForChanges(fileBuilder.files);
        });
        for (let file of files) {
            this.createNewTab(file);
        }
    }

    /**
     * Dequeues a new unique tab id. The tab id needs to be unique.
     *
     * @returns {number} - The dequeued tab id.
     */ 
    dequeueTabId() {
        // Store a class attribute to keep track of the current tab id
        if (this.tabId === undefined) {
            this.tabId = 0;
        }
        this.tabId += 1;
        return this.tabId;
    }

    /**
     * Creates a new empty tab.
     *
     * Displays a modal input form as a file name input and
     * creates the empty tab based on the given file name.
     */
    createNewEmptyTab() {
        let self = this;
        const fileCreationCallback = (fileName) => {
          if (!isValidJavaFilename(fileName) || fileName.trim() === '') {
            showPrompt(getString(msgs.invalid_filename, fileName), fileCreationCallback, fileName);
            return;
          }
          if (fileBuilder.contains(fileName)) {
            showPrompt(getString(msgs.duplicate_filename, fileName), fileCreationCallback, fileName);
            return;
          }
          const file = fileBuilder.build(fileName, '');
          hashComparator.lookForChanges(fileBuilder.files);
          if (file === undefined) return;
          self.createNewTab(file);
          self.toggleRenameDeleteButtons();
        };
        showPrompt(getString(msgs.choose_filename), fileCreationCallback);

    }

    /**
     * Creates a new tab based on a given file. Creates the tab asynchronously.
     *
     * @param {File} file - The file.
     * @returns {Tab} - The created tab.
     */
    createNewTab(file) {
        let tabId = this.dequeueTabId();
        let self = this;
        let tab = new Tab(tabId, file);
        this.tabs.push(tab);
        tab.build();
        tab.rename(file.fileName);
        self.activate(tabId);
        self.toggleRenameDeleteButtons();
        return tab;
    }

    /**
     * Switches to a given tab. The given tab appears as active,
     * all other tab appear as inactive. Loads the file, which is
     * attached to the given tab, into the editor view.
     *
     * @param {number} tabId - The id of the tab.
     */
    activate(tabId) {
        if (this.activeTab !== undefined) {
            this.activeTab.appearAsInactive();
        }
        this.activeTab = this.tabs.find(function(element) {return element.tabId === tabId;});
        this.editor.bind(this.activeTab.file);
        this.activeTab.appearAsActive();
        document.querySelector(`#${EDITOR_ID} > textarea`).focus();
    }

    /**
     * Displays a modal notification input form to rename
     * the selected tab and the file attached to it.
     *
     * @param tabId
     */
    edit(tabId) {
        this.activeTab = this.tabs.find(function(element) {return element.tabId === tabId;});
        this.activeTab.appearAsActive();
        const fileEditCallback = (fileName) => {
          if (fileName === this.activeTab.file.fileName) {
            return;
          }
          if (!isValidJavaFilename(fileName) || fileName.trim() === '') {
            showPrompt(getString(msgs.invalid_filename, fileName), fileEditCallback, fileName);
            return;
          }
          if (fileBuilder.contains(fileName)) {
            showPrompt(getString(msgs.duplicate_filename, fileName), fileEditCallback, fileName);
            return;
          }
          this.activeTab.file.fileName = fileName;
          this.activeTab.rename(fileName);
          document.querySelector(`#${EDITOR_ID} > textarea`).focus();
          hashComparator.lookForChanges(fileBuilder.files);
        };
        showPrompt(getString(msgs.edit_filename, this.activeTab.file.fileName), fileEditCallback, this.activeTab.file.fileName);
    }

    /**
     * Displays a modal confirmation form and removes
     * the active tab and the file attached to it, if confirmed.
     */
    destroyActiveTab() {
        if (this.activeTab === undefined) return;
        const deleteConfirmationCallback = () => {
          this.activeTab.appearAsInactive();
          const destroyedTabIndex = this.tabs.lastIndexOf(this.activeTab);
          this.tabs = this.tabs.filter((tab, i) => tab.tabId !== this.activeTab.tabId);
          this.editor.unbind();
          this.activeTab.destroy();
          this.activeTab = undefined;
          hashComparator.lookForChanges(fileBuilder.files);
          if (this.tabs.length > 0) {
            this.activate(this.tabs[destroyedTabIndex] && this.tabs[destroyedTabIndex].tabId || this.tabs[this.tabs.length - 1].tabId);
          }
          this.toggleRenameDeleteButtons();
        }
        showConfirmDialog(getString(msgs.delete_file_confirmation, this.activeTab.file.fileName), deleteConfirmationCallback);
    }

    toggleRenameDeleteButtons() {
      const deleteButton = document.getElementById(BTN_DELETE_FILE_ID);
      const renameButton = document.getElementById(BTN_RENAME_FILE_ID);
      const hasNoFiles = this.tabs.length === 0;
      deleteButton.disabled = hasNoFiles;
      renameButton.disabled = hasNoFiles;
    }
}


/**
 * Represents the code editor.
 *
 * Serves as a convenience wrapper for the ace.js editor.
 * On initiation, the editor renders the wrapped ace.js editor
 * into the specified html element. To improve performance,
 * there should only be one editor. After initiation, reuse the
 * editor with bind and unbind to edit a given file,
 * instead of creating a new editor every time.
 *
 * @example Usage of the editor:
 * -  Use a {@link Communicator} to fetch the latest checkpoint and its files.
 * -  Use a {@link FileBuilder}, to hold, delete and create files.
 * -  Use a {@link HashComparator} to compare files with a hash.
 * -  Use a {@link TabBar} to hold, delete and create tabs, which each bind to a file.
 * -  The {@link TabBar} creates an {@link Editor} as a servant.
 *    Subsequently, the {@link TabBar} controls binding and unbinding
 *    of the tabs and their corresponding files.
 * -  Update the hash of the {@link HashComparator} with {@link Editor#addOnChangeListener}.
 *    If the hash differs, the HashComparator will handle the visual representation
 *    through its {@link StatusButton}.
 */
class InloopEditor {
    /**
     * Provides the default editor configuration.
     *
     * @returns {Object} - The editor configuration.
     */
    static config() {
        return {
            highlightActiveLine: true,
            highlightSelectedWord: true,
            // Set editor to read only, because it should not be
            // accessed before any files are loaded or when no files
            // exist yet. There should be at least one file before the
            // editor accepts any inputs.
            readOnly: true,
            cursorStyle: "ace",
            mergeUndoDeltas: true,
            printMargin: 80,
            theme: "ace/theme/inloop",
            mode: "ace/mode/java",
            newLineMode: "auto",
            tabSize: 4,
            //maxLines: Infinity,
            enableBasicAutocompletion: false,
            enableLiveAutocompletion: false,
            fontFamily: "Menlo, Monaco, Consolas, \"Courier New\", monospace",
            fontSize: "10.5pt",
            value: "// Select or create files to continue"
        };
    }

    /**
     * Creates a new editor. Handles creation of the ace.js editor
     * with the default configuration.
     *
     * @constructor
     */
    constructor() {
        this.editor = ace.edit(EDITOR_ID);
        if (this.editor === undefined) {
            return;
        }
        this.editor.setOptions(InloopEditor.config());
    }

    /**
     * Adds a closure function, which is executed when the editor changes.
     *
     * @param {function} closure - The closure function.
     */
    addOnChangeListener(closure) {
        this.onChangeClosure = closure;
    }

    /**
     * Binds a given file to the editor, so that its contents
     * are displayed and changed on editor change.
     *
     * @param {File} file - The file to be bound.
     */
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

        this.editor.resize();
    }

    /**
     * Unbinds the currently bound file from the editor,
     * so that its contents are no longer changed on
     * editor change. Removes all file contents from
     * the editor view.
     */
    unbind() {
      
        if (this.editor === undefined) return;
        this.editor.removeAllListeners("change");
        this.editor.setValue("");
        this.editor.setReadOnly(true);
        this.editor.off("change");
    }
}


/**
 * Represents an interface to the editor backend.
 */
class Communicator {
    /**
     * Creates a communicator.
     *
     * @constructor
     */
    constructor() {}

    /**
     * Loads files and their MD5 hash from the last checkpoint asynchronously.
     * The last checkpoint is fetched via AJAX from the backend.
     *
     * @param {function} completion - The function to be called after load.
     * @param {Array} completion.files - The loaded files of the checkpoint.
     * @param {String} completion.hash - The MD5 hash of the checkpoint.
     */
    load(completion) {
        $.ajax({
            url: GET_LAST_CHECKPOINT_URL,
            type: "get",
            headers: {"X-CSRFToken": CSRF_TOKEN},
            datatype: "json",
            success: function(response) {
                if (response.success !== true) {
                    // Return empty files and empty hash
                    completion([], "");
                } else {
                    if (!response.files === null) {
                        // Return empty files and empty hash
                        completion([], "");
                    } else {
                        const editorFiles = [];
                        for (let file of response.files) {
                            editorFiles.push(new File(file.name, file.contents));
                        }
                        completion(editorFiles, response.checksum);
                    }
                }
            }
        });
    }

    /**
     * Saves the current editor state in asynchronously.
     * The current editor state is stored as a checkpoint
     * via AJAX in the backend.
     *
     * @param {function} [completion] - The function to be called after save.
     * @param {boolean} [completion.success] - The success status.
     */
    save(completion) {
        let files = [];
        for (let file of fileBuilder.files) {
            files.push({name: file.fileName, contents: file.fileContent});
        }
        let checksum = hashComparator.computeHash(fileBuilder.files);
        $.ajax({
            url: SAVE_CHECKPOINT_URL,
            type: "post",
            headers: {"X-CSRFToken": CSRF_TOKEN},
            contentType: "application/json; charset=utf-8",
            datatype: "json",
            data: JSON.stringify({checksum: checksum, files: files}),
            success: function(response) {
                if (response.success === true) {
                    hashComparator.updateHash(checksum);
                    hashComparator.lookForChanges(fileBuilder.files);
                    if (completion !== undefined) completion(true);
                } else {
                    if (completion !== undefined) completion(false);
                }
            }
        });
        document.querySelector(`#${EDITOR_ID} > textarea`).focus();
    }

    /**
     * Saves the given files asynchronously
     * and uploads them to the checker.
     *
     * @param {Array} files - The files to be uploaded.
     */
    upload(files) {
        this.save(function(success) {
            if (success !== true) {
                showAlert(getString(msgs.upload_failed));
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

document.getElementById(BTN_SAVE_ID).addEventListener('click', () => communicator.save());
document.getElementById(BTN_SUBMIT_ID).addEventListener('click', () => communicator.upload(fileBuilder.files));
document.getElementById(BTN_ADD_FILE_ID).addEventListener('click', () => tabBar.createNewEmptyTab());
document.getElementById(BTN_RENAME_FILE_ID).addEventListener('click', () => tabBar.edit(tabBar.activeTab.tabId));
document.getElementById(BTN_DELETE_FILE_ID).addEventListener('click', () => tabBar.destroyActiveTab(tabBar.activeTab.tabId));

function showPrompt(text, callback, value = '') {
  const result = window.prompt(`${text}\n\n`, value);
  result !== null && callback(result); 
}

function showConfirmDialog(text, callback) {
  const result = window.confirm(text);
  result && callback();
}

function showAlert(text) {
  window.alert(text);
}