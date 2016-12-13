from django.db import DatabaseError
from django.forms import ModelForm, Field, ValidationError, BooleanField
from django.forms.widgets import CheckboxInput

from explorer.models import Query, MSG_FAILED_BLACKLIST

_ = lambda x: x


class SqlField(Field):

    def validate(self, value):
        """
        Ensure that the SQL passes the blacklist and executes. Execution check is skipped if params are present.

        :param value: The SQL for this Query model.
        """

        query = Query(sql=value)

        passes_blacklist, failing_words = query.passes_blacklist()

        error = MSG_FAILED_BLACKLIST % ', '.join(failing_words) if not passes_blacklist else None

        if not error and not query.available_params():
            try:
                query.execute_query_only()
            except DatabaseError as e:
                error = str(e)

        if error:
            raise ValidationError(
                _(error),
                code="InvalidSql"
            )


class QueryForm(ModelForm):

    sql = SqlField()
    snapshot = BooleanField(widget=CheckboxInput, required=False)

    def clean(self):
        if self.instance and self.data.get('created_by_user', None):
            self.cleaned_data['created_by_user'] = self.instance.created_by_user
        return super(QueryForm, self).clean()

    @property
    def created_by_user_email(self):
        return self.instance.created_by_user.email if self.instance.created_by_user else '--'

    class Meta:
        model = Query
        fields = ['title', 'sql', 'description', 'snapshot']
