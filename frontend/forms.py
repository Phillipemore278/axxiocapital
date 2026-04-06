from django import forms

TOPIC_CHOICES = [
    ('Withdrawals', 'Withdrawals'),
    ('Deposits', 'Deposits'),
    ('Platform & Tools', 'Platform & Tools'),
    ('Monitoring & Support', 'Monitoring & Support'),
    ('Education & Training', 'Education & Training'),
    ('Other', 'Other'),
]

class ContactForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        label="Your Name",
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter name here', 'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email Address",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address', 'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        label="Phone",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number', 'class': 'form-control'})
    )
    subject = forms.CharField(
        max_length=150,
        label="Organization",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Subject', 'class': 'form-control'})
    )
    topic = forms.ChoiceField(
        choices=TOPIC_CHOICES,
        label="Want to Discuss About",
        required=True,
        widget=forms.Select(attrs={'class': 'selectmenu'})
    )
    message = forms.CharField(
        label="Message",
        required=True,
        widget=forms.Textarea(attrs={'placeholder': 'Message goes here', 'class': 'form-control'})
    )