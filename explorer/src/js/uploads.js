import { getCsrfToken } from "./csrf";

export function setupUploads() {
    var dropArea = document.getElementById('drop-area');
    var fileElem = document.getElementById('fileElem');

    if (dropArea) {
        dropArea.onclick = function() {
            fileElem.click();
        };

        dropArea.addEventListener('dragover', function(e) {
            e.preventDefault(); // Prevent default behavior (Prevent file from being opened)
            dropArea.classList.add('bg-info'); // Optional: add a style when dragging over
        });

        dropArea.addEventListener('dragleave', function(e) {
            dropArea.classList.remove('bg-info'); // Optional: remove style when not dragging over
        });

        dropArea.addEventListener('drop', function(e) {
            e.preventDefault();
            dropArea.classList.remove('bg-info'); // Optional: remove style after dropping

            let files = e.dataTransfer.files;
            if (files.length) {
                handleFiles(files[0]); // Assuming only one file is dropped
            }
        });

        fileElem.onchange = function() {
            if (this.files.length) {
                handleFiles(this.files[0]);
            }
        };
    }



    function handleFiles(file) {
        uploadFile(file);
    }

    function uploadFile(file) {
        let formData = new FormData();
        formData.append('file', file);

        fetch("../upload/", {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        }).then(response => response.json())
        .then(() => {
            window.location.reload();
        })
        .catch(error => console.error('Error:', error));
    }

    document.getElementById("test-connection-btn").addEventListener("click", function() {
        var form = document.getElementById("db-connection-form");
        var formData = new FormData(form);

        fetch("../../validate/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Connection successful!");
            } else {
                alert("Connection failed: " + data.error);
            }
        })
        .catch(error => console.error("Error:", error));
    });

}
