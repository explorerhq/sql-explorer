import {
    keymap, highlightSpecialChars, drawSelection, highlightActiveLine, dropCursor,
    lineNumbers, highlightActiveLineGutter
} from "@codemirror/view"
import {
    defaultHighlightStyle, syntaxHighlighting, indentOnInput, bracketMatching,
    foldGutter, foldKeymap
} from "@codemirror/language"
import {defaultKeymap, history, historyKeymap} from "@codemirror/commands"
import {searchKeymap, highlightSelectionMatches} from "@codemirror/search"
import {autocompletion, completionKeymap, closeBrackets, closeBracketsKeymap} from "@codemirror/autocomplete"
import {lintKeymap} from "@codemirror/lint"
import { Prec } from "@codemirror/state";
import {sql} from "@codemirror/lang-sql";


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



export const explorerSetup = (() => [
    sql(),
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
    keymap.of([
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...searchKeymap,
        ...historyKeymap,
        ...foldKeymap,
        ...completionKeymap,
        ...lintKeymap
    ])
])()
