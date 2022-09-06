from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from .utils import paginator_function
from .constants import NUMB_OF_POSTS


def index(request):
    """Главная страница."""
    template = 'posts/index.html'
    posts = Post.objects.select_related(
        'author',
        'group',
    )
    context = {
        'page_obj': paginator_function(request, posts, NUMB_OF_POSTS),
    }

    return render(request, template, context)


def group_posts(request, slug):
    """Страница с группами."""
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    posts = Post.objects.filter(group=group)
    context = {
        'group': group,
        'page_obj': paginator_function(request, posts, NUMB_OF_POSTS),
    }

    return render(request, template, context)


def profile(request, username):
    """Страница профайла пользователя."""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    following = Follow.objects.filter(
        user=request.user.id,
        author=author.id,
    ).exists()
    context = {
        'page_obj': paginator_function(request, posts, NUMB_OF_POSTS),
        'author': author,
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    """Страница поста."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = Comment.objects.filter(post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    """Создание нового поста."""
    template = 'posts/post_create.html'
    form = PostForm(request.POST)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect('posts:profile', post.author)

    context = {
        'form': form,
        'is_edit': False,
    }

    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    template = 'posts/post_create.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if request.user != post.author:

        return redirect('posts:post_detail', post_id)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Подписки пользователя."""
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        'follower': request.user,
        'page_obj': paginator_function(request, posts, NUMB_OF_POSTS),
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на пользователя."""
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if (author != request.user) and not follow.exists():
        Follow.objects.create(author=author, user=request.user)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от пользователя."""
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.get(author=author, user=user).delete()
    return redirect('posts:profile', username=username)
