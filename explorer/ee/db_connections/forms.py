from django import forms
from explorer.ee.db_connections.models import DatabaseConnection
import json
from django.core.exceptions import ValidationError


# This is very annoying, but Django renders the literal string 'null' in the form when displaying JSON
# via a TextInput widget. So this custom widget prevents that.
class JSONTextInput(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if value in (None, "", "null"):
            value = ""
        elif isinstance(value, dict):
            value = json.dumps(value)
        return super().render(name, value, attrs, renderer)

    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value in (None, "", "null"):
            return None
        try:
            return json.loads(value)
        except (TypeError, ValueError) as ex:
            raise ValidationError("Enter a valid JSON") from ex


class DatabaseConnectionForm(forms.ModelForm):
    class Meta:
        model = DatabaseConnection
        fields = "__all__"
        widgets = {
            "alias": forms.TextInput(attrs={"class": "form-control"}),
            "engine": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "user": forms.TextInput(attrs={"class": "form-control"}),
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
            "host": forms.TextInput(attrs={"class": "form-control"}),
            "port": forms.TextInput(attrs={"class": "form-control"}),
            "extras": JSONTextInput(attrs={"class": "form-control"}),
        }
