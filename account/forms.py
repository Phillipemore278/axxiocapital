from django import forms

from account.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

class UserRegistrationForm(forms.ModelForm):
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = [
            'email',
            'full_name',
            'nick_name',
            "phone",
            'address',
            'state',
            'country',
            'zipcode',
        ]

        labels = {
            'nick_name': 'Username',
            'zipcode': 'Zip / Postal Code',
        }

        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'nick_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number"
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address',
                'rows': 3
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Country'
            }),
            'zipcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter zip code'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match")

        return cleaned_data
    

class BootstrapLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Your Email',
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
        })
    )


class BootstrapPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                # 'placeholder': field.label,
            })

        # Optional: add custom labels
        self.fields['old_password'].label = "Current Password"
        self.fields['new_password1'].label = "New Password"
        self.fields['new_password2'].label = "Confirm New Password"


class AdminCustomerEditForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "full_name",
            "nick_name",
            "email",
            "phone",
            "address",
            "state",
            "country",
            "zipcode",
            "is_active",
            # "can_be_copied",
            "withdraw_status",
        ]

        labels = {
            'nick_name': 'Username',
            'zipcode': 'Zip / Postal Code',
        }

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter full name"
            }),
            "nick_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter username"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter address",
                "rows": 3
            }),
            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter state"
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Country'
            }),
            "zipcode": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter zip code"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "withdraw_status": forms.Select(attrs={
                'class': 'form-control'
            }),
            # "can_be_copied": forms.CheckboxInput(attrs={
            #     "class": "form-check-input"
            # }),
        }