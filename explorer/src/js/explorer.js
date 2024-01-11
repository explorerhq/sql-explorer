import $ from 'jquery';
import { EditorView } from "codemirror";

import { explorerSetup } from "./codemirror-config";

import cookie from 'cookiejs';
import List from 'list.js'

import 'floatthead'
import { getCsrfToken } from "./csrf";
import { toggleFavorite } from "./favorites";

import {pivotJq} from "./pivot";
import {csvFromTable} from "./table-to-csv";

import {schemaCompletionSource, StandardSQL} from "@codemirror/lang-sql";
import {StateEffect} from "@codemirror/state";


function editorFromTextArea(textarea) {
    let view = new EditorView({
        doc: textarea.value,
        extensions: [
            explorerSetup,
        ]})
    textarea.parentNode.insertBefore(view.dom, textarea)
    textarea.style.display = "none"
    if (textarea.form) textarea.form.addEventListener("submit", () => {
        textarea.value = view.state.doc.toString()
    })
    return view
}

export class ExplorerEditor {
    constructor(queryId) {
        this.queryId = queryId;
        this.$table = $("#preview");
        this.$rows = $("#rows");
        this.$form = $("form");
        this.$snapshotField = $("#id_snapshot");
        this.$paramFields = this.$form.find(".param");
        this.docChanged = false;

        this.$submit = $("#refresh_play_button, #save_button");
        if (!this.$submit.length) {
            this.$submit = $("#refresh_button");
        }

        this.editor = editorFromTextArea(document.getElementById("id_sql"));

        document.addEventListener('submitEventFromCM', (e) => {
            this.$submit.click();
        });

        document.addEventListener('docChanged', (e) => {
            this.docChanged = true;
        });

        pivotJq($);

        this.bind();

        if (cookie.get("schema_sidebar_open") === 'true') {
            this.showSchema(true);
        }
    }

    getParams() {
        var o = false;
        if(this.$paramFields.length) {
            o = {};
            this.$paramFields.each(function() {
                o[$(this).data("param")] = $(this).val();
            });
        }
        return o;
    }

    serializeParams(params) {
        var args = [];
        for(var key in params) {
            args.push(key + ":" + params[key]);
        }
        return encodeURIComponent(args.join("|"));
    }

    savePivotState(state) {
        const picked = (({ aggregatorName, rows, cols, rendererName, vals }) => ({ aggregatorName, rows, cols, rendererName, vals }))(state);
        const jsonString = JSON.stringify(picked);
        let bmark = btoa(jsonString);
        let $el = $("#pivot-bookmark");
        $el.attr("href", $el.data("baseurl") + "#" + bmark);
    }

    updateQueryString(key, value, url) {
        // http://stackoverflow.com/a/11654596/221390
        if (!url) url = window.location.href;
        var re = new RegExp("([?&])" + key + "=.*?(&|#|$)(.*)", "gi"),
            hash = url.split("#");

        if (re.test(url)) {
            if (typeof value !== "undefined" && value !== null)
                return url.replace(re, "$1" + key + "=" + value + "$2$3");
            else {
                url = hash[0].replace(re, "$1$3").replace(/(&|\?)$/, "");
                if (typeof hash[1] !== "undefined" && hash[1] !== null)
                    url += "#" + hash[1];
                return url;
            }
        }
        else {
            if (typeof value !== "undefined" && value !== null) {
                var separator = url.indexOf("?") !== -1 ? "&" : "?";
                url = hash[0] + separator + key + "=" + value;
                if (typeof hash[1] !== "undefined" && hash[1] !== null)
                    url += "#" + hash[1];
                return url;
            }
            else
                return url;
        }
    }

    formatSql() {
        let sqlText = this.editor.state.doc.toString();
        let editor = this.editor;

        $.ajax({
            url: "../format/",
            type: "POST",
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            data: {
                sql: sqlText
            },
            success: function(data) {
                editor.dispatch({
                    changes: {
                        from: 0,
                        to: editor.state.doc.length,
                        insert: data.formatted
                    }
                })
            }.bind(this)
        });
    }

    showRows() {
        var rows = this.$rows.val(),
            $form = $("#editor");
        $form.attr("action", this.updateQueryString("rows", rows, window.location.href));
        $form.submit();
    }

    showSchema(noAutofocus) {
        $("#schema_frame").attr("src", "../schema/" + $("#id_connection").val());
        if (noAutofocus === true) {
            $("#schema_frame").addClass("no-autofocus");
        }
        $("#query_area").removeClass("col").addClass("col-9");
        var schema$ = $("#schema");
        schema$.addClass("col-md-3");
        schema$.show();
        $("#show_schema_button").hide();
        $("#hide_schema_button").show();
        cookie.set("schema_sidebar_open", 'true');
        return false;
    }

    hideSchema() {
        $("#query_area").removeClass("col-9").addClass("col");
        var schema$ = $("#schema");
        schema$.removeClass("col-3");
        schema$.hide();
        $(this).hide();
        $("#show_schema_button").show();
        cookie.set("schema_sidebar_open", 'false');
        return false;
    }

