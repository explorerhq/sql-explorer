import {getConnElement, SchemaSvc} from "./schemaService"
import Choices from "choices.js"


function populateTableList() {

    if (window.tableChoices) {
        window.tableChoices.destroy();
        document.getElementById('id_table_name').innerHTML = '';
    }

    SchemaSvc.get().then(schema => {

        const tables = Object.keys(schema);
        const selectElement = document.getElementById('id_table_name');
        selectElement.toggleAttribute('data-trigger');

        selectElement.appendChild(document.createElement('option'));

        tables.forEach((t) => {
            const option = document.createElement('option');
            option.value = t;
            option.textContent = t;
            selectElement.appendChild(option);
        });

        window.tableChoices = new Choices('#id_table_name', {
            searchEnabled: true,
            shouldSort: true,
            placeholder: true,
            placeholderValue: 'Select table',
            position: 'bottom'
        });

    });
}

export function setupTableDescription() {
    getConnElement().addEventListener('change', populateTableList);
    populateTableList();
}
