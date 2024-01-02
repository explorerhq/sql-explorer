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

let updateListenerExtension = EditorView.updateListener.of((update) => {
  if (update.docChanged) {
    document.dispatchEvent(new CustomEvent('docChanged', {}));
  }
});

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
    sql({
        //schema: window.schema_json
    }),
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
    keymap.of([
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...searchKeymap,
        ...historyKeymap,
        ...foldKeymap,
        ...completionKeymap,
        ...lintKeymap,
        ...autocompleteKeymap
    ])
])()
