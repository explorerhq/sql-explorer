from django.test import TestCase
from django.forms.models import model_to_dict
from explorer.tests.factories import SimpleQueryFactory
from explorer.forms import QueryForm


class TestFormValidation(TestCase):

    def test_form_is_valid_with_valid_sql(self):
        q = SimpleQueryFactory(sql="select 1;")
        form = QueryForm(model_to_dict(q))
        self.assertTrue(form.is_valid())

    def test_form_is_not_valid_with_invalid_sql(self):
        q = SimpleQueryFactory(sql="select a;")
        form = QueryForm(model_to_dict(q))
        self.assertFalse(form.is_valid())

    def test_form_is_always_valid_with_params(self):
        q = SimpleQueryFactory(sql="select $$a$$;")
        form = QueryForm(model_to_dict(q))
        self.assertTrue(form.is_valid())