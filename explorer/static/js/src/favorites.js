import $ from 'jquery';

export function toggleFavorite() {
    let queryId = $(this).data('id');
    let favoriteUrl =  $(this).data('url');
    $.post(favoriteUrl, {}, function (data) {
        let is_favorite = data.is_favorite;
        let selector = '.query_favorite_toggle[data-id=' + queryId + ']';
        if (is_favorite) {
            $(selector).removeClass("bi-heart-fill").addClass("bi-heart");
        } else {
            $(selector).removeClass("bi-heart").addClass("bi-heart-fill");
        }
    }.bind(this), 'json').fail(function () {
        alert("error");
    });
}
