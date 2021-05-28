import json

from django import template

register = template.Library()


# register filers for django template
@register.filter
def get_type(value):
    return type(value)


@register.filter
def to_string(value):
    return str(value)


@register.filter
def get_len(value):
    return len(value)


@register.filter(is_safe=True)
def removeObj_id(value):
    for i in value:
        i["_id"] = ""
        i["id"] = str(i["id"])
    return value
