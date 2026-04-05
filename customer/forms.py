from django import forms
from django.utils import timezone

from account.models import KYC
from .models import Portfolio

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            })
        }


class KYCForm(forms.ModelForm):
    class Meta:
        model = KYC
        fields = [
            # Personal info
            'first_name',
            'last_name',
            'date_of_birth',
            'nationality',

            # Identity document
            'document_type',
            'document_number',
            'document_image',

            # Address
            'address',
            'city',
            'country',
            'address_proof',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),

            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'document_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'address_proof': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Required document fields
        if not cleaned_data.get('document_type'):
            self.add_error('document_type', 'Please select a document type.')

        if not cleaned_data.get('document_number'):
            self.add_error('document_number', 'Document number is required.')

        if not cleaned_data.get('document_image'):
            self.add_error('document_image', 'Please upload your identity document.')

        if not cleaned_data.get('address_proof'):
            self.add_error('address_proof', 'Please upload proof of address.')

        return cleaned_data

    def save(self, commit=True):
        kyc = super().save(commit=False)

        # Mark as submitted
        kyc.status = KYC.STATUS_PENDING
        kyc.submitted_at = timezone.now()

        if commit:
            kyc.save()

        return kyc