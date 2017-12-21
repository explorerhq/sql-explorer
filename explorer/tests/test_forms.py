from django.test import TestCase
from django.forms.models import model_to_dict
from explorer.tests.factories import SimpleQueryFactory
from explorer.forms import QueryForm


class TestFormValidation(TestCase):

    def test_form_is_valid_with_valid_sql(self):
        q = SimpleQueryFactory(sql="select 1;", created_by_user_id=None)
        form = QueryForm(model_to_dict(q))
        self.assertTrue(form.is_valid())

    def test_form_fails_blacklist(self):
        q = SimpleQueryFactory(sql="delete $$a$$;", created_by_user_id=None)
        q.params = {}
        form = QueryForm(model_to_dict(q))
        self.assertFalse(form.is_valid())
