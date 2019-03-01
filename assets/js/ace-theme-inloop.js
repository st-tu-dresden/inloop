ace.define("ace/theme/inloop",["require","exports","module","ace/lib/dom"], function(require, exports, module) {

exports.isDark = false;
exports.cssClass = "ace-inloop";
exports.cssText = "\
.ace-inloop .ace_tooltip .ace_doc-tooltip {\
background: #fff;\
background-image: none;\
border-radius: 8px;\
}\
.ace-inloop .ace_gutter {\
background: rgb(245, 245, 245);\
color: #111;\
}\
.ace-inloop  {\
background: rgb(250, 250, 250);\
color: #000;\
}\
.ace-inloop .ace_keyword {\
font-weight: bold;\
}\
.ace-inloop .ace_string {\
color: #D14;\
}\
.ace-inloop .ace_variable.ace_class {\
color: teal;\
}\
.ace-inloop .ace_constant.ace_numeric {\
color: #099;\
}\
.ace-inloop .ace_constant.ace_buildin {\
color: #0086B3;\
}\
.ace-inloop .ace_support.ace_function {\
color: #0086B3;\
}\
.ace-inloop .ace_comment {\
color: #998;\
font-style: italic;\
}\
.ace-inloop .ace_variable.ace_language  {\
color: #0086B3;\
}\
.ace-inloop .ace_paren {\
font-weight: bold;\
}\
.ace-inloop .ace_boolean {\
font-weight: bold;\
}\
.ace-inloop .ace_string.ace_regexp {\
color: #009926;\
font-weight: normal;\
}\
.ace-inloop .ace_variable.ace_instance {\
color: teal;\
}\
.ace-inloop .ace_constant.ace_language {\
font-weight: bold;\
}\
.ace-inloop .ace_cursor {\
color: black;\
}\
.ace-inloop.ace_focus .ace_marker-layer .ace_active-line {\
background: rgba(56,103,214, 0.1);\
}\
.ace-inloop .ace_marker-layer .ace_active-line {\
background: rgb(245, 245, 245);\
}\
.ace-inloop .ace_marker-layer .ace_selection {\
background: rgb(181, 213, 255);\
}\
.ace-inloop.ace_multiselect .ace_selection.ace_start {\
box-shadow: 0 0 3px 0px white;\
}\
.ace-inloop.ace_nobold .ace_line > span {\
font-weight: normal !important;\
}\
.ace-inloop .ace_marker-layer .ace_step {\
background: rgb(252, 255, 0);\
}\
.ace-inloop .ace_marker-layer .ace_stack {\
background: rgb(164, 229, 101);\
}\
.ace-inloop .ace_marker-layer .ace_bracket {\
margin: -1px 0 0 -1px;\
border: 1px solid rgb(192, 192, 192);\
}\
.ace-inloop .ace_gutter-active-line {\
background-color : rgba(0, 0, 0, 0.07);\
}\
.ace-inloop .ace_gutter-cell {\
color: #111;\
}\
.ace-inloop .ace_marker-layer .ace_selected-word {\
background: rgb(250, 250, 255);\
border: 1px solid rgb(200, 200, 250);\
}\
.ace-inloop .ace_invisible {\
color: #BFBFBF\
}\
.ace-inloop .ace_print-margin {\
width: 1px;\
background: #e8e8e8;\
}\
.ace-inloop .ace_indent-guide {}";

    var dom = require("../lib/dom");
    dom.importCssString(exports.cssText, exports.cssClass);
});
(function() {
    ace.require(["ace/theme/inloop"], function(m) {
        if (typeof module == "object" && typeof exports == "object" && module) {
            module.exports = m;
        }
    });
})();
