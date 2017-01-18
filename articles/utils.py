from __future__ import unicode_literals

import hashlib

from django.core.exceptions import ValidationError

from articles import ArticleContentType
from articles import get_embed, ArticleContentType


class ContentBlockValidationError(Exception):
    def __init__(self, message, _type):
        super(ContentBlockValidationError, self).__init__(message)
        self.type = _type


IS_REQUIRED = 'required'
MAX_LENGTH = 'max_length'
MIN_LENGTH = 'min_length'
REGEX_MATCH = 'regex_match'
NULLABLE = 'nullable'
ANY = 'any'

ROOT_VALIDATION_CFG = {
    'title': {IS_REQUIRED: True, MAX_LENGTH: 255},
    'cover': {IS_REQUIRED: True, NULLABLE: True},
    'blocks': {IS_REQUIRED: True}
}

BLOCK_BASE_VALIDATION_CFG = {
    'id': {IS_REQUIRED: True},
    'type': {IS_REQUIRED: True, ANY: ArticleContentType.__dict__.values()},
}

BLOCKS_VALIDATION_CFG = {
    ArticleContentType.TEXT: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 10000}
    },
    ArticleContentType.HEADER: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 255}
    },
    ArticleContentType.LEAD: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 500}
    },
    ArticleContentType.PHOTO: {},
    ArticleContentType.QUOTE: {},
    ArticleContentType.PHRASE: {},
    ArticleContentType.LIST: {},
    ArticleContentType.COLUMNS: {},
    ArticleContentType.VIDEO: {},
    ArticleContentType.AUDIO: {},
    ArticleContentType.POST: {},
    ArticleContentType.DIALOG: {},
}


class ContentValidator(object):
    @staticmethod
    def validate_structure(structure, field, params):
        if field not in structure and params.get(IS_REQUIRED):
            raise ValidationError('"%(field)s" is required', code=IS_REQUIRED, params={'field': field})
        if structure[field] is None and not params.get(NULLABLE):
            raise ValidationError('"%(field)s" can\'t be NULL', code=NULLABLE, params={'field': field})
        if (params.get(MAX_LENGTH) or params.get(MIN_LENGTH)) and not isinstance(structure[field], (str, unicode)):
            raise ValidationError('"%(field)s" must be STRING or UNICODE', code='type', params={'field': field})
        if params.get(MAX_LENGTH) and len(structure[field]) > params.get(MAX_LENGTH):
            raise ValidationError('"%(field)s" value is too long', code=MAX_LENGTH, params={'field': field})
        if params.get(MIN_LENGTH) and len(structure[field]) < params.get(MIN_LENGTH):
            raise ValidationError('"%(field)s" value is too short', code=MIN_LENGTH, params={'field': field})
        if params.get(ANY) and not any([structure[field] == v for v in params[ANY]]):
            raise ValidationError('"%(field)s" value is not one of allowed values', code=ANY, params={'field': field})

    def __call__(self, content):
        # root validation
        for field, params in ROOT_VALIDATION_CFG.items():
            self.validate_structure(content, field, params)


class ContentBlockMetaGenerator(object):
    @classmethod
    def get_instance(cls, content):
        if content.get('type') in [ArticleContentType.VIDEO, ArticleContentType.AUDIO, ArticleContentType.POST]:
            return EmbedBlockMetaGenerator(content, _type=content['type'])
        return cls(content)

    def __init__(self, content):
        self.content = content

    def is_valid(self):
        is_valid = True
        base_validation_cfg = BLOCK_BASE_VALIDATION_CFG.items()
        validation_cfg = BLOCKS_VALIDATION_CFG.get(self.content.get('type'), {}).items()
        for field, params in base_validation_cfg + validation_cfg:
            try:
                ContentValidator.validate_structure(self.content, field, params)
            except ValidationError:
                is_valid = False
        return is_valid

    def get_content_hash(self):
        return hashlib.md5(str(self.content)).hexdigest()

    def get_meta(self):
        return {
            'is_valid': self.is_valid(),
            'hash': self.get_content_hash()
        }


class EmbedBlockMetaGenerator(ContentBlockMetaGenerator):
    def __init__(self, content, _type=None):
        super(EmbedBlockMetaGenerator, self).__init__(content)
        self.type = _type

    def get_meta(self):
        meta = super(EmbedBlockMetaGenerator, self).get_meta()
        if self.is_valid():
            if self.content['type'] == ArticleContentType.VIDEO:
                embed = get_embed(self.content['value'], type='video')
            else:
                embed = get_embed(self.content['value'])
            meta['embed'] = embed
        return meta


def process_content(content):
    for block in content.get('blocks', []):
        meta = block.pop('__meta', {})
        meta_generator = ContentBlockMetaGenerator.get_instance(block)
        if meta_generator:
            if meta_generator.get_content_hash() != meta.get('hash'):
                block['__meta'] = meta_generator.get_meta()
    return content
