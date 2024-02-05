import {pivotJq} from "./pivot";
import {csvFromTable} from "./table-to-csv";
import $ from "jquery";
export function pivotSetup($) {

    let pivotState = {};
    if (window.location.hash) {
        try {
            pivotState = JSON.parse(atob(window.location.hash.slice(1)));
        } catch(e) {
            console.log(e);
        }
    }
    pivotState["onRefresh"] = savePivotState;

    pivotJq($);
    let pivotInput = $("#preview").clone();
    pivotInput.find("tr.stats-th").remove();
    $(".pivot-table").pivotUI(pivotInput, pivotState);

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
