from django import forms


class ChangeAuthorNameForm(forms.Form):
    author_name = forms.CharField(max_length=16)
    confirm_password = forms.CharField(max_length=16, widget=forms.PasswordInput)
