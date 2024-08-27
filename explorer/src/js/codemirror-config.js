import {
    keymap, highlightSpecialChars, drawSelection, highlightActiveLine, dropCursor,
    lineNumbers, highlightActiveLineGutter, EditorView
} from "@codemirror/view"
import {
    defaultHighlightStyle, syntaxHighlighting, indentOnInput, bracketMatching,
    foldGutter, foldKeymap
} from "@codemirror/language"
import {defaultKeymap, history, historyKeymap} from "@codemirror/commands"
import {searchKeymap, highlightSelectionMatches} from "@codemirror/search"
import {autocompletion, completionKeymap, closeBrackets, closeBracketsKeymap, acceptCompletion} from "@codemirror/autocomplete"
import {lintKeymap} from "@codemirror/lint"
import { Prec } from "@codemirror/state";
import {sql} from "@codemirror/lang-sql";
import { SchemaSvc } from "./schemaService"


let updateListenerExtension = EditorView.updateListener.of((update) => {
  if (update.docChanged) {
      document.dispatchEvent(new CustomEvent('docChanged', {}));
  }
});

const hideTooltipOnEsc = EditorView.domEventHandlers({
    keydown(event, view) {
        if (event.code === 'Escape') {
            const tooltip = document.getElementById('schema_tooltip');
            if (tooltip) {
                tooltip.classList.add('d-none');
                tooltip.classList.remove('d-block');
            }
            return true;
        }
        return false;
    }
});

function displaySchemaTooltip(content) {
    let tooltip = document.getElementById('schema_tooltip');
    if (tooltip) {
        tooltip.classList.remove('d-none');
        tooltip.classList.add('d-block');

        // Clear existing content
        tooltip.textContent = '';

        content.forEach(item => {
            let column = document.createElement('span');
            column.textContent = item;
            column.classList.add('mx-1')
            tooltip.appendChild(column);
        });
    }
}

function fetchAndShowSchema(view) {
    const { state } = view;
    const pos = state.selection.main.head;
    const wordRange = state.wordAt(pos);

    if (wordRange) {
        const tableName = state.doc.sliceString(wordRange.from, wordRange.to);
        SchemaSvc.get().then(schema => {
            let formattedSchema;
            if (schema.hasOwnProperty(tableName)) {
                displaySchemaTooltip(schema[tableName]);
            } else {
                const errorMsg = [`Table '${tableName}' not found in schema for connection`];
                displaySchemaTooltip(errorMsg);
            }
        });
    }
    return true;
}

const schemaKeymap = [
    {
        key: "Ctrl-S",
        mac: "Cmd-S",
        run: (editor) => {
            fetchAndShowSchema(editor);
            return true;
        }
    },
    {
        key: "Cmd-S",
        run: (editor) => {
            fetchAndShowSchema(editor);
            return true;
        }
    }
];

const submitEventFromCM = new CustomEvent('submitEventFromCM', {});
const submitKeymapArr = [
    {
        key: "Ctrl-Enter",
        run: () => {
            document.dispatchEvent(submitEventFromCM);
            return true;
        }
    },
    {
        key: "Cmd-Enter",
        run: () => {
            document.dispatchEvent(submitEventFromCM);
            return true;
        }
    }
]


const formatEventFromCM = new CustomEvent('formatEventFromCM', {});
const formatKeymap = [
    {
        key: "Ctrl-F",
        mac: "Cmd-F",
        run: () => {
            document.dispatchEvent(formatEventFromCM);
            return true;
        }
    },
    {
        key: "Ctrl-F",
        mac: "Cmd-F",
        run: () => {
            document.dispatchEvent(formatEventFromCM);
            return true;
        }
    }
]

const submitKeymap = Prec.highest(
    keymap.of(
      submitKeymapArr
    )
)

const autocompleteKeymap = [{key: "Tab", run: acceptCompletion}]


export const explorerSetup = (() => [
    sql({}),
    lineNumbers(),
    highlightActiveLineGutter(),
    highlightSpecialChars(),
    history(),
    foldGutter(),
    drawSelection(),
    dropCursor(),
    indentOnInput(),
    syntaxHighlighting(defaultHighlightStyle, {fallback: true}),
    bracketMatching(),
    closeBrackets(),
    autocompletion(),
    highlightActiveLine(),
    highlightSelectionMatches(),
    submitKeymap,
    updateListenerExtension,
    hideTooltipOnEsc,
    keymap.of([
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...searchKeymap,
        ...historyKeymap,
        ...foldKeymap,
        ...completionKeymap,
        ...lintKeymap,
        ...autocompleteKeymap,
        ...schemaKeymap,
        ...formatKeymap
    ])
])()
