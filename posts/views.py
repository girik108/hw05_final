from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm
from .shortcuts import get_or_none


User = get_user_model()


#@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related(
        'author', 'group').order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related(
        'author').order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page,
                                          'paginator': paginator})


def profile(request, username):
    """View функция профайла пользователя."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user.is_authenticated and get_or_none(Follow, user=request.user, author=author):
        following = True
    else:
        following = False
    return render(request, 'profile.html',
                  context={'author': author, 'page': page,
                           'paginator': paginator,
                           'following': following})


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.order_by('-created').all()
    form = CommentForm()
    return render(request, 'post.html', {'post': post,
                                         'author': author,
                                         'form': form,
                                         'items': comments})


@login_required
def post_edit(request, username, post_id):
    """View функция редактирования поста."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('post', username, post_id)

    data = {'title': 'Редактировать запись',
            'submit': 'Сохранить'}

    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('post', username, post_id)
    return render(request, 'newpost.html', {'form': form, 'data': data, 'post': post})


@login_required
def new_post(request):
    data = {'title': 'Новая запись',
            'submit': 'Добавить'}
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'newpost.html', {'form': form, 'data': data})


@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    authors = set()
    for f in Follow.objects.filter(user=request.user).select_related('author'):
        authors.add(f.author)
    post_list = Post.objects.filter(
        author__in=authors).order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        follow, created = Follow.objects.get_or_create(
            user=request.user, author=author)
    return redirect('profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_or_none(Follow, user=request.user, author=author)
    if follow:
        follow.delete()
    return redirect('profile', author)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)
