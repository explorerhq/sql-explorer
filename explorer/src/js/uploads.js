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

        let appendElem = document.getElementById('append');
        let appendValue = appendElem.value;
        if (appendValue) {
            formData.append('append', appendValue);
        }

        let xhr = new XMLHttpRequest();
        xhr.open('POST', `${window.baseUrlPath}connections/upload/`, true);
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
                let highlightValue = appendValue ? appendElem.options[appendElem.selectedIndex].text : file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
                 window.location.href = `../?highlight=${encodeURIComponent(highlightValue)}`;
            } else {
                console.error('Error:', xhr.response);
                uploadStatus.innerHTML = xhr.response;
            }
        };

        xhr.onerror = function() {
            console.error('Error:', xhr.statusText);
            uploadStatus.innerHTML = xhr.response;
        };

        xhr.send(formData);
    }

    let testConnBtn = document.getElementById("test-connection-btn");
    if (testConnBtn) {
        testConnBtn.addEventListener("click", function() {
            let form = document.getElementById("db-connection-form");
            let formData = new FormData(form);

            fetch(`${window.baseUrlPath}connections/validate/`, {
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
}
