from django.forms import ModelForm, Field, ValidationError
from report.models import Report

_ = lambda x: x


class SqlField(Field):

    def validate(self, value):
        report = Report(sql=value)
        headers, data, error = report.headers_and_data()
        if error:
            raise ValidationError(
                _(error),
                params={'value': value},
                code="InvalidSql"
            )


class ReportForm(ModelForm):

    sql = SqlField()

    class Meta:
        model = Report
        fields = ['title', 'sql', 'description', 'created_by']