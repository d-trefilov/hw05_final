from django.core.paginator import Paginator


def paginator_function(request, posts, numb_of_posts):
    """Пагинация."""
    paginator = Paginator(posts, numb_of_posts)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
