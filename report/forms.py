from django.forms import ModelForm
from report.models import Report
from django import forms

class ReportForm(ModelForm):

    class Meta:
        model = Report
        fields = ['title', 'sql', 'description', 'created_by']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'sql': forms.Textarea(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'created_by': forms.TextInput(attrs={'class': 'form-control'}),
        }