from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import page_func


POST_ON_PAGE = 10
SMALL_POST_TEXT = 30


def index(request) -> HttpResponse:
    posts = Post.objects.all()

    page_obj = page_func(request, posts, POST_ON_PAGE)
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'page_obj': page_obj,
        'index': True
    }
    return render(request, template, context)


def group_posts(request, slug) -> HttpResponse:
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = page_func(request, posts, POST_ON_PAGE)
    template = 'posts/group_list.html'
    title = f'Записи сообщества {group.title}'
    context = {
        'title': title,
        'group_info': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username) -> HttpResponse:
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author.id
        ).exists()
    else:
        following = None
    posts = Post.objects.filter(author=author)
    page_obj = page_func(request, posts, POST_ON_PAGE)
    title = 'Все посты пользователя ' + author.get_full_name()
    context = {
        'posts_count': posts.count(),
        'author': author,
        'title': title,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    posts_count = Post.objects.filter(author=post.author).only('id').count()
    title = 'Пост ' + post.text[:SMALL_POST_TEXT]
    context = {
        'title': title,
        'post': post,
        'posts_count': posts_count,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request) -> HttpResponse:
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        form.save(commit=False).author_id = request.user.pk
        form.save()
        return redirect('posts:profile', username=request.user)
    title = 'Создание поста'
    context = {
        'title': title,
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    title = 'Редактирование поста'
    context = {
        'title': title,
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Лента'
    posts = Post.objects.filter(
        author__in=request.user.follower.values_list('author')
    )
    page_obj = page_func(request, posts, POST_ON_PAGE)
    context = {
        'title': title,
        'page_obj': page_obj,
        'follow': True
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(
        user=request.user,
        author=author
    ).exists():
        return redirect('posts:profile', username=username)
    if author != request.user:
        Follow.objects.create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = get_object_or_404(
        Follow,
        user=request.user,
        author=author
    )
    following.delete()
    return redirect('posts:profile', username=username)
