from django.core.paginator import Paginator


def page_func(request, objects, pages: int):
    paginator = Paginator(objects, pages)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
