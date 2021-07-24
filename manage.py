#!/usr/bin/env python
import os
import sys

from django.core import management

sys.path.append(os.path.join(os.path.dirname(__file__), 'explorer'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'

if __name__ == "__main__":
    management.execute_from_command_line()
