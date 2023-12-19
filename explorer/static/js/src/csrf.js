import cookie from "cookiejs";

export function getCsrfToken() {
    if (csrfCookieHttpOnly) {
        let csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return csrfInput ? csrfInput.value : null;
    }
    return cookie.get(csrfCookieName);
}
