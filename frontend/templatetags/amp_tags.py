#! coding: utf-8
from __future__ import unicode_literals
from markdown import markdown
from django import template
from django.template.defaultfilters import stringfilter
register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def marked(value):
    return markdown(value)


@register.filter(is_safe=True)
def remark_html(item, index):
    try:
        remark = item.get('remarks', [])[index]
        participant = [el for el in item['participants'] if el.get('id') == remark.get('participant_id')][0]
        if participant.get('avatar') and participant.get('avatar').get('image'):
            avatar = '<div><amp-img src="%s" width="32" height="32" layout="fixed" /></div>' \
                     % participant['avatar']['image']
        else:
            avatar = '<span>%s</span>' % participant['name'][0]
        item_class = "remark%s" % (" question" if participant.get('is_interviewer') else "")
        return "<div class=\"%s\">%s%s</div>" % (item_class, avatar, remark['value'])

    except (IndexError, KeyError, ValueError) as e:
        print e
        return "<span>?</span>"



