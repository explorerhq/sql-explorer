import cookie from "cookiejs";

const csrfCookieName = document.getElementById('csrfCookieName').value;
const csrfCookieHttpOnly = document.getElementById('csrfCookieHttpOnly').value === "True";

export function getCsrfToken() {
    if (csrfCookieHttpOnly) {
        let csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return csrfInput ? csrfInput.value : null;
    }
    return cookie.get(csrfCookieName);
}
