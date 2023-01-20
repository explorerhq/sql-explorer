let toggle_favorite = function () {
    let queryId = $(this).data('id');
    let favoriteUrl =  $(this).data('url');
    $.post(favoriteUrl, {}, function (data) {
        let is_favorite = data.is_favorite;
        let selector = '.query_favorite_toggle[data-id=' + queryId + ']';
        if (is_favorite) {
            $(selector).removeClass("glyphicon-heart-empty").addClass("glyphicon-heart");
        } else {
            $(selector).removeClass("glyphicon-heart").addClass("glyphicon-heart-empty");
        }
    }.bind(this), 'json').fail(function () {
        alert("error");
    });
}
$('.query_favorite_toggle').click(toggle_favorite);
