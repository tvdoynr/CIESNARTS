from django import forms
from django.core.validators import RegexValidator


class LoginForm(forms.Form):
    id = forms.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex='^[0-9]*$',
                message='Username must be Numeric',
                code='invalid_username'
            ),
        ]
    )
    password = forms.CharField(widget=forms.PasswordInput)


class RegistrationForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    id = forms.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex='^[0-9]*$',
                message='Username must be Numeric',
                code='invalid_username'
            ),
        ]
    )
    email = forms.EmailField(
        error_messages={
            'invalid': 'The email format is invalid.',
        }
    )


class ForgotPasswordForm(forms.Form):
    id = forms.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex='^[0-9]*$',
                message='Username must be Numeric',
                code='invalid_username'
            ),
        ]
    )
