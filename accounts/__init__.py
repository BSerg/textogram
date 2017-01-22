#! coding: utf-8

from __future__ import unicode_literals

PHONE_PATTERN = '^\d{7,18}$'
PASSWORD_PATTERN = '^[^\s]{5,}$'
FIRST_NAME_PATTERN = '^[A-Za-zА-Яа-я][\w]+$'
LAST_NAME_PATTERN = '^(\w+\s?)*$'