from http import HTTPStatus

from django.test import TestCase, Client

from posts.models import Post, Group, User


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

    def test_pages_status_to_authorized_users(self):
        """Cтатус страниц и шаблонов для авторизованных пользователей."""
        url_status = {
            '/': [HTTPStatus.OK, 'posts/index.html'],
            f'/group/{self.group.slug}/': [
                HTTPStatus.OK, 'posts/group_list.html'],
            f'/profile/{self.user.username}/': [
                HTTPStatus.OK, 'posts/profile.html'],
            f'/posts/{self.post.id}/': [
                HTTPStatus.OK, 'posts/post_detail.html'],
            '/create/': [
                HTTPStatus.OK, 'posts/post_create.html'],
            f'/posts/{self.post.id}/edit/': [
                HTTPStatus.OK, 'posts/post_create.html'],
            'unexisting_page/': [HTTPStatus.NOT_FOUND, 'core/404.html'],
        }
        for address, status_template in url_status.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, status_template[0])
                self.assertTemplateUsed(response, status_template[1])

    def test_pages_status_to_unauthorized_users(self):
        """Проверка статуса страниц для не авторизованных пользователей."""
        url_status = {
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
        }
        for address, status in url_status.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status)

    def test_pages_status_to_author_post(self):
        """Проверка статуса страницы для автора поста"""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_status_to_not_author_post(self):
        """Проверка статуса страницы для не автора поста"""
        response = self.client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

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
