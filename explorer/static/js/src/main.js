import * as bootstrap from 'bootstrap'; // eslint-disable-line no-unused-vars
import {ExplorerEditor} from "./explorer"
import {setupQueryList} from "./query-list"
import {setupSchema} from "./schema";


// TODO add back in XLSX export support

const route_initializers = {
    explorer_index: setupQueryList,
    query_detail: () => new ExplorerEditor(queryId),
    query_create: () => new ExplorerEditor('new'),
    explorer_playground: () => new ExplorerEditor('new'),
    explorer_schema: setupSchema
};

document.addEventListener('DOMContentLoaded', function() {
    route_initializers[clientRoute]();
});
