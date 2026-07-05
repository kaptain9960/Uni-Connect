from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from forum.models import Department


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    role = forms.ChoiceField(choices=[('student', 'Student'), ('lecturer', 'Lecturer')])
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    matric_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'matric_number', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control glass-input'})


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control glass-input'})


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'department', 'matric_number', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control glass-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'bio':
                field.widget.attrs.update({'class': 'form-control glass-input'})


class VerifyOTPForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control glass-input'}))
    otp_code = forms.CharField(max_length=8, widget=forms.TextInput(attrs={'class': 'form-control glass-input'}))


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control glass-input'}))


class PasswordResetConfirmForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control glass-input'}))
    otp_code = forms.CharField(max_length=8, widget=forms.TextInput(attrs={'class': 'form-control glass-input'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control glass-input'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control glass-input'}))
