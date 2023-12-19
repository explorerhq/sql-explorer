import $ from "jquery";
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
        valueNames: ['name'],
        handlers: {'updated': [searchFocus]}
    };
    new List('queries', options);

    setUpEmailCsv();
}

function setUpEmailCsv() {
    let $emailCsv = $('.email-csv');
    let emailModal = new bootstrap.Modal('#emailCsvModal', {});
    let curQueryEmailId = null;

    let isValidEmail = function (email) {
        return /^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/i.test(email);
    };

    let showEmailSuccess = () => {
        const $msgSuccess = $('#email-success-msg');
        const $msgAlert = $('#email-error-msg');
        $msgSuccess.show();
        $msgAlert.hide();
        setTimeout(()=>emailModal.hide(), 2000);
    }

    let showEmailError = (msg) => {
        const $msgSuccess = $('#email-success-msg');
        const $msgAlert = $('#email-error-msg');
        $msgAlert.html(msg);
        $msgSuccess.hide();
        $msgAlert.show();
    }
    let handleEmailCsvSubmit = function (e) {
        let email = document.querySelector('#emailCsvInput').value;
        let url = '/' + curQueryEmailId + '/email_csv?email=' + email;
        if (isValidEmail(email)) {
            $.ajax({
                url: url,
                type: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                data: {
                    email: email
                },
                success: showEmailSuccess,
                error: (xhr, status, error) => {
                    showEmailError(error);
                }
            });
        } else {
            showEmailError('Email is invalid');
        }
    }

    document.querySelectorAll('#btnSubmitCsvEmail').forEach(function(element) {
        element.addEventListener('click', handleEmailCsvSubmit);
    });

    $emailCsv.on('click', function (e) {
        e.preventDefault();
        curQueryEmailId = $(this).data('query-id');
        emailModal.show();
    });

    const emailModalEl = document.getElementById('emailCsvModal')
    emailModalEl.addEventListener('hidden.bs.modal', event => {
        $('#email-success-msg').hide();
        $('#email-error-msg').hide();
    })
}
