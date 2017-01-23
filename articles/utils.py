from __future__ import unicode_literals

import hashlib

from django.core.exceptions import ValidationError

from articles import get_embed, ArticleContentType


class ContentBlockValidationError(Exception):
    def __init__(self, message, _type):
        super(ContentBlockValidationError, self).__init__(message)
        self.type = _type


IS_REQUIRED = 'REQUIRED'
MAX_LENGTH = 'MAX_LENGTH'
MIN_LENGTH = 'MIN_LENGTH'
REGEX_MATCH = 'REGEX_MATCH'
NULLABLE = 'NULLABLE'
TYPE = 'TYPE'
ANY = 'ANY'
STRUCTURE = 'STRUCTURE'
STRUCTURE_LIST = 'STRUCTURE_LIST'

PHOTO_VALIDATION_CFG = {
    'id': {IS_REQUIRED: True, NULLABLE: True, TYPE: int},
    'image': {IS_REQUIRED: True, TYPE: (str, unicode)},
    'caption': {IS_REQUIRED: False, TYPE: (str, unicode), MAX_LENGTH: 200},
}

ROOT_VALIDATION_CFG = {
    'title': {IS_REQUIRED: True, MAX_LENGTH: 150},
    'cover': {
        IS_REQUIRED: True,
        NULLABLE: True,
        STRUCTURE: PHOTO_VALIDATION_CFG},
    'blocks': {IS_REQUIRED: True}
}

BLOCK_BASE_VALIDATION_CFG = {
    'id': {IS_REQUIRED: True, TYPE: (str, unicode)},
    'type': {IS_REQUIRED: True, ANY: ArticleContentType.__dict__.values()},
}

BLOCKS_VALIDATION_CFG = {
    ArticleContentType.TEXT: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 3000}
    },
    ArticleContentType.HEADER: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 100}
    },
    ArticleContentType.LEAD: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 400}
    },
    ArticleContentType.PHOTO: {
        'photos': {IS_REQUIRED: True, STRUCTURE_LIST: PHOTO_VALIDATION_CFG}
    },
    ArticleContentType.QUOTE: {
        'image': {IS_REQUIRED: True, NULLABLE: True, STRUCTURE: PHOTO_VALIDATION_CFG},
        'value': {IS_REQUIRED: True, MAX_LENGTH: 500}
    },
    ArticleContentType.PHRASE: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 200}
    },
    ArticleContentType.LIST: {
        'value': {IS_REQUIRED: True, MAX_LENGTH: 3000}
    },
    ArticleContentType.COLUMNS: {
        'image': {IS_REQUIRED: True, STRUCTURE: PHOTO_VALIDATION_CFG},
        'value': {IS_REQUIRED: True, MAX_LENGTH: 300}
    },
    ArticleContentType.VIDEO: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.AUDIO: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.POST: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.DIALOG: {},
}


class ContentValidator(object):
    @staticmethod
    def validate_structure(structure, field, params):
        if field not in structure:
            if params.get(IS_REQUIRED):
                raise ValidationError('"%(field)s" is required', code=IS_REQUIRED, params={'field': field})
            else:
                return
        if structure[field] is None:
            if not params.get(NULLABLE):
                raise ValidationError('"%(field)s" can\'t be NULL', code=NULLABLE, params={'field': field})
            else:
                return
        if (params.get(MAX_LENGTH) or params.get(MIN_LENGTH)) and not isinstance(structure[field], (str, unicode)):
            raise ValidationError('"%(field)s" must be STRING or UNICODE', code='type', params={'field': field})
        if params.get(MAX_LENGTH) and len(structure[field]) > params.get(MAX_LENGTH):
            raise ValidationError('"%(field)s" value is too long', code=MAX_LENGTH, params={'field': field})
        if params.get(MIN_LENGTH) and len(structure[field]) < params.get(MIN_LENGTH):
            raise ValidationError('"%(field)s" value is too short', code=MIN_LENGTH, params={'field': field})
        if params.get(ANY) and not any([structure[field] == v for v in params[ANY]]):
            raise ValidationError('"%(field)s" value is not one of allowed values', code=ANY, params={'field': field})
        if params.get(TYPE) and not isinstance(structure[field], params.get(TYPE)):
            raise ValidationError('"%(field)s" value is not instance of available types', code=TYPE,
                                  params={'field': field})
        if params.get(STRUCTURE):
            _structure = structure[field]
            for _field, _params in params.get(STRUCTURE).items():
                try:
                    ContentValidator.validate_structure(_structure, _field, _params)
                except:
                    raise ValidationError('"%(field)s" value has not valid structure', code=STRUCTURE,
                                          params={'field': field})
        if params.get(STRUCTURE_LIST):
            if not isinstance(structure[field], list):
                raise ValidationError('"%(field)s" value is not a list', code=STRUCTURE_LIST, params={'field': field})
            for _structure in structure[field]:
                for _field, _params in params.get(STRUCTURE_LIST).items():
                    try:
                        ContentValidator.validate_structure(_structure, _field, _params)
                    except:
                        raise ValidationError('"%(field)s" value has not valid structure list', code=STRUCTURE_LIST,
                                              params={'field': field})

    def _root_validate(self, content):
        for field, params in ROOT_VALIDATION_CFG.items():
            self.validate_structure(content, field, params)

    def __call__(self, content):
        self._root_validate(content)


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
    is_valid = True
    for field, params in ROOT_VALIDATION_CFG.items():
        try:
            ContentValidator.validate_structure(content, field, params)
        except ValidationError as e:
            print e
            is_valid = False
    if is_valid:
        for block in content.get('blocks', []):
            block_is_valid = block.get('__meta', {}).get('is_valid')
            if block_is_valid is not None and not block_is_valid:
                is_valid = False
    content['__meta'] = {'is_valid': is_valid}
    return content
