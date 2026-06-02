from django import template
from django.db import models

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiplie une valeur par un argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def divide(value, arg):
    """Divise une valeur par un argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return value


@register.filter
def sum_attr(items, attr):
    """Calcule la somme d'un attribut sur une liste d'objets"""
    try:
        return sum(getattr(item, attr) if hasattr(item, attr) else item.get(attr) for item in items)
    except (TypeError, AttributeError):
        return 0


@register.filter
def index(items, i):
    """Retourne l'élément à l'index i"""
    try:
        return items[int(i)]
    except (IndexError, TypeError, ValueError):
        return ''


@register.filter
def attr(item, attr_name):
    """Retourne l'attribut d'un objet"""
    try:
        return getattr(item, attr_name, '')
    except AttributeError:
        return ''
