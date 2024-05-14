/*
This is the entrypoint for the client code, and for the Vite build. The basic
idea is to map a function to each page/url of the app that sets up the JS
needed for that page. The clientRoute and queryId are defined in base.html
template. clientRoute's value comes from the name of the Django URL pattern for
the page. The dynamic import() allows Vite to chunk the JS and only load what's
necessary for each page. Concretely, this matters because the pages with SQL
Editors require fairly heavy JS (CodeMirror).
*/
import * as bootstrap from 'bootstrap';

const route_initializers = {
    explorer_index:      () => import('./query-list').then(({setupQueryList}) => setupQueryList()),
    query_detail:        () => import('./explorer').then(({ExplorerEditor}) =>
        new ExplorerEditor(document.getElementById('queryIdGlobal').value)),
    query_create:        () => import('./explorer').then(({ExplorerEditor}) => new ExplorerEditor('new')),
    explorer_playground: () => import('./explorer').then(({ExplorerEditor}) => new ExplorerEditor('new')),
    explorer_schema:     () => import('./schema').then(({setupSchema}) => setupSchema()),
    explorer_connection_create:            () => import('./uploads').then(({setupUploads}) => setupUploads()),
    explorer_connection_update:            () => import('./uploads').then(({setupUploads}) => setupUploads())
};

document.addEventListener('DOMContentLoaded', function() {
    const clientRoute = document.getElementById('clientRoute').value;
    if (route_initializers.hasOwnProperty(clientRoute)) {
        route_initializers[clientRoute]();
    }
});
