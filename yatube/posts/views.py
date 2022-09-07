from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    return HttpResponse("Главная страница")


def group_posts(request, text):
    return HttpResponse('Страница, где посты отфильтрованы!'
                        f'<br>и {text}!')
