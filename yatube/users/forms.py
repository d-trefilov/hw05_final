from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Contact
from posts.models import User


class CreationForm(UserCreationForm):
    """Форма регистрации"""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class ContactForm(forms.ModelForm):
    """Форма для заполнения данных пользователя"""

    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'body')
