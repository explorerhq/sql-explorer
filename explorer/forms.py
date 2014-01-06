from django.forms import ModelForm, Field, ValidationError
from explorer.models import Query

_ = lambda x: x


class SqlField(Field):

    def validate(self, value):
        query = Query(sql=value)
        if not query.available_params():
            error = query.error_messages()
            if error:
                raise ValidationError(
                    _(error),
                    params={'value': value},
                    code="InvalidSql"
                )


class QueryForm(ModelForm):

    sql = SqlField()

    class Meta:
        model = Query
        fields = ['title', 'sql', 'description', 'created_by']