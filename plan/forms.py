from django import forms
from .models import Plan


class PlanForm(forms.ModelForm):

    class Meta:
        model = Plan
        fields = [
            "name",
            "plantype",
            "percent_increment",
            "short_description",
            "long_description",
            "duration_days",
            "min_amount",
            "is_featured",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter plan name"
            }),

            "plantype": forms.Select(attrs={
                "class": "form-select"
            }),

            "percent_increment": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.0001",
                "placeholder": "0.5000"
            }),

            "short_description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter a brief description (max 255 chars)"
            }),

            "long_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Enter a detailed description of the plan"
            }),

            "duration_days": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Optional duration in days"
            }),

            "min_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),

            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }