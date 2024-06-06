import { getCsrfToken } from "./csrf";

export function setupUploads() {
    var dropArea = document.getElementById('drop-area');
    var fileElem = document.getElementById('fileElem');
    var progressBar = document.getElementById('progress-bar');
    var uploadStatus = document.getElementById('upload-status');

    if (dropArea) {
        dropArea.onclick = function() {
            fileElem.click();
        };

        dropArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropArea.classList.add('bg-info');
        });

        dropArea.addEventListener('dragleave', function(e) {
            dropArea.classList.remove('bg-info');
        });

        dropArea.addEventListener('drop', function(e) {
            e.preventDefault();
            dropArea.classList.remove('bg-info');

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

        let xhr = new XMLHttpRequest();
        xhr.open('POST', '../upload/', true);
        xhr.setRequestHeader('X-CSRFToken', getCsrfToken());

        xhr.upload.onprogress = function(event) {
            if (event.lengthComputable) {
                let percentComplete = (event.loaded / event.total) * 100;
                progressBar.style.width = percentComplete + '%';
                progressBar.setAttribute('aria-valuenow', percentComplete);
                progressBar.innerHTML = percentComplete.toFixed(0) + '%';
                if (percentComplete > 99) {
                    uploadStatus.innerHTML = "Upload complete. Parsing and saving to S3...";
                }
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                window.location.href = "../";
            } else {
                console.error('Error:', xhr.statusText);
            }
        };

        xhr.onerror = function() {
            console.error('Error:', xhr.statusText);
        };

        xhr.send(formData);
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
