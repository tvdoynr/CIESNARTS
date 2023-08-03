from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from ckeditor.widgets import CKEditorWidget
from django.db.models import Q
from django.forms import TextInput

from accounts.models import Course, Semester, Profile, Section


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(max_length=16, widget=forms.PasswordInput(
        attrs={'style': 'max-width: 385px'}
    ))
    new_password = forms.CharField(max_length=16, widget=forms.PasswordInput(
        attrs={'style': 'max-width: 385px'}
    ))
    new_password_again = forms.CharField(max_length=16, widget=forms.PasswordInput(
        attrs={'style': 'max-width: 385px'}
    ))

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_again = cleaned_data.get('new_password_again')

        if new_password != new_password_again:
            self.add_error('new_password_again', 'New passwords must match.')


class ChangeEmailForm(forms.Form):
    new_email_address = forms.EmailField(
        widget=forms.TextInput(
            attrs={'style': 'max-width: 385px'}
        ),
        error_messages={
            'invalid': 'The email format is invalid.',
        }
    )
    confirm_password = forms.CharField(max_length=16, widget=forms.PasswordInput(
        attrs={'style': 'max-width: 385px'}
    ))


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
        fields = ['course_id', 'course_name', 'description', 'course_credit', 'semester']
        widgets = {
            'description': CKEditorWidget()
        }


class SectionForm(forms.ModelForm):
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    class Meta:
        model = Section
        fields = ['classroom', 'instructor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = User.objects.filter(profile__user_type='instructor')
        self.fields['instructor'].label_from_instance = self.label_from_instance


class DateInput(forms.DateInput):
    input_type = 'date'


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name', 'start_date', 'finish_date']
        widgets = {
            'name': TextInput(
                attrs={'style': 'max-width: 215px'}
            ),
            'start_date': DateInput(
                attrs={'style': 'max-width: 215px'}
            ),
            'finish_date': DateInput(
                attrs={'style': 'max-width: 215px'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        finish_date = cleaned_data.get('finish_date')

        if start_date and finish_date:
            if start_date > finish_date:
                raise forms.ValidationError(
                    "Finish date should be after the start date."
                )

            overlapping_semesters = Semester.objects.filter(
                Q(start_date__lte=start_date, finish_date__gte=start_date) |
                Q(start_date__lte=finish_date, finish_date__gte=finish_date) |
                Q(start_date__gte=start_date, finish_date__lte=finish_date)
            )
            if overlapping_semesters.exists():
                raise forms.ValidationError(
                    "The new semester's dates overlap with an existing semester!!!"
                )


class ProfileForm(forms.Form):
    profile_picture = forms.ImageField()
