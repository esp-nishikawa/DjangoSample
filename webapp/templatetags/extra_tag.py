from django import template
register = template.Library()


@register.simple_tag
def replace_query(request, field, value):
    """
    GETパラメータの一部を置き換える
    """
    get_dict = request.GET.copy()
    get_dict[field] = value
    return get_dict.urlencode()
