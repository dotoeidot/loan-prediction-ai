from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User


class UsernamePasswordResetForm(PasswordResetForm):

    email = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter your username',
            'required': True
        })
    )

    def get_users(self, username):
        try:
            user = User.objects.get(
                username=username,
                is_active=True
            )

            if user.has_usable_password():
                yield user

        except User.DoesNotExist:
            return