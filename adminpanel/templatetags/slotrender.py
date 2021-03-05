from django import template

register = template.Library()

@register.filter
def slot_value_check(obj):
    print(obj)
    return False

@register.simple_tag
def update_variable(value):
    return  value