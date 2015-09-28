var $emailCsv = $('.email-csv');

var isValidEmail = function (email) {
  return /^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/i.test(email);
};

$emailCsv.each(function () {
  var $this = $(this);
  $this.popover({
    html: true,
    trigger: 'manual',
    placement: 'left',
    content:
      '<form class="email-csv-form" action="' + $this.prop('href') + '">' +
        '<div class="input-group">' +
          '<input type="email" autofocus="true" name="email" class="form-control" placeholder="Email" />' +
          '<span class="input-group-btn">' +
            '<button type="submit" class="btn btn-primary">Send</button>' +
          '</span>' +
        '</div>' +
      '</form>'
  });
});

$emailCsv.on('click', function (e) {
  e.preventDefault();
  var $this = $(this);
  $emailCsv.not($this).popover('hide');
  $this.popover('toggle');
});

$('body').on('submit', '.email-csv-form', function (e) {
  e.preventDefault();
  var url = this.action;
  var $this = $(this);
  var email = $this.find('[name=email]').val()
  if (isValidEmail(email)) {
    $.ajax({
      url: url,
      type: 'POST',
      data: {
        email: $this.find('[name=email]').val()
      },
      success: function () {
        $this.closest('td').find('.email-csv').popover('hide');
      }
    });
  } else {
    $this.tooltip({
      title: 'Email is invalid',
      trigger: 'manual'
    });
    $this.tooltip('show');
    setTimeout(function () {
      $this.tooltip('hide');
    }, 3000)
  }
});