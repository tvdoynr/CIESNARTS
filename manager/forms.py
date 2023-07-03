from django import forms
from django.core.validators import RegexValidator

from accounts.models import Course, Semester, Profile


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(max_length=16, widget=forms.PasswordInput)
    new_password = forms.CharField(max_length=16, widget=forms.PasswordInput)
    new_password_again = forms.CharField(max_length=16, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_again = cleaned_data.get('new_password_again')

        if new_password != new_password_again:
            self.add_error('new_password_again', 'New passwords must match.')


class ChangeEmailForm(forms.Form):
    new_email_address = forms.EmailField(
        error_messages={
            'invalid': 'The email format is invalid.',
        }
    )
    confirm_password = forms.CharField(max_length=16, widget=forms.PasswordInput)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['CourseID', 'CourseName', 'Description', 'CourseCredit', 'semester']


class DateInput(forms.DateInput):
    input_type = 'date'


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'start_date', 'finish_date']
        widgets = {
            'start_date': DateInput(),
            'finish_date': DateInput(),
        }
