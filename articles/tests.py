from __future__ import unicode_literals

import hashlib
from pprint import pprint as pp

from django.core.exceptions import ValidationError
from django.test import TestCase

from articles import ArticleContentType
from articles.utils import IS_REQUIRED, ContentValidator, NULLABLE, TYPE, ANY, MAX_LENGTH, STRUCTURE, STRUCTURE_LIST, \
    MIN_LENGTH, ContentBlockMetaGenerator, process_content


class ArticleContentValidationTestCase(TestCase):
    def test_require(self):
        c1 = {'title': 'Hello'}
        ContentValidator.validate_structure(c1, 'title', {IS_REQUIRED: True})

        c2 = {'subtitle': 'World'}
        ContentValidator.validate_structure(c2, 'title', {IS_REQUIRED: False})

        c3 = {'slug': 'hello'}
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c3, 'title', {IS_REQUIRED: True})

    def test_nullable(self):
        c1 = {'field': None}
        ContentValidator.validate_structure(c1, 'field', {NULLABLE: True})

        c2 = {'field': None}
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c2, 'field', {})
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c2, 'field', {NULLABLE: False})

    def test_type(self):
        c1 = {'field': 'Hello'}
        ContentValidator.validate_structure(c1, 'field', {TYPE: (str, unicode)})
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c1, 'field', {TYPE: int})

    def test_any(self):
        c1 = {'field': 1}
        ContentValidator.validate_structure(c1, 'field', {ANY: [1, 2, 3]})
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c1, 'field', {ANY: ['a', 'b', 'c']})

    def test_max_length(self):
        c1 = {'field': 'Hello, World!!!'}
        ContentValidator.validate_structure(c1, 'field', {MAX_LENGTH: 100})
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c1, 'field', {MAX_LENGTH: 5})

        c2 = {'field': 125}
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c2, 'field', {MAX_LENGTH: 100})

    def test_min_length(self):
        c1 = {'field': 'Hello, World!!!'}
        ContentValidator.validate_structure(c1, 'field', {MIN_LENGTH: 5})
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c1, 'field', {MIN_LENGTH: 100})

    def test_structure(self):
        params = {
            STRUCTURE: {
                'width': {IS_REQUIRED: True, TYPE: int},
                'height': {IS_REQUIRED: True, TYPE: int},
                'name': {IS_REQUIRED: True, TYPE: (str, unicode)},
            }
        }
        c1 = {'field': {'width': 100, 'height': 200, 'name': 'figure'}}
        ContentValidator.validate_structure(c1, 'field', params)

        c2 = {'field': {'width': 100, 'height': 200}}
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c2, 'field', params)

    def test_structure_list(self):
        params = {
            STRUCTURE_LIST: {
                'width': {IS_REQUIRED: True, TYPE: int},
                'height': {IS_REQUIRED: True, TYPE: int},
                'name': {IS_REQUIRED: True, TYPE: (str, unicode)},
            }
        }
        c1 = {
            'field': [
                {'width': 100, 'height': 200, 'name': 'figure'},
                {'width': 200, 'height': 300, 'name': 'figure1'}
            ]
        }
        ContentValidator.validate_structure(c1, 'field', params)

        c2 = {
            'field': [
                {'width': 100, 'height': 200, 'name': 'figure'},
                {'height': 300, 'name': 'figure1'}
            ]
        }

        c3 = {
            'field': {'width': 100, 'height': 200, 'name': 'figure'}
        }

        self.assertRaises(ValidationError, ContentValidator.validate_structure, c2, 'field', params)
        self.assertRaises(ValidationError, ContentValidator.validate_structure, c3, 'field', params)


class ContentMetaGeneratorTestCase(TestCase):
    def test_meta(self):
        c1 = {
            'id': 'd66798c1-581b-4160-9244-436d7f5824cd',
            'type': ArticleContentType.TEXT,
            'value': 'Hello'
        }
        meta = ContentBlockMetaGenerator.get_instance(c1).get_meta()
        self.assertDictEqual(meta, {'is_valid': True, 'hash': hashlib.md5(str(c1)).hexdigest()})

    def test_process_content(self):
        content = {
            'title': 'Hello World!',
            'cover': None,
            'blocks': [
                {"type": 3, "id": "7f7d0105-d8ed-4b09-96f0-135d7e9791f8", "value": "Lorem Ipsum Tralala"},
            ]
        }
        process_content(content)

        self.assertDictEqual(content['__meta'], {'is_valid': True})
