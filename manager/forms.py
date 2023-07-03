from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from accounts.models import Course, Semester, Profile, Section


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


class CreateUserForm(forms.Form):
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
    user_type = forms.ChoiceField(
        choices=Profile.USER_TYPE_CHOICES
    )


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['CourseID', 'CourseName', 'Description', 'CourseCredit', 'semester']


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['Classroom', 'Instructors']
        labels = {
            'Classroom': 'Classroom:',
            'Instructors': 'Instructors:',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Instructors'].queryset = User.objects.filter(profile__user_type='instructor')


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


'''class CreateUserForm(forms.Form):
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
    user_type = forms.ChoiceField(
        choices=Profile.USER_TYPE_CHOICES
    )'''