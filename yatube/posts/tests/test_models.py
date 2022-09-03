import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post
from ..constants import LIMIT_POSTS

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()

small_gif = (
     b'\x47\x49\x46\x38\x39\x61\x02\x00'
     b'\x01\x00\x80\x00\x00\x00\x00\x00'
     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
     b'\x0A\x00\x3B'
)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост',
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(self.group))

    def test_models_names_have_correct_length(self):
        "Проверяем, что __str__ показывает верное количество символов."""
        expected_object_name = self.post.text[:LIMIT_POSTS]
        self.assertEqual(expected_object_name, str(self.post))

    def test_models_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value,
                )

    def test_models_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
