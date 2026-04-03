from django import forms
from .models import Transaction, Coin, Wallet
# from customer.models import Portfolio

class CoinForm(forms.ModelForm):
    class Meta:
        model = Coin
        fields = ['name', 'symbol', 'network']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter coin name'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter coin symbol'}),
            'network': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter network (optional)'}),
            # 'icon': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['coin', 'wallet_address']
        widgets = {
            'coin': forms.Select(attrs={'class': 'form-select'}),
            'wallet_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter wallet address'}),
            # 'qr_code': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class CustomerTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'payment_method',
            'currency',
            'amount',
            'note',
            'destination_bank',
            'account_number',
            'wallet_id',
            # 'coin_type',
        ]

        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter note (optional)'}),
            'destination_bank': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Destination Bank'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number'}),
            # 'coin_type': forms.Select(attrs={'class': 'form-select'}),
            'wallet_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet ID'}),
        }

    def __init__(self, *args, transaction_type=None, **kwargs):
        super().__init__(*args, **kwargs)

        # 👇 STORE CONTEXT
        self.transaction_type = transaction_type

        self.fields['currency'].required = False
        self.fields['currency'].initial = 'USD'

        # make all conditional fields optional by default
        self.fields['destination_bank'].required = False
        self.fields['account_number'].required = False
        self.fields['wallet_id'].required = False
        # self.fields['coin_type'].required = False

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")

        # 🚫 Do NOT enforce withdraw rules on deposits
        if self.transaction_type != "WITHDRAW":
            return cleaned_data

        if payment_method == "WIRE":
            if not cleaned_data.get("destination_bank"):
                self.add_error("destination_bank", "Destination bank is required for wire transfer.")
            if not cleaned_data.get("account_number"):
                self.add_error("account_number", "Account number is required for wire transfer.")

        if payment_method == "CRYPTO":
            if not cleaned_data.get("wallet_id"):
                self.add_error("wallet_id", "Wallet ID is required for crypto withdrawals.")
            if not cleaned_data.get("coin_type"):
                self.add_error("coin_type", "Coin type is required for crypto withdrawals.")

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount