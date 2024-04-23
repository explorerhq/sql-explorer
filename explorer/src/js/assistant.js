import {getCsrfToken} from "./csrf";
import { marked } from "marked";
import DOMPurify from "dompurify";
import * as bootstrap from 'bootstrap';
import $ from "jquery";
import List from "list.js";

function getErrorMessage() {
    const errorElement = document.querySelector('.alert-danger.db-error');
    return errorElement ? errorElement.textContent.trim() : null;
}

function assistantSearchFocus() {
    document.getElementById("search_assistant_tables").focus();
}

export function setUpAssistant(expand = false) {

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

    fetch('../schema.json/' + $("#id_connection").val())
    .then(response => {
        return response.json();
    })
    .then(data => {
        const keys = Object.keys(data);
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
    })
    .catch(error => {
        console.error('Error retrieving JSON schema:', error);
    });

    const checkbox = document.getElementById('include_other_tables');
    const additionalTableContainer = document.getElementById('additional_table_container');
    const assistantInputWrapper = document.getElementById('assistant_input_wrapper');

    function showHideExtraTables(checked) {
        if (checked) {
            additionalTableContainer.classList.remove('d-none');
            assistantInputWrapper.classList.remove('col-12');
            assistantInputWrapper.classList.add('col-9');
            assistantSearchFocus();
        } else {
            additionalTableContainer.classList.add('d-none');
            assistantInputWrapper.classList.remove('col-9');
            assistantInputWrapper.classList.add('col-12');
        }
    }
    checkbox.addEventListener('change', function() {
        showHideExtraTables(this.checked);
    });
    showHideExtraTables(checkbox.checked);

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
