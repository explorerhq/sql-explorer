from django.forms import ModelForm
from report.models import Report
from django import forms

class ReportForm(ModelForm):

    class Meta:
        model = Report
        fields = ['title', 'sql', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'sql': forms.Textarea(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }