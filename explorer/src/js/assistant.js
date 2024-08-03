import {getCsrfToken} from "./csrf";
import { marked } from "marked";
import DOMPurify from "dompurify";
import * as bootstrap from "bootstrap";
import { SchemaSvc, getConnElement } from "./schemaService"
import Choices from "choices.js"

function getErrorMessage() {
    const errorElement = document.querySelector('.alert-danger.db-error');
    return errorElement ? errorElement.textContent.trim() : null;
}

function setupTableList() {

    if(window.assistantChoices) {
        window.assistantChoices.destroy();
    }

    SchemaSvc.get().then(schema => {
        const keys = Object.keys(schema);
        const selectElement = document.createElement('select');
        selectElement.className = 'js-choice';
        selectElement.toggleAttribute('multiple');
        selectElement.toggleAttribute('data-trigger');

        keys.forEach((key) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key;
            selectElement.appendChild(option);
        });

        const tableList = document.getElementById('table-list');
        tableList.innerHTML = '';
        tableList.appendChild(selectElement);

        const choices = new Choices('.js-choice', {
            removeItemButton: true,
            searchEnabled: true,
            shouldSort: false,
            placeholder: true,
            placeholderValue: 'Relevant tables',
            position: 'bottom'
        });

        // TODO - nasty. Should be refactored. Used by submitAssistantAsk to get relevant tables.
        window.assistantChoices = choices;

        const selectAllButton = document.getElementById('select_all_button');
        selectAllButton.addEventListener('click', (e) => {
            e.preventDefault();
            choices.setChoiceByValue(keys);
        });

        const deselectAllButton = document.getElementById('deselect_all_button');
        deselectAllButton.addEventListener('click', (e) => {
            e.preventDefault();
            keys.forEach(k => {
                choices.removeActiveItemsByValue(k);
            });
        });

        selectRelevantTables(choices, keys);

        document.addEventListener('docChanged', (e) => {
            selectRelevantTables(choices, keys);
        });
    })
    .catch(error => {
        console.error('Error retrieving JSON schema:', error);
    });
}

function selectRelevantTables(choices, keys) {
    const textContent = window.editor.state.doc.toString();
    const textWords = new Set(textContent.split(/\s+/));
    const hasKeys = keys.filter(key => textWords.has(key));
    choices.setChoiceByValue(hasKeys);
}


export function setUpAssistant(expand = false) {

    getConnElement().addEventListener('change', setupTableList);
    setupTableList();

    const error = getErrorMessage();

    if (expand || error) {
        const myCollapseElement = document.getElementById('assistant_collapse');
        const bsCollapse = new bootstrap.Collapse(myCollapseElement, {
            toggle: false
        });
        bsCollapse.show();
        if (error) {
            document.getElementById('id_error_help_message').classList.remove('d-none');
        }
    }

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    document.getElementById('id_assistant_input').addEventListener('keydown', function (event) {
        if ((event.ctrlKey || event.metaKey) && (event.key === 'Enter')) {
            event.preventDefault();
            submitAssistantAsk();
        }
    });

    document.getElementById('ask_assistant_btn').addEventListener('click', submitAssistantAsk);
}

function submitAssistantAsk() {

    const data = {
        sql: window.editor?.state.doc.toString() ?? null,
        connection_id: document.getElementById("id_database_connection")?.value ?? null,
        assistant_request: document.getElementById("id_assistant_input")?.value ?? null,
        selected_tables: assistantChoices.getValue(true),
        db_error: getErrorMessage()
    };

    document.getElementById("assistant_response").innerHTML = '';
    document.getElementById("response_block").classList.remove('d-none');
    document.getElementById("assistant_spinner").classList.remove('d-none');

    fetch(`${window.baseUrlPath}assistant/`, {
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
