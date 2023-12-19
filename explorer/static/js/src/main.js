// Import all of Bootstrap's JS
import * as bootstrap from 'bootstrap'; // eslint-disable-line no-unused-vars

import {toggleFavorite} from "./favorites";
import {ExplorerEditor} from "./explorer"
import {setupList} from "./query-list"
import List from 'list.js'
import $ from "jquery";
import {getCsrfToken} from "./csrf";

const route_initializers = {
    explorer_index: function() {
        document.querySelectorAll('.query_favorite_toggle').forEach(function(element) {
            element.addEventListener('click', toggleFavorite);
        });
        function SearchFocus() {
            const searchElement = document.querySelector('.search');
            if (searchElement) {
                searchElement.focus();
            }
        }

        let options = {
            valueNames: [ 'name' ],
            handlers: { 'updated': [SearchFocus] }
        };
        new List('queries', options);
        setupList();
    },
    query_detail: function() {
        document.querySelectorAll('.query_favorite_toggle').forEach(function(element) {
            element.addEventListener('click', toggleFavorite);
        });
        new ExplorerEditor(queryId);
    },
    query_create: function() {
        new ExplorerEditor('new');
    },
    explorer_playground: function() {
        new ExplorerEditor('new');
    },
    explorer_schema: function() {
        function SearchFocus() {
            if (!$(window.parent.document.getElementById("schema_frame")).hasClass('no-autofocus')) {
                $(".search").focus();
            }
        }
        let options = {
            valueNames: [ 'name', 'app' ],
            handlers: { 'updated': [SearchFocus] }
        };
        new List('tables', options);

        $('#collapse_all').click(function(){
            $('.schema-table').hide();
        });
        $('#expand_all').click(function(){
            $('.schema-table').show();
        });
        $('.schema-header').click(function(){
            $(this).parent().find('.schema-table').toggle();
        });
    }
};

$.ajaxSetup({
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
    }
});

document.addEventListener('DOMContentLoaded', function() {
    route_initializers[clientRoute]();
});
