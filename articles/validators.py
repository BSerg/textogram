from __future__ import unicode_literals

import json

from django.core.exceptions import ValidationError

from articles import ArticleContentType


class ContentBlockValidationError(Exception):
    def __init__(self, message, _type):
        super(ContentBlockValidationError, self).__init__(message)
        self.type = _type


def validate_content_size(content):
    content_json = json.dumps(content)
    if len(content_json) > 1024*1024:
        raise ValidationError('Content size too large')


# CONTENT STRUCTURE VALIDATOR

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
    'caption': {IS_REQUIRED: False, TYPE: (str, unicode)},
    'size': {IS_REQUIRED: False, TYPE: (str, unicode)}
}

BLOCK_BASE_VALIDATION_CFG = {
    'id': {IS_REQUIRED: True, TYPE: (str, unicode)},
    'type': {IS_REQUIRED: True, ANY: ArticleContentType.__dict__.values()},
}

DIALOG_RECIPIENT_CFG = {

}

ROOT_VALIDATION_CFG = {
    'title': {IS_REQUIRED: True, MAX_LENGTH: 150},
    'cover': {
        IS_REQUIRED: True,
        NULLABLE: True,
        STRUCTURE: PHOTO_VALIDATION_CFG
    },
    'cover_clipped': {
        IS_REQUIRED: False,
        NULLABLE: True,
        STRUCTURE: PHOTO_VALIDATION_CFG
    },
    'blocks': {
        IS_REQUIRED: True,
        STRUCTURE_LIST: BLOCK_BASE_VALIDATION_CFG
    }
}

BLOCKS_VALIDATION_CFG = {
    ArticleContentType.TEXT: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.HEADER: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.LEAD: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.PHOTO: {
        'photos': {IS_REQUIRED: True, STRUCTURE_LIST: PHOTO_VALIDATION_CFG}
    },
    ArticleContentType.QUOTE: {
        'image': {IS_REQUIRED: True, NULLABLE: True, STRUCTURE: PHOTO_VALIDATION_CFG},
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.PHRASE: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.LIST: {
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
    },
    ArticleContentType.COLUMNS: {
        'image': {IS_REQUIRED: True, STRUCTURE: PHOTO_VALIDATION_CFG},
        'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
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
    ArticleContentType.DIALOG: {
        'participants': {
            IS_REQUIRED: True,
            STRUCTURE_LIST: {
                'id': {IS_REQUIRED: True, TYPE: int},
                'avatar': {
                    IS_REQUIRED: True,
                    NULLABLE: True,
                    STRUCTURE: PHOTO_VALIDATION_CFG
                },
                'name': {IS_REQUIRED: True, TYPE: (str, unicode)},
                'is_interviewer': {TYPE: bool}
            }
        },
        'remarks': {
            IS_REQUIRED: True,
            STRUCTURE_LIST: {
                'participant_id': {IS_REQUIRED: True, TYPE: int},
                'value': {IS_REQUIRED: True, TYPE: (str, unicode)}
            }
        }
    },
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
