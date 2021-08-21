# -*- coding: utf-8 -*-
from unittest.mock import patch, Mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from explorer.app_settings import EXPLORER_CONNECTIONS
from explorer.apps import _validate_connections


class TestApps(TestCase):

    @patch('explorer.apps._get_app_settings')
    def test_validates_default_connections(self, mock_get_settings):
        mock_settings = Mock()
        mock_settings.EXPLORER_DEFAULT_CONNECTION = 'garbage'
        mock_settings.EXPLORER_CONNECTIONS = EXPLORER_CONNECTIONS
        mock_get_settings.return_value = mock_settings

        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "EXPLORER_DEFAULT_CONNECTION is garbage, but that "
            "alias is not present in the values of EXPLORER_CONNECTIONS"
        ):
            _validate_connections()

    @patch('explorer.apps._get_app_settings')
    def test_rewrites_default_connection_if_referencing_django_db_name(self, mock_get_settings):
        mock_settings = Mock()
        mock_settings.EXPLORER_DEFAULT_CONNECTION = 'default'
        mock_settings.EXPLORER_CONNECTIONS = EXPLORER_CONNECTIONS
        mock_get_settings.return_value = mock_settings
        _validate_connections()
        self.assertEqual("SQLite", mock_settings.EXPLORER_DEFAULT_CONNECTION)

    @patch('explorer.apps._get_app_settings')
    def test_validates_all_connections(self, mock_get_settings):
        mock_settings = Mock()
        mock_settings.EXPLORER_DEFAULT_CONNECTION = 'garbage1'
        mock_settings.EXPLORER_CONNECTIONS = {'garbage1': 'in', 'garbage2': 'out'}
        mock_get_settings.return_value = mock_settings
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "EXPLORER_CONNECTIONS contains (garbage1, in), "
            "but in is not a valid Django DB connection."
        ):
            _validate_connections()
