"""
UI Service — Custom template tags and filters for the store app.
"""
from django import template

register = template.Library()


@register.filter(name="split")
def split_filter(value: str, delimiter: str = ",") -> list:
    """Split a string by delimiter. Usage: {{ "a,b,c"|split:"," }}"""
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter)]


@register.filter(name="get_item")
def get_item(dictionary, key):
    """Get an item from a dictionary by key. Usage: {{ mydict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter(name="subtract")
def subtract(value, arg):
    """Subtract arg from value. Usage: {{ value|subtract:2 }}"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value


@register.filter(name="multiply")
def multiply(value, arg):
    """Multiply value by arg. Usage: {{ value|multiply:2 }}"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value


@register.simple_tag
def url_replace(request, field, value):
    """Replace a single GET param while preserving others.
    Usage: {% url_replace request 'page' 2 %}
    """
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