    bind() {

        $(window).on("beforeunload", function () {
            // Only do this if changed-input is on the page and we"re not on the playground page.
            if (clientRoute === 'query_detail' && this.docChanged) {
                return "You have unsaved changes to your query.";
            }
        }.bind(this));

        // Disable unsaved changes warning when submitting the editor form
        $(document).on("submit", "#editor", function(event){
            // disable warning
            $(window).off("beforeunload");
        });

        let button = document.querySelector("#button-excel");
        if (button) {
                button.addEventListener("click", e => {
                let table = document.querySelector(".pvtTable");
                if (typeof (table) != 'undefined' && table != null) {
                    csvFromTable(table);
                }
            });
        }

        document.querySelectorAll('.query_favorite_toggle').forEach(function(element) {
            element.addEventListener('click', toggleFavorite);
        });

        $("#show_schema_button").click(this.showSchema);
        $("#hide_schema_button").click(this.hideSchema);

        $("#format_button").click(function(e) {
            e.preventDefault();
            this.formatSql();
        }.bind(this));

        $("#rows").keyup(function() {
            var curUrl = $("#fullscreen").attr("href");
            var newUrl = curUrl.replace(/rows=\d+/, "rows=" + $("#rows").val());
            $("#fullscreen").attr("href", newUrl);
        }.bind(this));

        $("#save_button").click(function() {
            var params = this.getParams(this);
            if(params) {
                this.$form.attr("action", "../" + this.queryId + "/?params=" + this.serializeParams(params));
            }
            this.$snapshotField.hide();
            this.$form.append(this.$snapshotField);
        }.bind(this));

        $("#save_only_button").click(function() {
            var params = this.getParams(this);
            if(params) {
                this.$form.attr('action', '../' + this.queryId + '/?show=0&params=' + this.serializeParams(params));
            } else {
                this.$form.attr('action', '../' + this.queryId + '/?show=0');
            }
            this.$snapshotField.hide();
            this.$form.append(this.$snapshotField);
        }.bind(this));

        $("#refresh_button").click(function(e) {
            e.preventDefault();
            var params = this.getParams();
            if(params) {
                window.location.href = "../" + this.queryId + "/?params=" + this.serializeParams(params);
            } else {
                window.location.href = "../" + this.queryId + "/";
            }
        }.bind(this));

        $("#refresh_play_button").click(function() {
            this.$form.attr("action", "../play/");
        }.bind(this));

        $("#playground_button").click(function(e) {
            e.preventDefault();
            this.$form.attr("action", "../play/?show=0");
            this.$form.submit();
        }.bind(this));

        $("#create_button").click(function() {
            this.$form.attr("action", "../new/");
        }.bind(this));

        $(".download-button").click(function(e) {
            var url = "../download?format=" + $(e.target).data("format");
            var params = this.getParams();
            if(params) {
                url = url + "&params=" + params;
            }
            this.$form.attr("action", url);
        }.bind(this));

        $(".download-query-button").click(function(e) {
            var url = "../download?format=" + $(e.target).data("format");
            var params = this.getParams();
            if(params) {
                url = url + "&params=" + params;
            }
            this.$form.attr("action", url);
        }.bind(this));

        $(".stats-expand").click(function(e) {
            e.preventDefault();
            $(".stats-expand").hide();
            $(".stats-wrapper").show();
            this.$table.floatThead("reflow");
        }.bind(this));

        $("#counter-toggle").click(function(e) {
            e.preventDefault();
            $(".counter").toggle();
            this.$table.floatThead("reflow");
        }.bind(this));

        $(".sort").click(function(e) {
            var t = $(e.target).data("sort");
            var dir = $(e.target).data("dir");
            $(".sort").addClass("bi-chevron-expand");
            $(".sort").removeClass("bi-chevron-down");
            $(".sort").removeClass("bi-chevron-up");
            if (dir === "asc"){
                $(e.target).data("dir", "desc");
                $(e.target).addClass("bi-chevron-up");
                $(e.target).removeClass("bi-chevron-down");
                $(e.target).removeClass("bi-chevron-expand");
            } else {
                $(e.target).data("dir", "asc");
                $(e.target).addClass("bi-chevron-down");
                $(e.target).removeClass("bi-chevron-up");
                $(e.target).removeClass("bi-chevron-expand");
            }
            var vals = [];
            var ct = 0;
            while (ct < this.$table.find("th").length) {
               vals.push(ct++);
            }
            var options = {
                valueNames: vals
            };
            var tableList = new List("preview", options);
            tableList.sort(t, { order: dir });
        }.bind(this));

        $("#preview-tab-label").click(function() {
            this.$table.floatThead("reflow");
        }.bind(this));

        var pivotState = window.location.hash;
        var navToPivot = false;
        if (!pivotState) {
            pivotState = {onRefresh: this.savePivotState};
        } else {
            try {
                pivotState = JSON.parse(atob(pivotState.substr(1)));
                pivotState["onRefresh"] = this.savePivotState;
                navToPivot = true;
            } catch(e) {
                pivotState = {onRefresh: this.savePivotState};
            }
        }

        $(".pivot-table").pivotUI(this.$table, pivotState);
        if (navToPivot) {
            let pivotEl = document.querySelector('#nav-pivot-tab')
            pivotEl.click()
        }

        setTimeout(function() {
            this.$table.floatThead({
                scrollContainer: function() {
                                    return this.$table.closest(".overflow-wrapper");
                                }.bind(this)
            });
        }.bind(this), 1);

        this.$rows.change(function() { this.showRows(); }.bind(this));
        this.$rows.keyup(function(event) {
            if(event.keyCode === 13){ this.showRows(); }
        }.bind(this));

        fetch('../schema.json/' + $("#id_connection").val())
            .then(response => {
                return response.json();
            })
            .then(data => {
                this.editor.dispatch({
                    effects: StateEffect.appendConfig.of(
                        StandardSQL.language.data.of({
                          autocomplete: schemaCompletionSource({schema: data})
                        })
                    )
                })
                return data;
            })
            .catch(error => {
                console.error('Error retrieving JSON schema:', error);
            });
    }
}
