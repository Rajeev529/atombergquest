from django import template

register = template.Library()

@register.filter
def dict_get(dictionary, key):
    """Return value from dictionary by key."""
    if dictionary is None:
        return ''
    return dictionary.get(key, '')