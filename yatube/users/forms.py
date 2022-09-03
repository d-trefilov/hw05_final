from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms

from .models import Contact


User = get_user_model()


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
