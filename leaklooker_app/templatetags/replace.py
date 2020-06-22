from django import template

register = template.Library()

@register.filter
def replace(value):
    return value.replace("'","")