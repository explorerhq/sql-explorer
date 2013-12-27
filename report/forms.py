from django.forms import ModelForm
from report.models import Report


class ReportForm(ModelForm):

    class Meta:
        model = Report
        fields = ['title', 'sql', 'description', 'created_by']