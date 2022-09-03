from xml.etree.ElementTree import Comment
from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма для создания нового поста"""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }


class CommentForm(forms.ModelForm):
    """Форма для создания комментария"""

    class Meta:
        model = Comment
        fields = ('text',)
