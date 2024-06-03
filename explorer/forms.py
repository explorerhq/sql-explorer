from django.forms import BooleanField, CharField, ModelForm, ValidationError
from django.forms.widgets import CheckboxInput, Select

from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION
from explorer.models import MSG_FAILED_BLACKLIST, Query


class SqlField(CharField):

    def validate(self, value):
        """
        Ensure that the SQL passes the blacklist.

        :param value: The SQL for this Query model.
        """
        super().validate(value)
        query = Query(sql=value)

        passes_blacklist, failing_words = query.passes_blacklist()

        error = MSG_FAILED_BLACKLIST % ", ".join(
            failing_words) if not passes_blacklist else None

        if error:
            raise ValidationError(
                error,
                code="InvalidSql"
            )


class QueryForm(ModelForm):

    sql = SqlField()
    snapshot = BooleanField(widget=CheckboxInput, required=False)
    connection = CharField(widget=Select, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["connection"].widget.choices = self.connections
        if not self.instance.connection:
            self.initial["connection"] = EXPLORER_DEFAULT_CONNECTION
        self.fields["connection"].widget.attrs["class"] = "form-select"

    def clean(self):
        # Don't overwrite created_by_user
        if self.instance and self.instance.created_by_user:
            self.cleaned_data["created_by_user"] = \
                self.instance.created_by_user
        return super().clean()

    @property
    def created_at_time(self):
        return self.instance.created_at.strftime("%Y-%m-%d")

    @property
    def connections(self):
        from explorer.connections import connections
        return [(c, c) for c in connections()]

    class Meta:
        model = Query
        fields = ["title", "sql", "description", "snapshot", "connection"]
