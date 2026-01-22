from django import forms
from .models import Person
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            'ari8mosEisagoghs',
            'hmeromhnia_eis',
            'syggrafeas',
            'koha',
            'titlos',
            'ekdoths',
            'ekdosh',
            'etosEkdoshs',
            'toposEkdoshs',
            'sxhma',
            'selides',
            'tomos',
            'troposPromPar',
            'ISBN',
            'sthlh1',
            'sthlh2',
        ]


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(label="")

class PersonManualForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = ['ari8mosEisagoghs']
        widgets = {
            'titlos': forms.Textarea(attrs={'rows': 1}),
            'syggrafeas': forms.Textarea(attrs={'rows': 1}),
            'troposPromPar': forms.Textarea(attrs={'rows': 1}),
            'ekdoths': forms.Textarea(attrs={'rows': 1}),
            'koha': forms.Textarea(attrs={'rows': 1}),
        }

