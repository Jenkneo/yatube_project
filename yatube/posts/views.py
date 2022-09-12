from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    template = 'posts/index.html'
    title = 'Это главная страница Yatube'
    context = {
        'title': title,
    }
    #Далее передать context третьим параметром.
    return render(request, template, context)


def group_list(request):
    template = 'posts/group_list.html'
    title = 'Здесь будет информация о группах проекта Yatube'
    context = {
        'title': title,
    }
    return render(request, template, context)
