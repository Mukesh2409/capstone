from django import forms
from django.contrib.auth.forms import UserCreationForm,UserChangeForm,authenticate
from .models import CustomUser,ProfileScan

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    profile_pic = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'profile_pic']


class ProfileScanForm(forms.ModelForm):
    class Meta:
        model = ProfileScan
        fields = ['username', 'bio', 'followers_count', 'following_count', 
                 'is_private', 'posts_count']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'is_private': forms.CheckboxInput(),
        }


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password")
        return cleaned_data

class ProfileEditForm(UserChangeForm):
    password = None  # Remove password field from the form

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_pic', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }