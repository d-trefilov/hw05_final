from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.guest_client = Client()

    def test_pages_status_to_unauthorized_users(self):
        """Проверка статуса страниц для неавторизованных пользователей."""
        url_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            'unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status in url_status.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status)

    def test_pages_status_to_authorized_users(self):
        """Проверка статуса страниц для авторизованных пользователей."""
        url_status = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
        }
        for address, status in url_status.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_pages_status_to_author_post(self):
        """Проверка статуса страницы для автора поста"""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_status_to_not_author_post(self):
        """Проверка статуса страницы для не автора поста"""
        response = self.client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            'unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_guest_users_to_post_create(self):
        """Проверка переадресации страницы post_create для гостя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_guest_users_to_post_edit(self):
        """Проверка переадресации страницы post_edit для гостя."""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True,
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/',
        )

    def test_authorized_users_to_post_edit(self):
        """Проверка переадресации страницы post_edit для не автора."""
        user1 = User.objects.create_user(username='HasNoName')
        self.guest_client.force_login(user1)
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True,
        )
        self.assertRedirects(
            response,
            f'/posts/{self.post.id}/',
        )

    def test_guest_users_to_post_comment(self):
        """Не авторизованный пользователь не может комментировать посты."""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/',
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/',
        )

    def test_authorized_users_to_post_comment(self):
        """Авторизованный пользователь может комментировать посты."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/',
        )
        self.assertRedirects(
            response,
            f'/posts/{self.post.id}/',
        )
