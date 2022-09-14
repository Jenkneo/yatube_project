from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Post, Group


# Create your views here.
def index(request):
    posts = Post.objects.order_by('-pub_date')[:10]
    template = 'posts/index.html'
    title = 'Это главная страница Yatube'
    context = {
        'title': title,
        'posts': posts,
    }
    #Далее передать context третьим параметром.
    return render(request, template, context)


def group_posts(request, group):
    group_info = get_object_or_404(Group, address=group)
    posts = Post.objects.filter(group=group_info).order_by('-pub_date')[:10]
    template = 'posts/group_posts.html'
    title = 'Здесь будет информация о группах проекта Yatube'
    context = {
        'title': title,
        'group_info': group_info,
        'posts': posts,
    }
    return render(request, template, context)
