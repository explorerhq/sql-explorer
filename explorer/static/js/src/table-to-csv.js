function tableToCSV(tableEl) {
    let csv_data = [];

    let rows = tableEl.getElementsByTagName('tr');
    for (let i = 0; i < rows.length; i++) {
        let cols = rows[i].querySelectorAll('td,th');

        let csvrow = [];
        for (let j = 0; j < cols.length; j++) {
            csvrow.push(cols[j].innerText);
        }
        csv_data.push(csvrow.join(","));
    }
    csv_data = csv_data.join('\n');

    return csv_data;
}

export function csvFromTable(className) {

    let csv_data = tableToCSV(className);

    let CSVFile = new Blob([csv_data], { type: "text/csv" });

    let temp_link = document.createElement('a');

    temp_link.download = "pivot.csv";
    temp_link.href = window.URL.createObjectURL(CSVFile);

    temp_link.style.display = "none";
    document.body.appendChild(temp_link);

    temp_link.click();
    document.body.removeChild(temp_link);
}
