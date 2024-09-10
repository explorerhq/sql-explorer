from django.forms import BooleanField, CharField, ModelForm, ValidationError
from django.forms.widgets import CheckboxInput, Select
from django.db.models import Value, IntegerField, When, Case

from explorer.models import MSG_FAILED_BLACKLIST, Query
from explorer.ee.db_connections.models import DatabaseConnection
from explorer.ee.db_connections.utils import default_db_connection


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
    few_shot = BooleanField(widget=CheckboxInput, required=False)
    database_connection = CharField(widget=Select, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["database_connection"].widget.choices = self.connections
        if not self.instance.database_connection:
            default_db = default_db_connection()
            self.initial["database_connection"] = default_db_connection().alias if default_db else None
        self.fields["database_connection"].widget.attrs["class"] = "form-select"

    def clean(self):
        # Don't overwrite created_by_user
        if self.instance and self.instance.created_by_user:
            self.cleaned_data["created_by_user"] = \
                self.instance.created_by_user
        return super().clean()

    def clean_database_connection(self):
        connection_id = self.cleaned_data.get("database_connection")
        if connection_id:
            try:
                return DatabaseConnection.objects.get(id=connection_id)
            except DatabaseConnection.DoesNotExist as e:
                raise ValidationError("Invalid database connection selected.") from e
        return None

    @property
    def created_at_time(self):
        return self.instance.created_at.strftime("%Y-%m-%d")

    @property
    def connections(self):
        default_db = default_db_connection()
        if default_db is None:
            return []

        # Ensure the default connection appears first in the dropdown in the form
        result = DatabaseConnection.objects.annotate(
            custom_order=Case(
                When(id=default_db_connection().id, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("custom_order", "id")
        return [(c.id, c.alias) for c in result.all()]

    class Meta:
        model = Query
        fields = ["title", "sql", "description", "snapshot", "database_connection", "few_shot"]
