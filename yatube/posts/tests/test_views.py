import shutil
import tempfile
from datetime import date

from django.test import TestCase, Client
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Follow, User
from ..constants import NUMB_OF_POSTS, NUMB_OF_POSTS_TEST, NUMB_OF_POSTS_2
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.strftime('%Y:%B:%D')
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.id
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        self.assertEqual(post_pub_date_0, date.today().strftime('%Y:%B:%D'))
        self.assertEqual(post_author_0, self.user.username)
        self.assertTrue(
            Post.objects.filter(
                text=post_text_0,
                group_id=post_group_0,
                id=post_id_0,
                image=post_image_0,
            ).exists()
        )

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug},
        ))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.strftime('%Y:%B:%D')
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.id
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        self.assertEqual(post_pub_date_0, date.today().strftime('%Y:%B:%D'))
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(response.context.get('group'), self.post.group)
        self.assertTrue(
            Post.objects.filter(
                text=post_text_0,
                group_id=post_group_0,
                id=post_id_0,
                image=post_image_0,
            ).exists()
        )

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user.username},
        ))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.strftime('%Y:%B:%D')
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.id
        post_id_0 = first_object.id
        post_image_0 = first_object.image
        self.assertEqual(post_pub_date_0, date.today().strftime('%Y:%B:%D'))
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(response.context.get('author'), self.user)
        self.assertTrue(
            Post.objects.filter(
                text=post_text_0,
                group_id=post_group_0,
                id=post_id_0,
                image=post_image_0,
            ).exists()
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            )
        )
        response_post_detail = response.context.get('post')
        self.assertEqual(response_post_detail.text, self.post.text)
        self.assertEqual(
            response_post_detail.pub_date.strftime('%Y:%B:%D'),
            date.today().strftime('%Y:%B:%D')
        )
        self.assertEqual(
            response_post_detail.author.username,
            self.user.username,
        )
        self.assertEqual(
            response_post_detail.group.title,
            self.post.group.title,
        )
        self.assertEqual(
            response_post_detail.id,
            self.post.id,
        )
        self.assertEqual(
            response_post_detail.image,
            self.post.image,
        )

    def test_post_incorrect_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        group_new = Group.objects.create(
            title='Другая группа',
            slug='other-slug',
            description='Другое описание',
        )
        post_new = Post.objects.create(
            author=self.user,
            text='Другой пост',
            group=group_new,
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug},
            )
        )
        self.assertNotIn(post_new, response.context['page_obj'].object_list)

    def test_post_create_edit_show_correct_context(self):
        """Шаблон post_create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            )
        )
        response_post_edit = response.context.get('post')
        self.assertEqual(
            response_post_edit.author.username,
            self.user.username,
        )
        self.assertEqual(response_post_edit.text, self.post.text)
        self.assertEqual(response_post_edit.group.title, self.post.group.title)
        self.assertTrue(response.context.get('form'), self.form)
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertIsInstance(response.context.get('is_edit'), bool)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_create',
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_cache(self):
        """Проверка кэширования index."""
        post_new = Post.objects.create(
            author=self.user,
            text='Проверка кэширования',
            group=self.group,
        )
        response1 = self.authorized_client.get(reverse('posts:index'))
        Post.objects.filter(id=post_new.id).delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response1.content, response3.content)

    def test_following(self):
        """Пользователь может подписываться на других пользователей."""
        User.objects.create_user(username='NoName')
        following_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': 'NoName'}),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count + 1)
        self.assertEqual(
            Follow.objects.first().user,
            self.user,
        )
        Follow.objects.filter(id=self.user.id).delete()
        self.assertNotEqual(Follow.objects.count(), following_count + 1)

    def test_followers_new_post(self):
        """Новая запись пользователя появляется в ленте подписчиков."""
        user_follow = User.objects.create_user(username='UserFollow')
        following_count1 = Follow.objects.filter(user=user_follow).count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': 'UserFollow'}),
            follow=True,
        )
        post_new = Post.objects.create(
            author=self.user,
            text='Пост тестирования подписок',
            group=self.group,
        )
        self.assertEqual(
            Follow.objects.count(),
            following_count1 + 1,
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=post_new.text,
            ).exists()
        )

    def test_unfollowers_new_post(self):
        """Новая запись пользователя не появляется в ленте не подписчиков."""
        user_unfollow = User.objects.create_user(username='UserUnFollow')
        following_count = Follow.objects.filter(user=user_unfollow).count()
        post_new = Post.objects.create(
            author=self.user,
            text='Пост тестирования подписок',
            group=self.group,
        )
        self.assertNotEqual(
            Follow.objects.filter(user=user_unfollow).count(),
            following_count + 1,
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=post_new.text,
            ).exists()
        )

    def test_unfollow_user(self):
        """Тест отписки."""
        User.objects.create_user(username='NoName')
        following_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': 'NoName'}),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count + 1)
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': 'NoName'}),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count)

    def test_unfollow_user(self):
        """Дважды подписаться на автора невозможно."""
        User.objects.create_user(username='NoName')
        following_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': 'NoName'}),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count + 1)
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': 'NoName'}),
            follow=True,
        )
        self.assertNotEqual(Follow.objects.count(), following_count + 2)

    def test_unfollow_user(self):
        """Пользователь не может подписаться сам на себя."""
        following_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': 'auth'}),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(NUMB_OF_POSTS_TEST):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_number_of_posts_per_page(self):
        """Проверка количества постов на странице."""
        page_number = {
            (reverse('posts:index')): NUMB_OF_POSTS,
            (reverse('posts:index') + '?page=2'): NUMB_OF_POSTS_2,
            (reverse('posts:group_list', kwargs={
                'slug': self.post.group.slug})): NUMB_OF_POSTS,
            (reverse('posts:group_list', kwargs={
                'slug': self.post.group.slug}) + '?page=2'): NUMB_OF_POSTS_2,
            (reverse('posts:profile', kwargs={
                'username': self.user.username})): NUMB_OF_POSTS,
            (reverse('posts:profile', kwargs={
                'username': self.user.username}) + '?page=2'): NUMB_OF_POSTS_2,
        }
        for page, number in page_number.items():
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(len(response.context['page_obj']), number)

    def test_correct_place_post_in_group_list(self):
        """Пост попал в нужное место на странице group_list."""
        post_new = Post.objects.create(
            author=self.user,
            text='Новый пост',
            group=self.post.group,
        )
        page_post = {
            (reverse('posts:index')): post_new,
            (reverse('posts:group_list', kwargs={
                'slug': self.post.group.slug})): post_new,
            (reverse('posts:profile', kwargs={
                'username': self.user.username})): post_new,
        }
        for page, post in page_post.items():
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    response.context['page_obj'].object_list[0],
                    post,
                )
