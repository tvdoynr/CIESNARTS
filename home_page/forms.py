from django import forms
from django.core.validators import RegexValidator


class LoginForm(forms.Form):
    id = forms.CharField(
        max_length=9,
        widget=forms.TextInput(attrs={'style':'max-width:385px'}),
        validators=[
            RegexValidator(
                regex='^[0-9]*$',
                message='Username must be Numeric',
                code='invalid_username'
            ),
        ]
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'style': 'max-width:385px'}))


class RegistrationForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    id = forms.CharField(
        max_length=9,
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
        max_length=9,
        validators=[
            RegexValidator(
                regex='^[0-9]*$',
                message='Username must be Numeric',
                code='invalid_username'
            ),
        ]
    )
