import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Comment
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст1',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_new = Post.objects.first()
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'auth'},
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post_new.text, form_data['text'])
        self.assertEqual(post_new.group.id, form_data['group'])
        self.assertEqual(post_new.author, self.user)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        group_new = Group.objects.create(
            title='Измененная группа',
            slug='change-slug',
            description='Измененное описание',
        )
        form_data = {
            'text': self.post.text,
            'group': group_new.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_edit.text, form_data['text'])
        self.assertEqual(post_edit.group.id, form_data['group'])
        self.assertEqual(post_edit.author, self.user)

    def test_comment_to_post_detail(self):
        """Комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        comment_new = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий',
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(
            Comment.objects.first().text,
            comment_new.text,
        )
