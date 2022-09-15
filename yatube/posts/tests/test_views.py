import shutil
import tempfile
from datetime import date

from django.test import TestCase, Client
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, Follow, User, Comment
from ..constants import NUMB_OF_POSTS, NUMB_OF_POSTS_TEST, NUMB_OF_POSTS_2
from posts.forms import PostForm, CommentForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follow = User.objects.create_user(username='UserFollow')
        cls.user_unfollow = User.objects.create_user(username='UserUnFollow')
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
        self.user_follow_client = Client()
        self.user_follow_client.force_login(PostPagesTests.user_follow)
        self.user_unfollow_client = Client()
        self.user_unfollow_client.force_login(PostPagesTests.user_unfollow)

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

    def test_index_group_list_profile_show_correct_context(self):
        """Шаблоны index, group_list, profile сформированы с правильным
        контекстом."""
        user_new = User.objects.create_user(username='Follower')
        Follow.objects.create(
            user=user_new,
            author=self.user,
        )
        Follow.objects.create(
            user=self.user,
            author=user_new,
        )
        templates_first_object = {
            reverse('posts:index'): ['page_obj', 0],
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}):
                ['page_obj', 0],
            reverse('posts:profile', kwargs={'username': self.user.username}):
                ['page_obj', 0],
        }
        for template, object in templates_first_object.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                element, number = object
                first_object = response.context[element][number]
                self.assertEqual(
                    first_object.pub_date.strftime('%Y:%B:%D'),
                    date.today().strftime('%Y:%B:%D'),
                )
                self.assertEqual(
                    first_object.author,
                    self.user,
                )
                self.assertEqual(self.post.text, first_object.text)
                self.assertEqual(self.post.group, first_object.group)
                self.assertEqual(self.post.id, first_object.id)
                self.assertEqual(self.post.image, first_object.image)
                if template == reverse(
                    'posts:group_list',
                    kwargs={'slug': self.post.group.slug},
                ):
                    self.assertEqual(
                        response.context.get('group'),
                        self.post.group,
                    )
                if template == reverse(
                    'posts:profile',
                    kwargs={'username': self.user.username}
                ):
                    self.assertEqual(
                        self.user.following,
                        first_object.author.following,
                    )
                    self.assertEqual(
                        self.user.follower,
                        first_object.author.follower,
                    )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        comment_new = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Пробный комментарий'
        )
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
            response_post_detail.author,
            self.user,
        )
        self.assertEqual(
            response_post_detail.group,
            self.post.group,
        )
        self.assertEqual(response_post_detail.id, self.post.id)
        self.assertEqual(response_post_detail.image, self.post.image)
        self.assertIn(comment_new, response.context.get('comments'))
        self.assertIsInstance(
            response.context['form'],
            CommentForm,
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
            response_post_edit.author,
            self.user,
        )
        self.assertEqual(response_post_edit.text, self.post.text)
        self.assertEqual(response_post_edit.group, self.post.group)
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
        user_new = User.objects.create_user(username='NoName')
        following_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': user_new.username}
            ),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=user_new
            ).exists()
        )

    def test_followers_new_post(self):
        """Новая запись пользователя появляется в ленте подписчиков."""
        Follow.objects.create(
            user=self.user_follow,
            author=self.user,
        )
        post_new = Post.objects.create(
            author=self.user,
            text='Пост тестирования подписок',
            group=self.group,
        )
        response = self.user_follow_client.get(reverse(
            'posts:follow_index',
        ))
        first_object = response.context['page_obj'][0]
        self.assertEqual(
            first_object.pub_date.strftime('%Y:%B:%D'),
            date.today().strftime('%Y:%B:%D'),
        )
        self.assertEqual(
            first_object.author,
            self.user,
        )
        self.assertEqual(post_new.text, first_object.text)
        self.assertEqual(post_new.group, first_object.group)
        self.assertEqual(post_new.id, first_object.id)
        self.assertEqual(post_new.image, first_object.image)
        self.assertEqual(
            self.user.follower,
            first_object.author.follower,
        )

    def test_unfollowers_new_post(self):
        """Новая запись пользователя не появляется в ленте не подписчиков."""
        Follow.objects.create(
            user=self.user_unfollow,
            author=self.user_follow,
        )
        post_new = Post.objects.create(
            author=self.user,
            text='Пост тестирования подписок',
            group=self.group,
        )
        response = self.user_unfollow_client.get(reverse(
            'posts:follow_index',
        ))
        self.assertNotIn(post_new.text, response.context)

    def test_unfollow_user(self):
        """Тест отписки."""
        following_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user_unfollow,
            author=self.user,
        )
        self.user_unfollow_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username}
            ),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_unfollow,
                author=self.user,
            ).exists()
        )

    def test_impossible_subscribe_to_the_author_twice(self):
        """Дважды подписаться на автора невозможно."""
        following_count = Follow.objects.count()
        self.user_follow_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            ),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count + 1)
        self.user_follow_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            ),
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), following_count + 1)

    def test_user_cannot_subscribe_yourself(self):
        """Пользователь не может подписаться сам на себя."""
        following_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            ),
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

    def test_correct_place_post_in_index_group_list_profile(self):
        """Пост попал в нужное место на странице index, group_list, profile."""
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
