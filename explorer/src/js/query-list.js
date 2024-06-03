import List from "list.js";
import {getCsrfToken} from "./csrf";
import {toggleFavorite} from "./favorites";
import * as bootstrap from 'bootstrap'; // eslint-disable-line no-unused-vars

function searchFocus() {
    const searchElement = document.querySelector('.search');
    if (searchElement) {
        searchElement.focus();
    }
}
export function setupQueryList() {

    document.querySelectorAll('.query_favorite_toggle').forEach(function (element) {
        element.addEventListener('click', toggleFavorite);
    });

    let options = {
        valueNames: ['sort-name', 'sort-created', 'sort-created', 'sort-last-run', 'sort-run-count', 'sort-connection'],
        handlers: {'updated': [searchFocus]}
    };
    new List('queries', options);

    setUpEmailCsv();
}

function setUpEmailCsv() {
    let emailModal = new bootstrap.Modal('#emailCsvModal', {});
    let curQueryEmailId = null;

    let isValidEmail = function (email) {
        return /^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/i.test(email);
    };

    let showEmailSuccess = () => {
        const msgSuccess = document.getElementById('email-success-msg');
        const msgAlert = document.getElementById('email-error-msg');
        msgSuccess.style.display = 'block';
        msgAlert.style.display = 'none';
        setTimeout(() => emailModal.hide(), 2000);
    }

    let showEmailError = (msg) => {
        const msgSuccess = document.getElementById('email-success-msg');
        const msgAlert = document.getElementById('email-error-msg');
        msgAlert.innerHTML = msg; // Equivalent to .html(msg) in jQuery
        msgSuccess.style.display = 'none';
        msgAlert.style.display = 'block';
    }
    let handleEmailCsvSubmit = function (e) {
        let email = document.querySelector('#emailCsvInput').value;
        let url = '/' + curQueryEmailId + '/email_csv?email=' + email;
        if (isValidEmail(email)) {
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    email: email
                }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                showEmailSuccess(data);
            })
            .catch((error) => {
                showEmailError(error.message);
            });
        } else {
            showEmailError('Email is invalid');
        }
    }

    document.querySelectorAll('#btnSubmitCsvEmail').forEach(function(element) {
        element.addEventListener('click', handleEmailCsvSubmit);
    });

    document.querySelectorAll('.email-csv').forEach(element => {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            curQueryEmailId = this.getAttribute('data-query-id');
            emailModal.show();
        });
    });

    const emailModalEl = document.getElementById('emailCsvModal');
    emailModalEl.addEventListener('hidden.bs.modal', event => {
        document.getElementById('email-success-msg').style.display = 'none';
        document.getElementById('email-error-msg').style.display = 'none';
    });
}
