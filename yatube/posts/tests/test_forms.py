import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, User
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


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
        cls.comment = Comment.objects.create(
            text='Первый комментарий',
            post=cls.post,
            author=cls.user,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_old_id = []
        for i in Post.objects.values_list('id', flat=True):
            posts_old_id.append(i)
        posts_count = len(posts_old_id)
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        posts_new = Post.objects.all().exclude(
            id__in=posts_old_id
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'auth'},
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(posts_new.count(), 1)
        self.assertEqual(form_data['text'], posts_new[0].text)
        self.assertEqual(form_data['group'], posts_new[0].group.id)
        self.assertEqual(self.user, posts_new[0].author)
        self.assertEqual(self.post.image, posts_new[0].image)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        group_new = Group.objects.create(
            title='Измененная группа',
            slug='change-slug',
            description='Измененное описание',
        )
        form_data = {
            'text': 'Тестовый текст1',
            'group': group_new.id,
            'image': self.uploaded,
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
        self.assertEqual(post_edit.image, 'posts/small.gif')

    def test_comment_to_post_detail(self):
        """Комментарий появляется на странице поста."""
        comments_old_id = []
        for i in Comment.objects.values_list('id', flat=True):
            comments_old_id.append(i)
        comments_count = len(comments_old_id)
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        comments_new = Comment.objects.all().exclude(
            id__in=comments_old_id
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comments_new.count(), 1)
        self.assertEqual(form_data['text'], comments_new[0].text)
        self.assertEqual(self.user, comments_new[0].author)
