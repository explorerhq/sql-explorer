import List from "list.js";

function searchFocus() {
    let schemaFrame = window.parent.document.getElementById("schema_frame");
    if (!schemaFrame.classList.contains('no-autofocus')) {
        document.querySelector(".search").focus();
    }
}

export function setupSchema() {

    let options = {
        valueNames: ['app-name'],
        handlers: {'updated': [searchFocus]}
    };

    new List('schema-contents', options);

    document.getElementById('collapse_all').addEventListener('click', function () {
        document.querySelectorAll('.schema-table').forEach(function (element) {
            element.style.display = 'none';
        });
    });

    document.getElementById('expand_all').addEventListener('click', function () {
        document.querySelectorAll('.schema-table').forEach(function (element) {
            element.style.display = '';
        });
    });

    document.querySelectorAll('.schema-header').forEach(function (header) {
        header.addEventListener('click', function () {
            let schemaTable = this.parentElement.querySelector('.schema-table');
            if (schemaTable.style.display === 'none' || schemaTable.style.display === '') {
                schemaTable.style.display = 'block';
            } else {
                schemaTable.style.display = 'none';
            }
        });
    });
}
