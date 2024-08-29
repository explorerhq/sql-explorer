from django import forms
from explorer.assistant.models import TableDescription
from explorer.ee.db_connections.utils import default_db_connection


class TableDescriptionForm(forms.ModelForm):
    class Meta:
        model = TableDescription
        fields = "__all__"
        widgets = {
            "database_connection": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Check if this is a new instance
            # Set the default value for database_connection
            self.fields["database_connection"].initial = default_db_connection()

        if self.instance and self.instance.table_name:
            choices = [(self.instance.table_name, self.instance.table_name)]
        else:
            choices = []

        f = forms.ChoiceField(
            choices=choices,
            widget=forms.Select(attrs={"class": "form-select", "data-placeholder": "Select table"})
        )

        # We don't actually care about validating the 'choices' that the ChoiceField does by default.
        # Really we are just using that field type in order to get a valid pre-populated Select widget on the client
        # But also it can't be blank!
        def valid_value_new(v):
            return bool(v)

        f.valid_value = valid_value_new

        self.fields["table_name"] = f

        if self.instance and self.instance.table_name:
            self.fields["table_name"].initial = self.instance.table_name
