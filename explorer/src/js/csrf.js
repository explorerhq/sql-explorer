import cookie from "cookiejs";

const csrfCookieName = document.getElementById('csrfCookieName').value;
const csrfTokenInDOM = document.getElementById('csrfTokenInDOM').value === "True";

export function getCsrfToken() {
    if (csrfTokenInDOM) {
        let csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return csrfInput ? csrfInput.value : null;
    }
    return cookie.get(csrfCookieName);
}
