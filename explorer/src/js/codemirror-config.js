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
            const tooltip = document.querySelector('#schema-tooltip');
            if (tooltip) tooltip.style.display = 'none';
            return true;
        }
        return false;
    }
});

function displaySchemaTooltip(editor, content) {
    let tooltip = document.getElementById('schema-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'schema-tooltip';
        tooltip.style.position = 'absolute';
        tooltip.style.bottom = '1rem';
        tooltip.style.zIndex = 1000;
        tooltip.style.backgroundColor = 'white';
        tooltip.style.border = '1px solid black';
        tooltip.style.padding = '5px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
        document.getElementById('sql_editor_container').appendChild(tooltip);
    }

    tooltip.textContent = content;
    tooltip.style.display = 'block';

}

function fetchAndShowSchema(view) {
    const { state } = view;
    const pos = state.selection.main.head;
    const wordRange = state.wordAt(pos);

    if (wordRange) {
        const tableName = state.doc.sliceString(wordRange.from, wordRange.to);
        const conn = document.querySelector('#id_connection').value;
        SchemaSvc.get(conn).then(schema => {
            let formattedSchema;
            if (schema.hasOwnProperty(tableName)) {
                formattedSchema = JSON.stringify(schema[tableName], null, 2);
            } else {
                formattedSchema = `Table '${tableName}' not found in schema for connection '${conn}'`;
            }
            displaySchemaTooltip(view, formattedSchema);
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
        ...schemaKeymap
    ])
])()
