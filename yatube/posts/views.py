from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    template = 'posts/index.html'
    return render(request, template)


def group_posts(request, text):
    return HttpResponse('Страница, где посты отфильтрованы!'
                        f'<br>и {text}!')
