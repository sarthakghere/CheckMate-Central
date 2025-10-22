from django import forms
from .models import College
from users.models import User

class RegisterCollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ['name', 'code']

    
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        code = cleaned_data.get("code")

        if name and College.objects.filter(name=name).exists():
            self.add_error("name", "A college with this name already exists.")

        if code and College.objects.filter(code=code).exists():
            self.add_error("code", "A college with this code already exists.")

        return cleaned_data

class RegisterCollegeUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'is_active': forms.CheckboxInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")

        if email and User.objects.filter(email=email).exists():
            self.add_error("email", "A user with this email already exists.")

        return cleaned_data

class CreateCollegeUserPasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Enter a strong password."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as above, for verification."
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two password fields didn't match.")

        return cleaned_data