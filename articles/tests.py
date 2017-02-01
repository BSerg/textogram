from __future__ import unicode_literals

import hashlib

from django.core.exceptions import ValidationError
from django.test import TestCase

from articles import ArticleContentType
from articles.utils import process_content, ContentBlockMetaGenerator, content_to_html
from articles.validation import IS_REQUIRED, MAX_LENGTH, MIN_LENGTH, NULLABLE, TYPE, ANY, STRUCTURE, STRUCTURE_LIST, \
    ContentValidator


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


class EmbedTestCase(TestCase):
    # TODO add embed tests
    pass


class ContentConverterTestCase(TestCase):
    def setUp(self):
        self.base_content = {'title': 'Hello TEST', 'cover': None, 'blocks': [], '__meta': {'is_valid': True}}

    def test_convert_text(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.TEXT,
            'value': 'Hello **World**!',
            '__meta': {'is_valid': True}
        })
        self.assertEqual('<p>Hello <strong>World</strong>!</p>', content_to_html(c))

    def test_convert_header(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.HEADER,
            'value': 'Header',
            '__meta': {'is_valid': True}
        })
        self.assertEqual('<h2>Header</h2>', content_to_html(c))

    def test_convert_lead(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.LEAD,
            'value': 'Donec rutrum congue leo eget malesuada.',
            '__meta': {'is_valid': True}
        })
        self.assertEqual('<div class="lead"><p>Donec rutrum congue leo eget malesuada.</p></div>', content_to_html(c))

    def test_convert_phrase(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.PHRASE,
            'value': 'Sed porttitor lectus nibh.\n\nVivamus magna justo, lacinia eget consectetur sed, convallis at tellus.',
            '__meta': {'is_valid': True}
        })
        self.assertEqual('<div class="phrase"><p>Sed porttitor lectus nibh.</p>\n<p>Vivamus magna justo, lacinia eget consectetur sed, convallis at tellus.</p></div>', content_to_html(c))

    def test_convert_list(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.LIST,
            'value': '* Sed porttitor lectus nibh.\n* Vivamus magna justo, lacinia eget consectetur sed, convallis at tellus.',
            '__meta': {'is_valid': True}
        })
        self.assertEqual('<ul>\n<li>Sed porttitor lectus nibh.</li>\n<li>Vivamus magna justo, lacinia eget consectetur sed, convallis at tellus.</li>\n</ul>', content_to_html(c))

    def test_convert_quote(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.QUOTE,
            'value': 'Sed porttitor lectus nibh.\n\nVivamus magna justo, lacinia eget consectetur sed, convallis at tellus.',
            '__meta': {'is_valid': True}
        })
        self.assertEqual(
            '<blockquote>\n<p>Sed porttitor lectus nibh.</p>\n<p>Vivamus magna justo, lacinia eget consectetur sed, convallis at tellus.</p>\n</blockquote>',
            content_to_html(c)
        )
        c['blocks'][0].update(image={
            'id': 1,
            'image': 'http://ya.ru/hello.jpg'
        })
        self.assertEqual(
            '<blockquote class="personal">\n<img src="http://ya.ru/hello.jpg"/>\n<p>Sed porttitor lectus nibh.</p>\n<p>Vivamus magna justo, lacinia eget consectetur sed, convallis at tellus.</p>\n</blockquote>',
            content_to_html(c)
        )

    def test_convert_columns(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.COLUMNS,
            'image': {
                'id': 1,
                'image': 'http://ya.ru/hello.jpg'
            },
            'value': 'Sed porttitor lectus nibh.\n\nVivamus magna justo, lacinia eget consectetur sed, convallis at tellus.',
            '__meta': {'is_valid': True}
        })
        self.assertEqual(
            '<div class="columns">\n<div class="column">\n<img src="http://ya.ru/hello.jpg"/>\n</div>\n<div class="column">\n<p>Sed porttitor lectus nibh.</p>\n<p>Vivamus magna justo, lacinia eget consectetur sed, convallis at tellus.</p>\n</div>\n</div>',
            content_to_html(c)
        )

