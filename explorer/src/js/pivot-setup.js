import {pivotJq} from "./pivot";
import {csvFromTable} from "./table-to-csv";
export function pivotSetup($, $table) {

    let pivotState = window.location.hash;
    if (!pivotState) {
        pivotState = {onRefresh: savePivotState};
    } else {
        try {
            pivotState = JSON.parse(atob(pivotState.slice(1)));
            pivotState["onRefresh"] = savePivotState;
        } catch(e) {
            pivotState = {onRefresh: savePivotState};
        }
    }

    pivotJq($);
    $(".pivot-table").pivotUI($table, pivotState);

    let csvButton = document.querySelector("#button-excel");
    if (csvButton) {
        csvButton.addEventListener("click", e => {
            let table = document.querySelector(".pvtTable");
            if (typeof (table) != 'undefined' && table != null) {
                csvFromTable(table);
            }
        });
    }
}

function savePivotState(state) {
    const picked = (({ aggregatorName, rows, cols, rendererName, vals }) => ({ aggregatorName, rows, cols, rendererName, vals }))(state);
    const jsonString = JSON.stringify(picked);
    let bmark = btoa(jsonString);
    let el = document.getElementById("pivot-bookmark");
    if(el) {
        el.setAttribute("href", el.dataset.baseurl + "#" + bmark);
    }
}
