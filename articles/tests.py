from __future__ import unicode_literals

import hashlib

from articles.validators import IS_REQUIRED, MAX_LENGTH, MIN_LENGTH, NULLABLE, TYPE, ANY, STRUCTURE, STRUCTURE_LIST, \
    ContentValidator
from django.core.exceptions import ValidationError
from django.test import TestCase

from articles import ArticleContentType
from articles.utils import process_content, ContentBlockMetaGenerator, content_to_html


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
        content = {"blocks": [{"type": 3, "id": "5e357b19-3e98-4c4a-84ae-2dcbc6457785", "value": "Sed porttitor lectus nibh. Sed porttitor lectus nibh. Curabitur non nulla sit amet nisl tempus convallis quis ac lectus."}, {"type": 2, "id": "d6e4854e-3892-44f6-882e-5d59200b048a", "value": "Cras ultricies ligula sed magna dictum porta."}, {"type": 1, "id": "3e2c44e9-fae3-4f45-8a3c-20d717261035", "value": "Proin eget tortor risus. Curabitur arcu erat, accumsan id imperdiet et, porttitor at sem. Curabitur non nulla sit amet nisl tempus convallis quis ac lectus. Donec rutrum congue leo eget malesuada. Vivamus suscipit tortor eget felis porttitor volutpat. Mauris blandit aliquet elit, eget tincidunt nibh pulvinar a. Cras ultricies ligula sed magna dictum porta. Vivamus suscipit tortor eget felis porttitor volutpat. Quisque velit nisi, pretium ut lacinia in, elementum id enim. Pellentesque in ipsum id orci porta dapibus.\n\nVivamus magna justo, lacinia eget consectetur sed, convallis at tellus. Donec sollicitudin molestie malesuada. Mauris blandit aliquet elit, eget tincidunt nibh pulvinar a. Donec sollicitudin molestie malesuada. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur aliquet quam id dui posuere blandit. Curabitur aliquet quam id dui posuere blandit. Curabitur arcu erat, accumsan id imperdiet et, porttitor at sem. Pellentesque in ipsum id orci porta dapibus. Nulla porttitor accumsan tincidunt."}, {"image": None, "type": 7, "id": "12c6b209-9cb2-4bf5-abb0-dbee00fe038a", "value": "Nulla porttitor accumsan tincidunt. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Donec velit neque, auctor sit amet aliquam vel, ullamcorper sit amet ligula. Cras ultricies ligula sed magna dictum porta. Nulla quis lorem ut libero malesuada feugiat."}], "__meta": {"is_valid": True}, "cover": {"image": "http://localhost:8000/data/images/26/4b/264b9286-fbd6-42dc-87d1-a9d5377aef22.jpg", "preview": "http://localhost:8000/data/cache/20/7c/207c0971bcd0b9e15eba03b4e5f094bb.jpg", "id": 254}, "title": "Hello"}
        process_content(content)
        from pprint import pprint
        pprint(content_to_html(content))

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

    def test_convert_dialogue(self):
        c = self.base_content
        c['blocks'].append({
            'type': ArticleContentType.DIALOG,
            'participants': [
                {
                    'id': 1,
                    'name': 'Q',
                    'avatar': {'id': 1, 'image': 'http://ya.ru/q.jpg'}
                },
                {
                    'id': 2,
                    'name': 'A',
                    'avatar': {'id': 2, 'image': 'http://ya.ru/a.jpg'}
                },

            ],
            'remarks': [
                {'participant_id': 1, 'value': 'question'},
                {'participant_id': 2, 'value': 'answer'},
            ],
            '__meta': {'is_valid': True}
        })
        from pprint import pprint
        pprint(content_to_html(c))

