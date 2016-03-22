#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'explorer'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'
from django.core import management
if __name__ == "__main__":
    management.execute_from_command_line()
