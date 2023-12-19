// Import all of Bootstrap's JS
import * as bootstrap from 'bootstrap'; // eslint-disable-line no-unused-vars

import {toggleFavorite} from "./favorites";
import {ExplorerEditor} from "./explorer"
import {setupList} from "./query-list"
import List from 'list.js'
import $ from "jquery";
import cookie from "cookiejs";

const route_initializers = {
    explorer_index: function() {
        document.querySelectorAll('.query_favorite_toggle').forEach(function(element) {
            element.addEventListener('click', toggleFavorite);
        });
        function SearchFocus() {
            const searchElement = document.querySelector('.search-foo');
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
        new ExplorerEditor(queryId);
    },
    explorer_playground: function() {
        new ExplorerEditor('new');
    },
};

function getCsrfToken() {
    if (csrfCookieHttpOnly) {
        return $('[name=csrfmiddlewaretoken]').val();
    }

    return cookie.get(csrfCookieName);
}

$.ajaxSetup({
    beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
    }
});

document.addEventListener('DOMContentLoaded', function() {
    route_initializers[clientRoute]();
});
