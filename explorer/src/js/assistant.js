import {getCsrfToken} from "./csrf";
import { marked } from "marked";
import DOMPurify from "dompurify";
import * as bootstrap from 'bootstrap';
import List from "list.js";
import { SchemaSvc, getConnElement } from "./schemaService"

function getErrorMessage() {
    const errorElement = document.querySelector('.alert-danger.db-error');
    return errorElement ? errorElement.textContent.trim() : null;
}

function setupTableList() {
    SchemaSvc.get().then(schema => {
        const keys = Object.keys(schema);
        const tableList = document.getElementById('table-list');
        tableList.innerHTML = '';

        keys.forEach((key, index) => {
            const div = document.createElement('div');
            div.className = 'form-check';

            const input = document.createElement('input');
            input.className = 'form-check-input table-checkbox';
            input.type = 'checkbox';
            input.value = key;
            input.id = 'flexCheckDefault' + index;

            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.setAttribute('for', input.id);
            label.textContent = key;

            div.appendChild(input);
            div.appendChild(label);
            tableList.appendChild(div);
        });

        let options = {
            valueNames: ['form-check-label'],
        };

        new List('additional_table_container', options);

        const selectAllButton = document.getElementById('select_all_button');
        const checkboxes = document.querySelectorAll('.table-checkbox');

        let selectState = 'all';

        selectAllButton.innerHTML = 'Select All';

        selectAllButton.addEventListener('click', (e) => {
            e.preventDefault();
            const isSelectingAll = selectState === 'all';
            checkboxes.forEach((checkbox) => {
                checkbox.checked = isSelectingAll;
            });
            selectState = isSelectingAll ? 'none' : 'all';
            selectAllButton.innerHTML = isSelectingAll ? 'Deselect All' : 'Select All';
        });
    })
    .catch(error => {
        console.error('Error retrieving JSON schema:', error);
    });
}

export function setUpAssistant(expand = false) {

    getConnElement().addEventListener('change', setupTableList);
    setupTableList();

    const error = getErrorMessage();

    if(expand || error) {
        const myCollapseElement = document.getElementById('assistant_collapse');
        const bsCollapse = new bootstrap.Collapse(myCollapseElement, {
          toggle: false
        });
        bsCollapse.show();
        if(error) {
            document.getElementById('id_error_help_message').classList.remove('d-none');
        }
    }

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    document.getElementById('id_assistant_input').addEventListener('keydown', function(event) {
        if ((event.ctrlKey || event.metaKey) && (event.key === 'Enter')) {
            event.preventDefault();
            submitAssistantAsk();
        }
    });

    document.getElementById('ask_assistant_btn').addEventListener('click', submitAssistantAsk);
}

function submitAssistantAsk() {

    const selectedTables = Array.from(
        document.querySelectorAll('.table-checkbox:checked')
    ).map(cb => cb.value);

    const data = {
        sql: window.editor?.state.doc.toString() ?? null,
        connection: document.getElementById("id_connection")?.value ?? null,
        assistant_request: document.getElementById("id_assistant_input")?.value ?? null,
        selected_tables: selectedTables,
        db_error: getErrorMessage()
    };

    document.getElementById("assistant_response").innerHTML = '';
    document.getElementById("response_block").classList.remove('d-none');
    document.getElementById("assistant_spinner").classList.remove('d-none');

    fetch('../assistant/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const output = DOMPurify.sanitize(marked.parse(data.message));
        document.getElementById("assistant_response").innerHTML = output;
        document.getElementById("assistant_spinner").classList.add('d-none');

        // If there is exactly one code block in the response and the SQL editor is empty
        // then copy the code directly into the editor
        const preElements = document.querySelectorAll('#assistant_response pre');
        if (preElements.length === 1 && window.editor?.state.doc.toString().trim() === "") {
            window.editor.dispatch({
                changes: {
                    from: 0,
                    insert: preElements[0].textContent
                }
            });
        }

        // Similarly, if there is no description, copy the prompt into the description
        const prompt = document.getElementById("id_assistant_input")?.value;
        const description = document.getElementById("id_description");
        if (description?.value === "") {
            description.value = prompt;
        }

        setUpCopyButtons();
    })
        .catch(error => {
        console.error('Error:', error);
    });
}

function setUpCopyButtons(){
    document.querySelectorAll('#assistant_response pre').forEach(pre => {

        const btn = document.createElement('i');
        btn.classList.add('copy-btn');
        btn.classList.add('bi-copy');
        const msg = document.createElement('span');
        msg.textContent = 'Copied!';
        msg.style.display = 'none';
        msg.style.marginLeft = '8px';
        btn.appendChild(msg);
        pre.appendChild(btn);

        btn.addEventListener('click', function() {
            const code = this.parentNode.firstElementChild.innerText;
            navigator.clipboard.writeText(code).then(() => {
                msg.style.display = 'inline';
                setTimeout(() => {
                    msg.style.display = 'none';
                }, 2000);
            }).catch(err => {
                console.error('Error in copying text: ', err);
            });
        });
    });
}
