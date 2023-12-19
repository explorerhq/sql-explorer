import $ from 'jquery';
import {getCsrfToken} from "./csrf";

export async function toggleFavorite() {
    let queryId = $(this).data('id');
    let favoriteUrl = $(this).data('url');

    try {
        let response = await fetch(favoriteUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({})
        });

        let data = await response.json();
        let is_favorite = data.is_favorite;
        let selector = '.query_favorite_toggle[data-id=' + queryId + ']';

        if (is_favorite) {
            $(selector).removeClass("bi-heart").addClass("bi-heart-fill");
        } else {
            $(selector).removeClass("bi-heart-fill").addClass("bi-heart");
        }
    } catch (error) {
        console.error('Error:', error);
        alert("error");
    }
}
