const route_initializers = {
    explorer_index: import('./query-list').then(({setupQueryList}) => setupQueryList),
    query_detail: () => import('./explorer').then(({ExplorerEditor}) => new ExplorerEditor(queryId)),
    query_create: () => import('./explorer').then(({ExplorerEditor}) => new ExplorerEditor(queryId)),
    explorer_playground: () => import('./explorer').then(({ExplorerEditor}) => new ExplorerEditor(queryId)),
    explorer_schema: import('./schema').then(({setupSchema}) => setupSchema),
};

document.addEventListener('DOMContentLoaded', function() {
    route_initializers[clientRoute]();
});
