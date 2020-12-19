# -*- coding: utf-8 -*-
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict
from django.test import TestCase

from explorer.forms import QueryForm
from explorer.tests.factories import SimpleQueryFactory


class TestFormValidation(TestCase):

    def test_form_is_valid_with_valid_sql(self):
        q = SimpleQueryFactory(sql="select 1;", created_by_user_id=None)
        form = QueryForm(model_to_dict(q))
        self.assertTrue(form.is_valid())

    def test_form_fails_null(self):
        with self.assertRaises(IntegrityError):
            SimpleQueryFactory(sql=None, created_by_user_id=None)

    def test_form_fails_blank(self):
        q = SimpleQueryFactory(sql='', created_by_user_id=None)
        q.params = {}
        form = QueryForm(model_to_dict(q))
        self.assertFalse(form.is_valid())

    def test_form_fails_blacklist(self):
        q = SimpleQueryFactory(sql="delete $$a$$;", created_by_user_id=None)
        q.params = {}
        form = QueryForm(model_to_dict(q))
        self.assertFalse(form.is_valid())
