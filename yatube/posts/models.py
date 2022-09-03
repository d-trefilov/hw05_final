from django.db import models
from django.contrib.auth import get_user_model

from .constants import LIMIT_POSTS

User = get_user_model()


class Group(models.Model):
    """Модель для хранения групп постов"""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = 'Группы'
        verbose_name_plural = 'Группы'

    def __str__(self):

        return self.title


class Post(models.Model):
    """Модель для хранения постов"""

    text = models.TextField(
        'Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        verbose_name = 'Посты'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)

    def __str__(self):

        return self.text[:LIMIT_POSTS]


class Comment(models.Model):
    """Модель для хранения комментариев"""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментарий',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Введите комментарий',
    )
    created = models.DateTimeField(
        verbose_name='Дата комментария',
        auto_now_add=True,
    )


class Follow(models.Model):
    """Модель для хранения подписок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='already_following'
            )
        ]
