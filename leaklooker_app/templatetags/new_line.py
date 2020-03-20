from django import template

register = template.Library()

@register.filter
def new_line(value):
    return value.replace(","," <br> ")