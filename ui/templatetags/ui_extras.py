from django import template

register = template.Library()

@register.filter
def attr(obj, name: str):
    """{{ obj|attr:'field' }}"""
    return getattr(obj, name, "")
@register.filter
def in_group(user, group_name: str) -> bool:
    try:
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False